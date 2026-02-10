import { useEffect, useState, useCallback, type FormEvent } from 'react'
import { BookOpen, Eye, Plus, Pencil } from 'lucide-react'
import { api } from '@/lib/api'
import { formatDate } from '@/lib/status'
import { useModal } from '@/components/ui/Modal'
import { useToast } from '@/components/ui/Toast'
import { DataTable, type Column } from '@/components/ui/DataTable'
import type { Course, CourseModule } from '@/types'
import s from '@/styles/shared.module.css'

/* ── Course Form ── */
function CourseForm({
  initial,
  onSubmit,
}: {
  initial?: Partial<Course>
  onSubmit: (data: Record<string, unknown>) => void
}) {
  const [form, setForm] = useState({
    name: initial?.name ?? '',
    description: initial?.description ?? '',
    semester: initial?.semester ?? '',
    total_sessions: initial?.total_sessions ?? '',
    start_date: initial?.start_date?.split('T')[0] ?? '',
    end_date: initial?.end_date?.split('T')[0] ?? '',
    is_active: initial?.is_active ?? true,
  })

  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [key]: e.target.type === 'checkbox' ? (e.target as HTMLInputElement).checked : e.target.value }))

  const handle = (e: FormEvent) => {
    e.preventDefault()
    const data: Record<string, unknown> = { ...form }
    if (data.total_sessions) data.total_sessions = Number(data.total_sessions)
    else delete data.total_sessions
    Object.keys(data).forEach(k => { if (data[k] === '') delete data[k] })
    onSubmit(data)
  }

  return (
    <form onSubmit={handle} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className={s['form-group']}>
        <label className={s['form-label']}>שם הקורס *</label>
        <input className={s.input} value={form.name} onChange={set('name')} required />
      </div>
      <div className={s['form-group']}>
        <label className={s['form-label']}>תיאור</label>
        <textarea className={s.textarea} value={form.description} onChange={set('description')} rows={2} />
      </div>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>סמסטר</label>
          <input className={s.input} value={form.semester} onChange={set('semester')} />
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>סה"כ שיעורים</label>
          <input className={s.input} type="number" value={form.total_sessions} onChange={set('total_sessions')} dir="ltr" />
        </div>
      </div>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>תאריך התחלה</label>
          <input className={s.input} type="date" value={form.start_date} onChange={set('start_date')} dir="ltr" />
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>תאריך סיום</label>
          <input className={s.input} type="date" value={form.end_date} onChange={set('end_date')} dir="ltr" />
        </div>
      </div>
      <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
        <input type="checkbox" checked={form.is_active} onChange={set('is_active')} />
        <span>פעיל</span>
      </label>
      <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>
        {initial?.id ? 'עדכן' : 'צור קורס'}
      </button>
    </form>
  )
}

