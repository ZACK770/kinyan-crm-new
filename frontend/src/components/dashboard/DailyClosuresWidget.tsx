import { Trophy, TrendingUp, Calendar } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import s from '@/styles/shared.module.css'

interface DailyClosuresData {
  today: {
    date: string
    performers: Array<{ id: number; name: string; closures: number }>
    total_performers: number
  }
  weekly: {
    from: string
    to: string
    performers: Array<{ 
      id: number
      name: string
      days_with_2plus_closures: number
      total_closures_week: number
    }>
    daily_breakdown: Array<{
      date: string
      performers: Array<{ id: number; name: string; closures: number }>
      total_performers: number
    }>
  }
}

interface DailyClosuresWidgetProps {
  data: DailyClosuresData | null
  loading: boolean
}

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899']

export function DailyClosuresWidget({ data, loading }: DailyClosuresWidgetProps) {
  if (loading) {
    return (
      <div className={s.card} style={{ padding: 20 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Trophy size={18} />
          סגירות יומיות (2+)
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 40 }}>
          <div style={{ color: 'var(--color-text-muted)' }}>טוען נתונים...</div>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className={s.card} style={{ padding: 20 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Trophy size={18} />
          סגירות יומיות (2+)
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 40 }}>
          <div style={{ color: 'var(--color-text-muted)' }}>אין נתונים להצגה</div>
        </div>
      </div>
    )
  }

  const { today, weekly } = data

  // Prepare chart data for weekly breakdown
  const chartData = weekly.daily_breakdown
    .slice()
    .reverse()
    .map(day => ({
      date: new Date(day.date).toLocaleDateString('he-IL', { day: '2-digit', month: '2-digit' }),
      performers: day.total_performers,
    }))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Today's Performers */}
      <div className={s.card} style={{ padding: 20 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Trophy size={18} style={{ color: '#10b981' }} />
          ביצעו 2+ סגירות היום ({today.date})
        </h3>
        
        {today.total_performers === 0 ? (
          <div style={{ 
            padding: 24, 
            textAlign: 'center', 
            color: 'var(--color-text-muted)',
            background: 'var(--color-bg-subtle, #f9fafb)',
            borderRadius: 8
          }}>
            אין עדיין מי שביצע 2+ סגירות היום
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {today.performers.map((performer, index) => (
              <div 
                key={performer.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: 12,
                  background: index === 0 ? 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)' : 'var(--color-bg-subtle, #f9fafb)',
                  borderRadius: 8,
                  border: index === 0 ? '2px solid #f59e0b' : '1px solid var(--color-border-light)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  {index === 0 && <Trophy size={20} style={{ color: '#f59e0b' }} />}
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>{performer.name}</div>
                    {index === 0 && (
                      <div style={{ fontSize: 11, color: '#92400e', fontWeight: 500 }}>🏆 מוביל היום</div>
                    )}
                  </div>
                </div>
                <div style={{
                  background: index === 0 ? '#f59e0b' : 'var(--color-primary)',
                  color: 'white',
                  padding: '4px 12px',
                  borderRadius: 12,
                  fontSize: 14,
                  fontWeight: 700,
                }}>
                  {performer.closures} סגירות
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Weekly Summary */}
      <div className={s.card} style={{ padding: 20 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <TrendingUp size={18} style={{ color: '#3b82f6' }} />
          ביצועים שבועיים (7 ימים אחרונים)
        </h3>
        
        {weekly.performers.length === 0 ? (
          <div style={{ 
            padding: 24, 
            textAlign: 'center', 
            color: 'var(--color-text-muted)',
            background: 'var(--color-bg-subtle, #f9fafb)',
            borderRadius: 8
          }}>
            אין מי שביצע 2+ סגירות בשבוע האחרון
          </div>
        ) : (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12, marginBottom: 20 }}>
              {weekly.performers.slice(0, 5).map((performer) => (
                <div 
                  key={performer.id}
                  style={{
                    padding: 16,
                    background: 'var(--color-bg-subtle, #f9fafb)',
                    borderRadius: 8,
                    border: '1px solid var(--color-border-light)',
                  }}
                >
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>{performer.name}</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                      <span style={{ fontWeight: 600, color: 'var(--color-primary)' }}>
                        {performer.days_with_2plus_closures}
                      </span> ימים עם 2+ סגירות
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                      סה"כ <span style={{ fontWeight: 600 }}>{performer.total_closures_week}</span> סגירות
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Daily Breakdown Chart */}
            <div style={{ marginTop: 20, paddingTop: 20, borderTop: '1px solid var(--color-border-light)' }}>
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                <Calendar size={16} />
                פילוח יומי - כמה אנשים ביצעו 2+ סגירות בכל יום
              </h4>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 11 }}
                    tickLine={false}
                  />
                  <YAxis 
                    tick={{ fontSize: 11 }}
                    tickLine={false}
                    allowDecimals={false}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      background: 'white', 
                      border: '1px solid #e5e7eb',
                      borderRadius: 8,
                      padding: 8,
                      fontSize: 12
                    }}
                    formatter={(value: any) => [`${value} אנשים`, 'ביצעו 2+ סגירות']}
                  />
                  <Bar dataKey="performers" radius={[4, 4, 0, 0]}>
                    {chartData.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
