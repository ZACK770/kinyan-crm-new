import { useEffect, useState } from 'react'
import {
  Users, RefreshCw, Settings, BarChart3, CheckCircle, XCircle,
  Plus, Trash2, Power,
} from 'lucide-react'
import { api } from '@/lib/api'
import { formatDate } from '@/lib/status'
import { useToast } from '@/components/ui/Toast'
import { useModal } from '@/components/ui/Modal'
import { PageHeader } from '@/components/ui/PageHeader'
import { SmartTable, type SmartColumn } from '@/components/ui/SmartTable'
import type { Salesperson } from '@/types'
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

interface SalespersonWithoutRules {
  id: number
  name: string
  email: string | null
  phone: string | null
}

export function SalesAssignmentRulesPage() {
  const [rules, setRules] = useState<AssignmentRules[]>([])
  const [stats, setStats] = useState<AssignmentStats[]>([])
  const [salespeople, setSalespeople] = useState<Salesperson[]>([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editForm, setEditForm] = useState<Partial<AssignmentRules>>({})
  const [activeTab, setActiveTab] = useState<'salespeople' | 'stats' | 'rules'>('salespeople')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [salesWithoutRules, setSalesWithoutRules] = useState<SalespersonWithoutRules[]>([])
  const [selectedSp, setSelectedSp] = useState<Salesperson | null>(null)
  const [createForm, setCreateForm] = useState<{
    salesperson_id: number | null
    daily_lead_limit: number | null
    priority_weight: number
    max_open_leads: number | null
    is_active: boolean
  }>({
    salesperson_id: null,
    daily_lead_limit: null,
    priority_weight: 5,
    max_open_leads: null,
    is_active: true
  })
  const toast = useToast()
  const { openModal, closeModal } = useModal()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [rulesData, statsData, withoutRulesData, spData] = await Promise.all([
        api.get<AssignmentRules[]>('/sales-assignment-rules/?include_stats=true'),
        api.get<AssignmentStats[]>('/sales-assignment-rules/stats'),
        api.get<SalespersonWithoutRules[]>('/sales-assignment-rules/salespeople-without-rules'),
        api.get<Salesperson[]>('/salespeople'),
      ])
      setRules(rulesData)
      setStats(statsData)
      setSalesWithoutRules(withoutRulesData)
      setSalespeople(spData)
    } catch (error) {
      toast.error('שגיאה', 'לא ניתן לטעון נתונים')
    } finally {
      setLoading(false)
    }
  }

  /* ── Salespeople inline update ── */
  const handleSpInlineUpdate = async (sp: Salesperson, field: string, value: unknown) => {
    try {
      const result = await api.patch<Salesperson>(`/salespeople/${sp.id}`, { [field]: value })
      toast.success('עודכן בהצלחה')
      setSalespeople(prev => prev.map(p => p.id === sp.id ? { ...p, ...result } : p))
    } catch {
      toast.error('שגיאה בעדכון')
      throw new Error('update failed')
    }
  }

  /* ── Create salesperson modal ── */
  const openCreateSp = () => {
    openModal({
      title: 'איש מכירות חדש',
      size: 'md',
      content: (
        <SalespersonForm onSubmit={async (data) => {
          try {
            await api.post('/salespeople', data)
            toast.success('איש מכירות נוצר בהצלחה')
            closeModal()
            loadData()
          } catch {
            toast.error('שגיאה ביצירת איש מכירות')
          }
        }} />
      ),
    })
  }

  /* ── Salesperson workspace (detail view) ── */
  const openSpWorkspace = async (sp: Salesperson) => {
    try {
      const full = await api.get<Salesperson>(`/salespeople/${sp.id}`)
      setSelectedSp(full)
    } catch {
      toast.error('שגיאה בטעינת פרטים')
    }
  }

  /* ── SmartTable columns for salespeople ── */
  const spColumns: SmartColumn<Salesperson>[] = [
    {
      key: 'name',
      header: 'שם',
      type: 'text',
      sortable: true,
      renderView: (r) => (
        <span style={{ fontWeight: 600, color: 'var(--color-primary)' }}>
          {r.name}
          {r.user_id && <span title="מקושר למשתמש" style={{ marginRight: 4, fontSize: 10, color: 'var(--color-text-muted)' }}>👤</span>}
        </span>
      ),
    },
    {
      key: 'phone',
      header: 'טלפון',
      type: 'text',
      className: s.mono,
      renderView: r => r.phone ? <span dir="ltr">{r.phone}</span> : <span style={{ color: 'var(--color-text-muted)' }}>—</span>,
    },
    {
      key: 'email',
      header: 'אימייל',
      type: 'text',
      renderView: r => r.email ? <span dir="ltr" style={{ fontSize: 13 }}>{r.email}</span> : <span style={{ color: 'var(--color-text-muted)' }}>—</span>,
    },
    {
      key: 'is_active',
      header: 'סטטוס',
      type: 'boolean',
      renderView: r => (
        <span className={`${s.badge} ${r.is_active ? s['badge-success'] : s['badge-gray']}`}>
          {r.is_active ? 'פעיל' : 'לא פעיל'}
        </span>
      ),
    },
    {
      key: 'total_leads',
      header: 'סה"כ לידים',
      type: 'number',
      editable: false,
      renderView: r => <strong>{r.total_leads ?? 0}</strong>,
    },
    {
      key: 'open_leads',
      header: 'לידים פתוחים',
      type: 'number',
      editable: false,
      renderView: r => <span>{r.open_leads ?? 0}</span>,
    },
    {
      key: 'converted_leads',
      header: 'המרות',
      type: 'number',
      editable: false,
      renderView: r => <span style={{ color: 'var(--success)' }}>{r.converted_leads ?? 0}</span>,
    },
    {
      key: 'notes',
      header: 'הערות',
      type: 'text',
      hiddenByDefault: true,
      sortable: false,
      renderView: r => {
        if (!r.notes) return <span style={{ color: 'var(--color-text-muted)' }}>—</span>
        const short = r.notes.length > 40 ? r.notes.slice(0, 40) + '…' : r.notes
        return <span title={r.notes} style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>{short}</span>
      },
    },
    {
      key: 'created_at',
      header: 'תאריך יצירה',
      type: 'datetime',
      className: s.muted,
      editable: false,
      hiddenByDefault: true,
      renderView: r => r.created_at ? formatDate(r.created_at) : '—',
    },
  ]

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

  const handleCreate = async () => {
    if (!createForm.salesperson_id) {
      toast.error('שגיאה', 'יש לבחור איש מכירות')
      return
    }
    try {
      await api.post('/sales-assignment-rules/', createForm)
      toast.success('נוצר', 'כללי שיוך נוצרו בהצלחה')
      setShowCreateModal(false)
      setCreateForm({
        salesperson_id: null,
        daily_lead_limit: null,
        priority_weight: 5,
        max_open_leads: null,
        is_active: true
      })
      loadData()
    } catch (error) {
      toast.error('שגיאה', 'לא ניתן ליצור כללים')
    }
  }

  const handleDelete = async (salespersonId: number, name: string) => {
    if (!confirm(`האם למחוק את כללי השיוך של ${name}?\nזה יחזיר אותו למצב round-robin רגיל.`)) return
    try {
      await api.delete(`/sales-assignment-rules/${salespersonId}`)
      toast.success('נמחק', 'כללי השיוך נמחקו בהצלחה')
      loadData()
    } catch (error) {
      toast.error('שגיאה', 'לא ניתן למחוק')
    }
  }

  const handleToggleActive = async (salespersonId: number, currentActive: boolean) => {
    try {
      await api.patch(`/sales-assignment-rules/${salespersonId}`, { is_active: !currentActive })
      toast.success('עודכן', currentActive ? 'הכללים הושבתו' : 'הכללים הופעלו')
      loadData()
    } catch (error) {
      toast.error('שגיאה', 'לא ניתן לעדכן')
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
        title="אנשי מכירות ושיוך"
        onRefresh={loadData}
        loading={loading}
      />

      <div style={{ marginBottom: 24, display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <button 
          className={`${s.btn} ${activeTab === 'salespeople' ? s['btn-primary'] : s['btn-secondary']}`}
          onClick={() => setActiveTab('salespeople')}
        >
          <Users size={16} />
          אנשי מכירות
        </button>
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
          כללי שיוך
        </button>
        <div style={{ flex: 1 }} />
        {activeTab === 'salespeople' && (
          <button className={`${s.btn} ${s['btn-success']}`} onClick={openCreateSp}>
            <Plus size={16} />
            איש מכירות חדש
          </button>
        )}
        {activeTab === 'rules' && salesWithoutRules.length > 0 && (
          <button className={`${s.btn} ${s['btn-success']}`} onClick={() => setShowCreateModal(true)}>
            <Plus size={16} />
            הוסף כללים ({salesWithoutRules.length})
          </button>
        )}
        {activeTab === 'rules' && (
          <button className={`${s.btn} ${s['btn-secondary']}`} onClick={handleResetDaily}>
            <RefreshCw size={16} />
            איפוס ספירות
          </button>
        )}
      </div>

      {/* ── Salespeople Tab ── */}
      {activeTab === 'salespeople' && (
        <div className={s.card}>
          <SmartTable
            columns={spColumns}
            data={salespeople}
            loading={loading}
            emptyText="אין אנשי מכירות"
            emptyIcon={<Users size={40} strokeWidth={1.5} />}
            onRowClick={openSpWorkspace}
            onUpdate={handleSpInlineUpdate}
            keyExtractor={(row) => row.id}
            storageKey="salespeople_table_v1"
            searchPlaceholder="חיפוש לפי שם, טלפון, אימייל..."
            searchFields={[
              { key: 'name', label: 'שם', weight: 3 },
              { key: 'phone', label: 'טלפון', weight: 2 },
              { key: 'email', label: 'אימייל', weight: 1 },
            ]}
            defaultPageSize={50}
          />
        </div>
      )}

      {/* ── Salesperson Workspace (detail panel) ── */}
      {selectedSp && (
        <SalespersonWorkspace
          sp={selectedSp}
          onClose={() => { setSelectedSp(null); loadData() }}
          onUpdate={async () => {
            const fresh = await api.get<Salesperson>(`/salespeople/${selectedSp.id}`)
            setSelectedSp(fresh)
          }}
        />
      )}

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

              <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                <button
                  className={`${s.btn} ${s['btn-sm']} ${rule.is_active ? s['btn-warning'] : s['btn-success']}`}
                  onClick={() => handleToggleActive(rule.salesperson_id, rule.is_active)}
                  title={rule.is_active ? 'השבת כללים' : 'הפעל כללים'}
                >
                  <Power size={14} />
                  {rule.is_active ? 'השבת' : 'הפעל'}
                </button>
                <button
                  className={`${s.btn} ${s['btn-sm']} ${s['btn-danger']}`}
                  onClick={() => handleDelete(rule.salesperson_id, rule.salesperson_name)}
                  title="מחק כללים"
                >
                  <Trash2 size={14} />
                  מחק
                </button>
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

      {showCreateModal && (
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
          zIndex: 1000
        }}>
          <div className={s.card} style={{ padding: 24, maxWidth: 500, width: '90%' }}>
            <h3 style={{ marginTop: 0 }}>יצירת כללי שיוך חדשים</h3>
            
            <div className={s['form-group']}>
              <label className={s['form-label']}>בחר איש מכירות</label>
              <select
                className={s.input}
                value={createForm.salesperson_id || ''}
                onChange={(e) => setCreateForm(prev => ({ ...prev, salesperson_id: Number(e.target.value) }))}
              >
                <option value="">-- בחר --</option>
                {salesWithoutRules.map(sp => (
                  <option key={sp.id} value={sp.id}>{sp.name}</option>
                ))}
              </select>
            </div>

            <div style={{ display: 'grid', gap: 16, gridTemplateColumns: '1fr 1fr', marginTop: 16 }}>
              <div className={s['form-group']}>
                <label className={s['form-label']}>מגבלה יומית</label>
                <input
                  className={s.input}
                  type="number"
                  value={createForm.daily_lead_limit ?? ''}
                  onChange={(e) => setCreateForm(prev => ({ ...prev, daily_lead_limit: e.target.value ? Number(e.target.value) : null }))}
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
                  value={createForm.priority_weight}
                  onChange={(e) => setCreateForm(prev => ({ ...prev, priority_weight: Number(e.target.value) }))}
                />
              </div>
              <div className={s['form-group']}>
                <label className={s['form-label']}>מקס' לידים פתוחים</label>
                <input
                  className={s.input}
                  type="number"
                  value={createForm.max_open_leads ?? ''}
                  onChange={(e) => setCreateForm(prev => ({ ...prev, max_open_leads: e.target.value ? Number(e.target.value) : null }))}
                  placeholder="ללא הגבלה"
                />
              </div>
              <div className={s['form-group']} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <input
                  type="checkbox"
                  checked={createForm.is_active}
                  onChange={(e) => setCreateForm(prev => ({ ...prev, is_active: e.target.checked }))}
                  id="create-active"
                />
                <label htmlFor="create-active" style={{ cursor: 'pointer' }}>פעיל</label>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
              <button className={`${s.btn} ${s['btn-primary']}`} onClick={handleCreate}>
                צור כללים
              </button>
              <button className={`${s.btn} ${s['btn-secondary']}`} onClick={() => setShowCreateModal(false)}>
                ביטול
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


/* ══════════════════════════════════════════════════════════════
   Salesperson Create Form (used in modal)
   ══════════════════════════════════════════════════════════════ */
function SalespersonForm({ onSubmit }: { onSubmit: (data: Record<string, string>) => void }) {
  const [form, setForm] = useState({ name: '', phone: '', email: '', notes: '' })
  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [key]: e.target.value }))

  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(form) }} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className={s['form-group']}>
        <label className={s['form-label']}>שם *</label>
        <input className={s.input} value={form.name} onChange={set('name')} required />
      </div>
      <div className={s['form-group']}>
        <label className={s['form-label']}>טלפון</label>
        <input className={s.input} value={form.phone} onChange={set('phone')} dir="ltr" />
      </div>
      <div className={s['form-group']}>
        <label className={s['form-label']}>אימייל</label>
        <input className={s.input} type="email" value={form.email} onChange={set('email')} dir="ltr" />
      </div>
      <div className={s['form-group']}>
        <label className={s['form-label']}>הערות</label>
        <textarea className={s.input} value={form.notes} onChange={set('notes')} rows={3} />
      </div>
      <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>צור איש מכירות</button>
    </form>
  )
}


