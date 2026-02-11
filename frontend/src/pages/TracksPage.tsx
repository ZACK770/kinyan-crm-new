import { useEffect, useState, useCallback, type FormEvent } from 'react'
import { Calendar, Plus } from 'lucide-react'
import { api } from '@/lib/api'
import { formatDate } from '@/lib/status'
import { useModal } from '@/components/ui/Modal'
import { useToast } from '@/components/ui/Toast'
import { DataTable, type Column } from '@/components/ui/DataTable'
import s from '@/styles/shared.module.css'

interface CourseTrack {
  id: number
  course_id: number
  lecturer_id: number
  name: string
  day_of_week: string
  start_time: string
  city: string
  zoom_url?: string
  price?: number
  current_module_id?: number
  current_session_number: number
  last_session_date?: string
  next_entry_date?: string
  is_active: boolean
  course?: { id: number; name: string }
  lecturer?: { id: number; name: string }
  current_module?: { id: number; name: string; sessions_count?: number }
}

interface Course {
  id: number
  name: string
}

interface Lecturer {
  id: number
  name: string
}

interface CourseModule {
  id: number
  name: string
  module_order: number
}

function TrackForm({
  initial,
  courses,
  lecturers,
  modules,
  onSubmit,
  onCancel,
}: {
  initial?: Partial<CourseTrack>
  courses: Course[]
  lecturers: Lecturer[]
  modules: CourseModule[]
  onSubmit: (data: Record<string, unknown>) => void
  onCancel?: () => void
}) {
  const [form, setForm] = useState({
    course_id: initial?.course_id ?? '',
    lecturer_id: initial?.lecturer_id ?? '',
    name: initial?.name ?? '',
    day_of_week: initial?.day_of_week ?? 'ראשון',
    start_time: initial?.start_time ?? '21:00',
    city: initial?.city ?? '',
    zoom_url: initial?.zoom_url ?? '',
    price: initial?.price ?? '',
    current_module_id: initial?.current_module_id ?? '',
    is_active: initial?.is_active ?? true,
  })

  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(prev => ({ ...prev, [key]: e.target.type === 'checkbox' ? (e.target as HTMLInputElement).checked : e.target.value }))

  const handle = (e: FormEvent) => {
    e.preventDefault()
    const data: Record<string, unknown> = { ...form }
    if (data.course_id) data.course_id = Number(data.course_id)
    if (data.lecturer_id) data.lecturer_id = Number(data.lecturer_id)
    if (data.price) data.price = Number(data.price)
    if (data.current_module_id) data.current_module_id = Number(data.current_module_id)
    else delete data.current_module_id
    Object.keys(data).forEach(k => { if (data[k] === '') delete data[k] })
    onSubmit(data)
  }

  return (
    <form onSubmit={handle} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      {!initial?.id && (
        <div className={s['form-row']}>
          <div className={s['form-group']}>
            <label className={s['form-label']}>קורס *</label>
            <select className={s.select} value={form.course_id} onChange={set('course_id')} required>
              <option value="">בחר קורס</option>
              {courses.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className={s['form-group']}>
            <label className={s['form-label']}>מרצה *</label>
            <select className={s.select} value={form.lecturer_id} onChange={set('lecturer_id')} required>
              <option value="">בחר מרצה</option>
              {lecturers.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
            </select>
          </div>
        </div>
      )}

      <div className={s['form-group']}>
        <label className={s['form-label']}>שם המסלול *</label>
        <input className={s.input} value={form.name} onChange={set('name')} required placeholder="למשל: שבת - רביעי 21:00 - בני ברק" />
      </div>

      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>יום השבוע *</label>
          <select className={s.select} value={form.day_of_week} onChange={set('day_of_week')} required>
            {['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת'].map(d => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>שעת התחלה *</label>
          <input className={s.input} type="time" value={form.start_time} onChange={set('start_time')} required dir="ltr" />
        </div>
      </div>

      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>עיר *</label>
          <input className={s.input} value={form.city} onChange={set('city')} required placeholder="בני ברק" />
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>מחיר (₪)</label>
          <input className={s.input} type="number" value={form.price} onChange={set('price')} dir="ltr" />
        </div>
      </div>

      <div className={s['form-group']}>
        <label className={s['form-label']}>חוברת נוכחית</label>
        <select className={s.select} value={form.current_module_id} onChange={set('current_module_id')}>
          <option value="">בחר חוברת</option>
          {modules.map(m => <option key={m.id} value={m.id}>{m.module_order}. {m.name}</option>)}
        </select>
      </div>

      <div className={s['form-group']}>
        <label className={s['form-label']}>קישור זום</label>
        <input className={s.input} type="url" value={form.zoom_url} onChange={set('zoom_url')} dir="ltr" />
      </div>

      {initial?.id && (
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
          <input type="checkbox" checked={form.is_active} onChange={set('is_active')} />
          <span>מסלול פעיל</span>
        </label>
      )}

      <div style={{ display: 'flex', gap: 8, paddingTop: 8 }}>
        <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>
          {initial?.id ? 'עדכן' : 'צור מסלול'}
        </button>
        {onCancel && (
          <button type="button" className={`${s.btn} ${s['btn-secondary']}`} onClick={onCancel}>
            ביטול
          </button>
        )}
      </div>
    </form>
  )
}

export function TracksPage() {
  const [tracks, setTracks] = useState<CourseTrack[]>([])
  const [courses, setCourses] = useState<Course[]>([])
  const [lecturers, setLecturers] = useState<Lecturer[]>([])
  const [modules, setModules] = useState<CourseModule[]>([])
  const [loading, setLoading] = useState(true)
  const [filterCity, setFilterCity] = useState('')
  const [showActiveOnly, setShowActiveOnly] = useState(true)
  const { openModal, closeModal } = useModal()
  const toast = useToast()

  const fetchTracks = useCallback(async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (filterCity) params.append('city', filterCity)
      if (showActiveOnly) params.append('is_active', 'true')
      const data = await api.get<CourseTrack[]>(`/course-tracks/?${params}`)
      setTracks(data)
    } catch (err) {
      toast.error('שגיאה בטעינת מסלולים')
    } finally {
      setLoading(false)
    }
  }, [filterCity, showActiveOnly, toast.error])

  const fetchCourses = useCallback(async () => {
    try {
      const data = await api.get<Course[]>('/courses/')
      setCourses(data)
    } catch (err) {
      console.error(err)
    }
  }, [])

  const fetchLecturers = useCallback(async () => {
    try {
      const data = await api.get<Lecturer[]>('/courses/lecturers')
      setLecturers(data)
    } catch (err) {
      console.error(err)
    }
  }, [])

  const fetchModules = useCallback(async (courseId: number) => {
    try {
      const data = await api.get<CourseModule[]>(`/courses/${courseId}/modules`)
      setModules(data)
    } catch (err) {
      console.error(err)
    }
  }, [])

  useEffect(() => {
    fetchTracks()
    fetchCourses()
    fetchLecturers()
  }, [fetchTracks, fetchCourses, fetchLecturers])

  const handleCreate = () => {
    openModal({
      title: 'מסלול חדש',
      content: (
        <TrackForm
          courses={courses}
          lecturers={lecturers}
          modules={modules}
          onSubmit={async (data) => {
            try {
              await api.post('/course-tracks/', data)
              toast.success('המסלול נוצר בהצלחה')
              closeModal()
              fetchTracks()
            } catch (err) {
              toast.error('שגיאה ביצירת מסלול')
            }
          }}
          onCancel={closeModal}
        />
      ),
    })
  }

  const handleEdit = (track: CourseTrack) => {
    if (track.course_id) fetchModules(track.course_id)
    openModal({
      title: 'עריכת מסלול',
      content: (
        <TrackForm
          initial={track}
          courses={courses}
          lecturers={lecturers}
          modules={modules}
          onSubmit={async (data) => {
            try {
              await api.put(`/course-tracks/${track.id}`, data)
              toast.success('המסלול עודכן בהצלחה')
              closeModal()
              fetchTracks()
            } catch (err) {
              toast.error('שגיאה בעדכון מסלול')
            }
          }}
          onCancel={closeModal}
        />
      ),
    })
  }

  const cities = Array.from(new Set(tracks.map(t => t.city))).sort()

  const columns: Column<CourseTrack>[] = [
    {
      key: 'name',
      header: 'שם המסלול',
      render: (t) => (
        <div>
          <div style={{ fontWeight: 500 }}>{t.name}</div>
          {t.course && <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>{t.course.name}</div>}
        </div>
      ),
    },
    {
      key: 'lecturer',
      header: 'מרצה',
      render: (t) => t.lecturer?.name ?? '—',
    },
    {
      key: 'schedule',
      header: 'יום ושעה',
      render: (t) => `${t.day_of_week} ${t.start_time}`,
    },
    {
      key: 'city',
      header: 'עיר',
      render: (t) => t.city,
    },
    {
      key: 'current_module',
      header: 'חוברת נוכחית',
      render: (t) => t.current_module ? `${t.current_module.name} (${t.current_session_number}/${t.current_module.sessions_count ?? '?'})` : '—',
    },
    {
      key: 'next_entry_date',
      header: 'נקודת כניסה הבאה',
      render: (t) => t.next_entry_date ? formatDate(t.next_entry_date) : '—',
    },
    {
      key: 'price',
      header: 'מחיר',
      render: (t) => t.price ? `₪${t.price.toLocaleString()}` : '—',
    },
    {
      key: 'is_active',
      header: 'סטטוס',
      render: (t) => (
        <span className={`${s.badge} ${t.is_active ? s['badge-green'] : s['badge-gray']}`}>
          {t.is_active ? 'פעיל' : 'לא פעיל'}
        </span>
      ),
    },
  ]

  return (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>מסלולי לימוד</h1>
        <div className={s['page-actions']}>
          <button className={`${s.btn} ${s['btn-primary']}`} onClick={handleCreate}>
            <Plus size={16} />
            מסלול חדש
          </button>
        </div>
      </div>

      <div className={s.card}>
        <div className={s.toolbar}>
          <select className={s['select-sm']} value={filterCity} onChange={(e) => setFilterCity(e.target.value)}>
            <option value="">כל הערים</option>
            {cities.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, cursor: 'pointer' }}>
            <input type="checkbox" checked={showActiveOnly} onChange={(e) => setShowActiveOnly(e.target.checked)} />
            מסלולים פעילים בלבד
          </label>
          <div style={{ flex: 1 }} />
          <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
            {tracks.length} מסלולים
          </span>
        </div>

        <div className={s['card-body-flush']}>
          {loading ? (
            <div className={s.loading}>טוען מסלולים...</div>
          ) : tracks.length === 0 ? (
            <div className={s.empty}>
              <Calendar size={48} className={s['empty-icon']} />
              <div className={s['empty-text']}>אין מסלולים</div>
            </div>
          ) : (
            <DataTable
              columns={columns}
              data={tracks}
              onRowClick={handleEdit}
              keyExtractor={(track) => track.id}
            />
          )}
        </div>
      </div>
    </div>
  )
}
