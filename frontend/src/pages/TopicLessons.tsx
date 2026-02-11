import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowRight, BookOpen, Video, FileText, Users } from 'lucide-react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import s from '@/styles/shared.module.css'

interface Lesson {
  id: number
  lesson_number: number
  title: string
  description: string | null
  video_url: string | null
  cover_image_url: string | null
  lecturer_name: string | null
  scheduled_date: string | null
  status: string
  assignment_title: string | null
  students_count: number
  assignment_submitted_count: number
}

interface TopicInfo {
  id: number
  name: string
  course_id: number
}

interface LessonsResponse {
  success: boolean
  topic: TopicInfo
  lessons: Lesson[]
}

export function TopicLessonsPage() {
  const { topicId } = useParams<{ topicId: string }>()
  const navigate = useNavigate()
  const toast = useToast()

  const [topic, setTopic] = useState<TopicInfo | null>(null)
  const [lessons, setLessons] = useState<Lesson[]>([])
  const [loading, setLoading] = useState(true)

  const fetchLessons = useCallback(async () => {
    if (!topicId) return
    setLoading(true)
    try {
      const data = await api.get<LessonsResponse>(`topics/topics/${topicId}/lessons`)
      if (data.success) {
        setTopic(data.topic)
        setLessons(data.lessons)
      }
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בטעינת מפגשים')
    } finally {
      setLoading(false)
    }
  }, [topicId, toast])

  useEffect(() => {
    fetchLessons()
  }, [fetchLessons])

  const openLessonWorkspace = (lessonId: number) => {
    navigate(`/admin/lessons/${lessonId}`)
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—'
    const date = new Date(dateStr)
    return date.toLocaleDateString('he-IL', { day: '2-digit', month: '2-digit', year: 'numeric' })
  }

  if (loading) {
    return (
      <div className={s.card}>
        <div style={{ padding: '2rem', textAlign: 'center' }}>טוען מפגשים...</div>
      </div>
    )
  }

  return (
    <div>
      <div className={s['page-header']}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button
            className={`${s.btn} ${s['btn-secondary']}`}
            onClick={() => topic && navigate(`/admin/courses/${topic.course_id}/topics`)}
          >
            <ArrowRight size={16} />
          </button>
          <div>
            <h1 className={s['page-title']}>{topic?.name}</h1>
            <p style={{ margin: '0.25rem 0 0', color: 'var(--muted)', fontSize: '0.9rem' }}>
              מפגשי הנושא
            </p>
          </div>
        </div>
      </div>

      <div className={s.card}>
        {lessons.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <BookOpen size={48} strokeWidth={1.5} style={{ margin: '0 auto 1rem', opacity: 0.3 }} />
            <p style={{ color: 'var(--muted)' }}>לא נמצאו מפגשים לנושא זה</p>
          </div>
        ) : (
          <div style={{ padding: '1rem' }}>
            {lessons.map((lesson) => (
              <div
                key={lesson.id}
                onClick={() => openLessonWorkspace(lesson.id)}
                style={{
                  display: 'flex',
                  gap: '1.5rem',
                  padding: '1.5rem',
                  marginBottom: '1rem',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--hover)'
                  e.currentTarget.style.borderColor = 'var(--primary)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent'
                  e.currentTarget.style.borderColor = 'var(--border)'
                }}
              >
                {/* Cover Image */}
                <div style={{
                  width: '120px',
                  height: '90px',
                  borderRadius: '6px',
                  overflow: 'hidden',
                  backgroundColor: 'var(--hover)',
                  flexShrink: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  {lesson.cover_image_url ? (
                    <img 
                      src={lesson.cover_image_url} 
                      alt={lesson.title}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                  ) : (
                    <Video size={32} strokeWidth={1.5} style={{ color: 'var(--muted)' }} />
                  )}
                </div>

                {/* Lesson Info */}
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '0.25rem 0.5rem',
                      borderRadius: '4px',
                      backgroundColor: 'var(--primary)',
                      color: 'white',
                      fontSize: '0.75rem',
                      fontWeight: 600
                    }}>
                      מפגש {lesson.lesson_number}
                    </span>
                    <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>
                      {lesson.title}
                    </h3>
                  </div>

                  {lesson.description && (
                    <p style={{ margin: '0.5rem 0', fontSize: '0.9rem', color: 'var(--muted)', lineHeight: 1.5 }}>
                      {lesson.description}
                    </p>
                  )}

                  <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.75rem', fontSize: '0.85rem' }}>
                    {lesson.lecturer_name && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--muted)' }}>
                        <Users size={14} />
                        <span>{lesson.lecturer_name}</span>
                      </div>
                    )}
                    
                    {lesson.scheduled_date && (
                      <div style={{ color: 'var(--muted)' }}>
                        📅 {formatDate(lesson.scheduled_date)}
                      </div>
                    )}

                    {lesson.video_url && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--success)' }}>
                        <Video size={14} />
                        <span>הקלטה זמינה</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Stats */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'flex-end' }}>
                  <span className={s.badge}>
                    {lesson.students_count} תלמידים
                  </span>
                  
                  {lesson.assignment_title && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                      <FileText size={14} style={{ color: 'var(--muted)' }} />
                      <span style={{ color: 'var(--muted)' }}>
                        {lesson.assignment_submitted_count}/{lesson.students_count} הגישו
                      </span>
                    </div>
                  )}

                  <span style={{
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 500,
                    backgroundColor: lesson.status === 'completed' ? 'var(--success-bg)' : 'var(--muted-bg)',
                    color: lesson.status === 'completed' ? 'var(--success)' : 'var(--muted)'
                  }}>
                    {lesson.status === 'completed' ? 'הסתיים' : 
                     lesson.status === 'scheduled' ? 'מתוכנן' : 
                     lesson.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
