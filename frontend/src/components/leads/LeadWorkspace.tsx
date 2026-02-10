import { useState, useCallback, useMemo, type ReactNode, type FormEvent } from 'react'
import {
  MessageSquarePlus,
  UserCheck,
  ArrowLeft,
  CreditCard,
  ListTodo,
  MessageCircle,
  History,
  Save,
} from 'lucide-react'
import { api } from '@/lib/api'
import { getStatus, formatDateTime } from '@/lib/status'
import { EditableField, type SelectOption } from '@/components/ui/EditableField'
import { useModal } from '@/components/ui/Modal'
import type { Lead, LeadInteraction, Salesperson, Course, Campaign } from '@/types'
import { LeadPaymentTab } from './LeadPaymentTab'
import s from '@/styles/shared.module.css'

/* ══════════════════════════════════════════════════════════════
   Lead Workspace — Full workspace view for lead management
   ═══════════════════════════════════════════════════════════════
   Supports both CREATE and EDIT modes:
   - CREATE: lead is null, shows form with fields
   - EDIT: lead is provided, inline editable fields (auto-save on blur)
   
   UX Improvements:
   - Auto-save on blur for edit mode (no OK/✓ buttons needed)
   - Unsaved changes detection for create mode
   - Confirmation dialog when closing with unsaved changes
   ══════════════════════════════════════════════════════════════ */

// Status badge helper
function Badge({ entity, value }: { entity: string; value?: string }) {
  const { label, color } = getStatus(entity, value)
  return <span className={`${s.badge} ${s[`badge-${color}`]}`}>{label}</span>
}

// Status options (Hebrew per SPEC)
const STATUS_OPTIONS: SelectOption[] = [
  { value: 'new', label: 'ליד חדש' },
  { value: 'first_call', label: 'חיוג ראשון' },
  { value: 'follow_up', label: 'במעקב' },
  { value: 'interested', label: 'מתעניין' },
  { value: 'payment_done', label: 'נסלק' },
  { value: 'converted', label: 'ליד סגור-לקוח' },
  { value: 'not_relevant', label: 'ליד סגור-לא רלוונטי' },
]

const SOURCE_OPTIONS: SelectOption[] = [
  { value: 'yemot', label: 'ימות המשיח' },
  { value: 'elementor', label: 'אלמנטור' },
  { value: 'manual', label: 'ידני' },
  { value: 'referral', label: 'הפניה' },
  { value: 'other', label: 'אחר' },
]

// Initial empty form state
const INITIAL_FORM = {
  full_name: '',
  family_name: '',
  phone: '',
  phone2: '',
  email: '',
  city: '',
  address: '',
  id_number: '',
  source_type: '',
  source_name: '',
  source_message: '',
  campaign_id: '',
  course_id: '',
  notes: '',
  salesperson_id: '',
  status: 'new',
}

interface LeadWorkspaceProps {
  lead?: Lead | null  // null/undefined = create mode
  salespersons: Salesperson[]
  campaigns: Campaign[]
  courses: Course[]
  onClose: () => void
  onUpdate: () => void
  onCreate?: (lead: Lead) => void  // Called after successful creation
  onAddInteraction?: () => void
  onConvert?: () => void
}

type TabId = 'interactions' | 'tasks' | 'payments' | 'inquiries'

