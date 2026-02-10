import { useEffect, useState, type FC } from 'react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui'
import type { DashboardOverview, SalespersonStats } from '@/types'
import styles from './Dashboard.module.css'

export const Dashboard: FC = () => {
  const toast = useToast()
  const [overview, setOverview] = useState<DashboardOverview | null>(null)
  const [salespeople, setSalespeople] = useState<SalespersonStats[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      setLoading(true)
      const [ov, sp] = await Promise.all([
        api.get<DashboardOverview>('/api/dashboard/overview'),
        api.get<SalespersonStats[]>('/api/dashboard/salespeople'),
      ])
      setOverview(ov)
      setSalespeople(sp)
    } catch (err: unknown) {
      const message = err && typeof err === 'object' && 'message' in err
        ? String((err as { message: string }).message)
        : 'שגיאה בטעינת נתונים'
      toast.error('שגיאה', message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className={styles.loading}>טוען נתונים...</div>
  }

  return (
    <div className={styles.dashboard}>
      {/* Page title */}
      <h1 style={{ fontSize: '1.57rem', fontWeight: 700 }}>דשבורד</h1>

      {/* Stats cards */}
      {overview && (
        <div className={styles.stats}>
          <StatCard label="סה״כ לידים" value={overview.total_leads} />
          <StatCard
            label="לידים חדשים"
            value={overview.new_leads}
            sub="ממתינים לטיפול"
          />
          <StatCard label="תלמידים" value={overview.total_students} />
          <StatCard label="הרשמות פעילות" value={overview.active_enrollments} />
          <StatCard
            label="הכנסות"
            value={`₪${overview.total_revenue.toLocaleString()}`}
            sub="סכום ששולם"
          />
        </div>
      )}

      {/* Salespeople section */}
      <div className={styles.section}>
        <div className={styles['section-header']}>
          <h3 className={styles['section-title']}>אנשי מכירות</h3>
        </div>
        {salespeople.length === 0 ? (
          <div className={styles.empty}>
            <span className={styles['empty-text']}>
              אין אנשי מכירות פעילים
            </span>
          </div>
        ) : (
          <table className={styles['sales-table']}>
            <thead>
              <tr>
                <th>שם</th>
                <th>סה״כ לידים</th>
                <th>לידים חדשים</th>
                <th>משימות פתוחות</th>
              </tr>
            </thead>
            <tbody>
              {salespeople.map((sp) => (
                <tr key={sp.id}>
                  <td style={{ fontWeight: 500 }}>{sp.name}</td>
                  <td className="mono">{sp.total_leads}</td>
                  <td className="mono">{sp.new_leads}</td>
                  <td className="mono">{sp.open_tasks}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

/* ---- Stat Card sub-component ---- */

interface StatCardProps {
  label: string
  value: number | string
  sub?: string
}

const StatCard: FC<StatCardProps> = ({ label, value, sub }) => (
  <div className={styles['stat-card']}>
    <span className={styles['stat-label']}>{label}</span>
    <span className={styles['stat-value']}>{value}</span>
    {sub && <span className={styles['stat-sub']}>{sub}</span>}
  </div>
)
