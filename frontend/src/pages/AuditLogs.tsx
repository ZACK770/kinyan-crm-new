import { useEffect, useState, type FC } from 'react'
import { FileText, Filter, RefreshCw, User } from 'lucide-react'
import { api } from '@/lib/api'
import { formatDateTime } from '@/lib/status'
import { useToast } from '@/components/ui/Toast'
import { DataTable, type Column } from '@/components/ui/DataTable'
import s from '@/styles/shared.module.css'

/* ══════════════════════════════════════════════════════════════
   Types
   ══════════════════════════════════════════════════════════════ */
interface AuditLog {
  id: number
  user_id: number | null
  user_name: string | null
  action: string
  entity_type: string | null
  entity_id: number | null
  description: string | null
  ip_address: string | null
  user_agent: string | null
  request_method: string | null
  request_path: string | null
  changes: string | null
  created_at: string
}

interface AuditLogsResponse {
  logs: AuditLog[]
  total: number
  page: number
  page_size: number
}

/* ══════════════════════════════════════════════════════════════
   Helper Functions
   ══════════════════════════════════════════════════════════════ */
function getActionLabel(action: string): string {
  const labels: Record<string, string> = {
    create: 'יצירה',
    update: 'עדכון',
    delete: 'מחיקה',
    view: 'צפייה',
    login: 'התחברות',
    logout: 'התנתקות',
    export: 'ייצוא',
    import: 'ייבוא',
  }
  return labels[action] || action
}

function getActionColor(action: string): string {
  const colors: Record<string, string> = {
    create: 'success',
    update: 'info',
    delete: 'danger',
    view: 'neutral',
    login: 'success',
    logout: 'neutral',
    export: 'warning',
    import: 'warning',
  }
  return colors[action] || 'neutral'
}

function getEntityLabel(entityType: string | null): string {
  if (!entityType) return '-'
  
  const labels: Record<string, string> = {
    leads: 'לידים',
    students: 'תלמידים',
    courses: 'קורסים',
    payments: 'תשלומים',
    expenses: 'הוצאות',
    users: 'משתמשים',
    campaigns: 'קמפיינים',
    tasks: 'משימות',
    inquiries: 'פניות',
    lecturers: 'מרצים',
    collections: 'גביה',
    commitments: 'התחייבויות',
    exams: 'מבחנים',
    attendance: 'נוכחות',
  }
  return labels[entityType] || entityType
}

/* ══════════════════════════════════════════════════════════════
   Action Badge Component
   ══════════════════════════════════════════════════════════════ */
function ActionBadge({ action }: { action: string }) {
  const label = getActionLabel(action)
  const color = getActionColor(action)
  return <span className={`${s.badge} ${s[`badge-${color}`]}`}>{label}</span>
}

/* ══════════════════════════════════════════════════════════════
   Main Component
   ══════════════════════════════════════════════════════════════ */
