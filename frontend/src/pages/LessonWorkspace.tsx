import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowRight, Video, FileText, Users, Save } from 'lucide-react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import s from '@/styles/shared.module.css'

interface LessonDetails {
  id: number
  title: string
  topic_name: string | null
  course_id: number
  lesson_number: number
  scheduled_date: string | null
  actual_date: string | null
  video_url: string | null
  video_duration: number | null
  lecturer_name: string | null
  cover_image_url: string | null
  description: string | null
  status: string
}

interface Assignment {
  title: string | null
  description: string | null
  file_url: string | null
  due_days: number
  submitted_count: number
  total_students: number
}

interface StudentProgress {
  student_id: number
  full_name: string
  attended: boolean
  video_watched: boolean
  video_watch_percentage: number
  assignment_submitted: boolean
  assignment_grade: number | null
}

interface WorkspaceResponse {
  success: boolean
  lesson: LessonDetails
  assignment: Assignment
  students: StudentProgress[]
}

type TabType = 'details' | 'assignment' | 'students'

export function LessonWorkspacePage() {
  const { lessonId } = useParams<{ lessonId: string }>()
  const navigate = useNavigate()
  const toast = useToast()

  const [activeTab, setActiveTab] = useState<TabType>('details')
  const [lesson, setLesson] = useState<LessonDetails | null>(null)
  const [assignment, setAssignment] = useState<Assignment | null>(null)
  const [students, setStudents] = useState<StudentProgress[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // Form state for editing
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    video_url: '',
    cover_image_url: '',
    lecturer_name: '',
    scheduled_date: '',
    actual_date: '',
    status: 'scheduled',
    assignment_title: '',
    assignment_description: '',
    assignment_file_url: '',
    assignment_due_days: 7
  })

  const fetchWorkspace = useCallback(async () => {
    if (!lessonId) return
    setLoading(true)
    try {
      const data = await api.get<WorkspaceResponse>(`topics/lessons/${lessonId}/workspace`)
      if (data.success) {
        setLesson(data.lesson)
        setAssignment(data.assignment)
        setStudents(data.students)
        
        setFormData({
          title: data.lesson.title,
          description: data.lesson.description || '',
          video_url: data.lesson.video_url || '',
          cover_image_url: data.lesson.cover_image_url || '',
          lecturer_name: data.lesson.lecturer_name || '',
          scheduled_date: data.lesson.scheduled_date ? data.lesson.scheduled_date.split('T')[0] : '',
          actual_date: data.lesson.actual_date ? data.lesson.actual_date.split('T')[0] : '',
          status: data.lesson.status,
          assignment_title: data.assignment.title || '',
          assignment_description: data.assignment.description || '',
          assignment_file_url: data.assignment.file_url || '',
          assignment_due_days: data.assignment.due_days
        })
      }
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בטעינת מפגש')
    } finally {
      setLoading(false)
    }
  }, [lessonId, toast])

  useEffect(() => {
    fetchWorkspace()
  }, [fetchWorkspace])

  const handleSave = async () => {
    if (!lessonId) return
    setSaving(true)
    try {
      await api.put(`topics/lessons/${lessonId}`, formData)
      toast.success('המפגש עודכן בהצלחה')
      await fetchWorkspace()
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בעדכון מפגש')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className={s.card}>
        <div style={{ padding: '2rem', textAlign: 'center' }}>טוען מפגש...</div>
      </div>
    )
  }

  if (!lesson) {
    return (
      <div className={s.card}>
        <div style={{ padding: '2rem', textAlign: 'center' }}>מפגש לא נמצא</div>
      </div>
    )
  }

  return (
    <div>
      <div className={s['page-header']}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: 1 }}>
          <button
            className={`${s.btn} ${s['btn-secondary']}`}
            onClick={() => navigate(-1)}
          >
            <ArrowRight size={16} />
          </button>
          <div style={{ flex: 1 }}>
            <h1 className={s['page-title']}>מפגש {lesson.lesson_number}: {lesson.title}</h1>
            <p style={{ margin: '0.25rem 0 0', color: 'var(--muted)', fontSize: '0.9rem' }}>
              {lesson.topic_name}
            </p>
          </div>
        </div>
        <button
          className={`${s.btn} ${s['btn-primary']}`}
          onClick={handleSave}
          disabled={saving}
        >
          <Save size={16} />
          {saving ? 'שומר...' : 'שמור שינויים'}
        </button>
      </div>

      {/* Tabs */}
      <div className={s.card} style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border)' }}>
          <button
            onClick={() => setActiveTab('details')}
            style={{
              flex: 1,
              padding: '1rem',
              border: 'none',
              background: 'transparent',
              borderBottom: activeTab === 'details' ? '2px solid var(--primary)' : '2px solid transparent',
              color: activeTab === 'details' ? 'var(--primary)' : 'var(--muted)',
              fontWeight: activeTab === 'details' ? 600 : 400,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            <Video size={18} style={{ marginLeft: '0.5rem', verticalAlign: 'middle' }} />
            פרטי המפגש
          </button>
          <button
            onClick={() => setActiveTab('assignment')}
            style={{
              flex: 1,
              padding: '1rem',
              border: 'none',
              background: 'transparent',
              borderBottom: activeTab === 'assignment' ? '2px solid var(--primary)' : '2px solid transparent',
              color: activeTab === 'assignment' ? 'var(--primary)' : 'var(--muted)',
              fontWeight: activeTab === 'assignment' ? 600 : 400,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            <FileText size={18} style={{ marginLeft: '0.5rem', verticalAlign: 'middle' }} />
            מטלה
          </button>
          <button
            onClick={() => setActiveTab('students')}
            style={{
              flex: 1,
              padding: '1rem',
              border: 'none',
              background: 'transparent',
              borderBottom: activeTab === 'students' ? '2px solid var(--primary)' : '2px solid transparent',
              color: activeTab === 'students' ? 'var(--primary)' : 'var(--muted)',
              fontWeight: activeTab === 'students' ? 600 : 400,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            <Users size={18} style={{ marginLeft: '0.5rem', verticalAlign: 'middle' }} />
            תלמידים ({students.length})
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className={s.card}>
        {activeTab === 'details' && (
          <div style={{ padding: '1.5rem' }}>
            <h3 style={{ marginBottom: '1.5rem', fontSize: '1.1rem', fontWeight: 600 }}>פרטי המפגש</h3>
            
            <div style={{ display: 'grid', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>כותרת</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className={s.input}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>תיאור</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className={s.input}
                  rows={3}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>מרצה</label>
                  <input
                    type="text"
                    value={formData.lecturer_name}
                    onChange={(e) => setFormData({ ...formData, lecturer_name: e.target.value })}
                    className={s.input}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>סטטוס</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className={s.input}
                  >
                    <option value="scheduled">מתוכנן</option>
                    <option value="completed">הסתיים</option>
                    <option value="cancelled">בוטל</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>תאריך מתוכנן</label>
                  <input
                    type="date"
                    value={formData.scheduled_date}
                    onChange={(e) => setFormData({ ...formData, scheduled_date: e.target.value })}
                    className={s.input}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>תאריך בפועל</label>
                  <input
                    type="date"
                    value={formData.actual_date}
                    onChange={(e) => setFormData({ ...formData, actual_date: e.target.value })}
                    className={s.input}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>קישור להקלטה</label>
                <input
                  type="url"
                  value={formData.video_url}
                  onChange={(e) => setFormData({ ...formData, video_url: e.target.value })}
                  className={s.input}
                  placeholder="https://..."
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>תמונת כיסוי</label>
                <input
                  type="url"
                  value={formData.cover_image_url}
                  onChange={(e) => setFormData({ ...formData, cover_image_url: e.target.value })}
                  className={s.input}
                  placeholder="https://..."
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'assignment' && (
          <div style={{ padding: '1.5rem' }}>
            <h3 style={{ marginBottom: '1.5rem', fontSize: '1.1rem', fontWeight: 600 }}>מטלה</h3>
            
            <div style={{ display: 'grid', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>כותרת המטלה</label>
                <input
                  type="text"
                  value={formData.assignment_title}
                  onChange={(e) => setFormData({ ...formData, assignment_title: e.target.value })}
                  className={s.input}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>תיאור המטלה</label>
                <textarea
                  value={formData.assignment_description}
                  onChange={(e) => setFormData({ ...formData, assignment_description: e.target.value })}
                  className={s.input}
                  rows={4}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>קובץ מטלה</label>
                <input
                  type="url"
                  value={formData.assignment_file_url}
                  onChange={(e) => setFormData({ ...formData, assignment_file_url: e.target.value })}
                  className={s.input}
                  placeholder="https://..."
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>ימים להגשה</label>
                <input
                  type="number"
                  value={formData.assignment_due_days}
                  onChange={(e) => setFormData({ ...formData, assignment_due_days: parseInt(e.target.value) })}
                  className={s.input}
                  min="1"
                />
              </div>

              {assignment && (
                <div style={{ 
                  padding: '1rem', 
                  backgroundColor: 'var(--hover)', 
                  borderRadius: '6px',
                  marginTop: '1rem'
                }}>
                  <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
                    <strong>{assignment.submitted_count}</strong> מתוך <strong>{assignment.total_students}</strong> תלמידים הגישו את המטלה
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'students' && (
          <div style={{ padding: '1.5rem' }}>
            <h3 style={{ marginBottom: '1.5rem', fontSize: '1.1rem', fontWeight: 600 }}>תלמידים במפגש</h3>
            
            {students.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--muted)' }}>
                אין תלמידים רשומים למפגש זה
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid var(--border)' }}>
                      <th style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 600 }}>שם</th>
                      <th style={{ padding: '0.75rem', textAlign: 'center', fontWeight: 600 }}>נוכחות</th>
                      <th style={{ padding: '0.75rem', textAlign: 'center', fontWeight: 600 }}>צפייה</th>
                      <th style={{ padding: '0.75rem', textAlign: 'center', fontWeight: 600 }}>מטלה</th>
                      <th style={{ padding: '0.75rem', textAlign: 'center', fontWeight: 600 }}>ציון</th>
                    </tr>
                  </thead>
                  <tbody>
                    {students.map((student) => (
                      <tr key={student.student_id} style={{ borderBottom: '1px solid var(--border)' }}>
                        <td style={{ padding: '0.75rem' }}>{student.full_name}</td>
                        <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                          {student.attended ? '✅' : '❌'}
                        </td>
                        <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                          {student.video_watch_percentage}%
                        </td>
                        <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                          {student.assignment_submitted ? '✅' : '❌'}
                        </td>
                        <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                          {student.assignment_grade ?? '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
