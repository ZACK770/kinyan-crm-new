import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowRight, BookOpen, Video, FileText, Users, Plus, Trash2, Calendar, ChevronLeft } from 'lucide-react'
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
  const [showCreate, setShowCreate] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [newDate, setNewDate] = useState('')
  const [creating, setCreating] = useState(false)

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

  const handleCreate = async () => {
    if (!newTitle.trim() || !topicId) return
    setCreating(true)
    try {
      await api.post(`topics/topics/${topicId}/lessons`, {
        title: newTitle.trim(),
        description: newDesc.trim() || null,
        scheduled_date: newDate || null
      })
      toast.success('מפגש נוצר בהצלחה')
      setNewTitle('')
      setNewDesc('')
      setNewDate('')
      setShowCreate(false)
      await fetchLessons()
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה ביצירת מפגש')
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (e: React.MouseEvent, lessonId: number) => {
    e.stopPropagation()
    if (!confirm('למחוק את המפגש?')) return
    try {
      await api.delete(`topics/lessons/${lessonId}`)
      toast.success('מפגש נמחק')
      await fetchLessons()
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה במחיקה')
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null
    const date = new Date(dateStr)
    return date.toLocaleDateString('he-IL', { day: '2-digit', month: '2-digit', year: 'numeric' })
  }

  const statusConfig: Record<string, { label: string; bg: string; color: string }> = {
    completed: { label: 'הסתיים', bg: '#dcfce7', color: '#16a34a' },
    scheduled: { label: 'מתוכנן', bg: '#dbeafe', color: '#2563eb' },
    cancelled: { label: 'בוטל', bg: '#fee2e2', color: '#dc2626' }
  }

  if (loading) {
    return (
      <div className={s.card}>
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--muted)' }}>
          <div style={{ width: '32px', height: '32px', border: '3px solid var(--border)', borderTopColor: 'var(--primary)', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 1rem' }} />
          טוען מפגשים...
        </div>
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
            title="חזרה לנושאים"
          >
            <ArrowRight size={16} />
          </button>
          <div>
            <h1 className={s['page-title']}>{topic?.name}</h1>
            <p style={{ margin: '0.25rem 0 0', color: 'var(--muted)', fontSize: '0.85rem' }}>
              {lessons.length} מפגשים
            </p>
          </div>
        </div>
        <button className={`${s.btn} ${s['btn-primary']}`} onClick={() => setShowCreate(true)}>
          <Plus size={16} /> מפגש חדש
        </button>
      </div>

      {/* Create Lesson Form */}
      {showCreate && (
        <div className={s.card} style={{ marginBottom: '1rem', border: '2px solid var(--primary)' }}>
          <div style={{ padding: '1.5rem' }}>
            <h3 style={{ margin: '0 0 1rem', fontSize: '1rem', fontWeight: 600 }}>מפגש חדש</h3>
            <div style={{ display: 'grid', gap: '0.75rem' }}>
              <input
                type="text"
                placeholder="כותרת המפגש *"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                className={s.input}
                autoFocus
                onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
              />
              <input
                type="text"
                placeholder="תיאור (אופציונלי)"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                className={s.input}
              />
              <div>
                <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.85rem', color: 'var(--muted)' }}>תאריך מתוכנן</label>
                <input
                  type="date"
                  value={newDate}
                  onChange={(e) => setNewDate(e.target.value)}
                  className={s.input}
                />
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                <button className={`${s.btn} ${s['btn-secondary']}`} onClick={() => { setShowCreate(false); setNewTitle(''); setNewDesc(''); setNewDate('') }}>
                  ביטול
                </button>
                <button className={`${s.btn} ${s['btn-primary']}`} onClick={handleCreate} disabled={creating || !newTitle.trim()}>
                  {creating ? 'יוצר...' : 'צור מפגש'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {lessons.length === 0 ? (
        <div className={s.card} style={{ padding: '4rem 2rem', textAlign: 'center' }}>
          <BookOpen size={56} strokeWidth={1.2} style={{ margin: '0 auto 1.5rem', opacity: 0.2, display: 'block' }} />
          <h3 style={{ margin: '0 0 0.5rem', fontWeight: 600 }}>אין מפגשים עדיין</h3>
          <p style={{ color: 'var(--muted)', margin: '0 0 1.5rem' }}>צור את המפגש הראשון לנושא זה</p>
          <button className={`${s.btn} ${s['btn-primary']}`} onClick={() => setShowCreate(true)}>
            <Plus size={16} /> צור מפגש ראשון
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {lessons.map((lesson) => (
            <div
              key={lesson.id}
              className={s.card}
              onClick={() => navigate(`/admin/lessons/${lesson.id}`)}
              style={{
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                border: '1px solid var(--border)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--primary)'
                e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.06)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border)'
                e.currentTarget.style.boxShadow = 'none'
              }}
            >
              <div style={{ display: 'flex', gap: '1.25rem', padding: '1.25rem' }}>
                {/* Cover / Number */}
                <div style={{
                  width: '80px',
                  height: '80px',
                  borderRadius: '10px',
                  overflow: 'hidden',
                  backgroundColor: 'var(--hover)',
                  flexShrink: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  position: 'relative'
                }}>
                  {lesson.cover_image_url ? (
                    <img 
                      src={lesson.cover_image_url} 
                      alt={lesson.title}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                  ) : (
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--primary)', lineHeight: 1 }}>
                        {lesson.lesson_number}
                      </div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--muted)', marginTop: '2px' }}>מפגש</div>
                    </div>
                  )}
                  {lesson.video_url && (
                    <div style={{
                      position: 'absolute',
                      bottom: '4px',
                      left: '4px',
                      width: '20px',
                      height: '20px',
                      borderRadius: '50%',
                      backgroundColor: '#16a34a',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <Video size={10} style={{ color: 'white' }} />
                    </div>
                  )}
                </div>

                {/* Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
                    <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 600 }}>
                      {lesson.title}
                    </h3>
                    {(() => {
                      const cfg = statusConfig[lesson.status] || statusConfig.scheduled
                      return (
                        <span style={{
                          padding: '0.15rem 0.5rem',
                          borderRadius: '20px',
                          fontSize: '0.7rem',
                          fontWeight: 600,
                          backgroundColor: cfg.bg,
                          color: cfg.color
                        }}>
                          {cfg.label}
                        </span>
                      )
                    })()}
                  </div>

                  {lesson.description && (
                    <p style={{ margin: '0 0 0.5rem', fontSize: '0.85rem', color: 'var(--muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {lesson.description}
                    </p>
                  )}

                  <div style={{ display: 'flex', gap: '1.25rem', fontSize: '0.8rem', color: 'var(--muted)' }}>
                    {lesson.lecturer_name && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <Users size={13} /> {lesson.lecturer_name}
                      </span>
                    )}
                    {formatDate(lesson.scheduled_date) && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <Calendar size={13} /> {formatDate(lesson.scheduled_date)}
                      </span>
                    )}
                    {lesson.assignment_title && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <FileText size={13} /> {lesson.assignment_submitted_count}/{lesson.students_count} הגישו
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
                  <button
                    onClick={(e) => handleDelete(e, lesson.id)}
                    style={{
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      padding: '0.4rem',
                      borderRadius: '6px',
                      color: 'var(--muted)',
                      transition: 'all 0.15s'
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.color = '#ef4444'; e.currentTarget.style.backgroundColor = '#fef2f2' }}
                    onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--muted)'; e.currentTarget.style.backgroundColor = 'transparent' }}
                    title="מחק מפגש"
                  >
                    <Trash2 size={16} />
                  </button>
                  <ChevronLeft size={18} style={{ color: 'var(--muted)', opacity: 0.5 }} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