/* ── Course Detail (modules table) ── */
function CourseDetail({ course }: { course: Course & { modules?: CourseModule[] } }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>שם הקורס</span>
          <span className={s['detail-value']}>{course.name}</span>
        </div>
        {course.description && (
          <div className={s['detail-row']}>
            <span className={s['detail-key']}>תיאור</span>
            <span className={s['detail-value']}>{course.description}</span>
          </div>
        )}
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>סמסטר</span>
          <span className={s['detail-value']}>{course.semester ?? '—'}</span>
        </div>
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>סה"כ שיעורים</span>
          <span className={s['detail-value']}>{course.total_sessions ?? '—'}</span>
        </div>
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>תאריך התחלה</span>
          <span className={s['detail-value']}>{formatDate(course.start_date)}</span>
        </div>
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>תאריך סיום</span>
          <span className={s['detail-value']}>{formatDate(course.end_date)}</span>
        </div>
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>פעיל</span>
          <span className={s['detail-value']}>
            <span className={`${s.badge} ${course.is_active ? s['badge-green'] : s['badge-gray']}`}>
              {course.is_active ? 'פעיל' : 'לא פעיל'}
            </span>
          </span>
        </div>
      </div>

      {/* Modules */}
      <div>
        <h4 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 600 }}>מודולים</h4>
        {course.modules?.length ? (
          <div className={s['table-wrapper']}>
            <table className={s.table}>
              <thead>
                <tr>
                  <th>#</th>
                  <th>שם</th>
                  <th>מס׳ שיעורים</th>
                  <th>שעות</th>
                  <th>תאריך התחלה</th>
                  <th>שעות</th>
                </tr>
              </thead>
              <tbody>
                {course.modules
                  .sort((a, b) => a.module_order - b.module_order)
                  .map(m => (
                    <tr key={m.id}>
                      <td>{m.module_order}</td>
                      <td>{m.name}</td>
                      <td>{m.sessions_count ?? '—'}</td>
                      <td>{m.hours_estimate ?? '—'}</td>
                      <td className={s.muted}>{formatDate(m.start_date)}</td>
                      <td className={s.muted}>
                        {m.start_time && m.end_time ? `${m.start_time}–${m.end_time}` : '—'}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className={s.empty} style={{ padding: 20 }}>
            <span className={s['empty-text']}>לא הוגדרו מודולים</span>
          </div>
        )}
      </div>
    </div>
  )
}

/* ══════════════════════════════════════════════════════════════
   Courses Page
   ══════════════════════════════════════════════════════════════ */
export function CoursesPage() {
  const { openModal, closeModal } = useModal()
  const toast = useToast()

  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(true)

  const fetchCourses = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get<Course[]>('courses')
      setCourses(data)
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה')
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => { fetchCourses() }, [fetchCourses])

  /* ── Create ── */
  const openCreate = () => {
    openModal({
      title: 'קורס חדש',
      size: 'md',
      content: (
        <CourseForm
          onSubmit={async data => {
            try {
              await api.post('courses', data)
              toast.success('קורס נוצר בהצלחה')
              closeModal()
              fetchCourses()
            } catch (err: unknown) {
              toast.error((err as { message?: string }).message ?? 'שגיאה')
            }
          }}
        />
      ),
    })
  }

  /* ── Edit ── */
  const openEdit = (course: Course) => {
    openModal({
      title: `עריכת קורס — ${course.name}`,
      size: 'md',
      content: (
        <CourseForm
          initial={course}
          onSubmit={async data => {
            try {
              await api.patch(`courses/${course.id}`, data)
              toast.success('קורס עודכן')
              closeModal()
              fetchCourses()
            } catch (err: unknown) {
              toast.error((err as { message?: string }).message ?? 'שגיאה')
            }
          }}
        />
      ),
    })
  }

  const openDetail = async (course: Course) => {
    try {
      const full = await api.get<Course & { modules?: CourseModule[] }>(`courses/${course.id}`)
      openModal({
        title: full.name,
        size: 'lg',
        content: <CourseDetail course={full} />,
      })
    } catch {
      toast.error('שגיאה בטעינת קורס')
    }
  }

  const columns: Column<Course>[] = [
    { key: 'name', header: 'שם הקורס' },
    { key: 'semester', header: 'סמסטר', render: r => r.semester ?? '—' },
    { key: 'total_sessions', header: 'שיעורים', render: r => r.total_sessions ?? '—' },
    {
      key: 'is_active',
      header: 'סטטוס',
      render: r => (
        <span className={`${s.badge} ${r.is_active ? s['badge-green'] : s['badge-gray']}`}>
          {r.is_active ? 'פעיל' : 'לא פעיל'}
        </span>
      ),
    },
    { key: 'start_date', header: 'התחלה', render: r => formatDate(r.start_date), className: s.muted },
    {
      key: '_actions',
      header: '',
      render: r => (
        <div style={{ display: 'flex', gap: 4 }}>
          <button className={`${s.btn} ${s['btn-ghost']} ${s['btn-xs']}`} onClick={e => { e.stopPropagation(); openDetail(r) }} title="פרטים">
            <Eye size={14} strokeWidth={1.5} />
          </button>
          <button className={`${s.btn} ${s['btn-ghost']} ${s['btn-xs']}`} onClick={e => { e.stopPropagation(); openEdit(r) }} title="עריכה">
            <Pencil size={14} strokeWidth={1.5} />
          </button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>קורסים</h1>
        <button className={`${s.btn} ${s['btn-primary']}`} onClick={openCreate}>
          <Plus size={16} strokeWidth={1.5} /> קורס חדש
        </button>
      </div>

      <div className={s.card}>
        <DataTable
          columns={columns}
          data={courses}
          loading={loading}
          emptyText="לא נמצאו קורסים"
          emptyIcon={<BookOpen size={40} strokeWidth={1.5} />}
          onRowClick={openDetail}
          keyExtractor={r => r.id}
        />
      </div>
    </div>
  )
}
