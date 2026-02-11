import { useEffect, useState } from 'react'
import { Activity, RefreshCw, Filter, Eye, CheckCircle, XCircle, Clock, Zap } from 'lucide-react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import { PageHeader } from '@/components/ui/PageHeader'
import s from '@/styles/shared.module.css'

interface WebhookLog {
  id: number
  webhook_type: string
  source_ip: string | null
  success: boolean
  action: string | null
  error_message: string | null
  entity_type: string | null
  entity_id: number | null
  processing_time_ms: number | null
  created_at: string
  raw_payload?: string | null
  result_data?: string | null
}

interface WebhookStats {
  total_webhooks: number
  successful: number
  failed: number
  by_type: Record<string, number>
  avg_processing_time_ms: number | null
}

export function WebhookLogsPage() {
  const [logs, setLogs] = useState<WebhookLog[]>([])
  const [stats, setStats] = useState<WebhookStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedLog, setSelectedLog] = useState<WebhookLog | null>(null)
  const [filters, setFilters] = useState({
    webhook_type: '',
    success: '',
    hours: 24
  })
  const toast = useToast()

  useEffect(() => {
    loadData()
  }, [filters])

  const loadData = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (filters.webhook_type) params.append('webhook_type', filters.webhook_type)
      if (filters.success !== '') params.append('success', filters.success)
      params.append('hours', filters.hours.toString())
      params.append('limit', '100')

      const [logsData, statsData] = await Promise.all([
        api.get<WebhookLog[]>(`/webhook-logs/?${params.toString()}`),
        api.get<WebhookStats>(`/webhook-logs/stats?hours=${filters.hours}`)
      ])
      setLogs(logsData)
      setStats(statsData)
    } catch (error) {
      toast.error('שגיאה', 'לא ניתן לטעון לוגים')
    } finally {
      setLoading(false)
    }
  }

  const viewDetails = async (logId: number) => {
    try {
      const log = await api.get<WebhookLog>(`/webhook-logs/${logId}`)
      setSelectedLog(log)
    } catch (error) {
      toast.error('שגיאה', 'לא ניתן לטעון פרטים')
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString('he-IL', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'elementor': 'primary',
      'yemot': 'info',
      'generic': 'secondary',
      'nedarim': 'success',
      'lesson-complete': 'warning',
      'lead-unified:elementor': 'primary',
      'lead-unified:yemot': 'info',
      'lead-unified:generic': 'secondary'
    }
    return colors[type] || 'secondary'
  }

  if (loading && !stats) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <RefreshCw size={32} style={{ animation: 'spin 1s linear infinite', color: 'var(--text-muted)' }} />
      </div>
    )
  }

  return (
    <div className={s.page}>
      <PageHeader
        title="לוגים של Webhooks"
        onRefresh={loadData}
        loading={loading}
      />

      {stats && (
        <div style={{ display: 'grid', gap: 16, gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', marginBottom: 24 }}>
          <div className={s.card} style={{ padding: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <Activity size={20} style={{ color: 'var(--primary)' }} />
              <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>סה"כ</span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 'bold' }}>{stats.total_webhooks}</div>
          </div>
          <div className={s.card} style={{ padding: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <CheckCircle size={20} style={{ color: 'var(--success)' }} />
              <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>הצליחו</span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: 'var(--success)' }}>
              {stats.successful}
              <span style={{ fontSize: 14, marginRight: 8 }}>
                ({stats.total_webhooks > 0 ? Math.round((stats.successful / stats.total_webhooks) * 100) : 0}%)
              </span>
            </div>
          </div>
          <div className={s.card} style={{ padding: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <XCircle size={20} style={{ color: 'var(--danger)' }} />
              <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>נכשלו</span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: 'var(--danger)' }}>{stats.failed}</div>
          </div>
          <div className={s.card} style={{ padding: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <Zap size={20} style={{ color: 'var(--warning)' }} />
              <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>זמן ממוצע</span>
            </div>
            <div style={{ fontSize: 24, fontWeight: 'bold' }}>
              {stats.avg_processing_time_ms ? `${Math.round(stats.avg_processing_time_ms)}ms` : 'N/A'}
            </div>
          </div>
        </div>
      )}

      <div className={s.card} style={{ padding: 16, marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <Filter size={16} />
          <span style={{ fontWeight: 'bold' }}>פילטרים:</span>
          
          <select
            className={s.input}
            style={{ width: 'auto', minWidth: 150 }}
            value={filters.webhook_type}
            onChange={(e) => setFilters(prev => ({ ...prev, webhook_type: e.target.value }))}
          >
            <option value="">כל הסוגים</option>
            <option value="elementor">Elementor</option>
            <option value="yemot">Yemot</option>
            <option value="generic">Generic</option>
            <option value="nedarim">Nedarim</option>
            <option value="lesson-complete">Lesson Complete</option>
          </select>

          <select
            className={s.input}
            style={{ width: 'auto', minWidth: 120 }}
            value={filters.success}
            onChange={(e) => setFilters(prev => ({ ...prev, success: e.target.value }))}
          >
            <option value="">הכל</option>
            <option value="true">הצליחו</option>
            <option value="false">נכשלו</option>
          </select>

          <select
            className={s.input}
            style={{ width: 'auto', minWidth: 120 }}
            value={filters.hours}
            onChange={(e) => setFilters(prev => ({ ...prev, hours: Number(e.target.value) }))}
          >
            <option value="1">שעה אחרונה</option>
            <option value="6">6 שעות</option>
            <option value="24">24 שעות</option>
            <option value="72">3 ימים</option>
            <option value="168">שבוע</option>
          </select>
        </div>
      </div>

      <div className={s.card}>
        <div style={{ overflowX: 'auto' }}>
          <table className={s.table}>
            <thead>
              <tr>
                <th>זמן</th>
                <th>סוג</th>
                <th>סטטוס</th>
                <th>פעולה</th>
                <th>ישות</th>
                <th>זמן עיבוד</th>
                <th>IP</th>
                <th>פעולות</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td style={{ fontSize: 12 }}>{formatDate(log.created_at)}</td>
                  <td>
                    <span className={`${s.badge} ${s[`badge-${getTypeColor(log.webhook_type)}`]}`}>
                      {log.webhook_type}
                    </span>
                  </td>
                  <td>
                    {log.success ? (
                      <span className={`${s.badge} ${s['badge-success']}`} style={{ display: 'flex', alignItems: 'center', gap: 4, width: 'fit-content' }}>
                        <CheckCircle size={12} />
                        הצליח
                      </span>
                    ) : (
                      <span className={`${s.badge} ${s['badge-danger']}`} style={{ display: 'flex', alignItems: 'center', gap: 4, width: 'fit-content' }}>
                        <XCircle size={12} />
                        נכשל
                      </span>
                    )}
                  </td>
                  <td>{log.action || '-'}</td>
                  <td>
                    {log.entity_type && log.entity_id ? (
                      <span style={{ fontSize: 12 }}>
                        {log.entity_type} #{log.entity_id}
                      </span>
                    ) : '-'}
                  </td>
                  <td>
                    {log.processing_time_ms ? (
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Clock size={12} />
                        {log.processing_time_ms}ms
                      </span>
                    ) : '-'}
                  </td>
                  <td style={{ fontSize: 12 }}>{log.source_ip || '-'}</td>
                  <td>
                    <button
                      className={`${s.btn} ${s['btn-sm']} ${s['btn-secondary']}`}
                      onClick={() => viewDetails(log.id)}
                    >
                      <Eye size={14} />
                      צפה
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {logs.length === 0 && (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
              <Activity size={48} style={{ opacity: 0.3, marginBottom: 16 }} />
              <div>אין webhooks בטווח הזמן שנבחר</div>
            </div>
          )}
        </div>
      </div>

      {selectedLog && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: 20
        }} onClick={() => setSelectedLog(null)}>
          <div className={s.card} style={{ padding: 24, maxWidth: 800, width: '100%', maxHeight: '90vh', overflow: 'auto' }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ margin: 0 }}>פרטי Webhook #{selectedLog.id}</h3>
              <button className={`${s.btn} ${s['btn-secondary']}`} onClick={() => setSelectedLog(null)}>
                סגור
              </button>
            </div>

            <div style={{ display: 'grid', gap: 12, marginBottom: 16 }}>
              <div><strong>סוג:</strong> {selectedLog.webhook_type}</div>
              <div><strong>זמן:</strong> {formatDate(selectedLog.created_at)}</div>
              <div><strong>סטטוס:</strong> {selectedLog.success ? '✅ הצליח' : '❌ נכשל'}</div>
              {selectedLog.action && <div><strong>פעולה:</strong> {selectedLog.action}</div>}
              {selectedLog.entity_type && <div><strong>ישות:</strong> {selectedLog.entity_type} #{selectedLog.entity_id}</div>}
              {selectedLog.processing_time_ms && <div><strong>זמן עיבוד:</strong> {selectedLog.processing_time_ms}ms</div>}
              {selectedLog.source_ip && <div><strong>IP מקור:</strong> {selectedLog.source_ip}</div>}
              {selectedLog.error_message && (
                <div style={{ padding: 12, background: 'var(--danger-bg)', borderRadius: 4 }}>
                  <strong style={{ color: 'var(--danger)' }}>שגיאה:</strong>
                  <pre style={{ margin: '8px 0 0 0', fontSize: 12, whiteSpace: 'pre-wrap' }}>{selectedLog.error_message}</pre>
                </div>
              )}
            </div>

            {selectedLog.raw_payload && (
              <div style={{ marginTop: 16 }}>
                <strong>Payload מקורי:</strong>
                <pre style={{
                  background: 'var(--bg-secondary)',
                  padding: 12,
                  borderRadius: 4,
                  fontSize: 12,
                  overflow: 'auto',
                  maxHeight: 300,
                  marginTop: 8
                }}>
                  {JSON.stringify(JSON.parse(selectedLog.raw_payload), null, 2)}
                </pre>
              </div>
            )}

            {selectedLog.result_data && (
              <div style={{ marginTop: 16 }}>
                <strong>תוצאה:</strong>
                <pre style={{
                  background: 'var(--bg-secondary)',
                  padding: 12,
                  borderRadius: 4,
                  fontSize: 12,
                  overflow: 'auto',
                  maxHeight: 300,
                  marginTop: 8
                }}>
                  {JSON.stringify(JSON.parse(selectedLog.result_data), null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
