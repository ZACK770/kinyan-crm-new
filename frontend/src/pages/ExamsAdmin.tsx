import { useCallback, useEffect, useMemo, useState } from 'react'
import { BookOpen, Calendar, Plus, Trash2 } from 'lucide-react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import { SmartTable, type SmartColumn } from '@/components/ui/SmartTable'
import type { Course, Exam, ExamDate } from '@/types'
import s from '@/styles/shared.module.css'

type TabKey = 'exams' | 'dates'

type ExamFormState = {
  name: string
  course_id: string
  exam_type: string
  lecturer_id: string
  exam_date: string
  questionnaire_url: string
  answers_url: string
  material: string
  registration_price: string
  registration_url: string
  is_registration_open: boolean
}

type ExamDateFormState = {
  date: string
  description: string
  is_active: boolean
  max_registrations: string
}

function toExamForm(exam: Exam | null): ExamFormState {
  return {
    name: exam?.name ?? '',
    course_id: exam?.course_id != null ? String(exam.course_id) : '',
    exam_type: exam?.exam_type ?? 'בכתב',
    lecturer_id: exam?.lecturer_id != null ? String(exam.lecturer_id) : '',
    exam_date: exam?.exam_date ?? '',
    questionnaire_url: exam?.questionnaire_url ?? '',
    answers_url: exam?.answers_url ?? '',
    material: exam?.material ?? '',
    registration_price: exam?.registration_price != null ? String(exam.registration_price) : '',
    registration_url: exam?.registration_url ?? '',
    is_registration_open: exam?.is_registration_open !== false,
  }
}

function toExamDateForm(ed: ExamDate | null): ExamDateFormState {
  return {
    date: ed?.date ?? '',
    description: ed?.description ?? '',
    is_active: ed?.is_active ?? true,
    max_registrations: ed?.max_registrations != null ? String(ed.max_registrations) : '',
  }
}

