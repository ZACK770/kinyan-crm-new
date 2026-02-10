import { useEffect, useState, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { BookOpen, Plus, ArrowRight } from 'lucide-react'
import { api } from '@/lib/api'
import { formatDate } from '@/lib/status'
import { useToast } from '@/components/ui/Toast'
import { SmartTable, type SmartColumn } from '@/components/ui/SmartTable'
import { CourseWorkspace } from '@/components/courses'
import type { Course } from '@/types'
import s from '@/styles/shared.module.css'

/* ── Badge helper ── */
function Badge({ value }: { value: boolean }) {
  return (
    <span className={`${s.badge} ${value ? s['badge-green'] : s['badge-gray']}`}>
      {value ? 'פעיל' : 'לא פעיל'}
    </span>
  )
}

/* ══════════════════════════════════════════════════════════════
   Courses Page
   ══════════════════════════════════════════════════════════════ */
export function CoursesPage() {
  const toast = useToast()

  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(true)
  
  // Workspace view state: 'list' | 'create' | Course object (edit mode)
  type ViewMode = 'list' | 'create'
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)
  const [searchParams, setSearchParams] = useSearchParams()

  // Auto-open create form when ?create=true (from entity '+' button)
  useEffect(() => {
    if (searchParams.get('create') === 'true') {
      setViewMode('create')
      setSelectedCourse(null)
      setSearchParams({}, { replace: true })
    }
  }, [searchParams, setSearchParams])

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

  /* ── Navigation ── */
  const backToList = () => {
    setSelectedCourse(null)
    setViewMode('list')
  }

  const openCreate = () => {
    setSelectedCourse(null)
    setViewMode('create')
  }

  const openEdit = (course: Course) => {
    setSelectedCourse(course)
  }

  const handleCreatedCourse = (course: Course) => {
    setCourses(prev => [course, ...prev])
    backToList()
  }

  const refreshSelectedCourse = async () => {
    if (!selectedCourse) return
    try {
      const updated = await api.get<Course>(`courses/${selectedCourse.id}`)
      setSelectedCourse(updated)
      setCourses(prev => prev.map(c => c.id === updated.id ? updated : c))
    } catch {
      toast.error('שגיאה בטעינת קורס')
    }
  }

  const columns: SmartColumn<Course>[] = [
    { key: 'name', header: 'שם הקורס', type: 'text', sortable: true },
    { key: 'semester', header: 'סמסטר', type: 'text', render: r => r.semester ?? '—' },
    { key: 'price', header: 'מחיר', type: 'text', render: r => r.price ? `₪${r.price}` : '—', className: s.muted },
    { key: 'payments_count', header: 'תשלומים', type: 'text', render: r => r.payments_count || '—', className: s.muted },
    { key: 'total_sessions', header: 'שיעורים', type: 'text', render: r => r.total_sessions ?? '—' },
    {
      key: 'is_active',
      header: 'סטטוס',
      type: 'text',
      render: r => <Badge value={r.is_active} />,
    },
    { key: 'start_date', header: 'התחלה', type: 'text', render: r => formatDate(r.start_date), className: s.muted },
  ]

  // Show workspace for create or edit
  if (viewMode === 'create') {
    return (
      <div>
        <div className={s['page-header']}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button className={`${s.btn} ${s['btn-ghost']}`} onClick={backToList}>
              <ArrowRight size={18} /> חזרה
            </button>
            <h1 className={s['page-title']} style={{ fontSize: '1.2rem' }}>קורס חדש</h1>
          </div>
        </div>
        
        <CourseWorkspace
          course={null}
          onClose={backToList}
          onUpdate={() => {}}
          onCreate={handleCreatedCourse}
        />
      </div>
    )
  }

  // Show workspace in EDIT mode (selectedCourse exists)
  if (selectedCourse) {
    return (
      <div>
        <div className={s['page-header']}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button className={`${s.btn} ${s['btn-ghost']}`} onClick={backToList}>
              <ArrowRight size={18} /> חזרה
            </button>
            <h1 className={s['page-title']} style={{ fontSize: '1.2rem' }}>
              {selectedCourse.name}
            </h1>
          </div>
        </div>
        
        <CourseWorkspace
          course={selectedCourse}
          onClose={backToList}
          onUpdate={refreshSelectedCourse}
        />
      </div>
    )
  }

  return (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>קורסים</h1>
        <button className={`${s.btn} ${s['btn-primary']}`} onClick={openCreate}>
          <Plus size={16} strokeWidth={1.5} /> קורס חדש
        </button>
      </div>

      <div className={s.card}>
        <SmartTable
          columns={columns}
          data={courses}
          loading={loading}
          emptyText="לא נמצאו קורסים"
          emptyIcon={<BookOpen size={40} strokeWidth={1.5} />}
          onRowClick={openEdit}
          keyExtractor={r => r.id}
        />
      </div>
    </div>
  )
}
