import { useEffect, useState, useCallback, type FormEvent } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Plus,
  Phone,
  Eye,
  Pencil,
  MessageSquarePlus,
  UserCheck,
} from 'lucide-react'
import { api } from '@/lib/api'
import { getStatus, getSourceLabel, formatDate, formatDateTime } from '@/lib/status'
import { useModal } from '@/components/ui/Modal'
import { useToast } from '@/components/ui/Toast'
import { SmartTable, type SmartColumn } from '@/components/ui/SmartTable'
import { LeadWorkspace } from '@/components/leads'
import type { Lead, LeadInteraction, Salesperson, Course, Campaign } from '@/types'
import s from '@/styles/shared.module.css'

/* ── status badge helper ── */
function Badge({ entity, value }: { entity: string; value?: string }) {
  const { label, color } = getStatus(entity, value)
  return <span className={`${s.badge} ${s[`badge-${color}`]}`}>{label}</span>
}

/* ══════════════════════════════════════════════════════════════
   Lead Create / Edit Form
   ══════════════════════════════════════════════════════════════ */
function LeadForm({
  initial,
  salespersons,
  campaigns,
  courses,
  onSubmit,
}: {
  initial?: Partial<Lead>
  salespersons: Salesperson[]
  campaigns: Campaign[]
  courses: Course[]
  onSubmit: (data: Record<string, unknown>) => void
}) {
  const [form, setForm] = useState({
    full_name: initial?.full_name ?? '',
    family_name: initial?.family_name ?? '',
    phone: initial?.phone ?? '',
    phone2: initial?.phone2 ?? '',
    email: initial?.email ?? '',
    city: initial?.city ?? '',
    source_type: initial?.source_type ?? '',
    campaign_id: initial?.campaign_id ?? '',
    course_id: initial?.course_id ?? '',
    notes: initial?.notes ?? '',
    salesperson_id: initial?.salesperson_id ?? '',
    status: initial?.status ?? 'new',
  })

  // Get selected course for price display
  const selectedCourse = courses.find(c => c.id === Number(form.course_id))

  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [key]: e.target.value }))

  const handle = (e: FormEvent) => {
    e.preventDefault()
    const data: Record<string, unknown> = { ...form }
    if (data.salesperson_id) data.salesperson_id = Number(data.salesperson_id)
    else delete data.salesperson_id
    if (data.campaign_id) data.campaign_id = Number(data.campaign_id)
    else delete data.campaign_id
    if (data.course_id) data.course_id = Number(data.course_id)
    else delete data.course_id
    // Remove empty strings
    Object.keys(data).forEach(k => { if (data[k] === '') delete data[k] })
    onSubmit(data)
  }

  return (
    <form onSubmit={handle} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>שם פרטי *</label>
          <input className={s.input} value={form.full_name} onChange={set('full_name')} required />
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>שם משפחה</label>
          <input className={s.input} value={form.family_name} onChange={set('family_name')} />
        </div>
      </div>

      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>טלפון *</label>
          <input className={s.input} value={form.phone} onChange={set('phone')} required dir="ltr" />
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>טלפון 2</label>
          <input className={s.input} value={form.phone2} onChange={set('phone2')} dir="ltr" />
        </div>
      </div>

      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>אימייל</label>
          <input className={s.input} type="email" value={form.email} onChange={set('email')} dir="ltr" />
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>עיר</label>
          <input className={s.input} value={form.city} onChange={set('city')} />
        </div>
      </div>

      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>מקור</label>
          <select className={s.select} value={form.source_type} onChange={set('source_type')}>
            <option value="">— בחר —</option>
            <option value="yemot">ימות המשיח</option>
            <option value="elementor">אלמנטור</option>
            <option value="manual">ידני</option>
            <option value="referral">הפניה</option>
            <option value="other">אחר</option>
          </select>
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>קמפיין</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <select className={s.select} value={form.campaign_id} onChange={set('campaign_id')} style={{ flex: 1 }}>
              <option value="">— בחר קמפיין —</option>
              {campaigns.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <button
              type="button"
              className={`${s.btn} ${s['btn-icon']} ${s['btn-ghost']}`}
              title="צור חדש"
              onClick={() => window.open('/campaigns?create=true', '_blank')}
              style={{ flexShrink: 0, padding: 6 }}
            >
              <Plus size={16} />
            </button>
          </div>
        </div>
      </div>

      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>קורס מבוקש</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <select className={s.select} value={form.course_id} onChange={set('course_id')} style={{ flex: 1 }}>
              <option value="">— בחר קורס —</option>
              {courses.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <button
              type="button"
              className={`${s.btn} ${s['btn-icon']} ${s['btn-ghost']}`}
              title="צור חדש"
              onClick={() => window.open('/courses?create=true', '_blank')}
              style={{ flexShrink: 0, padding: 6 }}
            >
              <Plus size={16} />
            </button>
          </div>
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>איש מכירות</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <select className={s.select} value={form.salesperson_id} onChange={set('salesperson_id')} style={{ flex: 1 }}>
              <option value="">— ללא —</option>
              {salespersons.map(sp => (
                <option key={sp.id} value={sp.id}>{sp.name}</option>
              ))}
            </select>
            <button
              type="button"
              className={`${s.btn} ${s['btn-icon']} ${s['btn-ghost']}`}
              title="צור חדש"
              onClick={() => window.open('/leads?create=true', '_blank')}
              style={{ flexShrink: 0, padding: 6 }}
            >
              <Plus size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Show course price if selected */}
      {selectedCourse && (
        <div className={s['detail-row']} style={{ background: 'var(--bg-accent)', padding: '8px 12px', borderRadius: 6 }}>
          <span className={s['detail-key']}>קורס נבחר</span>
          <span className={s['detail-value']} style={{ fontWeight: 600 }}>{selectedCourse.name}</span>
        </div>
      )}

      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>סטטוס</label>
          <select className={s.select} value={form.status} onChange={set('status')}>
            <option value="new">חדש</option>
            <option value="contacted">נוצר קשר</option>
            <option value="interested">מעוניין</option>
            <option value="converted">הומר</option>
            <option value="irrelevant">לא רלוונטי</option>
          </select>
        </div>
      </div>

      <div className={s['form-group']}>
        <label className={s['form-label']}>הערות</label>
        <textarea className={s.textarea} value={form.notes} onChange={set('notes')} rows={3} />
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-start', gap: 8, paddingTop: 8 }}>
        <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>
          {initial?.id ? 'עדכן' : 'צור ליד'}
        </button>
      </div>
    </form>
  )
}