export function ExamsAdminPage() {
  const toast = useToast()

  const [tab, setTab] = useState<TabKey>('exams')

  const [courses, setCourses] = useState<Course[]>([])

  const [exams, setExams] = useState<Exam[]>([])
  const [loadingExams, setLoadingExams] = useState(false)
  const [examView, setExamView] = useState<'list' | 'create' | 'edit' | 'assign'>('list')
  const [selectedExam, setSelectedExam] = useState<Exam | null>(null)

  const [examDates, setExamDates] = useState<ExamDate[]>([])
  const [loadingDates, setLoadingDates] = useState(false)
  const [dateView, setDateView] = useState<'list' | 'create' | 'edit' | 'assign'>('list')
  const [selectedDate, setSelectedDate] = useState<ExamDate | null>(null)

  const [assignedExams, setAssignedExams] = useState<Exam[]>([])
  const [assignExamId, setAssignExamId] = useState<string>('')
  const [loadingAssignments, setLoadingAssignments] = useState(false)

  const [formExam, setFormExam] = useState<ExamFormState>(() => toExamForm(null))
  const [savingExam, setSavingExam] = useState(false)

  const [formDate, setFormDate] = useState<ExamDateFormState>(() => toExamDateForm(null))
  const [savingDate, setSavingDate] = useState(false)

  const fetchCourses = useCallback(async () => {
    try {
      const data = await api.get<Course[]>('courses')
      setCourses(data)
    } catch {
      // ignore
    }
  }, [])

  const fetchExams = useCallback(async () => {
    setLoadingExams(true)
    try {
      const data = await api.get<Exam[]>('exams?limit=1000')
      setExams(data)
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בטעינת מבחנים')
    } finally {
      setLoadingExams(false)
    }
  }, [toast])

  const fetchExamDates = useCallback(async () => {
    setLoadingDates(true)
    try {
      const data = await api.get<ExamDate[]>('exams/exam-dates?limit=2000')
      setExamDates(data)
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בטעינת מועדים')
    } finally {
      setLoadingDates(false)
    }
  }, [toast])

  const fetchAssignments = useCallback(async (examDateId: number) => {
    setLoadingAssignments(true)
    try {
      const data = await api.get<Exam[]>(`exams/exam-dates/${examDateId}/exams`)
      setAssignedExams(data)
    } catch {
      setAssignedExams([])
    } finally {
      setLoadingAssignments(false)
    }
  }, [])

  useEffect(() => {
    fetchCourses()
    fetchExams()
    fetchExamDates()
  }, [fetchCourses, fetchExams, fetchExamDates])

  useEffect(() => {
    if (selectedDate && dateView === 'assign') {
      fetchAssignments(selectedDate.id)
    }
  }, [selectedDate, dateView, fetchAssignments])

  const courseNameById = useMemo(() => {
    const m = new Map<number, string>()
    for (const c of courses) m.set(c.id, c.name)
    return m
  }, [courses])

  const openCreateExam = () => {
    setSelectedExam(null)
    setFormExam(toExamForm(null))
    setExamView('create')
  }

  const openEditExam = (row: Exam) => {
    setSelectedExam(row)
    setFormExam(toExamForm(row))
    setExamView('edit')
  }

  const backToExamList = () => {
    setSelectedExam(null)
    setExamView('list')
  }

  const openCreateDate = () => {
    setSelectedDate(null)
    setFormDate(toExamDateForm(null))
    setDateView('create')
  }

  const openEditDate = (row: ExamDate) => {
    setSelectedDate(row)
    setFormDate(toExamDateForm(row))
    setDateView('edit')
  }

  const openAssignDate = (row: ExamDate) => {
    setSelectedDate(row)
    setAssignExamId('')
    setDateView('assign')
  }

  const backToDateList = () => {
    setSelectedDate(null)
    setDateView('list')
  }

  const saveExam = async () => {
    if (!formExam.name.trim()) {
      toast.error('שם מבחן הוא שדה חובה')
      return
    }
    if (!formExam.course_id) {
      toast.error('חובה לבחור קורס')
      return
    }

    const payload: Record<string, unknown> = {
      name: formExam.name.trim(),
      course_id: Number(formExam.course_id),
      exam_type: formExam.exam_type || 'בכתב',
      lecturer_id: formExam.lecturer_id ? Number(formExam.lecturer_id) : null,
      exam_date: formExam.exam_date || null,
      questionnaire_url: formExam.questionnaire_url || null,
      answers_url: formExam.answers_url || null,
      material: formExam.material || null,
      registration_price: formExam.registration_price ? Number(formExam.registration_price) : null,
      registration_url: formExam.registration_url || null,
      is_registration_open: !!formExam.is_registration_open,
    }

    setSavingExam(true)
    try {
      if (examView === 'create') {
        await api.post('exams', payload)
        toast.success('נוצר בהצלחה')
      } else if (examView === 'edit' && selectedExam) {
        await api.patch(`exams/${selectedExam.id}`, payload)
        toast.success('עודכן בהצלחה')
      }
      await fetchExams()
      backToExamList()
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בשמירה')
    } finally {
      setSavingExam(false)
    }
  }

  const deleteExam = async (row: Exam) => {
    const ok = window.confirm(`למחוק את המבחן "${row.name}"?`)
    if (!ok) return
    try {
      await api.delete(`exams/${row.id}`)
      toast.success('נמחק בהצלחה')
      fetchExams()
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה במחיקה')
    }
  }

  const saveDate = async () => {
    if (!formDate.date) {
      toast.error('תאריך הוא שדה חובה')
      return
    }

    const payload: Record<string, unknown> = {
      date: formDate.date,
      description: formDate.description || null,
      is_active: !!formDate.is_active,
      max_registrations: formDate.max_registrations ? Number(formDate.max_registrations) : null,
    }

    setSavingDate(true)
    try {
      if (dateView === 'create') {
        await api.post('exams/exam-dates', payload)
        toast.success('נוצר בהצלחה')
      } else if (dateView === 'edit' && selectedDate) {
        await api.patch(`exams/exam-dates/${selectedDate.id}`, payload)
        toast.success('עודכן בהצלחה')
      }
      await fetchExamDates()
      backToDateList()
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בשמירה')
    } finally {
      setSavingDate(false)
    }
  }

  const deleteDate = async (row: ExamDate) => {
    const ok = window.confirm(`למחוק את המועד ${row.date}?`)
    if (!ok) return
    try {
      await api.delete(`exams/exam-dates/${row.id}`)
      toast.success('נמחק בהצלחה')
      fetchExamDates()
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה במחיקה')
    }
  }

  const assignExamToDate = async () => {
    if (!selectedDate) return
    if (!assignExamId) {
      toast.error('בחר מבחן לשיוך')
      return
    }

    try {
      await api.post(`exams/exam-dates/${selectedDate.id}/exams`, { exam_id: Number(assignExamId) })
      toast.success('שויך בהצלחה')
      fetchAssignments(selectedDate.id)
      setAssignExamId('')
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בשיוך')
    }
  }

  const unassignExamFromDate = async (examId: number) => {
    if (!selectedDate) return
    try {
      await api.delete(`exams/exam-dates/${selectedDate.id}/exams/${examId}`)
      toast.success('הוסר שיוך')
      fetchAssignments(selectedDate.id)
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בהסרת שיוך')
    }
  }

  const examColumns: SmartColumn<Exam>[] = [
    { key: 'name', header: 'שם', type: 'text', sortable: true },
    {
      key: 'course_id',
      header: 'קורס',
      type: 'text',
      render: (r) => courseNameById.get(r.course_id) ?? String(r.course_id),
      sortable: true,
    },
    { key: 'exam_type', header: 'סוג', type: 'text', render: r => r.exam_type ?? '—' },
    { key: 'exam_date', header: 'תאריך', type: 'date', render: r => r.exam_date ?? '—', className: s.muted },
    { key: 'registration_price', header: 'מחיר', type: 'currency', render: r => r.registration_price ?? null, className: s.muted },
    { key: 'is_registration_open', header: 'פתוח', type: 'boolean', render: r => r.is_registration_open !== false },
    {
      key: '_actions',
      header: 'פעולות',
      type: 'text',
      sortable: false,
      render: (r) => (
        <div style={{ display: 'flex', gap: 8 }} onClick={(e) => e.stopPropagation()}>
          <button className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`} onClick={() => openEditExam(r)}>
            עריכה
          </button>
          <button className={`${s.btn} ${s['btn-danger']} ${s['btn-sm']}`} onClick={() => deleteExam(r)} title="מחיקה">
            <Trash2 size={14} />
          </button>
        </div>
      ),
    },
  ]

  const dateColumns: SmartColumn<ExamDate>[] = [
    { key: 'date', header: 'תאריך', type: 'date', sortable: true },
    { key: 'description', header: 'תיאור', type: 'text', render: r => r.description ?? '—', className: s.muted },
    { key: 'is_active', header: 'פעיל', type: 'boolean', render: r => r.is_active },
    { key: 'max_registrations', header: 'קיבולת', type: 'number', render: r => r.max_registrations ?? '—', className: s.muted },
    {
      key: '_actions',
      header: 'פעולות',
      type: 'text',
      sortable: false,
      render: (r) => (
        <div style={{ display: 'flex', gap: 8 }} onClick={(e) => e.stopPropagation()}>
          <button className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`} onClick={() => openEditDate(r)}>
            עריכה
          </button>
          <button className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`} onClick={() => openAssignDate(r)}>
            שיוכים
          </button>
          <button className={`${s.btn} ${s['btn-danger']} ${s['btn-sm']}`} onClick={() => deleteDate(r)}>
            <Trash2 size={14} />
          </button>
        </div>
      ),
    },
  ]

  const renderTabs = () => (
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
      <button
        className={`${s.btn} ${tab === 'exams' ? s['btn-primary'] : s['btn-secondary']}`}
        onClick={() => { setTab('exams'); backToExamList(); backToDateList() }}
      >
        <BookOpen size={16} />
        מבחנים
      </button>
      <button
        className={`${s.btn} ${tab === 'dates' ? s['btn-primary'] : s['btn-secondary']}`}
        onClick={() => { setTab('dates'); backToExamList(); backToDateList() }}
      >
        <Calendar size={16} />
        מועדי בחינה
      </button>
    </div>
  )

  const renderExamForm = () => (
    <div className={s.card}>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>{examView === 'create' ? 'מבחן חדש' : `עריכת מבחן: ${selectedExam?.name ?? ''}`}</h1>
        <button className={`${s.btn} ${s['btn-secondary']}`} onClick={backToExamList}>
          חזרה
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div className={s['form-row']}>
          <div className={s['form-group']}>
            <label className={s['form-label']}>שם *</label>
            <input className={s.input} value={formExam.name} onChange={(e) => setFormExam(p => ({ ...p, name: e.target.value }))} />
          </div>
          <div className={s['form-group']}>
            <label className={s['form-label']}>קורס *</label>
            <select className={s.select} value={formExam.course_id} onChange={(e) => setFormExam(p => ({ ...p, course_id: e.target.value }))}>
              <option value="">— בחר —</option>
              {courses.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div className={s['form-row']}>
          <div className={s['form-group']}>
            <label className={s['form-label']}>סוג</label>
            <input className={s.input} value={formExam.exam_type} onChange={(e) => setFormExam(p => ({ ...p, exam_type: e.target.value }))} />
          </div>
          <div className={s['form-group']}>
            <label className={s['form-label']}>תאריך (אופציונלי)</label>
            <input className={s.input} type="date" value={formExam.exam_date} onChange={(e) => setFormExam(p => ({ ...p, exam_date: e.target.value }))} />
          </div>
        </div>

        <div className={s['form-row']}>
          <div className={s['form-group']}>
            <label className={s['form-label']}>מחיר הרשמה</label>
            <input className={s.input} type="number" value={formExam.registration_price} onChange={(e) => setFormExam(p => ({ ...p, registration_price: e.target.value }))} />
          </div>
          <div className={s['form-group']}>
            <label className={s['form-label']}>הרשמה פתוחה?</label>
            <label className={s['checkbox-label']}>
              <input
                type="checkbox"
                checked={formExam.is_registration_open}
                onChange={(e) => setFormExam(p => ({ ...p, is_registration_open: e.target.checked }))}
              />
              פתוח
            </label>
          </div>
        </div>

        <div className={s['form-group']}>
          <label className={s['form-label']}>לינק הרשמה</label>
          <input className={s.input} value={formExam.registration_url} onChange={(e) => setFormExam(p => ({ ...p, registration_url: e.target.value }))} dir="ltr" />
        </div>

        <div className={s['form-group']}>
          <label className={s['form-label']}>שאלון (URL)</label>
          <input className={s.input} value={formExam.questionnaire_url} onChange={(e) => setFormExam(p => ({ ...p, questionnaire_url: e.target.value }))} dir="ltr" />
        </div>

        <div className={s['form-group']}>
          <label className={s['form-label']}>תשובות (URL)</label>
          <input className={s.input} value={formExam.answers_url} onChange={(e) => setFormExam(p => ({ ...p, answers_url: e.target.value }))} dir="ltr" />
        </div>

        <div className={s['form-group']}>
          <label className={s['form-label']}>חומר (פנימי)</label>
          <textarea className={s.textarea} rows={3} value={formExam.material} onChange={(e) => setFormExam(p => ({ ...p, material: e.target.value }))} />
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <button className={`${s.btn} ${s['btn-primary']}`} onClick={saveExam} disabled={savingExam}>
            {savingExam ? 'שומר...' : 'שמור'}
          </button>
          <button className={`${s.btn} ${s['btn-secondary']}`} onClick={backToExamList} disabled={savingExam}>
            ביטול
          </button>
        </div>
      </div>
    </div>
  )

  const renderDateForm = () => (
    <div className={s.card}>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>{dateView === 'create' ? 'מועד בחינה חדש' : `עריכת מועד: ${selectedDate?.date ?? ''}`}</h1>
        <button className={`${s.btn} ${s['btn-secondary']}`} onClick={backToDateList}>
          חזרה
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div className={s['form-row']}>
          <div className={s['form-group']}>
            <label className={s['form-label']}>תאריך *</label>
            <input className={s.input} type="date" value={formDate.date} onChange={(e) => setFormDate(p => ({ ...p, date: e.target.value }))} />
          </div>
          <div className={s['form-group']}>
            <label className={s['form-label']}>קיבולת</label>
            <input className={s.input} type="number" value={formDate.max_registrations} onChange={(e) => setFormDate(p => ({ ...p, max_registrations: e.target.value }))} />
          </div>
        </div>

        <div className={s['form-group']}>
          <label className={s['form-label']}>תיאור</label>
          <input className={s.input} value={formDate.description} onChange={(e) => setFormDate(p => ({ ...p, description: e.target.value }))} />
        </div>

        <div className={s['form-group']}>
          <label className={s['form-label']}>סטטוס</label>
          <label className={s['checkbox-label']}>
            <input type="checkbox" checked={formDate.is_active} onChange={(e) => setFormDate(p => ({ ...p, is_active: e.target.checked }))} />
            פעיל
          </label>
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <button className={`${s.btn} ${s['btn-primary']}`} onClick={saveDate} disabled={savingDate}>
            {savingDate ? 'שומר...' : 'שמור'}
          </button>
          <button className={`${s.btn} ${s['btn-secondary']}`} onClick={backToDateList} disabled={savingDate}>
            ביטול
          </button>
        </div>
      </div>
    </div>
  )

  const renderAssign = () => (
    <div className={s.card}>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>שיוך מבחנים למועד: {selectedDate?.date}</h1>
        <button className={`${s.btn} ${s['btn-secondary']}`} onClick={backToDateList}>חזרה</button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div className={s['form-row']}>
          <div className={s['form-group']}>
            <label className={s['form-label']}>בחר מבחן לשיוך</label>
            <select className={s.select} value={assignExamId} onChange={(e) => setAssignExamId(e.target.value)}>
              <option value="">— בחר —</option>
              {exams.map(ex => (
                <option key={ex.id} value={ex.id}>
                  {courseNameById.get(ex.course_id) ? `${courseNameById.get(ex.course_id)} • ` : ''}{ex.name}
                </option>
              ))}
            </select>
          </div>
          <div className={s['form-group']}>
            <label className={s['form-label']}>&nbsp;</label>
            <button className={`${s.btn} ${s['btn-primary']}`} onClick={assignExamToDate} disabled={loadingAssignments}>
              הוסף
            </button>
          </div>
        </div>

        <div className={s.card} style={{ padding: 0 }}>
          <div style={{ padding: 12, borderBottom: '1px solid var(--border)' }}>
            <b>משויכים ({assignedExams.length})</b>
          </div>
          {loadingAssignments ? (
            <div style={{ padding: 16, color: 'var(--color-text-muted)' }}>טוען...</div>
          ) : assignedExams.length === 0 ? (
            <div style={{ padding: 16, color: 'var(--color-text-muted)' }}>אין מבחנים משויכים</div>
          ) : (
            <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
              {assignedExams.map(a => (
                <div key={a.id} style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'center', border: '1px solid var(--border)', borderRadius: 8, padding: 10 }}>
                  <div>
                    <div style={{ fontWeight: 700 }}>
                      {courseNameById.get(a.course_id) ? `${courseNameById.get(a.course_id)} • ` : ''}{a.name}
                    </div>
                    <div className={s.muted} style={{ fontSize: 12 }}>
                      {a.exam_type || '—'}{typeof a.registration_price === 'number' ? ` • ₪${a.registration_price}` : ''}{a.is_registration_open === false ? ' • הרשמה סגורה' : ''}
                    </div>
                  </div>
                  <button className={`${s.btn} ${s['btn-danger']} ${s['btn-sm']}`} onClick={() => unassignExamFromDate(a.id)}>
                    הסר
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )

  const renderExamsList = () => (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>מבחנים</h1>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {renderTabs()}
          <button className={`${s.btn} ${s['btn-primary']}`} onClick={openCreateExam}>
            <Plus size={16} /> מבחן חדש
          </button>
        </div>
      </div>

      <div className={s.card}>
        <SmartTable
          columns={examColumns}
          data={exams}
          loading={loadingExams}
          emptyText="לא נמצאו מבחנים"
          emptyIcon={<BookOpen size={40} strokeWidth={1.5} />}
          onRowClick={openEditExam}
          keyExtractor={r => r.id}
          storageKey="admin_exams"
        />
      </div>
    </div>
  )

  const renderDatesList = () => (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>מועדי בחינה</h1>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {renderTabs()}
          <button className={`${s.btn} ${s['btn-primary']}`} onClick={openCreateDate}>
            <Plus size={16} /> מועד חדש
          </button>
        </div>
      </div>

      <div className={s.card}>
        <SmartTable
          columns={dateColumns}
          data={examDates}
          loading={loadingDates}
          emptyText="לא נמצאו מועדים"
          emptyIcon={<Calendar size={40} strokeWidth={1.5} />}
          onRowClick={openAssignDate}
          keyExtractor={r => r.id}
          storageKey="admin_exam_dates"
        />
      </div>
    </div>
  )

  const renderExamsTab = () => {
    if (examView === 'create' || examView === 'edit') return renderExamForm()
    return renderExamsList()
  }

  const renderDatesTab = () => {
    if (dateView === 'create' || dateView === 'edit') return renderDateForm()
    if (dateView === 'assign') return renderAssign()
    return renderDatesList()
  }

  return (
    <div>
      {tab === 'exams' ? renderExamsTab() : renderDatesTab()}
    </div>
  )
}
