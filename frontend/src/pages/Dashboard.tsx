import { useEffect, useState, useCallback, type FC, type ReactNode } from 'react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui'
import {
  Users, TrendingUp, PhoneCall, DollarSign, Target,
  ArrowUpRight, ArrowDownRight, Minus, RefreshCw,
  BarChart3, PieChart as PieChartIcon, Activity, Filter,
} from 'lucide-react'
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar,
  PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend,
} from 'recharts'
import { DashboardFilters, type FilterState } from '@/components/dashboard/DashboardFilters'
import { MetricsWidgets } from '@/components/dashboard/MetricsWidgets'
import s from './Dashboard.module.css'

/* ── Color palette ── */
const COLORS = ['#3b82f6', '#8b5cf6', '#f59e0b', '#22c55e', '#f43f5e', '#06b6d4', '#ec4899', '#14b8a6']
const SP_COLORS = ['#3b82f6', '#8b5cf6', '#f59e0b', '#22c55e', '#f43f5e', '#06b6d4', '#ec4899', '#14b8a6']

/* ── Types ── */
interface AdvancedDashboard {
  period: { from: string; to: string; days: number }
  kpis: {
    total_leads_all_time: number
    total_leads: number; prev_leads: number
    converted: number; prev_converted: number
    conversion_rate: number; prev_conversion_rate: number
    total_interactions: number
    revenue: number; prev_revenue: number
  }
  status_distribution: { name: string; value: number }[]
  lead_trends: { date: string; leads: number }[]
  funnel: { stage: string; value: number }[]
  source_breakdown: { source: string; count: number }[]
  interaction_types: { type: string; count: number }[]
  salesperson_performance: {
    id: number; name: string; total_leads: number; new_leads: number
    converted: number; in_progress: number; conversion_rate: number
    interactions: number; open_tasks: number
  }[]
  lead_responses: { response: string; count: number }[]
}

type DatePreset = 7 | 14 | 30 | 90 | 365

