import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { BookOpen, Video, FileText, Download, CheckCircle, Clock, Award, Play } from 'lucide-react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import s from '@/styles/shared.module.css'

interface LessonProgress {
  attended: boolean
  video_watched: boolean
  video_watch_percentage: number
  assignment_submitted: boolean
  assignment_grade: number | null
}

interface PortalLesson {
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
  progress: LessonProgress | null
}

interface PortalTopic {
  id: number
  name: string
  order_index: number
  lessons_count: number
  lessons: PortalLesson[]
}

interface PortalProgress {
  completed_lessons: number
  total_lessons: number
  percentage: number
  is_graduate: boolean
}

interface PortalData {
  success: boolean
  student: { id: number; full_name: string; is_graduate: boolean }
  course: { id: number; name: string }
  topics: PortalTopic[]
  progress: PortalProgress
}

export function StudentPortalPage() {
  const { studentId, courseId } = useParams<{ studentId: string; courseId: string }>()
  const toast = useToast()

  const [data, setData] = useState<PortalData | null>(null)
  const [selectedTopic, setSelectedTopic] = useState<PortalTopic | null>(null)
  const [selectedLesson, setSelectedLesson] = useState<PortalLesson | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchPortal = useCallback(async () => {
    if (!studentId || !courseId) return
    setLoading(true)
    try {
      const result = await api.get<PortalData>(`topics/student-portal/${studentId}/${courseId}`)
      if (result.success) {
        setData(result)
        if (result.topics.length > 0) {
          setSelectedTopic(result.topics[0])
          if (result.topics[0].lessons.length > 0) {
            setSelectedLesson(result.topics[0].lessons[0])
          }
        }
      }
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בטעינת הפורטל')
    } finally {
      setLoading(false)
    }
  }, [studentId, courseId, toast])

  useEffect(() => {
    fetchPortal()
  }, [fetchPortal])

  const handleTopicSelect = (topic: PortalTopic) => {
    setSelectedTopic(topic)
    if (topic.lessons.length > 0) {
      setSelectedLesson(topic.lessons[0])
    } else {
      setSelectedLesson(null)
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null
    const date = new Date(dateStr)
    return date.toLocaleDateString('he-IL', { day: '2-digit', month: 'long', year: 'numeric' })
  }

  const isLessonDone = (lesson: PortalLesson) => {
    return lesson.progress && (lesson.progress.attended || lesson.progress.video_watch_percentage >= 80)
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '400px' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: '40px', height: '40px', border: '3px solid var(--border)', borderTopColor: 'var(--primary)', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 1rem' }} />
          <p style={{ color: 'var(--muted)' }}>טוען פורטל תלמיד...</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className={s.card} style={{ padding: '3rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--muted)' }}>לא נמצאו נתונים</p>
      </div>
    )
  }

  const { student, course, progress, topics } = data

  return (
    <div>
      {/* Hero Header */}
      <div style={{
        background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #a855f7 100%)',
        borderRadius: '16px',
        padding: '2rem 2.5rem',
        marginBottom: '1.5rem',
        color: 'white',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{ position: 'absolute', top: '-20px', left: '-20px', width: '120px', height: '120px', borderRadius: '50%', background: 'rgba(255,255,255,0.08)' }} />
        <div style={{ position: 'absolute', bottom: '-30px', right: '40px', width: '160px', height: '160px', borderRadius: '50%', background: 'rgba(255,255,255,0.05)' }} />
        
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <p style={{ margin: '0 0 0.25rem', fontSize: '0.9rem', opacity: 0.85 }}>שלום,</p>
              <h1 style={{ margin: '0 0 0.5rem', fontSize: '1.75rem', fontWeight: 700 }}>{student.full_name}</h1>
              <p style={{ margin: 0, fontSize: '0.95rem', opacity: 0.9 }}>{course.name}</p>
            </div>
            {progress.is_graduate && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 1rem',
                backgroundColor: 'rgba(255,255,255,0.2)',
                borderRadius: '30px',
                fontWeight: 600,
                fontSize: '0.95rem'
              }}>
                <Award size={20} />
                בוגר הקורס
              </div>
            )}
          </div>

          {/* Progress Bar */}
          <div style={{ marginTop: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
              <span style={{ fontWeight: 600 }}>{progress.percentage}% הושלם</span>
              <span style={{ opacity: 0.8 }}>{progress.completed_lessons}/{progress.total_lessons} מפגשים</span>
            </div>
            <div style={{ width: '100%', height: '10px', backgroundColor: 'rgba(255,255,255,0.2)', borderRadius: '5px', overflow: 'hidden' }}>
              <div style={{
                width: `${progress.percentage}%`,
                height: '100%',
                background: 'linear-gradient(90deg, #fbbf24, #f59e0b)',
                borderRadius: '5px',
                transition: 'width 0.5s ease'
              }} />
            </div>
          </div>
        </div>
      </div>

      {/* Main Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '1.5rem', minHeight: 'calc(100vh - 280px)' }}>
        {/* Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', overflowY: 'auto', maxHeight: 'calc(100vh - 280px)' }}>
          {topics.map((topic) => {
            const isActive = selectedTopic?.id === topic.id
            const topicDone = topic.lessons.length > 0 && topic.lessons.every(isLessonDone)
            
            return (
              <div key={topic.id}>
                {/* Topic Header */}
                <button
                  onClick={() => handleTopicSelect(topic)}
                  style={{
                    width: '100%',
                    padding: '0.85rem 1rem',
                    border: isActive ? '2px solid var(--primary)' : '1px solid var(--border)',
                    borderRadius: '10px',
                    background: isActive ? 'var(--primary-bg)' : 'var(--card)',
                    textAlign: 'right',
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem'
                  }}
                >
                  <span style={{
                    display: 'flex',
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    background: topicDone ? 'linear-gradient(135deg, #16a34a, #22c55e)' : isActive ? 'linear-gradient(135deg, var(--primary), #6366f1)' : 'var(--muted-bg)',
                    color: topicDone || isActive ? 'white' : 'var(--muted)',
                    fontSize: '0.8rem',
                    fontWeight: 700,
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    {topicDone ? <CheckCircle size={16} /> : topic.order_index + 1}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: isActive ? 600 : 500, color: isActive ? 'var(--primary)' : 'var(--text)' }}>
                      {topic.name}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '2px' }}>
                      {topic.lessons_count} מפגשים
                    </div>
                  </div>
                </button>

                {/* Lessons under active topic */}
                {isActive && topic.lessons.length > 0 && (
                  <div style={{ paddingRight: '1rem', marginTop: '0.5rem' }}>
                    {topic.lessons.map((lesson) => {
                      const done = isLessonDone(lesson)
                      const isSelected = selectedLesson?.id === lesson.id
                      return (
                        <button
                          key={lesson.id}
                          onClick={() => setSelectedLesson(lesson)}
                          style={{
                            width: '100%',
                            padding: '0.6rem 0.75rem',
                            border: 'none',
                            borderRight: isSelected ? '3px solid var(--primary)' : '3px solid transparent',
                            background: isSelected ? 'var(--hover)' : 'transparent',
                            textAlign: 'right',
                            cursor: 'pointer',
                            transition: 'all 0.1s',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            borderRadius: '0 6px 6px 0',
                            marginBottom: '2px'
                          }}
                        >
                          {done ? (
                            <CheckCircle size={14} style={{ color: '#16a34a', flexShrink: 0 }} />
                          ) : (
                            <div style={{
                              width: '14px', height: '14px', borderRadius: '50%',
                              border: '2px solid var(--border)', flexShrink: 0
                            }} />
                          )}
                          <span style={{
                            fontSize: '0.82rem',
                            fontWeight: isSelected ? 600 : 400,
                            color: isSelected ? 'var(--primary)' : 'var(--text)',
                            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
                          }}>
                            {lesson.lesson_number}. {lesson.title}
                          </span>
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Main Content */}
        <div style={{ overflowY: 'auto', maxHeight: 'calc(100vh - 280px)' }}>
          {selectedLesson ? (
            <div className={s.card} style={{ overflow: 'hidden' }}>
              {/* Lesson Hero */}
              <div style={{
                padding: '2rem 2.5rem',
                background: 'linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%)',
                borderBottom: '1px solid var(--border)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                  <span style={{
                    padding: '0.3rem 0.85rem',
                    borderRadius: '20px',
                    background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
                    color: 'white',
                    fontSize: '0.8rem',
                    fontWeight: 600
                  }}>
                    מפגש {selectedLesson.lesson_number}
                  </span>
                  {selectedLesson.lecturer_name && (
                    <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
                      {selectedLesson.lecturer_name}
                    </span>
                  )}
                  {isLessonDone(selectedLesson) && (
                    <span style={{
                      padding: '0.2rem 0.6rem',
                      borderRadius: '20px',
                      backgroundColor: '#dcfce7',
                      color: '#16a34a',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem'
                    }}>
                      <CheckCircle size={12} /> הושלם
                    </span>
                  )}
                </div>
                <h1 style={{ margin: '0 0 0.5rem', fontSize: '1.6rem', fontWeight: 700, color: '#1e293b' }}>
                  {selectedLesson.title}
                </h1>
                {selectedLesson.scheduled_date && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--muted)', fontSize: '0.85rem' }}>
                    <Clock size={14} />
                    <span>{formatDate(selectedLesson.scheduled_date)}</span>
                  </div>
                )}
              </div>

              {/* Video */}
              {selectedLesson.video_url ? (
                <div style={{ padding: '2rem 2.5rem', borderBottom: '1px solid var(--border)' }}>
                  <h3 style={{ margin: '0 0 1rem', fontSize: '1.05rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Video size={18} style={{ color: 'var(--primary)' }} />
                    הקלטת השיעור
                  </h3>
                  <div style={{
                    position: 'relative',
                    paddingBottom: '56.25%',
                    height: 0,
                    overflow: 'hidden',
                    borderRadius: '12px',
                    backgroundColor: '#0f172a'
                  }}>
                    <iframe
                      src={selectedLesson.video_url}
                      style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 'none' }}
                      allowFullScreen
                    />
                  </div>
                  {selectedLesson.progress && selectedLesson.progress.video_watch_percentage > 0 && (
                    <div style={{ marginTop: '0.75rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--muted)', marginBottom: '0.3rem' }}>
                        <span>התקדמות צפייה</span>
                        <span>{selectedLesson.progress.video_watch_percentage}%</span>
                      </div>
                      <div style={{ width: '100%', height: '4px', backgroundColor: 'var(--hover)', borderRadius: '2px', overflow: 'hidden' }}>
                        <div style={{ width: `${selectedLesson.progress.video_watch_percentage}%`, height: '100%', backgroundColor: 'var(--primary)', borderRadius: '2px' }} />
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ padding: '3rem 2.5rem', borderBottom: '1px solid var(--border)', textAlign: 'center' }}>
                  <div style={{
                    width: '64px', height: '64px', borderRadius: '50%',
                    backgroundColor: 'var(--hover)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    margin: '0 auto 1rem'
                  }}>
                    <Play size={28} style={{ color: 'var(--muted)', marginRight: '-2px' }} />
                  </div>
                  <p style={{ color: 'var(--muted)', margin: 0 }}>הקלטה עדיין לא זמינה</p>
                </div>
              )}

              {/* Description */}
              {selectedLesson.description && (
                <div style={{ padding: '2rem 2.5rem', borderBottom: '1px solid var(--border)' }}>
                  <h3 style={{ margin: '0 0 0.75rem', fontSize: '1.05rem', fontWeight: 600 }}>תיאור</h3>
                  <p style={{ margin: 0, lineHeight: 1.7, color: '#475569', fontSize: '0.95rem' }}>
                    {selectedLesson.description}
                  </p>
                </div>
              )}

              {/* Assignment */}
              {selectedLesson.assignment_title && (
                <div style={{ padding: '2rem 2.5rem' }}>
                  <h3 style={{ margin: '0 0 1rem', fontSize: '1.05rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <FileText size={18} style={{ color: '#f59e0b' }} />
                    מטלה
                  </h3>

                  <div style={{
                    padding: '1.5rem',
                    background: 'linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)',
                    borderRadius: '12px',
                    border: '1px solid #fde68a',
                    marginBottom: '1rem'
                  }}>
                    <h4 style={{ margin: '0 0 0.5rem', fontSize: '1rem', fontWeight: 600, color: '#92400e' }}>
                      {selectedLesson.assignment_title}
                    </h4>
                    {selectedLesson.assignment_description && (
                      <p style={{ margin: '0.5rem 0', lineHeight: 1.6, color: '#a16207', fontSize: '0.9rem' }}>
                        {selectedLesson.assignment_description}
                      </p>
                    )}
                    <div style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: '#b45309' }}>
                      מועד הגשה: {selectedLesson.assignment_due_days} ימים מתאריך השיעור
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
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

                    {selectedLesson.progress?.assignment_submitted ? (
                      <div style={{
                        padding: '0.6rem 1rem',
                        backgroundColor: '#dcfce7',
                        color: '#16a34a',
                        borderRadius: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        fontWeight: 600,
                        fontSize: '0.9rem'
                      }}>
                        <CheckCircle size={18} />
                        <span>המטלה הוגשה</span>
                        {selectedLesson.progress.assignment_grade !== null && (
                          <span style={{ marginRight: '0.5rem', padding: '0.15rem 0.5rem', backgroundColor: '#bbf7d0', borderRadius: '4px' }}>
                            ציון: {selectedLesson.progress.assignment_grade}
                          </span>
                        )}
                      </div>
                    ) : (
                      <button className={`${s.btn} ${s['btn-primary']}`} style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                        <FileText size={16} />
                        הגש מטלה
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* No content fallback */}
              {!selectedLesson.video_url && !selectedLesson.description && !selectedLesson.assignment_title && (
                <div style={{ padding: '3rem', textAlign: 'center' }}>
                  <p style={{ color: 'var(--muted)' }}>תוכן המפגש יעלה בקרוב</p>
                </div>
              )}
            </div>
          ) : (
            <div className={s.card} style={{ padding: '4rem', textAlign: 'center' }}>
              <BookOpen size={56} strokeWidth={1.2} style={{ margin: '0 auto 1.5rem', opacity: 0.15, display: 'block' }} />
              <h3 style={{ margin: '0 0 0.5rem', fontWeight: 600, color: 'var(--text)' }}>בחר מפגש</h3>
              <p style={{ color: 'var(--muted)', margin: 0 }}>לחץ על מפגש מהרשימה כדי לצפות בתוכן</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
