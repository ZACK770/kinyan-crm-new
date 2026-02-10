import { useEffect, useState } from 'react'
import { Users, RefreshCw, Settings, BarChart3, CheckCircle, XCircle } from 'lucide-react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import { PageHeader } from '@/components/ui/PageHeader'
import s from '@/styles/shared.module.css'

interface AssignmentRules {
  id: number
  salesperson_id: number
  salesperson_name: string
  daily_lead_limit: number | null
  daily_leads_assigned: number
  last_reset_date: string | null
  priority_weight: number
  max_open_leads: number | null
  status_filters: string[] | null
  is_active: boolean
  current_open_leads?: number
}

interface AssignmentStats {
  salesperson_id: number
  salesperson_name: string
  total_leads: number
  open_leads: number
  daily_assigned: number
  daily_limit: number | null
  priority_weight: number
  is_available: boolean
  availability_reason: string | null
}

export function SalesAssignmentRulesPage() {
  const [rules, setRules] = useState<AssignmentRules[]>([])
  const [stats, setStats] = useState<AssignmentStats[]>([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editForm, setEditForm] = useState<Partial<AssignmentRules>>({})
  const [activeTab, setActiveTab] = useState<'stats' | 'rules'>('stats')
  const toast = useToast()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [rulesData, statsData] = await Promise.all([
        api.get<AssignmentRules[]>('/sales-assignment-rules/?include_stats=true'),
        api.get<AssignmentStats[]>('/sales-assignment-rules/stats')
      ])
      setRules(rulesData)
      setStats(statsData)
    } catch (error) {
      toast.error('שגיאה', 'לא ניתן לטעון נתונים')
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (rule: AssignmentRules) => {
    setEditingId(rule.id)
    setEditForm({
      daily_lead_limit: rule.daily_lead_limit,
      priority_weight: rule.priority_weight,
      max_open_leads: rule.max_open_leads,
      is_active: rule.is_active
    })
  }

  const handleSave = async (salespersonId: number) => {
    try {
      await api.patch(`/sales-assignment-rules/${salespersonId}`, editForm)
      toast.success('נשמר', 'הכללים עודכנו בהצלחה')
      setEditingId(null)
      loadData()
    } catch (error) {
      toast.error('שגיאה', 'לא ניתן לשמור')
    }
  }

  const handleResetDaily = async () => {
    if (!confirm('האם לאפס את כל הספירות היומיות?')) return
    try {
      await api.post('/sales-assignment-rules/reset-daily-counts', {})
      toast.success('אופס', 'ספירות יומיות אופסו בהצלחה')
      loadData()
    } catch (error) {
      toast.error('שגיאה', 'לא ניתן לאפס')
    }
  }

  const set = (key: keyof typeof editForm) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : 
                  e.target.type === 'number' ? (e.target.value ? Number(e.target.value) : null) :
                  e.target.value
    setEditForm(prev => ({ ...prev, [key]: value }))
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <RefreshCw size={32} style={{ animation: 'spin 1s linear infinite', color: 'var(--text-muted)' }} />
      </div>
    )
  }

  return (
    <div className={s.page}>
      <PageHeader
        title="ניהול שיוך לידים"
        onRefresh={loadData}
        loading={loading}
      />

      <div style={{ marginBottom: 24, display: 'flex', gap: 12, alignItems: 'center' }}>
        <button 
          className={`${s.btn} ${activeTab === 'stats' ? s['btn-primary'] : s['btn-secondary']}`}
          onClick={() => setActiveTab('stats')}
        >
          <BarChart3 size={16} />
          סטטיסטיקות
        </button>
        <button 
          className={`${s.btn} ${activeTab === 'rules' ? s['btn-primary'] : s['btn-secondary']}`}
          onClick={() => setActiveTab('rules')}
        >
          <Settings size={16} />
          כללים
        </button>
        <div style={{ flex: 1 }} />
        <button className={`${s.btn} ${s['btn-secondary']}`} onClick={handleResetDaily}>
          <RefreshCw size={16} />
          איפוס ספירות יומיות
        </button>
      </div>

      {activeTab === 'stats' && (
        <div style={{ display: 'grid', gap: 16, gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))' }}>
          {stats.map((stat) => (
            <div key={stat.salesperson_id} className={s.card} style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: 18 }}>{stat.salesperson_name}</h3>
                {stat.is_available ? (
                  <span className={`${s.badge} ${s['badge-success']}`} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <CheckCircle size={14} />
                    זמין
                  </span>
                ) : (
                  <span className={`${s.badge} ${s['badge-danger']}`} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <XCircle size={14} />
                    לא זמין
                  </span>
                )}
              </div>
              {stat.availability_reason && (
                <p style={{ fontSize: 12, color: 'var(--danger)', marginBottom: 12 }}>
                  {stat.availability_reason}
                </p>
              )}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>לידים היום:</span>
                  <strong>
                    {stat.daily_assigned}
                    {stat.daily_limit && ` / ${stat.daily_limit}`}
                  </strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>לידים פתוחים:</span>
                  <strong>{stat.open_leads}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>סה"כ לידים:</span>
                  <strong>{stat.total_leads}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>משקל העדפה:</span>
                  <strong>×{stat.priority_weight}</strong>
                </div>
              </div>
            </div>
          ))}
          {stats.length === 0 && (
            <div className={s.card} style={{ padding: 20, gridColumn: '1 / -1' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--warning)' }}>
                <Users size={20} />
                <span>אין כללי שיוך מוגדרים. עבור לכרטיסיית "כללים" כדי להגדיר.</span>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'rules' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {rules.map((rule) => (
            <div key={rule.id} className={s.card} style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 style={{ margin: 0, fontSize: 18 }}>{rule.salesperson_name}</h3>
                <div style={{ display: 'flex', gap: 8 }}>
                  {editingId === rule.id ? (
                    <>
                      <button 
                        className={`${s.btn} ${s['btn-primary']} ${s['btn-sm']}`}
                        onClick={() => handleSave(rule.salesperson_id)}
                      >
                        שמור
                      </button>
                      <button 
                        className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`}
                        onClick={() => setEditingId(null)}
                      >
                        ביטול
                      </button>
                    </>
                  ) : (
                    <button 
                      className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`}
                      onClick={() => handleEdit(rule)}
                    >
                      ערוך
                    </button>
                  )}
                </div>
              </div>

              {editingId === rule.id ? (
                <div style={{ display: 'grid', gap: 16, gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
                  <div className={s['form-group']}>
                    <label className={s['form-label']}>מגבלה יומית</label>
                    <input
                      className={s.input}
                      type="number"
                      value={editForm.daily_lead_limit ?? ''}
                      onChange={set('daily_lead_limit')}
                      placeholder="ללא הגבלה"
                    />
                  </div>
                  <div className={s['form-group']}>
                    <label className={s['form-label']}>משקל העדפה (1-10)</label>
                    <input
                      className={s.input}
                      type="number"
                      min="1"
                      max="10"
                      value={editForm.priority_weight ?? 1}
                      onChange={set('priority_weight')}
                    />
                  </div>
                  <div className={s['form-group']}>
                    <label className={s['form-label']}>מקסימום לידים פתוחים</label>
                    <input
                      className={s.input}
                      type="number"
                      value={editForm.max_open_leads ?? ''}
                      onChange={set('max_open_leads')}
                      placeholder="ללא הגבלה"
                    />
                  </div>
                  <div className={s['form-group']} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <input
                      type="checkbox"
                      checked={editForm.is_active ?? true}
                      onChange={set('is_active')}
                      id={`active-${rule.id}`}
                    />
                    <label htmlFor={`active-${rule.id}`} style={{ cursor: 'pointer' }}>פעיל</label>
                  </div>
                </div>
              ) : (
                <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', fontSize: 14 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>מגבלה יומית:</span>
                    <strong>{rule.daily_lead_limit ?? 'ללא הגבלה'}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>לידים היום:</span>
                    <strong>{rule.daily_leads_assigned}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>משקל העדפה:</span>
                    <strong>×{rule.priority_weight}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>מקס' פתוחים:</span>
                    <strong>{rule.max_open_leads ?? 'ללא הגבלה'}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>לידים פתוחים:</span>
                    <strong>{rule.current_open_leads ?? 0}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>סטטוס:</span>
                    <span className={`${s.badge} ${rule.is_active ? s['badge-success'] : s['badge-secondary']}`}>
                      {rule.is_active ? 'פעיל' : 'לא פעיל'}
                    </span>
                  </div>
                </div>
              )}
            </div>
          ))}
          {rules.length === 0 && (
            <div className={s.card} style={{ padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--warning)' }}>
                <Users size={20} />
                <span>אין כללי שיוך. צור כללים דרך ה-API או פנה למנהל המערכת.</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