/* ══════════════════════════════════════════════════════════════
   Salesperson Workspace — Full detail view (like LeadWorkspace)
   ══════════════════════════════════════════════════════════════ */
function SalespersonWorkspace({
  sp,
  onClose,
  onUpdate,
}: {
  sp: Salesperson
  onClose: () => void
  onUpdate: () => Promise<void>
}) {
  const toast = useToast()

  const handleSave = async (field: string, value: string | boolean) => {
    try {
      await api.patch(`/salespeople/${sp.id}`, { [field]: value })
      toast.success('נשמר')
      await onUpdate()
    } catch {
      toast.error('שגיאה בשמירה')
    }
  }

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'var(--color-bg)', zIndex: 100, overflow: 'auto',
      padding: '24px 32px',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}>
        <button className={`${s.btn} ${s['btn-secondary']}`} onClick={onClose}>
          ← חזרה לרשימה
        </button>
        <h2 style={{ margin: 0 }}>{sp.name}</h2>
        {sp.user_id && (
          <span className={`${s.badge} ${s['badge-blue']}`}>מקושר למשתמש</span>
        )}
        <span className={`${s.badge} ${sp.is_active ? s['badge-success'] : s['badge-gray']}`}>
          {sp.is_active ? 'פעיל' : 'לא פעיל'}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, maxWidth: 900 }}>
        {/* Left column — Details */}
        <div className={s.card} style={{ padding: 20 }}>
          <h3 style={{ marginTop: 0, marginBottom: 16 }}>פרטים</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <EditableRow label="שם" value={sp.name} onSave={(v) => handleSave('name', v)} />
            <EditableRow label="טלפון" value={sp.phone || ''} onSave={(v) => handleSave('phone', v)} dir="ltr" />
            <EditableRow label="אימייל" value={sp.email || ''} onSave={(v) => handleSave('email', v)} dir="ltr" />
            <EditableRow label="קוד הפניה" value={sp.ref_code || ''} onSave={(v) => handleSave('ref_code', v)} />
            <EditableRow label="Webhook URL" value={sp.notification_webhook_url || ''} onSave={(v) => handleSave('notification_webhook_url', v)} dir="ltr" />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>התראות על ליד חדש</span>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={sp.notify_on_new_lead ?? true}
                  onChange={(e) => handleSave('notify_on_new_lead', e.target.checked)}
                />
                {sp.notify_on_new_lead ? 'כן' : 'לא'}
              </label>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>פעיל</span>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={sp.is_active}
                  onChange={(e) => handleSave('is_active', e.target.checked)}
                />
                {sp.is_active ? 'כן' : 'לא'}
              </label>
            </div>
          </div>
        </div>

        {/* Right column — Stats + Notes */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className={s.card} style={{ padding: 20 }}>
            <h3 style={{ marginTop: 0, marginBottom: 16 }}>סטטיסטיקות</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, textAlign: 'center' }}>
              <div>
                <div style={{ fontSize: 28, fontWeight: 700 }}>{sp.total_leads ?? 0}</div>
                <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>סה"כ לידים</div>
              </div>
              <div>
                <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--warning)' }}>{sp.open_leads ?? 0}</div>
                <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>פתוחים</div>
              </div>
              <div>
                <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--success)' }}>{sp.converted_leads ?? 0}</div>
                <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>המרות</div>
              </div>
            </div>
          </div>

          <div className={s.card} style={{ padding: 20 }}>
            <h3 style={{ marginTop: 0, marginBottom: 12 }}>הערות</h3>
            <EditableTextarea value={sp.notes || ''} onSave={(v) => handleSave('notes', v)} />
          </div>

          <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
            <div>נוצר: {sp.created_at ? formatDate(sp.created_at) : '—'}</div>
          </div>
        </div>
      </div>
    </div>
  )
}