export function LeadWorkspace({
  lead,
  salespersons,
  campaigns,
  courses,
  onClose,
  onUpdate,
  onCreate,
  onAddInteraction,
  onConvert,
}: LeadWorkspaceProps) {
  const isCreateMode = !lead
  const [activeTab, setActiveTab] = useState<TabId>('interactions')
  const [isSaving, setIsSaving] = useState(false)
  const { confirm } = useModal()
  
  // Form state for create mode
  const [form, setForm] = useState(INITIAL_FORM)

  // Check if form has been modified (dirty state)
  const isDirty = useMemo(() => {
    if (!isCreateMode) return false // Edit mode uses auto-save, no dirty tracking
    return Object.keys(INITIAL_FORM).some(
      key => form[key as keyof typeof form] !== INITIAL_FORM[key as keyof typeof INITIAL_FORM]
    )
  }, [isCreateMode, form])

  const updateForm = (field: string, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }))
  }
  
  // Inline save handler (edit mode)
  const saveField = useCallback(async (field: string, value: string | number | null) => {
    if (!lead) return
    try {
      await api.patch(`/leads/${lead.id}`, { [field]: value })
      onUpdate()
    } catch (err) {
      console.error('Failed to update field:', err)
      throw err
    }
  }, [lead?.id, onUpdate])

  // Close handler with unsaved changes confirmation
  const handleClose = useCallback(async () => {
    if (isDirty) {
      const shouldDiscard = await confirm({
        title: 'שינויים לא נשמרו',
        message: 'יש לך שינויים שלא נשמרו. האם לבטל אותם?',
        confirmLabel: 'בטל שינויים',
        cancelLabel: 'המשך לערוך',
        danger: true,
      })
      if (!shouldDiscard) return
    }
    onClose()
  }, [isDirty, confirm, onClose])

  // Create handler
  const handleCreate = async (e: FormEvent) => {
    e.preventDefault()
    if (!form.full_name.trim() || !form.phone.trim()) return

    setIsSaving(true)
    try {
      const data: Record<string, unknown> = { ...form }
      // Convert IDs to numbers
      if (data.salesperson_id) data.salesperson_id = Number(data.salesperson_id)
      else delete data.salesperson_id
      if (data.campaign_id) data.campaign_id = Number(data.campaign_id)
      else delete data.campaign_id
      if (data.course_id) data.course_id = Number(data.course_id)
      else delete data.course_id
      // Remove empty strings
      Object.keys(data).forEach(k => { if (data[k] === '') delete data[k] })
      
      const newLead = await api.post<Lead>('leads', data)
      onCreate?.(newLead)
    } catch (err) {
      console.error('Failed to create lead:', err)
    } finally {
      setIsSaving(false)
    }
  }

  // Build select options
  const salespersonOptions: SelectOption[] = salespersons.map(sp => ({
    value: sp.id,
    label: sp.name,
  }))
  
  const campaignOptions: SelectOption[] = campaigns.map(c => ({
    value: c.id,
    label: c.name,
  }))
  
  const courseOptions: SelectOption[] = courses.map(c => ({
    value: c.id,
    label: c.name,
  }))

  const isConverted = lead ? (lead.status === 'converted' || !!lead.student_id) : false

  // Find related names for display (edit mode only)
  const salesperson = lead ? salespersons.find(sp => sp.id === lead.salesperson_id) : null
  const campaign = lead ? campaigns.find(c => c.id === lead.campaign_id) : null

  // Section header helper
  const SectionHeader = ({ children }: { children: string }) => (
    <h4 style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 8, textTransform: 'uppercase' }}>
      {children}
    </h4>
  )

  // ═══════════════════════════════════════════════════════════
  // CREATE MODE — Same layout as edit mode, fields start empty
  // First: quick create (name + phone), then full workspace
  // ═══════════════════════════════════════════════════════════
  if (isCreateMode) {
    return (
      <div className={s.workspace}>
        {/* Left Sidebar — same as edit mode */}
        <form onSubmit={handleCreate} className={s.workspace__sidebar}>
          {/* Header */}
          <div className={s.workspace__header}>
            <div className={s.workspace__title}>
              <span>{form.full_name || 'ליד חדש'} {form.family_name}</span>
              <Badge entity="leads" value={form.status} />
            </div>
            <button type="button" className={`${s.btn} ${s['btn-ghost']} ${s['btn-icon']}`} onClick={handleClose} title="חזור">
              <ArrowLeft size={18} />
            </button>
          </div>

          {/* Contact Info */}
          <div>
            <SectionHeader>פרטי קשר</SectionHeader>
            <div className={s['field-grid']}>
              <EditableField label="שם פרטי *" value={form.full_name} onSave={v => { updateForm('full_name', String(v ?? '')); return Promise.resolve() }} />
              <EditableField label="שם משפחה" value={form.family_name} onSave={v => { updateForm('family_name', String(v ?? '')); return Promise.resolve() }} />
              <EditableField label="טלפון *" value={form.phone} dir="ltr" onSave={v => { updateForm('phone', String(v ?? '')); return Promise.resolve() }} />
              <EditableField label="טלפון נוסף" value={form.phone2} dir="ltr" onSave={v => { updateForm('phone2', String(v ?? '')); return Promise.resolve() }} />
              <EditableField label="אימייל" value={form.email} dir="ltr" onSave={v => { updateForm('email', String(v ?? '')); return Promise.resolve() }} />
              <EditableField label="עיר" value={form.city} onSave={v => { updateForm('city', String(v ?? '')); return Promise.resolve() }} />
            </div>
            <div className={`${s['field-grid']} ${s['field-grid--single']}`}>
              <EditableField label="כתובת" value={form.address} onSave={v => { updateForm('address', String(v ?? '')); return Promise.resolve() }} />
              <EditableField label="תעודת זהות" value={form.id_number} dir="ltr" onSave={v => { updateForm('id_number', String(v ?? '')); return Promise.resolve() }} />
            </div>
          </div>

          {/* Sales Info */}
          <div>
            <SectionHeader>שיוך מכירות</SectionHeader>
            <div className={`${s['field-grid']} ${s['field-grid--single']}`}>
              <EditableField
                label="סטטוס"
                value={form.status}
                displayValue={<Badge entity="leads" value={form.status} />}
                type="select"
                options={STATUS_OPTIONS}
                onSave={v => { updateForm('status', String(v ?? 'new')); return Promise.resolve() }}
              />
              <EditableField
                label="איש מכירות"
                value={form.salesperson_id || null}
                displayValue={salespersons.find(sp => sp.id === Number(form.salesperson_id))?.name}
                type="entity-select"
                options={salespersonOptions}
                onSave={v => { updateForm('salesperson_id', String(v ?? '')); return Promise.resolve() }}
                entityCreatePath="/leads"
              />
            </div>
          </div>

          {/* Source Info */}
          <div>
            <SectionHeader>מקור הגעה</SectionHeader>
            <div className={`${s['field-grid']} ${s['field-grid--single']}`}>
              <EditableField
                label="מקור"
                value={form.source_type || null}
                type="select"
                options={SOURCE_OPTIONS}
                onSave={v => { updateForm('source_type', String(v ?? '')); return Promise.resolve() }}
              />
              <EditableField
                label="קמפיין"
                value={form.campaign_id || null}
                displayValue={campaigns.find(c => c.id === Number(form.campaign_id))?.name}
                type="entity-select"
                options={campaignOptions}
                onSave={v => { updateForm('campaign_id', String(v ?? '')); return Promise.resolve() }}
                entityCreatePath="/campaigns"
              />
              <EditableField label="שם מקור" value={form.source_name} onSave={v => { updateForm('source_name', String(v ?? '')); return Promise.resolve() }} />
              <EditableField label="הודעה מהמקור" value={form.source_message} type="textarea" onSave={v => { updateForm('source_message', String(v ?? '')); return Promise.resolve() }} />
            </div>
          </div>

          {/* Course Interest */}
          <div>
            <SectionHeader>התעניינות</SectionHeader>
            <div className={`${s['field-grid']} ${s['field-grid--single']}`}>
              <EditableField
                label="קורס מבוקש"
                value={form.course_id || null}
                displayValue={courses.find(c => c.id === Number(form.course_id))?.name}
                type="entity-select"
                options={courseOptions}
                onSave={v => { updateForm('course_id', String(v ?? '')); return Promise.resolve() }}
                entityCreatePath="/courses"
              />
            </div>
          </div>

          {/* Notes */}
          <div>
            <SectionHeader>הערות</SectionHeader>
            <EditableField label="הערות" value={form.notes} type="textarea" onSave={v => { updateForm('notes', String(v ?? '')); return Promise.resolve() }} />
          </div>

          {/* Submit button */}
          <div style={{ display: 'flex', gap: 12, paddingTop: 16, borderTop: '1px solid var(--color-border-light)' }}>
            <button type="submit" className={`${s.btn} ${s['btn-primary']}`} disabled={isSaving || !form.full_name.trim() || !form.phone.trim()}>
              <Save size={16} /> {isSaving ? 'שומר...' : 'צור ליד'}
            </button>
            <button type="button" className={`${s.btn} ${s['btn-ghost']}`} onClick={handleClose}>
              ביטול
            </button>
          </div>
        </form>

        {/* Main Area — Empty tabs placeholder (no ID yet) */}
        <div className={s.workspace__main}>
          <div className={s.tabs}>
            <TabButton id="interactions" active icon={<History size={14} />} label="היסטוריה" onClick={() => {}} />
            <TabButton id="tasks" active={false} icon={<ListTodo size={14} />} label="משימות" onClick={() => {}} />
            <TabButton id="payments" active={false} icon={<CreditCard size={14} />} label="תשלומים" onClick={() => {}} />
            <TabButton id="inquiries" active={false} icon={<MessageCircle size={14} />} label="פניות" onClick={() => {}} />
          </div>
          <div className={s.workspace__section}>
            <div className={s['empty-state']}>
              <MessageCircle size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
              <div>שמור את הליד כדי להוסיף פעילויות</div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ═══════════════════════════════════════════════════════════
  // EDIT MODE — Inline editable fields
  // ═══════════════════════════════════════════════════════════
  return (
    <div className={s.workspace}>
      {/* Left Sidebar — Lead Details */}
      <div className={s.workspace__sidebar}>
        {/* Header */}
        <div className={s.workspace__header}>
          <div className={s.workspace__title}>
            <span>{lead!.full_name} {lead!.family_name ?? ''}</span>
            <Badge entity="leads" value={lead!.status} />
          </div>
          <button className={`${s.btn} ${s['btn-ghost']} ${s['btn-icon']}`} onClick={onClose} title="חזור">
            <ArrowLeft size={18} />
          </button>
        </div>

        {/* Converted badge */}
        {isConverted && lead!.student_id && (
          <div style={{ 
            background: 'var(--color-success-light, #f0fdf4)', 
            padding: '10px 12px', 
            borderRadius: 8,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}>
            <UserCheck size={16} style={{ color: 'var(--color-success, #16a34a)' }} />
            <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-success, #16a34a)' }}>
              הומר לתלמיד #{lead!.student_id}
            </span>
          </div>
        )}

        {/* Quick Actions */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {!isConverted && onConvert && (
            <button className={`${s.btn} ${s['btn-primary']} ${s['btn-sm']}`} onClick={onConvert}>
              <UserCheck size={14} /> המר לתלמיד
            </button>
          )}
          {onAddInteraction && (
            <button className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`} onClick={onAddInteraction}>
              <MessageSquarePlus size={14} /> הוסף פעילות
            </button>
          )}
        </div>

        {/* Contact Info */}
        <div>
          <SectionHeader>פרטי קשר</SectionHeader>
          <div className={s['field-grid']}>
            <EditableField
              label="שם פרטי"
              value={lead!.full_name}
              onSave={v => saveField('full_name', v)}
            />
            <EditableField
              label="שם משפחה"
              value={lead!.family_name}
              onSave={v => saveField('family_name', v)}
            />
            <EditableField
              label="טלפון"
              value={lead!.phone}
              dir="ltr"
              onSave={v => saveField('phone', v)}
            />
            <EditableField
              label="טלפון נוסף"
              value={lead!.phone2}
              dir="ltr"
              onSave={v => saveField('phone2', v)}
            />
            <EditableField
              label="אימייל"
              value={lead!.email}
              dir="ltr"
              onSave={v => saveField('email', v)}
            />
            <EditableField
              label="עיר"
              value={lead!.city}
              onSave={v => saveField('city', v)}
            />
          </div>
          <div className={`${s['field-grid']} ${s['field-grid--single']}`}>
            <EditableField
              label="כתובת"
              value={lead!.address}
              onSave={v => saveField('address', v)}
            />
            <EditableField
              label="תעודת זהות"
              value={lead!.id_number}
              dir="ltr"
              onSave={v => saveField('id_number', v)}
            />
          </div>
        </div>

        {/* Sales Info */}
        <div>
          <SectionHeader>שיוך מכירות</SectionHeader>
          <div className={`${s['field-grid']} ${s['field-grid--single']}`}>
            <EditableField
              label="סטטוס"
              value={lead!.status}
              displayValue={<Badge entity="leads" value={lead!.status} />}
              type="select"
              options={STATUS_OPTIONS}
              onSave={v => saveField('status', v)}
              disabled={!!isConverted}
            />
            <EditableField
              label="איש מכירות"
              value={lead!.salesperson_id}
              displayValue={salesperson?.name}
              type="entity-select"
              options={salespersonOptions}
              onSave={v => saveField('salesperson_id', v)}
              entityCreatePath="/leads"
            />
          </div>
        </div>

        {/* Source Info */}
        <div>
          <SectionHeader>מקור הגעה</SectionHeader>
          <div className={`${s['field-grid']} ${s['field-grid--single']}`}>
            <EditableField
              label="מקור"
              value={lead!.source_type}
              type="select"
              options={SOURCE_OPTIONS}
              onSave={v => saveField('source_type', v)}
            />
            <EditableField
              label="קמפיין"
              value={lead!.campaign_id}
              displayValue={campaign?.name}
              type="entity-select"
              options={campaignOptions}
              onSave={v => saveField('campaign_id', v)}
              entityCreatePath="/campaigns"
            />
            <EditableField
              label="שם מקור"
              value={lead!.source_name}
              onSave={v => saveField('source_name', v)}
            />
            <EditableField
              label="הודעה מהמקור"
              value={lead!.source_message}
              type="textarea"
              onSave={v => saveField('source_message', v)}
            />
          </div>
        </div>

        {/* Course Interest */}
        <div>
          <SectionHeader>התעניינות</SectionHeader>
          <div className={`${s['field-grid']} ${s['field-grid--single']}`}>
            <EditableField
              label="קורס מבוקש"
              value={lead!.course_id}
              displayValue={courses.find(c => c.id === lead!.course_id)?.name}
              type="entity-select"
              options={courseOptions}
              onSave={v => saveField('course_id', v)}
              entityCreatePath="/courses"
            />
          </div>
        </div>

        {/* Notes */}
        <div>
          <SectionHeader>הערות</SectionHeader>
          <EditableField
            label="הערות"
            value={lead!.notes}
            type="textarea"
            onSave={v => saveField('notes', v)}
          />
        </div>

        {/* Meta info */}
        <div style={{ 
          marginTop: 'auto', 
          paddingTop: 16, 
          borderTop: '1px solid var(--color-border-light)',
          fontSize: 11,
          color: 'var(--color-text-muted)',
        }}>
          <div>נוצר: {formatDateTime(lead!.created_at)}</div>
          {lead!.updated_at && <div>עודכן: {formatDateTime(lead!.updated_at)}</div>}
          {lead!.conversion_date && <div>הומר: {formatDateTime(lead!.conversion_date)}</div>}
        </div>
      </div>

      {/* Main Area — Linked Entities */}
      <div className={s.workspace__main}>
        {/* Tabs */}
        <div className={s.tabs}>
          <TabButton 
            id="interactions" 
            active={activeTab === 'interactions'}
            onClick={() => setActiveTab('interactions')}
            icon={<History size={14} />}
            label="היסטוריה"
            count={lead!.interactions?.length}
          />
          <TabButton 
            id="tasks" 
            active={activeTab === 'tasks'}
            onClick={() => setActiveTab('tasks')}
            icon={<ListTodo size={14} />}
            label="משימות"
          />
          <TabButton 
            id="payments" 
            active={activeTab === 'payments'}
            onClick={() => setActiveTab('payments')}
            icon={<CreditCard size={14} />}
            label="תשלומים"
          />
          <TabButton 
            id="inquiries" 
            active={activeTab === 'inquiries'}
            onClick={() => setActiveTab('inquiries')}
            icon={<MessageCircle size={14} />}
            label="פניות"
          />
        </div>

        {/* Tab Content */}
        <div className={s.workspace__section}>
          {activeTab === 'interactions' && (
            <InteractionsTab 
              interactions={lead!.interactions || []} 
              onAdd={onAddInteraction}
            />
          )}
          {activeTab === 'tasks' && (
            <TasksTab leadId={lead!.id} />
          )}
          {activeTab === 'payments' && (
            <PaymentsTab lead={lead!} courses={courses} onUpdate={onUpdate} />
          )}
          {activeTab === 'inquiries' && (
            <InquiriesTab leadId={lead!.id} />
          )}
        </div>
      </div>
    </div>
  )
}

// Tab button component
function TabButton({ 
  active, 
  onClick, 
  icon, 
  label, 
  count 
}: { 
  id?: string
  active: boolean
  onClick: () => void
  icon: ReactNode
  label: string
  count?: number
}) {
  return (
    <button
      className={`${s.tab} ${active ? s['tab--active'] : ''}`}
      onClick={onClick}
    >
      {icon}
      <span>{label}</span>
      {count !== undefined && count > 0 && (
        <span style={{ 
          background: active ? 'var(--color-primary)' : 'var(--color-border)',
          color: active ? '#fff' : 'var(--color-text-secondary)',
          padding: '1px 6px',
          borderRadius: 10,
          fontSize: 10,
          fontWeight: 600,
        }}>
          {count}
        </span>
      )}
    </button>
  )
}

// Interactions Tab
function InteractionsTab({ 
  interactions, 
  onAdd 
}: { 
  interactions: LeadInteraction[]
  onAdd?: () => void
}) {
  if (interactions.length === 0) {
    return (
      <div className={s['empty-state']}>
        <MessageCircle size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
        <div>אין פעילות עדיין</div>
        {onAdd && (
          <button className={`${s.btn} ${s['btn-primary']} ${s['btn-sm']}`} onClick={onAdd} style={{ marginTop: 12 }}>
            <MessageSquarePlus size={14} /> הוסף פעילות ראשונה
          </button>
        )}
      </div>
    )
  }

  return (
    <div className={s.workspace__section_content}>
      {onAdd && (
        <div style={{ padding: '8px 16px', borderBottom: '1px solid var(--color-border-light)', display: 'flex', justifyContent: 'flex-end' }}>
          <button className={`${s.btn} ${s['btn-primary']} ${s['btn-sm']}`} onClick={onAdd}>
            <MessageSquarePlus size={14} /> הוסף פעילות
          </button>
        </div>
      )}
      <div className={s.timeline} style={{ padding: 16 }}>
        {interactions.map(interaction => (
          <div key={interaction.id} className={s['timeline-item']}>
            <div className={s['timeline-dot']} style={{ 
              background: interaction.interaction_type === 'call' ? 'var(--color-primary)' : 'var(--color-border)' 
            }} />
            <div className={s['timeline-content']}>
              <div className={s['timeline-date']}>
                {formatDateTime(interaction.created_at)}
                {interaction.user_name && <span> • {interaction.user_name}</span>}
              </div>
              <div className={s['timeline-text']}>
                <Badge entity="interaction_type" value={interaction.interaction_type} />
                {interaction.call_status && (
                  <span style={{ marginRight: 8 }}>
                    <Badge entity="call_status" value={interaction.call_status} />
                  </span>
                )}
              </div>
              {interaction.description && (
                <div style={{ marginTop: 4, fontSize: 13, color: 'var(--color-text)' }}>
                  {interaction.description}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// Tasks Tab (placeholder - to be expanded)
function TasksTab({ leadId: _leadId }: { leadId: number }) {
  return (
    <div className={s['empty-state']}>
      <ListTodo size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
      <div>אין משימות מקושרות</div>
      <div style={{ fontSize: 12, marginTop: 4 }}>משימות מכירות קשורות לליד יופיעו כאן</div>
    </div>
  )
}

// Payments Tab - uses LeadPaymentTab component
function PaymentsTab({ lead, courses, onUpdate }: { lead: Lead; courses: Course[]; onUpdate: () => void }) {
  return <LeadPaymentTab lead={lead} courses={courses} onUpdate={onUpdate} />
}

// Inquiries Tab (placeholder - to be expanded)
function InquiriesTab({ leadId: _leadId }: { leadId: number }) {
  return (
    <div className={s['empty-state']}>
      <MessageCircle size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
      <div>אין פניות נכנסות</div>
      <div style={{ fontSize: 12, marginTop: 4 }}>פניות נכנסות מהליד יופיעו כאן</div>
    </div>
  )
}

export default LeadWorkspace
