import { useEffect, useState } from 'react'
import { BarChart3, TrendingUp, Users, Phone, Globe, Award, AlertCircle } from 'lucide-react'
import { api } from '@/lib/api'
import s from '@/styles/shared.module.css'

interface AnalyticsData {
  period: string
  updated_at: string
  sales: {
    total_conversions: number
    salespeople: Array<{ name: string; conversions: number }>
  }
  leads: {
    total: number
    new: number
    in_process: number
    not_relevant: number
    total_closures: number
  }
  sources: {
    'טלפוני': number
    'אלמנטור': number
    'אחר': number
  }
  statuses: Record<string, number>
  conversions_by_source: {
    'טלפוני': number
    'אלמנטור': number
    'אחר': number
  }
  courses: {
    by_status: Array<{
      course_name: string
      'לא טופלו': number
      'בתהליך': number
      'נסלק/סגור': number
      'לא רלוונטי': number
      total: number
    }>
    conversion_rates: Array<{
      course_name: string
      total_leads: number
      conversions: number
      conversion_rate: number
    }>
  }
  insights: string[]
  comparison: {
    previous_month: {
      total_conversions: number
      total_leads: number
      conversion_rate: number
    }
    change: {
      conversions_percent: number
      leads_percent: number
      conversion_rate_percent: number
    }
  } | null
}