/* ── Inline editable row helper ── */
function EditableRow({
  label, value, onSave, dir,
}: {
  label: string; value: string; onSave: (v: string) => void; dir?: string
}) {
  const [editing, setEditing] = useState(false)
  const [val, setVal] = useState(value)

  useEffect(() => { setVal(value) }, [value])

  const save = () => {
    if (val !== value) onSave(val)
    setEditing(false)
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', minHeight: 32 }}>
      <span style={{ color: 'var(--color-text-muted)', fontSize: 13, minWidth: 100 }}>{label}</span>
      {editing ? (
        <input
          autoFocus
          className={s.input}
          style={{ flex: 1, marginRight: 8, padding: '4px 8px', fontSize: 13 }}
          value={val}
          onChange={(e) => setVal(e.target.value)}
          onBlur={save}
          onKeyDown={(e) => { if (e.key === 'Enter') save(); if (e.key === 'Escape') { setVal(value); setEditing(false) } }}
          dir={dir}
        />
      ) : (
        <span
          onClick={() => setEditing(true)}
          style={{ cursor: 'pointer', flex: 1, textAlign: 'left', marginRight: 8, fontSize: 13, direction: dir as 'ltr' | 'rtl' | undefined }}
          title="לחץ לעריכה"
        >
          {value || <span style={{ color: 'var(--color-text-muted)' }}>—</span>}
        </span>
      )}
    </div>
  )
}


/* ── Editable textarea helper ── */
function EditableTextarea({ value, onSave }: { value: string; onSave: (v: string) => void }) {
  const [editing, setEditing] = useState(false)
  const [val, setVal] = useState(value)

  useEffect(() => { setVal(value) }, [value])

  const save = () => {
    if (val !== value) onSave(val)
    setEditing(false)
  }

  if (editing) {
    return (
      <textarea
        autoFocus
        className={s.input}
        style={{ width: '100%', minHeight: 80, fontSize: 13 }}
        value={val}
        onChange={(e) => setVal(e.target.value)}
        onBlur={save}
      />
    )
  }

  return (
    <div
      onClick={() => setEditing(true)}
      style={{ cursor: 'pointer', fontSize: 13, minHeight: 40, whiteSpace: 'pre-wrap', color: value ? undefined : 'var(--color-text-muted)' }}
      title="לחץ לעריכה"
    >
      {value || 'אין הערות — לחץ להוספה'}
    </div>
  )
}