/* ══════════════════════════════════════════════════════════════
   Add Interaction Form
   ══════════════════════════════════════════════════════════════ */
function InteractionForm({ onSubmit }: { onSubmit: (data: Record<string, unknown>) => void }) {
  const [form, setForm] = useState({
    interaction_type: 'call',
    call_status: '',
    description: '',
  })
  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [key]: e.target.value }))

  const handle = (e: FormEvent) => {
    e.preventDefault()
    const data: Record<string, unknown> = { ...form }
    Object.keys(data).forEach(k => { if (data[k] === '') delete data[k] })
    onSubmit(data)
  }

  return (
    <form onSubmit={handle} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>סוג</label>
          <select className={s.select} value={form.interaction_type} onChange={set('interaction_type')}>
            <option value="call">שיחה</option>
            <option value="sms">SMS</option>
            <option value="whatsapp">וואטסאפ</option>
            <option value="email">אימייל</option>
            <option value="meeting">פגישה</option>
            <option value="note">הערה</option>
          </select>
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>סטטוס שיחה</label>
          <select className={s.select} value={form.call_status} onChange={set('call_status')}>
            <option value="">— —</option>
            <option value="answered">ענה</option>
            <option value="no_answer">לא ענה</option>
            <option value="busy">תפוס</option>
            <option value="voicemail">תא קולי</option>
          </select>
        </div>
      </div>
      <div className={s['form-group']}>
        <label className={s['form-label']}>תיאור</label>
        <textarea className={s.textarea} value={form.description} onChange={set('description')} rows={3} />
      </div>
      <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>הוסף</button>
    </form>
  )
}

/* ══════════════════════════════════════════════════════════════
   Convert Lead to Student Form
   ══════════════════════════════════════════════════════════════ */
