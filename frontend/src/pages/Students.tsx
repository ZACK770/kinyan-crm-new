import { useEffect, useState, useCallback } from 'react'
import { Plus, GraduationCap, Eye, ArrowRight, BookOpen } from 'lucide-react'
import { api } from '@/lib/api'
import { getStatus, formatDate, formatCurrency } from '@/lib/status'
import { useModal } from '@/components/ui/Modal'
import { useToast } from '@/components/ui/Toast'
import { SmartTable, type SmartColumn } from '@/components/ui/SmartTable'
import type { Student, Course, Enrollment } from '@/types'
import s from '@/styles/shared.module.css'

function Badge({ entity, value }: { entity: string; value?: string }) {
  const { label, color } = getStatus(entity, value)
  return <span className={`${s.badge} ${s[`badge-${color}`]}`}>{label}</span>
}

/* ── Convert Lead to Student Form ── */
function ConvertForm({ onSubmit, onCancel }: { onSubmit: (leadId: number) => void; onCancel?: () => void }) {
  const [leadId, setLeadId] = useState('')
  return (
    <form onSubmit={e => { e.preventDefault(); onSubmit(Number(leadId)) }} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className={s['form-group']}>
        <label className={s['form-label']}>מזהה ליד</label>
        <input className={s.input} type="number" value={leadId} onChange={e => setLeadId(e.target.value)} required dir="ltr" />
      </div>
      <div style={{ display: 'flex', gap: 8, paddingTop: 8 }}>
        <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>המר לתלמיד</button>
        {onCancel && (
          <button type="button" className={`${s.btn} ${s['btn-secondary']}`} onClick={onCancel}>ביטול</button>
        )}
      </div>
    </form>
  )
}

