import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowRight, GripVertical, BookOpen, Plus, Trash2, ChevronLeft } from 'lucide-react'
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
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [creating, setCreating] = useState(false)

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
      toast.success('סדר הנושאים עודכן')
      await fetchTopics()
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בעדכון סדר')
      await fetchTopics()
    } finally {
      setDraggedIndex(null)
    }
  }

  const handleCreate = async () => {
    if (!newName.trim() || !courseId) return
    setCreating(true)
    try {
      await api.post(`topics/courses/${courseId}/topics`, {
        name: newName.trim(),
        description: newDesc.trim() || null
      })
      toast.success('נושא נוצר בהצלחה')
      setNewName('')
      setNewDesc('')
      setShowCreate(false)
      await fetchTopics()
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה ביצירת נושא')
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (e: React.MouseEvent, topicId: number) => {
    e.stopPropagation()
    if (!confirm('למחוק את הנושא? כל המפגשים שלו יימחקו.')) return
    try {
      await api.delete(`topics/topics/${topicId}`)
      toast.success('נושא נמחק')
      await fetchTopics()
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה במחיקה')
    }
  }

  if (loading) {
    return (
      <div className={s.card}>
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--muted)' }}>
          <div style={{ width: '32px', height: '32px', border: '3px solid var(--border)', borderTopColor: 'var(--primary)', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 1rem' }} />
          טוען נושאים...
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
            onClick={() => navigate('/courses')}
            title="חזרה לקורסים"
          >
            <ArrowRight size={16} />
          </button>
          <div>
            <h1 className={s['page-title']}>ניהול נושאים</h1>
            <p style={{ margin: '0.25rem 0 0', color: 'var(--muted)', fontSize: '0.85rem' }}>
              גרור להזיז סדר, לחץ לצפייה במפגשים
            </p>
          </div>
        </div>
        <button className={`${s.btn} ${s['btn-primary']}`} onClick={() => setShowCreate(true)}>
          <Plus size={16} /> נושא חדש
        </button>
      </div>

      {/* Create Topic Form */}
      {showCreate && (
        <div className={s.card} style={{ marginBottom: '1rem', border: '2px solid var(--primary)' }}>
          <div style={{ padding: '1.5rem' }}>
            <h3 style={{ margin: '0 0 1rem', fontSize: '1rem', fontWeight: 600 }}>נושא חדש</h3>
            <div style={{ display: 'grid', gap: '0.75rem' }}>
              <input
                type="text"
                placeholder="שם הנושא *"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
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
              <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                <button className={`${s.btn} ${s['btn-secondary']}`} onClick={() => { setShowCreate(false); setNewName(''); setNewDesc('') }}>
                  ביטול
                </button>
                <button className={`${s.btn} ${s['btn-primary']}`} onClick={handleCreate} disabled={creating || !newName.trim()}>
                  {creating ? 'יוצר...' : 'צור נושא'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className={s.card}>
        {topics.length === 0 ? (
          <div style={{ padding: '4rem 2rem', textAlign: 'center' }}>
            <BookOpen size={56} strokeWidth={1.2} style={{ margin: '0 auto 1.5rem', opacity: 0.2, display: 'block' }} />
            <h3 style={{ margin: '0 0 0.5rem', fontWeight: 600, color: 'var(--text)' }}>אין נושאים עדיין</h3>
            <p style={{ color: 'var(--muted)', margin: '0 0 1.5rem' }}>צור את הנושא הראשון כדי להתחיל לבנות את מבנה הקורס</p>
            <button className={`${s.btn} ${s['btn-primary']}`} onClick={() => setShowCreate(true)}>
              <Plus size={16} /> צור נושא ראשון
            </button>
          </div>
        ) : (
          <div style={{ padding: '0.75rem' }}>
            {topics.map((topic, index) => (
              <div
                key={topic.id}
                draggable
                onDragStart={() => handleDragStart(index)}
                onDragOver={(e) => handleDragOver(e, index)}
                onDragEnd={handleDragEnd}
                onClick={() => navigate(`/admin/topics/${topic.id}/lessons`)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem',
                  padding: '1rem 1.25rem',
                  marginBottom: '0.5rem',
                  border: '1px solid var(--border)',
                  borderRadius: '10px',
                  backgroundColor: draggedIndex === index ? 'var(--primary-bg)' : 'var(--card)',
                  cursor: 'grab',
                  transition: 'all 0.15s ease',
                  boxShadow: draggedIndex === index ? '0 4px 12px rgba(0,0,0,0.1)' : 'none'
                }}
                onMouseEnter={(e) => {
                  if (draggedIndex === null) {
                    e.currentTarget.style.backgroundColor = 'var(--hover)'
                    e.currentTarget.style.borderColor = 'var(--primary)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (draggedIndex === null) {
                    e.currentTarget.style.backgroundColor = 'var(--card)'
                    e.currentTarget.style.borderColor = 'var(--border)'
                  }
                }}
              >
                <GripVertical size={18} style={{ color: 'var(--muted)', flexShrink: 0, opacity: 0.5 }} />
                
                <span style={{ 
                  display: 'flex',
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, var(--primary), #6366f1)',
                  color: 'white',
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}>
                  {index + 1}
                </span>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>
                    {topic.name}
                  </h4>
                  {topic.description && (
                    <p style={{ margin: '0.25rem 0 0', fontSize: '0.85rem', color: 'var(--muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {topic.description}
                    </p>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexShrink: 0 }}>
                  <span style={{
                    padding: '0.3rem 0.75rem',
                    borderRadius: '20px',
                    fontSize: '0.8rem',
                    fontWeight: 500,
                    backgroundColor: topic.lessons_count > 0 ? 'var(--primary-bg)' : 'var(--muted-bg)',
                    color: topic.lessons_count > 0 ? 'var(--primary)' : 'var(--muted)'
                  }}>
                    {topic.lessons_count} מפגשים
                  </span>
                  
                  <button
                    onClick={(e) => handleDelete(e, topic.id)}
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
                    title="מחק נושא"
                  >
                    <Trash2 size={16} />
                  </button>

                  <ChevronLeft size={18} style={{ color: 'var(--muted)', opacity: 0.5 }} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