export function LeadAnalytics() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [year, setYear] = useState(new Date().getFullYear())
  const [month, setMonth] = useState(new Date().getMonth() + 1)
  const [comparePrevious, setComparePrevious] = useState(false)

  const fetchAnalytics = async () => {
    setLoading(true)
    try {
      const result = await api.get<AnalyticsData>(
        `leads/analytics?year=${year}&month=${month}&compare_previous=${comparePrevious}`
      )
      setData(result)
    } catch (err) {
      console.error('Error loading analytics:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAnalytics()
  }, [year, month, comparePrevious])

  const formatHebrewMonth = (y: number, m: number) => {
    const months = [
      'ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני',
      'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר'
    ]
    return `${months[m - 1]} ${y}`
  }

  const formatChange = (value: number) => {
    const sign = value >= 0 ? '+' : ''
    return `${sign}${value}%`
  }

  if (loading) {
    return (
      <div className={s.card} style={{ padding: 40, textAlign: 'center' }}>
        <div>טוען נתונים...</div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className={s.card} style={{ padding: 40, textAlign: 'center' }}>
        <AlertCircle size={48} style={{ color: 'var(--color-danger)', marginBottom: 16 }} />
        <div>שגיאה בטעינת נתונים</div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 24, fontWeight: 600 }}>דוח סיכום חודשי</h2>
          <div style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
            {formatHebrewMonth(year, month)} • עודכן לאחרונה: {new Date(data.updated_at).toLocaleTimeString('he-IL')}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <select
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
            className={s.select}
            style={{ padding: '8px 12px' }}
          >
            {Array.from({ length: 12 }, (_, i) => (
              <option key={i + 1} value={i + 1}>
                {i + 1}
              </option>
            ))}
          </select>
          <select
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className={s.select}
            style={{ padding: '8px 12px' }}
          >
            {[year - 1, year, year + 1].map(y => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={comparePrevious}
              onChange={(e) => setComparePrevious(e.target.checked)}
              style={{ width: 18, height: 18 }}
            />
            <span>השוואה לחודש קודם</span>
          </label>
        </div>
      </div>

      {/* Main KPI - Conversions */}
      <div
        className={s.card}
        style={{
          background: 'linear-gradient(135deg, #1e3a5f 0%, #10b981 100%)',
          color: 'white',
          padding: 32,
          borderRadius: 16
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: 16, opacity: 0.9, marginBottom: 8 }}>סך סגירות החודש</div>
            <div style={{ fontSize: 48, fontWeight: 700, lineHeight: 1 }}>{data.sales.total_conversions}</div>
            <div style={{ fontSize: 14, opacity: 0.8, marginTop: 8 }}>ביצועי שיא! 🎉</div>
          </div>
          <Award size={64} style={{ opacity: 0.3 }} />
        </div>
      </div>

      {/* Cards Row - Leads Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 16 }}>
        <div className={s.card} style={{ padding: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
            <Phone size={24} style={{ color: 'var(--color-primary)' }} />
            <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>סה"כ פניות</div>
          </div>
          <div style={{ fontSize: 36, fontWeight: 600 }}>{data.leads.total}</div>
        </div>

        <div className={s.card} style={{ padding: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
            <Users size={24} style={{ color: 'var(--color-success)' }} />
            <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>חדשים (לא טופלו)</div>
          </div>
          <div style={{ fontSize: 36, fontWeight: 600 }}>{data.leads.new}</div>
        </div>

        <div className={s.card} style={{ padding: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
            <TrendingUp size={24} style={{ color: 'var(--color-warning)' }} />
            <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>בתהליך</div>
          </div>
          <div style={{ fontSize: 36, fontWeight: 600 }}>{data.leads.in_process}</div>
        </div>

        <div className={s.card} style={{ padding: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
            <AlertCircle size={24} style={{ color: 'var(--color-danger)' }} />
            <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>לא רלוונטי</div>
          </div>
          <div style={{ fontSize: 36, fontWeight: 600 }}>{data.leads.not_relevant}</div>
        </div>
      </div>

      {/* Comparison with previous month */}
      {data.comparison && (
        <div className={s.card} style={{ padding: 24 }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: 18, fontWeight: 600 }}>השוואה לחודש הקודם</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
            <div>
              <div style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 4 }}>סגירות</div>
              <div style={{ fontSize: 24, fontWeight: 600 }}>
                {data.comparison.previous_month.total_conversions} → {data.sales.total_conversions}
              </div>
              <div style={{ 
                fontSize: 14, 
                color: data.comparison.change.conversions_percent >= 0 ? 'var(--color-success)' : 'var(--color-danger)',
                fontWeight: 600 
              }}>
                {formatChange(data.comparison.change.conversions_percent)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 4 }}>לידים</div>
              <div style={{ fontSize: 24, fontWeight: 600 }}>
                {data.comparison.previous_month.total_leads} → {data.leads.total}
              </div>
              <div style={{ 
                fontSize: 14, 
                color: data.comparison.change.leads_percent >= 0 ? 'var(--color-success)' : 'var(--color-danger)',
                fontWeight: 600 
              }}>
                {formatChange(data.comparison.change.leads_percent)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 4 }}>יחס המרה</div>
              <div style={{ fontSize: 24, fontWeight: 600 }}>
                {data.comparison.previous_month.conversion_rate}% → {(data.sales.total_conversions / data.leads.total * 100).toFixed(1)}%
              </div>
              <div style={{ 
                fontSize: 14, 
                color: data.comparison.change.conversion_rate_percent >= 0 ? 'var(--color-success)' : 'var(--color-danger)',
                fontWeight: 600 
              }}>
                {formatChange(data.comparison.change.conversion_rate_percent)}%
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Sales Leaders */}
      <div className={s.card} style={{ padding: 24 }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: 18, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Award size={20} style={{ color: '#f59e0b' }} />
          נבחרת השיאנים
        </h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'right' }}>
                <th style={{ padding: '12px 8px', fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)' }}>דירוג</th>
                <th style={{ padding: '12px 8px', fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)' }}>שם נציג</th>
                <th style={{ padding: '12px 8px', fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)' }}>סגירות</th>
              </tr>
            </thead>
            <tbody>
              {data.sales.salespeople.map((sp, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '12px 8px' }}>
                    {idx === 0 && '🥇'}
                    {idx === 1 && '🥈'}
                    {idx === 2 && '🥉'}
                    {idx > 2 && idx + 1}
                  </td>
                  <td style={{ padding: '12px 8px', fontWeight: 600 }}>{sp.name}</td>
                  <td style={{ padding: '12px 8px' }}>{sp.conversions}</td>
                </tr>
              ))}
              {data.sales.salespeople.length === 0 && (
                <tr>
                  <td colSpan={3} style={{ padding: 24, textAlign: 'center', color: 'var(--text-secondary)' }}>
                    אין נתונים
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Status Bars */}
      <div className={s.card} style={{ padding: 24 }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: 18, fontWeight: 600 }}>משפך המכירות</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {Object.entries(data.statuses).map(([status, count]) => {
            const percentage = data.leads.total > 0 ? (count / data.leads.total * 100) : 0
            const colors: Record<string, string> = {
              'בתהליך': '#10b981',
              'לא רלוונטי': '#6b7280',
              'נסלק/סגור': '#ef4444',
              'לא טופלו': '#f59e0b',
              'מתעניין': '#3b82f6',
              'במעקב': '#8b5cf6',
              'ליד ישן': '#ec4899',
              'חיוג ראשון': '#06b6d4'
            }
            const color = colors[status] || '#6b7280'
            return (
              <div key={status}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 14 }}>{status}</span>
                  <span style={{ fontSize: 14, fontWeight: 600 }}>{count} ({percentage.toFixed(1)}%)</span>
                </div>
                <div style={{ height: 8, background: 'var(--bg-accent)', borderRadius: 4, overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${percentage}%`,
                      background: color,
                      borderRadius: 4,
                      transition: 'width 0.3s ease'
                    }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Sources */}
      <div className={s.card} style={{ padding: 24 }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: 18, fontWeight: 600 }}>מקורות הגעה</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
          <div style={{ padding: 16, background: 'var(--bg-accent)', borderRadius: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <Phone size={20} style={{ color: 'var(--color-primary)' }} />
              <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>טלפוני</span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 600 }}>{data.sources['טלפוני']}</div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
              {data.conversions_by_source['טלפוני']} סגירות
            </div>
          </div>
          <div style={{ padding: 16, background: 'var(--bg-accent)', borderRadius: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <Globe size={20} style={{ color: 'var(--color-success)' }} />
              <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>אלמנטור</span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 600 }}>{data.sources['אלמנטור']}</div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
              {data.conversions_by_source['אלמנטור']} סגירות
            </div>
          </div>
          <div style={{ padding: 16, background: 'var(--bg-accent)', borderRadius: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <BarChart3 size={20} style={{ color: 'var(--color-warning)' }} />
              <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>אחר</span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 600 }}>{data.sources['אחר']}</div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
              {data.conversions_by_source['אחר']} סגירות
            </div>
          </div>
        </div>
      </div>

      {/* Courses Analysis */}
      <div className={s.card} style={{ padding: 24 }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: 18, fontWeight: 600 }}>ניתוח לפי קורסים</h3>
        
        {/* Conversion Rates */}
        <div style={{ marginBottom: 24 }}>
          <h4 style={{ margin: '0 0 12px 0', fontSize: 16, fontWeight: 600 }}>יחס המרה לפי קורס</h4>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'right' }}>
                  <th style={{ padding: '12px 8px', fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)' }}>קורס</th>
                  <th style={{ padding: '12px 8px', fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)' }}>סה"כ לידים</th>
                  <th style={{ padding: '12px 8px', fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)' }}>סגירות</th>
                  <th style={{ padding: '12px 8px', fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)' }}>יחס המרה</th>
                </tr>
              </thead>
              <tbody>
                {data.courses.conversion_rates.map((course, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '12px 8px', fontWeight: 600 }}>{course.course_name}</td>
                    <td style={{ padding: '12px 8px' }}>{course.total_leads}</td>
                    <td style={{ padding: '12px 8px' }}>{course.conversions}</td>
                    <td style={{ padding: '12px 8px' }}>
                      <span style={{
                        padding: '4px 8px',
                        borderRadius: 4,
                        fontSize: 14,
                        fontWeight: 600,
                        background: course.conversion_rate >= 20 ? 'var(--bg-success)' : 
                                   course.conversion_rate >= 10 ? 'var(--bg-warning)' : 'var(--bg-danger)',
                        color: course.conversion_rate >= 20 ? 'var(--color-success)' : 
                                course.conversion_rate >= 10 ? 'var(--color-warning)' : 'var(--color-danger)'
                      }}>
                        {course.conversion_rate}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Insights */}
      <div
        className={s.card}
        style={{
          padding: 24,
          background: 'linear-gradient(135deg, #e0f2fe 0%, #f0fdf4 100%)',
          border: '1px solid #bae6fd'
        }}
      >
        <h3 style={{ margin: '0 0 16px 0', fontSize: 18, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
          <BarChart3 size={20} style={{ color: '#0284c7' }} />
          תובנות מערכת
        </h3>
        <ul style={{ margin: 0, paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 8 }}>
          {data.insights.map((insight, idx) => (
            <li key={idx} style={{ fontSize: 14, lineHeight: 1.6 }}>
              {insight}
            </li>
          ))}
          {data.insights.length === 0 && (
            <li style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              אין תובנות זמינות עדיין
            </li>
          )}
        </ul>
      </div>
    </div>
  )
}