/* ── Main Dashboard ── */
export const Dashboard: FC = () => {
  const toast = useToast()
  const [data, setData] = useState<AdvancedDashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState<DatePreset>(30)
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const [customRange, setCustomRange] = useState(false)
  
  // Advanced metrics state
  const [showAdvancedMetrics, setShowAdvancedMetrics] = useState(false)
  const [metricsData, setMetricsData] = useState<any>(null)
  const [metricsLoading, setMetricsLoading] = useState(false)
  const [salespeople, setSalespeople] = useState<Array<{ id: number; name: string }>>([])
  const [filters, setFilters] = useState<FilterState | null>(null)

  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      const params = customRange && fromDate && toDate
        ? `from_date=${fromDate}&to_date=${toDate}`
        : `days=${days}`
      const result = await api.get<AdvancedDashboard>(`/api/dashboard/advanced?${params}`)
      setData(result)
    } catch (err: unknown) {
      const message = err && typeof err === 'object' && 'message' in err
        ? String((err as { message: string }).message)
        : 'שגיאה בטעינת נתונים'
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }, [days, fromDate, toDate, customRange])

  const loadMetrics = useCallback(async (filterState: FilterState) => {
    try {
      setMetricsLoading(true)
      const params = new URLSearchParams()
      if (filterState.fromDate) params.append('from_date', filterState.fromDate)
      if (filterState.toDate) params.append('to_date', filterState.toDate)
      if (filterState.cutoffDate) params.append('cutoff_date', filterState.cutoffDate)
      if (filterState.statuses.length) params.append('statuses', filterState.statuses.join(','))
      if (filterState.salespersonIds.length) params.append('salesperson_ids', filterState.salespersonIds.join(','))
      if (filterState.sources.length) params.append('sources', filterState.sources.join(','))
      params.append('days_to_first_call', String(filterState.daysToFirstCall))
      
      const result = await api.get(`/api/dashboard/metrics?${params.toString()}`)
      setMetricsData(result)
    } catch (err: unknown) {
      const message = err && typeof err === 'object' && 'message' in err
        ? String((err as { message: string }).message)
        : 'שגיאה בטעינת מטריקות'
      toast.error(message)
    } finally {
      setMetricsLoading(false)
    }
  }, [])

  useEffect(() => { loadData() }, [loadData])

  // Load salespeople for filters
  useEffect(() => {
    api.get<Array<{ id: number; name: string }>>('/api/leads/salespersons')
      .then(setSalespeople)
      .catch(() => {})
  }, [])

  // Load metrics when filters change
  useEffect(() => {
    if (showAdvancedMetrics && filters) {
      loadMetrics(filters)
    }
  }, [showAdvancedMetrics, filters, loadMetrics])

  const selectPreset = (d: DatePreset) => {
    setCustomRange(false)
    setDays(d)
  }

  if (loading && !data) {
    return (
      <div className={s.loading}>
        <div className={s['loading-spinner']} />
      </div>
    )
  }

  if (!data) return null

  const { kpis } = data

  return (
    <div className={s.dashboard}>
      {/* ── Header with date controls ── */}
      <div className={s.header}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <h1>דשבורד מכירות</h1>
          <button
            className={`${s['date-btn']} ${showAdvancedMetrics ? s['date-btn-active'] : ''}`}
            onClick={() => setShowAdvancedMetrics(!showAdvancedMetrics)}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <Filter size={14} />
            {showAdvancedMetrics ? 'תצוגה רגילה' : 'מטריקות מתקדמות'}
          </button>
        </div>
        <div className={s['header-actions']}>
          {!showAdvancedMetrics && ([7, 14, 30, 90, 365] as DatePreset[]).map(d => (
            <button
              key={d}
              className={`${s['date-btn']} ${!customRange && days === d ? s['date-btn-active'] : ''}`}
              onClick={() => selectPreset(d)}
            >
              {d === 7 ? 'שבוע' : d === 14 ? 'שבועיים' : d === 30 ? 'חודש' : d === 90 ? 'רבעון' : 'שנה'}
            </button>
          ))}
          {!showAdvancedMetrics && (
            <>
              <input
                type="date"
                className={s['date-input']}
                value={fromDate}
                onChange={e => { setFromDate(e.target.value); setCustomRange(true) }}
              />
              <span style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>—</span>
              <input
                type="date"
                className={s['date-input']}
            value={toDate}
            onChange={e => { setToDate(e.target.value); setCustomRange(true) }}
          />
          <button className={s['date-btn']} onClick={loadData} title="רענן">
            <RefreshCw size={14} />
          </button>
            </>
          )}
        </div>
      </div>

      {/* ── Advanced Metrics View ── */}
      {showAdvancedMetrics ? (
        <>
          <DashboardFilters 
            onFilterChange={setFilters}
            salespeople={salespeople}
          />
          <MetricsWidgets 
            data={metricsData}
            loading={metricsLoading}
          />
        </>
      ) : (
        <>
          {/* ── KPI Cards ── */}
          <div className={s.kpis}>
        <KpiCard
          icon={<Users size={18} />}
          label="סה״כ לידים במערכת"
          value={kpis.total_leads_all_time}
          color="blue"
        />
        <KpiCard
          icon={<Activity size={18} />}
          label="לידים בתקופה"
          value={kpis.total_leads}
          prev={kpis.prev_leads}
          color="purple"
        />
        <KpiCard
          icon={<Target size={18} />}
          label="הומרו"
          value={kpis.converted}
          prev={kpis.prev_converted}
          color="green"
        />
        <KpiCard
          icon={<TrendingUp size={18} />}
          label="אחוז המרה"
          value={`${kpis.conversion_rate}%`}
          prev={kpis.prev_conversion_rate}
          currentNum={kpis.conversion_rate}
          isPct
          color="purple"
        />
        <KpiCard
          icon={<PhoneCall size={18} />}
          label="פניות / שיחות"
          value={kpis.total_interactions}
          color="orange"
        />
        <KpiCard
          icon={<DollarSign size={18} />}
          label="הכנסות"
          value={`₪${kpis.revenue.toLocaleString()}`}
          prev={kpis.prev_revenue}
          currentNum={kpis.revenue}
          color="rose"
        />
      </div>

      {/* ── Row 1: Trends + Funnel ── */}
      <div className={s['grid-2']}>
        <Widget title="מגמת לידים" icon={<Activity size={15} />}>
          {data.lead_trends.length === 0 ? (
            <div className={s.empty}><span className={s['empty-text']}>אין נתונים</span></div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={data.lead_trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis
                  dataKey="date" tick={{ fontSize: 11 }} tickLine={false} axisLine={false}
                  tickFormatter={(v: string | number) => { const d = new Date(v); return `${d.getDate()}/${d.getMonth()+1}` }}
                />
                <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={35} />
                <Tooltip content={<ChartTooltip />} />
                <Line
                  type="monotone" dataKey="leads" name="לידים"
                  stroke="#3b82f6" strokeWidth={2.5} dot={false}
                  activeDot={{ r: 5, fill: '#3b82f6' }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </Widget>

        <Widget title="משפך המרה" icon={<Filter size={15} />}>
          <div className={s.funnel}>
            {data.funnel.map((step, i) => {
              const maxVal = data.funnel[0]?.value || 1
              const pct = Math.round((step.value / maxVal) * 100)
              return (
                <div key={step.stage} className={s['funnel-step']}>
                  <span className={s['funnel-label']}>{step.stage}</span>
                  <div className={s['funnel-bar-wrap']}>
                    <div
                      className={`${s['funnel-bar']} ${s[`funnel-bar--${i}`]}`}
                      style={{ width: `${Math.max(pct, 3)}%` }}
                    />
                    {pct > 15 && <span className={s['funnel-pct']}>{pct}%</span>}
                  </div>
                  <span className={s['funnel-value']}>{step.value}</span>
                </div>
              )
            })}
          </div>
        </Widget>
      </div>

      {/* ── Row 2: Status Pie + Sources Bar ── */}
      <div className={s['grid-2']}>
        <Widget title="התפלגות סטטוסים" icon={<PieChartIcon size={15} />}>
          {data.status_distribution.length === 0 ? (
            <div className={s.empty}><span className={s['empty-text']}>אין נתונים</span></div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={data.status_distribution}
                  cx="50%" cy="50%"
                  innerRadius={55} outerRadius={95}
                  paddingAngle={3}
                  dataKey="value"
                  label={(props: any) => `${props.name} (${((props.percent ?? 0) * 100).toFixed(0)}%)`}
                  labelLine={{ strokeWidth: 1 }}
                  style={{ fontSize: 11 }}
                >
                  {data.status_distribution.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Widget>

        <Widget title="מקורות לידים" icon={<BarChart3 size={15} />}>
          {data.source_breakdown.length === 0 ? (
            <div className={s.empty}><span className={s['empty-text']}>אין נתונים</span></div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.source_breakdown} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis
                  type="category" dataKey="source" tick={{ fontSize: 12 }}
                  tickLine={false} axisLine={false} width={90}
                />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="count" name="לידים" radius={[0, 6, 6, 0]} barSize={22}>
                  {data.source_breakdown.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </Widget>
      </div>

      {/* ── Row 3: Interaction Types Donut + Lead Responses ── */}
      <div className={s['grid-2']}>
        <Widget title="סוגי פניות" icon={<PhoneCall size={15} />}>
          {data.interaction_types.length === 0 ? (
            <div className={s.empty}><span className={s['empty-text']}>אין נתונים</span></div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={data.interaction_types.map(d => ({ name: d.type, value: d.count }))}
                  cx="50%" cy="50%"
                  innerRadius={45} outerRadius={85}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {data.interaction_types.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
                <Legend
                  verticalAlign="bottom" height={36}
                  formatter={(value: string) => <span style={{ fontSize: 12 }}>{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Widget>

        <Widget title="תגובות לידים" icon={<Users size={15} />}>
          {data.lead_responses.length === 0 ? (
            <div className={s.empty}><span className={s['empty-text']}>אין נתונים</span></div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={data.lead_responses}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="response" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={35} />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="count" name="לידים" radius={[6, 6, 0, 0]} barSize={32}>
                  {data.lead_responses.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </Widget>
      </div>

      {/* ── Salesperson Performance Table ── */}
      <Widget title="ביצועי אנשי מכירות" icon={<Target size={15} />}>
        {data.salesperson_performance.length === 0 ? (
          <div className={s.empty}><span className={s['empty-text']}>אין אנשי מכירות פעילים</span></div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className={s['sales-table']}>
              <thead>
                <tr>
                  <th>שם</th>
                  <th>לידים</th>
                  <th>חדשים</th>
                  <th>בטיפול</th>
                  <th>הומרו</th>
                  <th>% המרה</th>
                  <th>פניות</th>
                  <th>משימות פתוחות</th>
                </tr>
              </thead>
              <tbody>
                {data.salesperson_performance.map((sp, i) => (
                  <tr key={sp.id}>
                    <td>
                      <div className={s['sp-name']}>
                        <div
                          className={s['sp-avatar']}
                          style={{ background: SP_COLORS[i % SP_COLORS.length] }}
                        >
                          {sp.name.charAt(0)}
                        </div>
                        {sp.name}
                      </div>
                    </td>
                    <td style={{ fontWeight: 600 }}>{sp.total_leads}</td>
                    <td>{sp.new_leads}</td>
                    <td>{sp.in_progress}</td>
                    <td style={{ fontWeight: 600 }}>{sp.converted}</td>
                    <td>
                      <span className={`${s['rate-badge']} ${
                        sp.conversion_rate >= 20 ? s['rate-badge--high'] :
                        sp.conversion_rate >= 10 ? s['rate-badge--mid'] :
                        s['rate-badge--low']
                      }`}>
                        {sp.conversion_rate}%
                      </span>
                    </td>
                    <td>{sp.interactions}</td>
                    <td>{sp.open_tasks}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Widget>

      {/* ── Salesperson Comparison Chart ── */}
      {data.salesperson_performance.length > 0 && (
        <Widget title="השוואת אנשי מכירות" icon={<BarChart3 size={15} />}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.salesperson_performance}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={35} />
              <Tooltip content={<ChartTooltip />} />
              <Legend formatter={(value: string) => <span style={{ fontSize: 12 }}>{value}</span>} />
              <Bar dataKey="total_leads" name="לידים" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={20} />
              <Bar dataKey="converted" name="הומרו" fill="#22c55e" radius={[4, 4, 0, 0]} barSize={20} />
              <Bar dataKey="interactions" name="פניות" fill="#f59e0b" radius={[4, 4, 0, 0]} barSize={20} />
            </BarChart>
          </ResponsiveContainer>
        </Widget>
      )}
        </>
      )}
    </div>
  )
}


/* ════════════════════════════════════════════════════════════
   Sub-components
   ════════════════════════════════════════════════════════════ */

/* ── KPI Card ── */
interface KpiCardProps {
  icon: ReactNode
  label: string
  value: number | string
  prev?: number
  currentNum?: number
  isPct?: boolean
  color: 'blue' | 'green' | 'purple' | 'orange' | 'rose'
}

const KpiCard: FC<KpiCardProps> = ({ icon, label, value, prev, currentNum, isPct, color }) => {
  let changeEl: ReactNode = null
  if (prev !== undefined) {
    const cur = currentNum ?? (typeof value === 'number' ? value : 0)
    const diff = isPct ? cur - prev : (prev === 0 ? (cur > 0 ? 100 : 0) : Math.round(((cur - prev) / prev) * 100))
    const cls = diff > 0 ? s['kpi-change--up'] : diff < 0 ? s['kpi-change--down'] : s['kpi-change--neutral']
    const Icon = diff > 0 ? ArrowUpRight : diff < 0 ? ArrowDownRight : Minus
    changeEl = (
      <span className={`${s['kpi-change']} ${cls}`}>
        <Icon size={12} />
        {Math.abs(diff)}{isPct ? ' נק' : '%'}
      </span>
    )
  }

  return (
    <div className={`${s['kpi-card']} ${s[`kpi-card--${color}`]}`}>
      <div className={`${s['kpi-icon']} ${s[`kpi-icon--${color}`]}`}>{icon}</div>
      <span className={s['kpi-label']}>{label}</span>
      <span className={s['kpi-value']}>{value}</span>
      {changeEl}
    </div>
  )
}


/* ── Widget wrapper ── */
interface WidgetProps {
  title: string
  icon?: ReactNode
  children: ReactNode
}

const Widget: FC<WidgetProps> = ({ title, icon, children }) => (
  <div className={s.widget}>
    <div className={s['widget-header']}>
      <span className={s['widget-title']}>{icon}{title}</span>
    </div>
    <div className={s['widget-body']}>
      {children}
    </div>
  </div>
)


/* ── Custom Tooltip ── */
const ChartTooltip: FC<any> = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className={s['chart-tooltip']}>
      {label && <div className={s['chart-tooltip-label']}>{label}</div>}
      {payload.map((p: any, i: number) => (
        <div key={i} className={s['chart-tooltip-value']} style={{ color: p.color }}>
          {p.name}: <strong>{typeof p.value === 'number' ? p.value.toLocaleString() : p.value}</strong>
        </div>
      ))}
    </div>
  )
}
