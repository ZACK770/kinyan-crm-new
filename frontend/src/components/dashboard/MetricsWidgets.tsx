import { TrendingUp, TrendingDown, Phone, Target, Clock, Users } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import s from '@/styles/shared.module.css'

interface MetricsData {
  lead_treatment: {
    total_leads: number
    leads_in_process: number
    neglected_leads: number
    avg_time_to_first_call_days: number
  }
  conversions: {
    converted_leads: number
    conversion_rate: number
    avg_time_to_conversion_days: number
  }
  monthly_comparison: {
    current_month: {
      total: number
      converted: number
      conversion_rate: number
    }
    previous_month: {
      total: number
      converted: number
      conversion_rate: number
    }
    change: {
      total_diff: number
      converted_diff: number
      rate_diff: number
    }
  }
}

interface MetricsWidgetsProps {
  data: MetricsData | null
  loading: boolean
}

function MetricCard({ 
  title, 
  value, 
  subtitle, 
  icon: Icon, 
  trend 
}: { 
  title: string
  value: string | number
  subtitle?: string
  icon: any
  trend?: { value: number; isPositive: boolean }
}) {
  return (
    <div className={s.card} style={{ padding: 20 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{ 
          width: 40, 
          height: 40, 
          borderRadius: 8, 
          background: 'var(--color-primary-light, #eff6ff)', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: 'var(--color-primary)'
        }}>
          <Icon size={20} />
        </div>
        {trend && (
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 4,
            fontSize: 13,
            fontWeight: 600,
            color: trend.isPositive ? 'var(--color-success)' : 'var(--color-error)'
          }}>
            {trend.isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
            {Math.abs(trend.value)}%
          </div>
        )}
      </div>
      <div style={{ fontSize: 13, color: 'var(--color-text-muted)', marginBottom: 4 }}>{title}</div>
      <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--color-text)' }}>{value}</div>
      {subtitle && <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 4 }}>{subtitle}</div>}
    </div>
  )
}

export function MetricsWidgets({ data, loading }: MetricsWidgetsProps) {
  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 60 }}>
        <div style={{ color: 'var(--color-text-muted)' }}>טוען נתונים...</div>
      </div>
    )
  }

  if (!data) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 60 }}>
        <div style={{ color: 'var(--color-text-muted)' }}>אין נתונים להצגה</div>
      </div>
    )
  }

  const { lead_treatment, conversions, monthly_comparison } = data

  // Calculate trends
  const totalTrend = monthly_comparison.change.total_diff !== 0
    ? {
        value: Math.round(Math.abs(monthly_comparison.change.total_diff / monthly_comparison.previous_month.total * 100)),
        isPositive: monthly_comparison.change.total_diff > 0
      }
    : undefined

  const conversionTrend = monthly_comparison.change.rate_diff !== 0
    ? {
        value: Math.abs(monthly_comparison.change.rate_diff),
        isPositive: monthly_comparison.change.rate_diff > 0
      }
    : undefined

  // Prepare comparison chart data
  const comparisonData = [
    {
      name: 'חודש קודם',
      'סה"כ לידים': monthly_comparison.previous_month.total,
      'הומרו': monthly_comparison.previous_month.converted,
      'אחוז המרה': monthly_comparison.previous_month.conversion_rate,
    },
    {
      name: 'חודש נוכחי',
      'סה"כ לידים': monthly_comparison.current_month.total,
      'הומרו': monthly_comparison.current_month.converted,
      'אחוז המרה': monthly_comparison.current_month.conversion_rate,
    },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
        <MetricCard
          title="סה״כ לידים"
          value={lead_treatment.total_leads}
          icon={Users}
          trend={totalTrend}
        />
        <MetricCard
          title="לידים בתהליך"
          value={lead_treatment.leads_in_process}
          subtitle={`${Math.round(lead_treatment.leads_in_process / lead_treatment.total_leads * 100)}% מהלידים`}
          icon={Target}
        />
        <MetricCard
          title="לידים מוזנחים"
          value={lead_treatment.neglected_leads}
          subtitle={`${Math.round(lead_treatment.neglected_leads / lead_treatment.total_leads * 100)}% מהלידים`}
          icon={Phone}
        />
        <MetricCard
          title="זמן ממוצע לחיוג ראשון"
          value={`${lead_treatment.avg_time_to_first_call_days} ימים`}
          icon={Clock}
        />
        <MetricCard
          title="הומרו"
          value={conversions.converted_leads}
          subtitle={`${conversions.conversion_rate}% אחוז המרה`}
          icon={TrendingUp}
          trend={conversionTrend}
        />
        <MetricCard
          title="זמן ממוצע להמרה"
          value={`${conversions.avg_time_to_conversion_days} ימים`}
          icon={Clock}
        />
      </div>

      {/* Monthly Comparison Chart */}
      <div className={s.card} style={{ padding: 20 }}>
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>השוואה חודשית</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={comparisonData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="name" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="left" />
            <Tooltip 
              contentStyle={{ 
                background: 'white', 
                border: '1px solid #e5e7eb',
                borderRadius: 8,
                padding: 12
              }}
            />
            <Legend />
            <Bar yAxisId="left" dataKey='סה"כ לידים' fill="#3b82f6" />
            <Bar yAxisId="left" dataKey="הומרו" fill="#10b981" />
            <Bar yAxisId="right" dataKey="אחוז המרה" fill="#f59e0b" />
          </BarChart>
        </ResponsiveContainer>
        
        {/* Change indicators */}
        <div style={{ display: 'flex', gap: 24, marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--color-border-light)' }}>
          <div>
            <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 4 }}>שינוי בלידים</div>
            <div style={{ 
              fontSize: 18, 
              fontWeight: 600,
              color: monthly_comparison.change.total_diff >= 0 ? 'var(--color-success)' : 'var(--color-error)'
            }}>
              {monthly_comparison.change.total_diff >= 0 ? '+' : ''}{monthly_comparison.change.total_diff}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 4 }}>שינוי בהמרות</div>
            <div style={{ 
              fontSize: 18, 
              fontWeight: 600,
              color: monthly_comparison.change.converted_diff >= 0 ? 'var(--color-success)' : 'var(--color-error)'
            }}>
              {monthly_comparison.change.converted_diff >= 0 ? '+' : ''}{monthly_comparison.change.converted_diff}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 4 }}>שינוי באחוז המרה</div>
            <div style={{ 
              fontSize: 18, 
              fontWeight: 600,
              color: monthly_comparison.change.rate_diff >= 0 ? 'var(--color-success)' : 'var(--color-error)'
            }}>
              {monthly_comparison.change.rate_diff >= 0 ? '+' : ''}{monthly_comparison.change.rate_diff}%
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