export const AuditLogsPage: FC = () => {
  const toast = useToast()
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  
  // Filters
  const [filterAction, setFilterAction] = useState<string>('')
  const [filterEntity, setFilterEntity] = useState<string>('')
  const [filterDays, setFilterDays] = useState<string>('30')

  useEffect(() => {
    loadLogs()
  }, [page, filterAction, filterEntity, filterDays])

  async function loadLogs() {
    try {
      setLoading(true)
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '50',
      })
      
      if (filterAction) params.append('action', filterAction)
      if (filterEntity) params.append('entity_type', filterEntity)
      if (filterDays) params.append('days', filterDays)
      
      const data = await api.get<AuditLogsResponse>(`/api/audit-logs?${params}`)
      setLogs(data.logs)
      setTotal(data.total)
    } catch (err: unknown) {
      const message = err && typeof err === 'object' && 'message' in err
        ? String((err as { message: string }).message)
        : 'שגיאה בטעינת לוגים'
      toast.error('שגיאה', message)
    } finally {
      setLoading(false)
    }
  }

  function handleRefresh() {
    loadLogs()
  }

  function handleClearFilters() {
    setFilterAction('')
    setFilterEntity('')
    setFilterDays('30')
    setPage(1)
  }

  // Table columns
  const columns: Column<AuditLog>[] = [
    {
      key: 'created_at',
      header: 'תאריך ושעה',
      render: (log) => (
        <div style={{ fontSize: '0.875rem', whiteSpace: 'nowrap' }}>
          {formatDateTime(log.created_at)}
        </div>
      ),
    },
    {
      key: 'action',
      header: 'פעולה',
      render: (log) => <ActionBadge action={log.action} />,
    },
    {
      key: 'user_name',
      header: 'משתמש',
      render: (log) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <User size={14} strokeWidth={2} style={{ color: '#6b7280' }} />
          <span>{log.user_name || 'מערכת'}</span>
        </div>
      ),
    },
    {
      key: 'entity_type',
      header: 'ישות',
      render: (log) => (
        <span style={{ fontSize: '0.875rem' }}>
          {getEntityLabel(log.entity_type)}
          {log.entity_id && <span style={{ color: '#6b7280' }}> #{log.entity_id}</span>}
        </span>
      ),
    },
    {
      key: 'description',
      header: 'תיאור',
      render: (log) => (
        <div style={{ maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {log.description || '-'}
        </div>
      ),
    },
    {
      key: 'ip_address',
      header: 'IP',
      render: (log) => (
        <span style={{ fontSize: '0.8rem', fontFamily: 'monospace', color: '#6b7280', direction: 'ltr' }}>
          {log.ip_address || '-'}
        </span>
      ),
    },
  ]

  return (
    <div style={{ padding: '1.5rem', maxWidth: '100%' }}>
      {/* Header */}
      <div className={s['page-header']}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <FileText size={28} strokeWidth={1.8} />
          <div>
            <h1 className={s['page-title']}>יומן פעילות</h1>
            <p className={s['page-subtitle']}>תיעוד כל הפעולות במערכת</p>
          </div>
        </div>
        
        <button
          className={`${s.btn} ${s['btn-secondary']}`}
          onClick={handleRefresh}
          disabled={loading}
        >
          <RefreshCw size={16} strokeWidth={2} />
          רענן
        </button>
      </div>

      {/* Filters */}
      <div className={s.card} style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <Filter size={18} strokeWidth={2} />
          <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>סינון</h3>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
          <div className={s['form-group']}>
            <label className={s['form-label']}>סוג פעולה</label>
            <select
              className={s.input}
              value={filterAction}
              onChange={(e) => { setFilterAction(e.target.value); setPage(1) }}
            >
              <option value="">הכל</option>
              <option value="create">יצירה</option>
              <option value="update">עדכון</option>
              <option value="delete">מחיקה</option>
              <option value="view">צפייה</option>
              <option value="login">התחברות</option>
              <option value="export">ייצוא</option>
            </select>
          </div>

          <div className={s['form-group']}>
            <label className={s['form-label']}>ישות</label>
            <select
              className={s.input}
              value={filterEntity}
              onChange={(e) => { setFilterEntity(e.target.value); setPage(1) }}
            >
              <option value="">הכל</option>
              <option value="leads">לידים</option>
              <option value="students">תלמידים</option>
              <option value="courses">קורסים</option>
              <option value="payments">תשלומים</option>
              <option value="expenses">הוצאות</option>
              <option value="users">משתמשים</option>
              <option value="campaigns">קמפיינים</option>
              <option value="tasks">משימות</option>
            </select>
          </div>

          <div className={s['form-group']}>
            <label className={s['form-label']}>תקופה</label>
            <select
              className={s.input}
              value={filterDays}
              onChange={(e) => { setFilterDays(e.target.value); setPage(1) }}
            >
              <option value="1">יום אחרון</option>
              <option value="7">שבוע אחרון</option>
              <option value="30">חודש אחרון</option>
              <option value="90">3 חודשים</option>
              <option value="180">6 חודשים</option>
              <option value="365">שנה</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button
              className={`${s.btn} ${s['btn-secondary']}`}
              onClick={handleClearFilters}
              style={{ width: '100%' }}
            >
              נקה סינון
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div style={{ marginBottom: '1rem', color: '#6b7280', fontSize: '0.875rem' }}>
        {loading ? (
          'טוען...'
        ) : (
          <>סה״כ {total.toLocaleString('he-IL')} רשומות</>
        )}
      </div>

      {/* Data Table */}
      <DataTable
        columns={columns}
        data={logs}
        loading={loading}
        emptyText="אין רשומות להצגה"
        keyExtractor={(log) => log.id}
      />

      {/* Pagination */}
      {total > 50 && (
        <div className={s.pagination}>
          <button
            className={s['pagination-btn']}
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1 || loading}
          >
            הקודם
          </button>
          <span className={s['pagination-info']}>
            עמוד {page} מתוך {Math.ceil(total / 50)}
          </span>
          <button
            className={s['pagination-btn']}
            onClick={() => setPage(p => p + 1)}
            disabled={page >= Math.ceil(total / 50) || loading}
          >
            הבא
          </button>
        </div>
      )}
    </div>
  )
}
