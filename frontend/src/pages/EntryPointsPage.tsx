/**
 * EntryPointsPage - דף נקודות כניסה
 */
import { useEffect, useState, useCallback } from 'react'
import { MapPin, Calendar, Users, Clock, DollarSign, RefreshCw } from 'lucide-react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import s from '@/styles/shared.module.css'

interface EntryPoint {
  track_id: number
  track_name: string
  course_name?: string
  lecturer_name?: string
  city: string
  day_of_week: string
  start_time: string
  next_entry_date: string
  current_module_name?: string
  price?: number
  zoom_url?: string
}

export function EntryPointsPage() {
  const [entryPoints, setEntryPoints] = useState<EntryPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [filterCity, setFilterCity] = useState('')
  const [filterDays, setFilterDays] = useState(30)
  const toast = useToast()

  const fetchEntryPoints = useCallback(async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams({ days_ahead: filterDays.toString() })
      if (filterCity) params.append('city', filterCity)
      const data = await api.get<{ entry_points: EntryPoint[] }>(`/course-tracks/upcoming-entry-points?${params}`)
      setEntryPoints(data.entry_points || [])
    } catch (err) {
      toast.error('שגיאה בטעינת נקודות כניסה')
    } finally {
      setLoading(false)
    }
  }, [filterCity, filterDays, toast])

  useEffect(() => {
    fetchEntryPoints()
  }, [fetchEntryPoints])

  const cities = Array.from(new Set(entryPoints.map(ep => ep.city))).sort()

  const groupedByDate = entryPoints.reduce((acc, ep) => {
    const date = ep.next_entry_date
    if (!acc[date]) acc[date] = []
    acc[date].push(ep)
    return acc
  }, {} as Record<string, EntryPoint[]>)

  const sortedDates = Object.keys(groupedByDate).sort()

  return (
    <div>
      <div className={s['page-header']}>
        <div>
          <h1 className={s['page-title']}>נקודות כניסה קרובות</h1>
          <p style={{ fontSize: 14, color: 'var(--color-text-secondary)', marginTop: 4 }}>
            מסלולים שמתחילים חוברת חדשה - הזדמנות לשילוב לידים
          </p>
        </div>
        <div className={s['page-actions']}>
          <button className={`${s.btn} ${s['btn-secondary']}`} onClick={fetchEntryPoints}>
            <RefreshCw size={16} />
            רענן
          </button>
        </div>
      </div>

      <div className={s.card}>
        <div className={s.toolbar}>
          <select className={s['select-sm']} value={filterCity} onChange={(e) => setFilterCity(e.target.value)}>
            <option value="">כל הערים</option>
            {cities.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <select className={s['select-sm']} value={filterDays} onChange={(e) => setFilterDays(Number(e.target.value))}>
            <option value={7}>שבוע קדימה</option>
            <option value={14}>שבועיים קדימה</option>
            <option value={30}>חודש קדימה</option>
            <option value={60}>חודשיים קדימה</option>
            <option value={90}>3 חודשים קדימה</option>
          </select>
          <div style={{ flex: 1 }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 24, fontWeight: 700, color: 'var(--color-primary)' }}>{entryPoints.length}</span>
            <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>נקודות כניסה</span>
          </div>
        </div>

        <div className={s['card-body-flush']}>
          {loading ? (
            <div className={s.loading}>טוען נקודות כניסה...</div>
          ) : entryPoints.length === 0 ? (
            <div className={s.empty}>
              <Calendar size={48} className={s['empty-icon']} />
              <div className={s['empty-text']}>אין נקודות כניסה בטווח הזמן שנבחר</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {sortedDates.map(date => {
                const entryDate = new Date(date)
                const today = new Date()
                const daysUntil = Math.ceil((entryDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
                const dateLabel = daysUntil === 0 ? 'היום' : daysUntil === 1 ? 'מחר' : daysUntil === 2 ? 'מחרתיים' : `בעוד ${daysUntil} ימים`
                const points = groupedByDate[date]

                return (
                  <div key={date} style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                    <div style={{ 
                      background: 'linear-gradient(to left, #eff6ff, #e0f2fe)', 
                      padding: '12px 20px',
                      borderBottom: '1px solid var(--color-border-light)'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                          <Calendar size={20} style={{ color: 'var(--color-primary)' }} />
                          <div>
                            <div style={{ fontWeight: 600, fontSize: 15 }}>
                              {entryDate.toLocaleDateString('he-IL', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                            </div>
                            <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>{dateLabel}</div>
                          </div>
                        </div>
                        <div style={{ textAlign: 'left' }}>
                          <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--color-primary)' }}>{points.length}</div>
                          <div style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>מסלולים</div>
                        </div>
                      </div>
                    </div>

                    {points.map((ep, idx) => (
                      <div key={`${ep.track_id}-${idx}`} style={{ 
                        padding: '16px 20px',
                        borderBottom: idx < points.length - 1 ? '1px solid var(--color-border-light)' : 'none',
                        transition: 'background var(--transition-fast)',
                        cursor: 'pointer'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = '#fafbfc'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                      >
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                          <div>
                            <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 4 }}>{ep.track_name}</div>
                            {ep.course_name && (
                              <span className={`${s.badge} ${s['badge-blue']}`}>{ep.course_name}</span>
                            )}
                          </div>

                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, fontSize: 13 }}>
                            {ep.lecturer_name && (
                              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-text)' }}>
                                <Users size={16} style={{ color: 'var(--color-text-muted)' }} />
                                <span style={{ fontWeight: 500 }}>מרצה:</span>
                                <span>{ep.lecturer_name}</span>
                              </div>
                            )}

                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-text)' }}>
                              <MapPin size={16} style={{ color: 'var(--color-text-muted)' }} />
                              <span>{ep.city}</span>
                              <span style={{ color: 'var(--color-text-muted)' }}>•</span>
                              <Clock size={16} style={{ color: 'var(--color-text-muted)' }} />
                              <span>{ep.day_of_week} {ep.start_time}</span>
                            </div>

                            {ep.current_module_name && (
                              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-text)' }}>
                                <span style={{ fontWeight: 500 }}>חוברת מתחילה:</span>
                                <span>{ep.current_module_name}</span>
                              </div>
                            )}

                            {ep.price && (
                              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-text)' }}>
                                <DollarSign size={16} style={{ color: 'var(--color-text-muted)' }} />
                                <span style={{ fontWeight: 500 }}>מחיר:</span>
                                <span>₪{ep.price.toLocaleString()}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
