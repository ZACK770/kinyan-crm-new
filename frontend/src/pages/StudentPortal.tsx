import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { BookOpen, Video, FileText, Download, CheckCircle, Clock } from 'lucide-react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import s from '@/styles/shared.module.css'

interface Topic {
  id: number
  name: string
  order_index: number
  lessons_count: number
}

interface Lesson {
  id: number
  lesson_number: number
  title: string
  description: string | null
  video_url: string | null
  cover_image_url: string | null
  lecturer_name: string | null
  scheduled_date: string | null
  assignment_title: string | null
  assignment_description: string | null
  assignment_file_url: string | null
  assignment_due_days: number
  progress: {
    attended: boolean
    video_watched: boolean
    video_watch_percentage: number
    assignment_submitted: boolean
    assignment_grade: number | null
  } | null
}

interface StudentProgress {
  is_graduate: boolean
  progress_percentage: number
  completed_topics: number
  total_topics: number
  current_topic: {
    id: number
    name: string
  } | null
}

export function StudentPortalPage() {
  const { studentId, courseId } = useParams<{ studentId: string; courseId: string }>()
  const toast = useToast()

  const [topics, setTopics] = useState<Topic[]>([])
  const [selectedTopic, setSelectedTopic] = useState<Topic | null>(null)
  const [lessons, setLessons] = useState<Lesson[]>([])
  const [selectedLesson, setSelectedLesson] = useState<Lesson | null>(null)
  const [progress, setProgress] = useState<StudentProgress | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchTopics = useCallback(async () => {
    if (!courseId) return
    try {
      const data = await api.get<{ success: boolean; topics: Topic[] }>(`topics/courses/${courseId}/topics`)
      if (data.success) {
        setTopics(data.topics)
        if (data.topics.length > 0) {
          setSelectedTopic(data.topics[0])
        }
      }
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בטעינת נושאים')
    }
  }, [courseId, toast])

  const fetchProgress = useCallback(async () => {
    if (!studentId) return
    try {
      const data = await api.get<{ success: boolean; progress: StudentProgress }>(`topics/students/${studentId}/progress`)
      if (data.success) {
        setProgress(data.progress)
      }
    } catch (err: unknown) {
      console.error('Failed to fetch progress:', err)
    }
  }, [studentId])

  const fetchLessons = useCallback(async (topicId: number) => {
    try {
      const data = await api.get<{ success: boolean; lessons: Lesson[] }>(`topics/topics/${topicId}/lessons`)
      if (data.success) {
        setLessons(data.lessons)
        if (data.lessons.length > 0) {
          setSelectedLesson(data.lessons[0])
        }
      }
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בטעינת מפגשים')
    }
  }, [toast])

  useEffect(() => {
    const init = async () => {
      setLoading(true)
      await Promise.all([fetchTopics(), fetchProgress()])
      setLoading(false)
    }
    init()
  }, [fetchTopics, fetchProgress])

  useEffect(() => {
    if (selectedTopic) {
      fetchLessons(selectedTopic.id)
    }
  }, [selectedTopic, fetchLessons])

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—'
    const date = new Date(dateStr)
    return date.toLocaleDateString('he-IL', { day: '2-digit', month: '2-digit', year: 'numeric' })
  }

  if (loading) {
    return (
      <div className={s.card}>
        <div style={{ padding: '2rem', textAlign: 'center' }}>טוען...</div>
      </div>
    )
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '1.5rem', height: 'calc(100vh - 120px)' }}>
      {/* Sidebar - Topics & Lessons */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', overflowY: 'auto' }}>
        {/* Progress Card */}
        {progress && (
          <div className={s.card} style={{ padding: '1.5rem' }}>
            <h3 style={{ margin: '0 0 1rem', fontSize: '1rem', fontWeight: 600 }}>ההתקדמות שלי</h3>
            
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                <span>{progress.progress_percentage.toFixed(0)}%</span>
                <span style={{ color: 'var(--muted)' }}>
                  {progress.completed_topics}/{progress.total_topics} נושאים
                </span>
              </div>
              <div style={{ 
                width: '100%', 
                height: '8px', 
                backgroundColor: 'var(--hover)', 
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{ 
                  width: `${progress.progress_percentage}%`, 
                  height: '100%', 
                  backgroundColor: 'var(--primary)',
                  transition: 'width 0.3s ease'
                }} />
              </div>
            </div>

            {progress.is_graduate ? (
              <div style={{ 
                padding: '0.75rem', 
                backgroundColor: 'var(--success-bg)', 
                color: 'var(--success)',
                borderRadius: '6px',
                textAlign: 'center',
                fontWeight: 600
              }}>
                🎓 בוגר!
              </div>
            ) : progress.current_topic && (
              <div style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
                נושא נוכחי: <strong>{progress.current_topic.name}</strong>
              </div>
            )}
          </div>
        )}

        {/* Topics List */}
        <div className={s.card}>
          <div style={{ padding: '1rem', borderBottom: '1px solid var(--border)' }}>
            <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600 }}>נושאים</h3>
          </div>
          <div style={{ padding: '0.5rem' }}>
            {topics.map((topic) => (
              <button
                key={topic.id}
                onClick={() => setSelectedTopic(topic)}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: 'none',
                  background: selectedTopic?.id === topic.id ? 'var(--primary-bg)' : 'transparent',
                  borderRight: selectedTopic?.id === topic.id ? '3px solid var(--primary)' : '3px solid transparent',
                  textAlign: 'right',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                <span style={{
                  display: 'flex',
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  backgroundColor: selectedTopic?.id === topic.id ? 'var(--primary)' : 'var(--muted-bg)',
                  color: selectedTopic?.id === topic.id ? 'white' : 'var(--muted)',
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}>
                  {topic.order_index + 1}
                </span>
                <span style={{ 
                  fontSize: '0.9rem',
                  fontWeight: selectedTopic?.id === topic.id ? 600 : 400,
                  color: selectedTopic?.id === topic.id ? 'var(--primary)' : 'inherit'
                }}>
                  {topic.name}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Lessons List */}
        {selectedTopic && (
          <div className={s.card}>
            <div style={{ padding: '1rem', borderBottom: '1px solid var(--border)' }}>
              <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600 }}>מפגשים</h3>
            </div>
            <div style={{ padding: '0.5rem' }}>
              {lessons.map((lesson) => (
                <button
                  key={lesson.id}
                  onClick={() => setSelectedLesson(lesson)}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    border: 'none',
                    background: selectedLesson?.id === lesson.id ? 'var(--primary-bg)' : 'transparent',
                    borderRight: selectedLesson?.id === lesson.id ? '3px solid var(--primary)' : '3px solid transparent',
                    textAlign: 'right',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
                      מפגש {lesson.lesson_number}
                    </span>
                    {lesson.progress?.video_watched && (
                      <CheckCircle size={14} style={{ color: 'var(--success)' }} />
                    )}
                  </div>
                  <div style={{ 
                    fontSize: '0.85rem',
                    fontWeight: selectedLesson?.id === lesson.id ? 600 : 400,
                    color: selectedLesson?.id === lesson.id ? 'var(--primary)' : 'inherit'
                  }}>
                    {lesson.title}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Main Content - Lesson Details */}
      <div style={{ overflowY: 'auto' }}>
        {selectedLesson ? (
          <div className={s.card}>
            {/* Lesson Header */}
            <div style={{ 
              padding: '2rem',
              background: 'linear-gradient(135deg, var(--primary-bg) 0%, var(--hover) 100%)',
              borderBottom: '1px solid var(--border)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                <span style={{
                  padding: '0.25rem 0.75rem',
                  borderRadius: '4px',
                  backgroundColor: 'var(--primary)',
                  color: 'white',
                  fontSize: '0.85rem',
                  fontWeight: 600
                }}>
                  מפגש {selectedLesson.lesson_number}
                </span>
                {selectedLesson.lecturer_name && (
                  <span style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
                    מרצה: {selectedLesson.lecturer_name}
                  </span>
                )}
              </div>
              <h1 style={{ margin: '0 0 0.5rem', fontSize: '1.75rem', fontWeight: 700 }}>
                {selectedLesson.title}
              </h1>
              {selectedLesson.scheduled_date && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--muted)', fontSize: '0.9rem' }}>
                  <Clock size={16} />
                  <span>{formatDate(selectedLesson.scheduled_date)}</span>
                </div>
              )}
            </div>

            {/* Video Section */}
            {selectedLesson.video_url && (
              <div style={{ padding: '2rem', borderBottom: '1px solid var(--border)' }}>
                <h3 style={{ margin: '0 0 1rem', fontSize: '1.1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Video size={20} />
                  הקלטת השיעור
                </h3>
                <div style={{ 
                  position: 'relative',
                  paddingBottom: '56.25%',
                  height: 0,
                  overflow: 'hidden',
                  borderRadius: '8px',
                  backgroundColor: 'var(--hover)'
                }}>
                  <iframe
                    src={selectedLesson.video_url}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '100%',
                      border: 'none'
                    }}
                    allowFullScreen
                  />
                </div>
                {selectedLesson.progress && (
                  <div style={{ marginTop: '1rem', fontSize: '0.9rem', color: 'var(--muted)' }}>
                    צפית: {selectedLesson.progress.video_watch_percentage}%
                  </div>
                )}
              </div>
            )}

            {/* Description */}
            {selectedLesson.description && (
              <div style={{ padding: '2rem', borderBottom: '1px solid var(--border)' }}>
                <h3 style={{ margin: '0 0 1rem', fontSize: '1.1rem', fontWeight: 600 }}>תיאור</h3>
                <p style={{ margin: 0, lineHeight: 1.6, color: 'var(--muted)' }}>
                  {selectedLesson.description}
                </p>
              </div>
            )}

            {/* Assignment Section */}
            {selectedLesson.assignment_title && (
              <div style={{ padding: '2rem' }}>
                <h3 style={{ margin: '0 0 1rem', fontSize: '1.1rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <FileText size={20} />
                  מטלה
                </h3>
                
                <div style={{ 
                  padding: '1.5rem',
                  backgroundColor: 'var(--hover)',
                  borderRadius: '8px',
                  marginBottom: '1rem'
                }}>
                  <h4 style={{ margin: '0 0 0.5rem', fontSize: '1rem', fontWeight: 600 }}>
                    {selectedLesson.assignment_title}
                  </h4>
                  {selectedLesson.assignment_description && (
                    <p style={{ margin: '0.5rem 0', lineHeight: 1.6, color: 'var(--muted)' }}>
                      {selectedLesson.assignment_description}
                    </p>
                  )}
                  <div style={{ marginTop: '1rem', fontSize: '0.85rem', color: 'var(--muted)' }}>
                    מועד הגשה: {selectedLesson.assignment_due_days} ימים מתאריך השיעור
                  </div>
                </div>

                {selectedLesson.assignment_file_url && (
                  <a
                    href={selectedLesson.assignment_file_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`${s.btn} ${s['btn-secondary']}`}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
                  >
                    <Download size={16} />
                    הורד קובץ מטלה
                  </a>
                )}

                {selectedLesson.progress && (
                  <div style={{ marginTop: '1.5rem' }}>
                    {selectedLesson.progress.assignment_submitted ? (
                      <div style={{ 
                        padding: '1rem',
                        backgroundColor: 'var(--success-bg)',
                        color: 'var(--success)',
                        borderRadius: '6px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                      }}>
                        <CheckCircle size={20} />
                        <span>המטלה הוגשה</span>
                        {selectedLesson.progress.assignment_grade !== null && (
                          <span style={{ marginRight: 'auto', fontWeight: 600 }}>
                            ציון: {selectedLesson.progress.assignment_grade}
                          </span>
                        )}
                      </div>
                    ) : (
                      <button className={`${s.btn} ${s['btn-primary']}`}>
                        <FileText size={16} />
                        הגש מטלה
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className={s.card} style={{ padding: '3rem', textAlign: 'center' }}>
            <BookOpen size={48} strokeWidth={1.5} style={{ margin: '0 auto 1rem', opacity: 0.3 }} />
            <p style={{ color: 'var(--muted)' }}>בחר מפגש מהרשימה</p>
          </div>
        )}
      </div>
    </div>
  )
}