/* ── Enroll Form ── */
function EnrollForm({ courses, onSubmit }: { courses: Course[]; onSubmit: (courseId: number) => void }) {
  const [courseId, setCourseId] = useState('')
  return (
    <form onSubmit={e => { e.preventDefault(); if (courseId) onSubmit(Number(courseId)) }} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className={s['form-group']}>
        <label className={s['form-label']}>קורס</label>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <select className={s.select} value={courseId} onChange={e => setCourseId(e.target.value)} required style={{ flex: 1 }}>
            <option value="">— בחר קורס —</option>
            {courses.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <button
            type="button"
            className={`${s.btn} ${s['btn-icon']} ${s['btn-ghost']}`}
            title="צור חדש"
            onClick={() => window.open('/courses?create=true', '_blank')}
            style={{ flexShrink: 0, padding: 6 }}
          >
            <Plus size={16} />
          </button>
        </div>
      </div>
      <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>רשום לקורס</button>
    </form>
  )
}

/* ── Student Detail ── */
function StudentDetail({
  student,
  courses,
  onEnroll,
}: {
  student: Student
  courses: Course[]
  onEnroll: () => void
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>שם</span>
          <span className={s['detail-value']}>{student.full_name}</span>
        </div>
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>טלפון</span>
          <span className={s['detail-value']} dir="ltr">{student.phone}</span>
        </div>
        {student.email && (
          <div className={s['detail-row']}>
            <span className={s['detail-key']}>אימייל</span>
            <span className={s['detail-value']} dir="ltr">{student.email}</span>
          </div>
        )}
        {student.city && (
          <div className={s['detail-row']}>
            <span className={s['detail-key']}>עיר</span>
            <span className={s['detail-value']}>{student.city}</span>
          </div>
        )}
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>סטטוס</span>
          <span className={s['detail-value']}><Badge entity="student" value={student.status} /></span>
        </div>
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>סטטוס תשלום</span>
          <span className={s['detail-value']}><Badge entity="payment" value={student.payment_status} /></span>
        </div>
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>סה"כ מחיר</span>
          <span className={s['detail-value']}>{formatCurrency(student.total_price)}</span>
        </div>
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>סה"כ שולם</span>
          <span className={s['detail-value']}>{formatCurrency(student.total_paid)}</span>
        </div>
        {student.id_number && (
          <div className={s['detail-row']}>
            <span className={s['detail-key']}>ת.ז.</span>
            <span className={s['detail-value']} dir="ltr">{student.id_number}</span>
          </div>
        )}
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>תאריך הצטרפות</span>
          <span className={s['detail-value']}>{formatDate(student.created_at)}</span>
        </div>
      </div>

      {/* Enrollments */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h4 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>הרשמות</h4>
          <button className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`} onClick={onEnroll}>
            <BookOpen size={14} strokeWidth={1.5} /> רשום לקורס
          </button>
        </div>
        {student.enrollments?.length ? (
          <div className={s['table-wrapper']}>
            <table className={s.table}>
              <thead>
                <tr>
                  <th>קורס</th>
                  <th>סטטוס</th>
                  <th>מודול נוכחי</th>
                  <th>שיעורים שנותרו</th>
                </tr>
              </thead>
              <tbody>
                {student.enrollments.map((en: Enrollment) => {
                  const course = courses.find(c => c.id === en.course_id)
                  return (
                    <tr key={en.id}>
                      <td>{course?.name ?? `קורס #${en.course_id}`}</td>
                      <td><Badge entity="enrollment" value={en.status} /></td>
                      <td>{en.current_module} / {en.total_modules ?? '—'}</td>
                      <td>{en.sessions_remaining ?? '—'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className={s.empty} style={{ padding: 20 }}>
            <span className={s['empty-text']}>לא רשום לקורסים</span>
          </div>
        )}
      </div>
    </div>
  )
}

/* ══════════════════════════════════════════════════════════════
   Students Page
   ══════════════════════════════════════════════════════════════ */
export function StudentsPage() {
  const { openModal, closeModal } = useModal()
  const toast = useToast()

  const [students, setStudents] = useState<Student[]>([])
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(true)

  // Workspace view state
  type ViewMode = 'list' | 'convert'
  const [viewMode, setViewMode] = useState<ViewMode>('list')

  const backToList = () => setViewMode('list')

  const fetchStudents = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get<Student[]>('students?limit=200')
      setStudents(data)
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה')
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => { fetchStudents() }, [fetchStudents])
  useEffect(() => { api.get<Course[]>('courses').then(setCourses).catch(() => {}) }, [])

  /* Detail */
  const openDetail = async (stu: Student) => {
    try {
      const full = await api.get<Student>(`students/${stu.id}`)
      showDetail(full)
    } catch { toast.error('שגיאה') }
  }

  const showDetail = (stu: Student) => {
    openModal({
      title: stu.full_name,
      size: 'lg',
      content: (
        <StudentDetail
          student={stu}
          courses={courses}
          onEnroll={() => { closeModal(); openEnroll(stu) }}
        />
      ),
    })
  }

  /* Enroll */
  const openEnroll = (stu: Student) => {
    openModal({
      title: `רישום ${stu.full_name} לקורס`,
      size: 'sm',
      content: (
        <EnrollForm
          courses={courses}
          onSubmit={async courseId => {
            try {
              await api.post(`students/${stu.id}/enroll`, { course_id: courseId })
              toast.success('נרשם בהצלחה')
              closeModal()
              fetchStudents()
            } catch (err: unknown) { toast.error((err as { message?: string }).message ?? 'שגיאה') }
          }}
        />
      ),
    })
  }

  /* Convert lead */
  const openConvert = () => {
    setViewMode('convert')
  }

  const handleInlineUpdate = async (stu: Student, field: string, value: unknown) => {
    try {
      await api.patch(`students/${stu.id}`, { [field]: value })
      toast.success('עודכן')
      setStudents(prev => prev.map(s => s.id === stu.id ? { ...s, [field]: value } : s))
    } catch { toast.error('שגיאה בעדכון') }
  }

  const columns: SmartColumn<Student>[] = [
    { 
      key: 'full_name', 
      header: 'שם מלא', 
      type: 'text',
      sortable: true,
      filterable: true,
      render: (r) => (
        <span style={{ fontWeight: 600, color: 'var(--color-primary)', cursor: 'pointer' }} onClick={() => openDetail(r)}>
          {r.full_name}
        </span>
      )
    },
    { 
      key: 'phone', 
      header: 'טלפון', 
      type: 'text',
      className: s.mono, 
      renderView: r => <span dir="ltr">{r.phone}</span>,
      editable: false
    },
    { 
      key: 'status', 
      header: 'סטטוס', 
      type: 'select',
      options: [
        { value: 'active', label: 'פעיל' },
        { value: 'inactive', label: 'לא פעיל' },
        { value: 'graduated', label: 'סיים' },
      ],
      renderView: r => <Badge entity="student" value={r.status} />
    },
    { 
      key: 'payment_status', 
      header: 'תשלום', 
      type: 'select',
      options: [
        { value: 'paid', label: 'שולם' },
        { value: 'partial', label: 'חלקי' },
        { value: 'pending', label: 'ממתין' },
        { value: 'not_paid', label: 'לא שולם' },
      ],
      renderView: r => <Badge entity="payment" value={r.payment_status} />
    },
    { 
      key: 'total_paid', 
      header: 'שולם', 
      type: 'currency',
      renderView: r => formatCurrency(r.total_paid),
      editable: false
    },
    { 
      key: 'created_at', 
      header: 'הצטרפות', 
      type: 'date',
      className: s.muted,
      renderView: r => formatDate(r.created_at),
      editable: false
    },
    {
      key: '_actions',
      header: '',
      type: 'text',
      width: 50,
      render: r => (
        <button className={`${s.btn} ${s['btn-ghost']} ${s['btn-xs']}`} onClick={e => { e.stopPropagation(); openDetail(r) }}>
          <Eye size={14} strokeWidth={1.5} />
        </button>
      ),
    },
  ]

  /* ── Workspace: convert lead ── */
  if (viewMode === 'convert') {
    return (
      <div>
        <div className={s['page-header']}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button className={`${s.btn} ${s['btn-ghost']}`} onClick={backToList} style={{ padding: '6px 10px' }}>
              <ArrowRight size={18} /> חזרה לרשימה
            </button>
            <h1 className={s['page-title']} style={{ fontSize: '1.2rem' }}>המרת ליד לתלמיד</h1>
          </div>
        </div>
        <div className={s.card} style={{ padding: 24, maxWidth: 600 }}>
          <ConvertForm
            onSubmit={async leadId => {
              try {
                await api.post('students/convert', { lead_id: leadId })
                toast.success('ליד הומר לתלמיד')
                fetchStudents()
                backToList()
              } catch (err: unknown) {
                toast.error((err as { message?: string }).message ?? 'שגיאה')
              }
            }}
            onCancel={backToList}
          />
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>תלמידים</h1>
        <div className={s['page-actions']}>
          <button className={`${s.btn} ${s['btn-secondary']}`} onClick={openConvert}>
            המר ליד
          </button>
          <button className={`${s.btn} ${s['btn-primary']}`} onClick={openConvert}>
            <Plus size={16} strokeWidth={1.5} /> תלמיד חדש
          </button>
        </div>
      </div>

      <div className={s.card}>
        <SmartTable
          columns={columns}
          data={students}
          loading={loading}
          emptyText="לא נמצאו תלמידים"
          emptyIcon={<GraduationCap size={40} strokeWidth={1.5} />}
          onRowClick={openDetail}
          keyExtractor={r => r.id}
          storageKey="students_table_v1"
          onUpdate={handleInlineUpdate}
        />
      </div>
    </div>
  )
}