function ConvertLeadForm({
  courses,
  onSubmit,
}: {
  courses: Course[]
  onSubmit: (courseId: number | null) => void
}) {
  const [courseId, setCourseId] = useState('')
  
  const handle = (e: FormEvent) => {
    e.preventDefault()
    onSubmit(courseId ? Number(courseId) : null)
  }

  const selectedCourse = courses.find(c => c.id === Number(courseId))

  return (
    <form onSubmit={handle} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: 14 }}>
        המרה לתלמיד תיצור רשומת תלמיד חדשה עם כל הפרטים מהליד.
      </p>
      
      <div className={s['form-group']}>
        <label className={s['form-label']}>קורס להרשמה (אופציונלי)</label>
        <select className={s.select} value={courseId} onChange={e => setCourseId(e.target.value)}>
          <option value="">— ללא הרשמה לקורס —</option>
          {courses.map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      {selectedCourse && (
        <div className={s['detail-row']} style={{ background: 'var(--bg-accent)', padding: '8px 12px', borderRadius: 6 }}>
          <span className={s['detail-key']}>קורס נבחר</span>
          <span className={s['detail-value']} style={{ fontWeight: 600 }}>{selectedCourse.name}</span>
        </div>
      )}

      <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>
        <UserCheck size={16} strokeWidth={1.5} />
        {courseId ? 'המר והרשם לקורס' : 'המר לתלמיד'}
      </button>
    </form>
  )
}

/* ══════════════════════════════════════════════════════════════
   Lead Detail (shown in modal)
   ══════════════════════════════════════════════════════════════ */
