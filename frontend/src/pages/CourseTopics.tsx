import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowRight, GripVertical, BookOpen } from 'lucide-react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import s from '@/styles/shared.module.css'

interface Topic {
  id: number
  name: string
  description: string | null
  order_index: number
  lessons_count: number
  first_lesson: {
    id: number
    title: string
    scheduled_date: string | null
  } | null
}

interface TopicsResponse {
  success: boolean
  topics: Topic[]
}

export function CourseTopicsPage() {
  const { courseId } = useParams<{ courseId: string }>()
  const navigate = useNavigate()
  const toast = useToast()

  const [topics, setTopics] = useState<Topic[]>([])
  const [loading, setLoading] = useState(true)
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)

  const fetchTopics = useCallback(async () => {
    if (!courseId) return
    setLoading(true)
    try {
      const data = await api.get<TopicsResponse>(`topics/courses/${courseId}/topics`)
      if (data.success) {
        setTopics(data.topics)
      }
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בטעינת נושאים')
    } finally {
      setLoading(false)
    }
  }, [courseId, toast])

  useEffect(() => {
    fetchTopics()
  }, [fetchTopics])

  const handleDragStart = (index: number) => {
    setDraggedIndex(index)
  }

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault()
    if (draggedIndex === null || draggedIndex === index) return

    const newTopics = [...topics]
    const draggedTopic = newTopics[draggedIndex]
    newTopics.splice(draggedIndex, 1)
    newTopics.splice(index, 0, draggedTopic)

    setTopics(newTopics)
    setDraggedIndex(index)
  }

  const handleDragEnd = async () => {
    if (draggedIndex === null) return

    const newOrder = topics.map(t => t.id)
    
    try {
      await api.post(`topics/courses/${courseId}/topics/reorder`, {
        new_order: newOrder
      })
      toast.success('סדר הנושאים עודכן בהצלחה')
      await fetchTopics()
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בעדכון סדר הנושאים')
      await fetchTopics()
    } finally {
      setDraggedIndex(null)
    }
  }

  const openTopicLessons = (topicId: number) => {
    navigate(`/admin/topics/${topicId}/lessons`)
  }

  if (loading) {
    return (
      <div className={s.card}>
        <div style={{ padding: '2rem', textAlign: 'center' }}>טוען נושאים...</div>
      </div>
    )
  }

  return (
    <div>
      <div className={s['page-header']}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button
            className={`${s.btn} ${s['btn-secondary']}`}
            onClick={() => navigate('/admin/courses')}
          >
            <ArrowRight size={16} />
          </button>
          <h1 className={s['page-title']}>ניהול נושאים</h1>
        </div>
      </div>

      <div className={s.card}>
        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border)' }}>
          <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>
            נושאי הקורס
          </h3>
          <p style={{ margin: '0.5rem 0 0', color: 'var(--muted)', fontSize: '0.9rem' }}>
            גרור והזז נושאים כדי לשנות את הסדר. לחץ על נושא לצפייה במפגשים.
          </p>
        </div>

        {topics.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <BookOpen size={48} strokeWidth={1.5} style={{ margin: '0 auto 1rem', opacity: 0.3 }} />
            <p style={{ color: 'var(--muted)' }}>לא נמצאו נושאים לקורס זה</p>
          </div>
        ) : (
          <div style={{ padding: '1rem' }}>
            {topics.map((topic, index) => (
              <div
                key={topic.id}
                draggable
                onDragStart={() => handleDragStart(index)}
                onDragOver={(e) => handleDragOver(e, index)}
                onDragEnd={handleDragEnd}
                onClick={() => openTopicLessons(topic.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem',
                  padding: '1rem',
                  marginBottom: '0.5rem',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  backgroundColor: draggedIndex === index ? 'var(--hover)' : 'transparent',
                  cursor: 'grab',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  if (draggedIndex === null) {
                    e.currentTarget.style.backgroundColor = 'var(--hover)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (draggedIndex === null) {
                    e.currentTarget.style.backgroundColor = 'transparent'
                  }
                }}
              >
                <GripVertical size={20} style={{ color: 'var(--muted)', flexShrink: 0 }} />
                
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                    <span style={{ 
                      display: 'flex',
                      width: '24px',
                      height: '24px',
                      borderRadius: '50%',
                      backgroundColor: 'var(--primary)',
                      color: 'white',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      {index + 1}
                    </span>
                    <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>
                      {topic.name}
                    </h4>
                  </div>
                  
                  {topic.description && (
                    <p style={{ margin: '0.25rem 0 0 2rem', fontSize: '0.85rem', color: 'var(--muted)' }}>
                      {topic.description}
                    </p>
                  )}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.25rem' }}>
                  <span className={s.badge}>
                    {topic.lessons_count} מפגשים
                  </span>
                  {topic.first_lesson && (
                    <span style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
                      מתחיל: {topic.first_lesson.title}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
