import { CheckCircle, Clock, AlertCircle, TrendingUp, Users, Target } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import s from '@/styles/shared.module.css'

interface TaskMetricsData {
  by_status: Record<string, number>
  by_user: Array<{ user_id: number; name: string; count: number }>
  by_salesperson: Array<{ salesperson_id: number; name: string; count: number }>
  by_priority: Record<number, number>
  by_type: Record<string, number>
  overdue_count: number
  created_today: number
  completed_today: number
  summary: {
    total_all: number
    total_open: number
    total_completed: number
    total_cancelled: number
    completion_rate: number
  }
}

interface TaskMetricsDashboardProps {
  data: TaskMetricsData | null
  loading: boolean
}

const STATUS_COLORS: Record<string, string> = {
  'חדש': '#3b82f6',
  'בטיפול': '#f59e0b',
  'הושלם': '#22c55e',
  'בוטל': '#f43f5e',
}

const PRIORITY_LABELS: Record<number, string> = {
  0: 'רגיל',
  1: 'נמוך',
  2: 'גבוה',
  3: 'דחוף',
}

const TYPE_LABELS: Record<string, string> = {
  'sales': 'מכירות',
  'class_management': 'ניהול כיתה',
  'shipping': 'משלוח',
  'general': 'כללי',
}

function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'var(--color-primary)',
}: {
  title: string
  value: string | number
  subtitle?: string
  icon: any
  color?: string
}) {
  return (
    <div className={s.card} style={{ padding: 20 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{
          width: 40,
          height: 40,
          borderRadius: 8,
          background: color + '20',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: color
        }}>
          <Icon size={20} />
        </div>
      </div>
      <div style={{ fontSize: 13, color: 'var(--color-text-muted)', marginBottom: 4 }}>{title}</div>
      <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--color-text)' }}>{value}</div>
      {subtitle && <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 4 }}>{subtitle}</div>}
    </div>
  )
}

export function TaskMetricsDashboard({ data, loading }: TaskMetricsDashboardProps) {
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

  const { by_status, by_user, by_salesperson, by_priority, by_type, summary, overdue_count, created_today, completed_today } = data

  // Prepare status chart data
  const statusData = Object.entries(by_status).map(([status, count]) => ({
    name: status,
    value: count,
    fill: STATUS_COLORS[status] || '#6b7280'
  }))

  // Prepare priority chart data
  const priorityData = Object.entries(by_priority)
    .map(([priority, count]) => ({
      name: PRIORITY_LABELS[Number(priority)] || priority,
      value: count
    }))
    .sort((a, b) => b.value - a.value)

  // Prepare type chart data
  const typeData = Object.entries(by_type)
    .map(([type, count]) => ({
      name: TYPE_LABELS[type] || type,
      value: count
    }))
    .sort((a, b) => b.value - a.value)

  // Prepare user chart data (top 10)
  const userData = by_user.slice(0, 10).map(u => ({
    name: u.name.split('@')[0], // Show only email prefix
    value: u.count
  }))

  // Prepare salesperson chart data (top 10)
  const salespersonData = by_salesperson.slice(0, 10).map(sp => ({
    name: sp.name,
    value: sp.count
  }))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16 }}>
        <MetricCard
          title="סה״כ משימות"
          value={summary.total_all}
          icon={Target}
          color="#3b82f6"
        />
        <MetricCard
          title="משימות פתוחות"
          value={summary.total_open}
          subtitle={`${Math.round(summary.total_open / summary.total_all * 100)}% מהכלל`}
          icon={Clock}
          color="#f59e0b"
        />
        <MetricCard
          title="משימות שאיחרו"
          value={overdue_count}
          icon={AlertCircle}
          color="#f43f5e"
        />
        <MetricCard
          title="נוצרו היום"
          value={created_today}
          icon={TrendingUp}
          color="#3b82f6"
        />
        <MetricCard
          title="הושלמו היום"
          value={completed_today}
          icon={CheckCircle}
          color="#22c55e"
        />
        <MetricCard
          title="אחוז השלמה"
          value={`${summary.completion_rate}%`}
          subtitle={`${summary.total_completed} מתוך ${summary.total_all}`}
          icon={Users}
          color="#8b5cf6"
        />
      </div>

      {/* Charts Row 1: Status Pie + Priority Bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 16 }}>
        {/* Status Distribution */}
        <div className={s.card} style={{ padding: 20 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>פילוח לפי סטטוס</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {statusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Priority Distribution */}
        <div className={s.card} style={{ padding: 20 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>פילוח לפי עדיפות</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={priorityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip
                contentStyle={{
                  background: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: 8,
                  padding: 12
                }}
              />
              <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2: Tasks by User + Tasks by Salesperson */}
      {(userData.length > 0 || salespersonData.length > 0) && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 16 }}>
          {userData.length > 0 && (
            <div className={s.card} style={{ padding: 20 }}>
              <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>משימות פתוחות לפי משתמש (10 מובילים)</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={userData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={100} />
                  <Tooltip
                    contentStyle={{
                      background: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: 8,
                      padding: 12
                    }}
                  />
                  <Bar dataKey="value" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {salespersonData.length > 0 && (
            <div className={s.card} style={{ padding: 20 }}>
              <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>משימות פתוחות לפי איש מכירות (10 מובילים)</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={salespersonData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={100} />
                  <Tooltip
                    contentStyle={{
                      background: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: 8,
                      padding: 12
                    }}
                  />
                  <Bar dataKey="value" fill="#22c55e" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Type Distribution */}
      {typeData.length > 0 && (
        <div className={s.card} style={{ padding: 20 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>פילוח לפי סוג משימה</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={typeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip
                contentStyle={{
                  background: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: 8,
                  padding: 12
                }}
              />
              <Bar dataKey="value" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