function LeadDetail({
  lead,
  salespersons,
  courses: _courses,
  onEdit,
  onAddInteraction,
  onConvert,
}: {
  lead: Lead
  salespersons: Salesperson[]
  courses: Course[]
  onEdit: () => void
  onAddInteraction: () => void
  onConvert: () => void
}) {
  const sp = salespersons.find(s => s.id === lead.salesperson_id)
  const isConverted = lead.status === 'converted' || lead.student_id
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Info section */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, gap: 8 }}>
          <h4 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>פרטי ליד</h4>
          <div style={{ display: 'flex', gap: 8 }}>
            {!isConverted && (
              <button className={`${s.btn} ${s['btn-primary']} ${s['btn-sm']}`} onClick={onConvert}>
                <UserCheck size={14} strokeWidth={1.5} /> המר לתלמיד
              </button>
            )}
            <button className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`} onClick={onEdit}>
              <Pencil size={14} strokeWidth={1.5} /> עריכה
            </button>
          </div>
        </div>
        {isConverted && lead.student_id && (
          <div className={s['detail-row']} style={{ background: 'var(--bg-success)', padding: '8px 12px', borderRadius: 6, marginBottom: 12 }}>
            <span className={s['detail-key']}>🎉 הומר לתלמיד</span>
            <span className={s['detail-value']} style={{ fontWeight: 600 }}>תלמיד #{lead.student_id}</span>
          </div>
        )}
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>שם</span>
          <span className={s['detail-value']}>{lead.full_name} {lead.family_name ?? ''}</span>
        </div>
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>טלפון</span>
          <span className={s['detail-value']} dir="ltr" style={{ textAlign: 'left' }}>{lead.phone}</span>
        </div>
        {lead.email && (
          <div className={s['detail-row']}>
            <span className={s['detail-key']}>אימייל</span>
            <span className={s['detail-value']} dir="ltr">{lead.email}</span>
          </div>
        )}
        {lead.city && (
          <div className={s['detail-row']}>
            <span className={s['detail-key']}>עיר</span>
            <span className={s['detail-value']}>{lead.city}</span>
          </div>
        )}
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>סטטוס</span>
          <span className={s['detail-value']}><Badge entity="lead" value={lead.status} /></span>
        </div>
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>מקור</span>
          <span className={s['detail-value']}>{getSourceLabel(lead.source_type)}</span>
        </div>
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>איש מכירות</span>
          <span className={s['detail-value']}>{sp?.name ?? '—'}</span>
        </div>
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>תאריך יצירה</span>
          <span className={s['detail-value']}>{formatDateTime(lead.created_at)}</span>
        </div>
        {lead.notes && (
          <div className={s['detail-row']}>
            <span className={s['detail-key']}>הערות</span>
            <span className={s['detail-value']}>{lead.notes}</span>
          </div>
        )}
      </div>

      {/* Interactions timeline */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h4 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>אינטראקציות</h4>
          <button className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`} onClick={onAddInteraction}>
            <MessageSquarePlus size={14} strokeWidth={1.5} /> הוסף
          </button>
        </div>
        {lead.interactions?.length ? (
          <div className={s.timeline}>
            {lead.interactions.map((ia: LeadInteraction) => (
              <div key={ia.id} className={s['timeline-item']}>
                <span className={s['timeline-dot']} />
                <div className={s['timeline-content']}>
                  <div className={s['timeline-date']}>{formatDateTime(ia.interaction_date || ia.created_at)}</div>
                  <div className={s['timeline-text']}>
                    <strong>{ia.interaction_type}</strong>
                    {ia.call_status && ` — ${ia.call_status}`}
                    {ia.description && ` · ${ia.description}`}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className={s.empty} style={{ padding: 20 }}>
            <span className={s['empty-text']}>אין אינטראקציות עדיין</span>
          </div>
        )}
      </div>
    </div>
  )
}

/* ══════════════════════════════════════════════════════════════
   Leads Page
   ══════════════════════════════════════════════════════════════ */
export function LeadsPage() {
  const { openModal, closeModal } = useModal()
  const toast = useToast()

  const [leads, setLeads] = useState<Lead[]>([])
  const [salespersons, setSalespersons] = useState<Salesperson[]>([])
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(true)
  
  // Workspace view state: 'list' | 'create' | Lead object (edit mode)
  type ViewMode = 'list' | 'create'
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null)
  const [searchParams, setSearchParams] = useSearchParams()

  // Auto-open create form when ?create=true (from entity '+' button)
  useEffect(() => {
    if (searchParams.get('create') === 'true') {
      setViewMode('create')
      setSelectedLead(null)
      setSearchParams({}, { replace: true })
    }
  }, [searchParams, setSearchParams])

  /* ── Fetch Reference Data ── */
  useEffect(() => {
    // Load salespeople, campaigns, courses in parallel
    Promise.all([
      api.get<Salesperson[]>('leads/salespersons').catch(() => []),
      api.get<Campaign[]>('campaigns').catch(() => []),
      api.get<Course[]>('courses').catch(() => []),
    ]).then(([sp, camp, crs]) => {
      setSalespersons(sp)
      setCampaigns(camp)
      setCourses(crs)
    })
  }, [])

  /* ── Fetch Leads ── */
  const fetchLeads = useCallback(async () => {
    setLoading(true)
    try {
      // Fetch leads (API max limit is 200)
      const data = await api.get<Lead[]>('leads?limit=200')
      setLeads(data)
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בטעינת לידים')
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => { fetchLeads() }, [fetchLeads])

  /* ── Inline Update ── */
  const handleInlineUpdate = async (lead: Lead, field: string, value: unknown) => {
    try {
      const payload: Record<string, unknown> = { [field]: value }
      // Handle special fields conversions if needed
      await api.patch(`leads/${lead.id}`, payload)
      toast.success('עודכן בהצלחה')
      
      // Update local state to avoid full reload
      setLeads(prev => prev.map(p => p.id === lead.id ? { ...p, ...payload } : p))
    } catch (err) {
      toast.error('שגיאה בעדכון')
      throw err // SmartTable will catch this to revert/show error
    }
  }

  /* ── Bulk Actions ── */
  const handleBulkUpdate = async (selectedLeads: Lead[], field: string, value: unknown) => {
    try {
      const ids = selectedLeads.map(l => l.id)
      await api.post('leads/bulk-update', { ids, field, value })
      toast.success(`עודכנו ${ids.length} לידים`)
      fetchLeads()
    } catch (err) {
      toast.error('שגיאה בעדכון מרובה')
    }
  }

  const handleBulkDelete = async (selectedLeads: Lead[]) => {
    try {
      const ids = selectedLeads.map(l => l.id)
      await api.post('leads/bulk-delete', { ids })
      toast.success(`נמחקו ${ids.length} לידים`)
      fetchLeads()
    } catch (err) {
      toast.error('שגיאה במחיקה')
    }
  }

  /* ── Create — Opens workspace in create mode ── */
  const openCreate = () => {
    setSelectedLead(null)
    setViewMode('create')
  }

  /* ── Open Lead Workspace (full view) ── */
  const openLeadWorkspace = async (lead: Lead) => {
    try {
      const full = await api.get<Lead>(`leads/${lead.id}`)
      setSelectedLead(full)
      setViewMode('list')  // Not 'create' — we have a selected lead
    } catch {
      toast.error('שגיאה בטעינת פרטי ליד')
    }
  }

  /* ── Back to list ── */
  const backToList = () => {
    setSelectedLead(null)
    setViewMode('list')
  }

  const refreshSelectedLead = async () => {
    if (!selectedLead) return
    try {
      const fresh = await api.get<Lead>(`leads/${selectedLead.id}`)
      setSelectedLead(fresh)
    } catch {
      // Ignore refresh errors
    }
  }

  /* ── Detail (legacy modal - can be removed) ── */
  const openDetail = async (lead: Lead) => {
    // Now opens workspace instead of modal
    openLeadWorkspace(lead)
  }

  const showDetailModal = (lead: Lead) => {
    openModal({
      title: `${lead.full_name} ${lead.family_name ?? ''}`.trim(),
      size: 'lg',
      content: (
        <LeadDetail
          lead={lead}
          salespersons={salespersons}
          courses={courses}
          onEdit={() => {
            closeModal()
            openEdit(lead)
          }}
          onAddInteraction={() => {
            closeModal()
            openAddInteraction(lead.id)
          }}
          onConvert={() => {
            closeModal()
            openConvert(lead)
          }}
        />
      ),
    })
  }

  /* ── Convert Lead to Student ── */
  const openConvert = (lead: Lead) => {
    openModal({
      title: `המרה לתלמיד — ${lead.full_name}`,
      size: 'md',
      content: (
        <ConvertLeadForm
          courses={courses}
          onSubmit={async (courseId) => {
            try {
              const result = await api.post<{ success: boolean; student_id?: number; message?: string }>(
                `leads/${lead.id}/convert`,
                { course_id: courseId || null }
              )
              toast.success(result.message ?? 'ליד הומר לתלמיד בהצלחה!')
              closeModal()
              fetchLeads()
            } catch (err: unknown) {
              toast.error((err as { message?: string }).message ?? 'שגיאה בהמרה')
            }
          }}
        />
      ),
    })
  }

  /* ── Edit ── */
  const openEdit = (lead: Lead) => {
    openModal({
      title: `עריכת ליד — ${lead.full_name}`,
      size: 'lg',
      content: (
        <LeadForm
          initial={lead}
          salespersons={salespersons}
          campaigns={campaigns}
          courses={courses}
          onSubmit={async data => {
            try {
              await api.patch(`leads/${lead.id}`, data)
              toast.success('ליד עודכן')
              closeModal()
              fetchLeads()
            } catch (err: unknown) {
              toast.error((err as { message?: string }).message ?? 'שגיאה')
            }
          }}
        />
      ),
    })
  }

  /* ── Add Interaction ── */
  const openAddInteraction = (leadId: number) => {
    openModal({
      title: 'הוספת אינטראקציה',
      size: 'md',
      content: (
        <InteractionForm
          onSubmit={async data => {
            try {
              await api.post(`leads/${leadId}/interactions`, data)
              toast.success('אינטראקציה נוספה')
              closeModal()
              // Refresh and reopen detail
              const fresh = await api.get<Lead>(`leads/${leadId}`)
              showDetailModal(fresh)
            } catch (err: unknown) {
              toast.error((err as { message?: string }).message ?? 'שגיאה')
            }
          }}
        />
      ),
    })
  }

  /* ── Columns (SmartTable) ── */
  const columns: SmartColumn<Lead>[] = [
    { 
      key: 'full_name', 
      header: 'שם מלא', 
      type: 'text',
      sortable: true,
      filterable: true,
      render: (r) => (
        <span 
          style={{ fontWeight: 600, color: 'var(--color-primary)', cursor: 'pointer' }}
          onClick={() => openDetail(r)}
        >
          {r.full_name} {r.family_name ?? ''}
        </span>
      )
    },
    { 
      key: 'phone', 
      header: 'טלפון', 
      type: 'text',
      className: s.mono, 
      renderView: r => <span dir="ltr">{r.phone}</span>,
      editable: false // Phone usually shouldn't be edited inline easily
    },
    { 
      key: 'status', 
      header: 'סטטוס', 
      type: 'select',
      options: [
        { value: 'new', label: 'חדש' },
        { value: 'contacted', label: 'נוצר קשר' },
        { value: 'interested', label: 'מעוניין' },
        { value: 'converted', label: 'הומר' },
        { value: 'irrelevant', label: 'לא רלוונטי' },
      ],
    },
    { 
      key: 'salesperson_id', 
      header: 'איש מכירות', 
      type: 'select',
      options: salespersons.map(sp => ({ value: sp.id, label: sp.name })),
    },
    { 
      key: 'source_type', 
      header: 'מקור', 
      type: 'select',
      options: [
        { value: 'yemot', label: 'ימות המשיח' },
        { value: 'elementor', label: 'אלמנטור' },
        { value: 'manual', label: 'ידני' },
        { value: 'referral', label: 'הפניה' },
        { value: 'other', label: 'אחר' },
      ],
    },
    { 
      key: 'created_at', 
      header: 'תאריך יצירה', 
      type: 'datetime',
      className: s.muted,
      editable: false,
      renderView: r => formatDate(r.created_at)
    },
    {
      key: '_actions',
      header: '',
      type: 'text',
      width: 80,
      render: r => (
        <div style={{ display: 'flex', gap: 4 }}>
          <button
            className={`${s.btn} ${s['btn-ghost']} ${s['btn-xs']}`}
            onClick={e => { e.stopPropagation(); openDetail(r) }}
            title="צפה"
          >
            <Eye size={14} strokeWidth={1.5} />
          </button>
          <button
            className={`${s.btn} ${s['btn-ghost']} ${s['btn-xs']}`}
            onClick={e => { e.stopPropagation(); openEdit(r) }}
            title="ערוך"
          >
            <Pencil size={14} strokeWidth={1.5} />
          </button>
        </div>
      ),
    },
  ]

  // Handle created lead — go to workspace in edit mode
  const handleCreatedLead = async (newLead: Lead) => {
    toast.success('ליד נוצר בהצלחה')
    fetchLeads()
    // Open the newly created lead in workspace
    setSelectedLead(newLead)
    setViewMode('list')
  }

  // Show workspace in CREATE mode
  if (viewMode === 'create') {
    return (
      <LeadWorkspace
        lead={null}
        salespersons={salespersons}
        campaigns={campaigns}
        courses={courses}
        onClose={backToList}
        onUpdate={() => {}}
        onCreate={handleCreatedLead}
      />
    )
  }

  // Show workspace in EDIT mode (selectedLead exists)
  if (selectedLead) {
    return (
      <LeadWorkspace
        lead={selectedLead}
        salespersons={salespersons}
        campaigns={campaigns}
        courses={courses}
        onClose={backToList}
        onUpdate={refreshSelectedLead}
        onAddInteraction={() => openAddInteraction(selectedLead.id)}
        onConvert={() => openConvert(selectedLead)}
      />
    )
  }

  return (
    <div>
      {/* Page header */}
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>לידים</h1>
        <div className={s['page-actions']}>
          <button className={`${s.btn} ${s['btn-primary']}`} onClick={openCreate}>
            <Plus size={16} strokeWidth={1.5} /> ליד חדש
          </button>
        </div>
      </div>

      {/* Card with SmartTable */}
      <div className={s.card}>
        <SmartTable
          columns={columns as SmartColumn<Lead>[]}
          data={leads}
          loading={loading}
          emptyText="לא נמצאו לידים"
          emptyIcon={<Phone size={40} strokeWidth={1.5} />}
          onRowClick={openLeadWorkspace}
          onUpdate={handleInlineUpdate}
          onDelete={handleBulkDelete}
          onBulkUpdate={handleBulkUpdate}
          keyExtractor={(row) => row.id}
          storageKey="leads_table_v1"
          bulkActions={[
            {
              id: 'assign_sp',
              label: 'שיוך לאיש מכירות',
              icon: <UserCheck size={14} />,
              action: (selected) => {
                // TODO: Open modal to select SP
                toast.success(`נבחרו ${selected.length} לידים לשיוך`)
              }
            }
          ]}
        />
      </div>
    </div>
  )
}
