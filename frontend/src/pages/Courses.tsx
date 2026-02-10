import { useEffect, useState, useCallback } from 'react'
import { BookOpen, Eye } from 'lucide-react'
import { api } from '@/lib/api'
import { formatDate } from '@/lib/status'
import { useModal } from '@/components/ui/Modal'
import { useToast } from '@/components/ui/Toast'
import { DataTable, type Column } from '@/components/ui/DataTable'
import type { Course, CourseModule } from '@/types'
import s from '@/styles/shared.module.css'

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
  const { openModal } = useModal()
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
        <button className={`${s.btn} ${s['btn-ghost']} ${s['btn-xs']}`} onClick={e => { e.stopPropagation(); openDetail(r) }}>
          <Eye size={14} strokeWidth={1.5} />
        </button>
      ),
    },
  ]

  return (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>קורסים</h1>
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
