import { useState, useCallback, useEffect, useMemo, type ReactNode, type FormEvent } from 'react'
import {
  MessageSquarePlus,
  UserCheck,
  ArrowLeft,
  CreditCard,
  ListTodo,
  MessageCircle,
  History,
  Save,
  ChevronDown,
  Mail,
  Send,
  CheckCircle2,
  XCircle,
  Upload,
  FileText,
  X,
  Paperclip,
} from 'lucide-react'
import { api } from '@/lib/api'
import { getStatus, formatDateTime } from '@/lib/status'
import { EditableField, type SelectOption } from '@/components/ui/EditableField'
import { useModal } from '@/components/ui/Modal'
import type { Lead, LeadInteraction, Salesperson, Course, Campaign } from '@/types'
import { LeadPaymentTab } from './LeadPaymentTab'
// @ts-ignore - used in conversion tab
import LeadConversionChecklist from './LeadConversionChecklist'
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

// Status options — values must match DB (Hebrew)
const STATUS_OPTIONS: SelectOption[] = [
  { value: 'ליד חדש', label: 'ליד חדש' },
  { value: 'ליד בתהליך', label: 'ליד בתהליך' },
  { value: 'חיוג ראשון', label: 'חיוג ראשון' },
  { value: 'נסלק', label: 'נסלק' },
  { value: 'תלמיד פעיל', label: 'תלמיד פעיל' },
  { value: 'לא רלוונטי', label: 'לא רלוונטי' },
]

const SOURCE_OPTIONS: SelectOption[] = [
  { value: 'yemot', label: 'ימות המשיח' },
  { value: 'elementor', label: 'אלמנטור' },
  { value: 'manual', label: 'ידני' },
  { value: 'referral', label: 'הפניה' },
  { value: 'ייבוא ממערכת ישנה', label: 'ייבוא ממערכת ישנה' },
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
  requested_course: '',
  notes: '',
  salesperson_id: '',
  status: 'ליד חדש',
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

type TabId = 'interactions' | 'tasks' | 'payments' | 'conversion' | 'inquiries' | 'emails'

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
      
      const result = await api.post<{ lead_id: number; action: string }>('leads', data)
      // API returns {lead_id: N}, fetch the full lead object
      const fullLead = await api.get<Lead>(`leads/${result.lead_id}`)
      if (result.action === 'updated') {
        alert('ליד עם טלפון זה כבר קיים במערכת — פותח את הליד הקיים')
      }
      onCreate?.(fullLead)
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
  
  const isConverted = lead ? (lead.status === 'converted' || !!lead.student_id) : false

  // Find related names for display (edit mode only)
  const salesperson = lead ? salespersons.find(sp => sp.id === lead.salesperson_id) : null
  const campaign = lead ? campaigns.find(c => c.id === lead.campaign_id) : null

  // Collapsible section with toggle
  const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({})
  const toggleSection = (key: string) => {
    setCollapsedSections(prev => ({ ...prev, [key]: !prev[key] }))
  }
  const CollapsibleSection = ({ id, title, children: content, divider = false }: { id: string; title: string; children: ReactNode; divider?: boolean }) => {
    const isCollapsed = !!collapsedSections[id]
    return (
      <div className={divider ? s['section-divider'] : undefined}>
        <h4 className={s['section-header']} onClick={() => toggleSection(id)}>
          <ChevronDown
            size={14}
            className={`${s['section-header__chevron']} ${isCollapsed ? s['section-header__chevron--collapsed'] : ''}`}
          />
          {title}
        </h4>
        <div className={`${s['section-content']} ${isCollapsed ? s['section-content--collapsed'] : ''}`}>
          {content}
        </div>
      </div>
    )
  }

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
          <CollapsibleSection id="create-contact" title="פרטי קשר">
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
          </CollapsibleSection>

          {/* Sales Info */}
          <CollapsibleSection id="create-sales" title="שיוך מכירות" divider>
            <div className={`${s['field-grid']} ${s['field-grid--single']}`}>
              <EditableField
                label="סטטוס"
                value={form.status}
                displayValue={<Badge entity="leads" value={form.status} />}
                type="select"
                options={STATUS_OPTIONS}
                onSave={v => { updateForm('status', String(v ?? 'ליד חדש')); return Promise.resolve() }}
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
          </CollapsibleSection>

          {/* Source Info */}
          <CollapsibleSection id="create-source" title="מקור הגעה" divider>
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
          </CollapsibleSection>

          {/* Course Interest */}
          <CollapsibleSection id="create-course" title="התעניינות" divider>
            <div className={`${s['field-grid']} ${s['field-grid--single']}`}>
              <EditableField
                label="קורס מבוקש"
                value={form.requested_course}
                onSave={v => { updateForm('requested_course', String(v ?? '')); return Promise.resolve() }}
              />
            </div>
          </CollapsibleSection>

          {/* Notes */}
          <CollapsibleSection id="create-notes" title="הערות" divider>
            <EditableField label="הערות" value={form.notes} type="textarea" onSave={v => { updateForm('notes', String(v ?? '')); return Promise.resolve() }} />
          </CollapsibleSection>

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
        <CollapsibleSection id="edit-contact" title="פרטי קשר">
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
        </CollapsibleSection>

        {/* Sales Info */}
        <CollapsibleSection id="edit-sales" title="שיוך מכירות" divider>
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
        </CollapsibleSection>

        {/* Source Info */}
        <CollapsibleSection id="edit-source" title="מקור הגעה" divider>
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
        </CollapsibleSection>

        {/* Course Interest */}
        <CollapsibleSection id="edit-course" title="התעניינות" divider>
          <div className={`${s['field-grid']} ${s['field-grid--single']}`}>
            <EditableField
              label="קורס מבוקש"
              value={lead!.requested_course}
              onSave={v => saveField('requested_course', v)}
            />
          </div>
        </CollapsibleSection>

        {/* Notes */}
        <CollapsibleSection id="edit-notes" title="הערות" divider>
          <EditableField
            label="הערות"
            value={lead!.notes}
            type="textarea"
            onSave={v => saveField('notes', v)}
          />
        </CollapsibleSection>

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
            id="conversion" 
            active={activeTab === 'conversion'}
            onClick={() => setActiveTab('conversion')}
            icon={<CheckCircle2 size={14} />}
            label="המרה לתלמיד"
          />
          <TabButton 
            id="inquiries" 
            active={activeTab === 'inquiries'}
            onClick={() => setActiveTab('inquiries')}
            icon={<MessageCircle size={14} />}
            label="פניות"
          />
          <TabButton 
            id="emails" 
            active={activeTab === 'emails'}
            onClick={() => setActiveTab('emails')}
            icon={<Mail size={14} />}
            label="מיילים"
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
          {activeTab === 'conversion' && (
            <LeadConversionChecklist lead={lead!} onUpdate={onUpdate} />
          )}
          {activeTab === 'inquiries' && (
            <InquiriesTab leadId={lead!.id} />
          )}
          {activeTab === 'emails' && (
            <EmailsTab lead={lead!} onUpdate={onUpdate} />
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
              {interaction.form_product && (
                <div style={{ marginTop: 4, fontSize: 13, color: 'var(--color-primary)' }}>
                  מסלול: {interaction.form_product}
                </div>
              )}
              {interaction.form_content && (
                <div style={{ marginTop: 4, fontSize: 13, color: 'var(--color-text)', whiteSpace: 'pre-wrap' }}>
                  {interaction.form_content}
                </div>
              )}
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

// Emails Tab — Send emails to lead + view history
interface SentEmail {
  id: number
  subject: string
  body: string
  status: string
  send_method: string
  created_at: string
  sent_at: string | null
  attachments?: Array<{
    id: number
    filename: string
    size_bytes: number
    content_type: string
  }>
}

interface EmailTemplate {
  id: number
  name: string
  subject: string
  body_html: string
  category: string | null
  track_type: string | null
  attachments: Array<{
    id: number
    filename: string
    size_bytes: number
  }>
}

function EmailsTab({ lead, onUpdate }: { lead: Lead; onUpdate: () => void }) {
  const [emails, setEmails] = useState<SentEmail[]>([])
  const [loading, setLoading] = useState(true)
  const [showCompose, setShowCompose] = useState(false)
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [sending, setSending] = useState(false)
  const [sendResult, setSendResult] = useState<{ ok: boolean; msg: string } | null>(null)
  const [templates, setTemplates] = useState<EmailTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<number | null>(null)
  const [uploadedFiles, setUploadedFiles] = useState<Array<{ id: number; filename: string; size_bytes: number }>>([])
  const [uploading, setUploading] = useState(false)

  const fetchEmails = useCallback(async () => {
    try {
      const data = await api.get<SentEmail[]>(`/messages/lead/${lead.id}`)
      setEmails(data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }, [lead.id])

  const fetchTemplates = useCallback(async () => {
    try {
      const data = await api.get<EmailTemplate[]>('/templates/?is_active=true')
      setTemplates(data)
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => { 
    fetchEmails()
    fetchTemplates()
  }, [fetchEmails, fetchTemplates])

  const handleTemplateSelect = (templateId: number) => {
    const template = templates.find(t => t.id === templateId)
    if (template) {
      setSubject(template.subject)
      setBody(template.body_html)
      setSelectedTemplate(templateId)
      setUploadedFiles(template.attachments.map(a => ({ id: a.id, filename: a.filename, size_bytes: a.size_bytes })))
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setUploading(true)
    try {
      for (const file of Array.from(files)) {
        const formData = new FormData()
        formData.append('file', file)
        const result = await api.upload<{ id: number; filename: string; size_bytes: number }>(
          '/files/upload?entity_type=temp&entity_id=0',
          formData
        )
        setUploadedFiles(prev => [...prev, result])
      }
    } catch (err: any) {
      alert(err?.message || 'העלאת קובץ נכשלה')
    } finally {
      setUploading(false)
    }
  }

  const handleRemoveFile = (fileId: number) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId))
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const handleSend = async () => {
    if (!subject.trim() || !body.trim()) return
    setSending(true)
    setSendResult(null)
    try {
      await api.post('/messages/send-email', {
        lead_id: lead.id,
        subject: subject.trim(),
        body: body.trim(),
        template_id: selectedTemplate,
        file_ids: uploadedFiles.map(f => f.id),
      })
      setSendResult({ ok: true, msg: `המייל נשלח בהצלחה ל-${lead.email}${uploadedFiles.length > 0 ? ` עם ${uploadedFiles.length} קבצים` : ''}` })
      setSubject('')
      setBody('')
      setSelectedTemplate(null)
      setUploadedFiles([])
      setShowCompose(false)
      fetchEmails()
      onUpdate()
    } catch (err: any) {
      setSendResult({ ok: false, msg: err?.message || 'שליחת המייל נכשלה' })
    } finally {
      setSending(false)
    }
  }

  return (
    <div className={s.workspace__section_content}>
      {/* Compose / Action bar */}
      <div style={{ padding: '8px 16px', borderBottom: '1px solid var(--color-border-light)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {!lead.email ? (
          <span style={{ color: 'var(--color-warning, #d97706)', fontSize: 13 }}>⚠ לליד אין כתובת מייל — הוסף מייל בפרטי הקשר</span>
        ) : (
          <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{lead.email}</span>
        )}
        <button
          className={`${s.btn} ${s['btn-primary']} ${s['btn-sm']}`}
          onClick={() => setShowCompose(!showCompose)}
          disabled={!lead.email}
        >
          <Mail size={14} /> {showCompose ? 'סגור' : 'כתוב מייל'}
        </button>
      </div>

      {/* Send result toast */}
      {sendResult && (
        <div style={{
          padding: '10px 16px',
          background: sendResult.ok ? 'var(--color-success-light, #f0fdf4)' : 'var(--color-danger-light, #fef2f2)',
          color: sendResult.ok ? 'var(--color-success, #16a34a)' : 'var(--color-danger, #dc2626)',
          display: 'flex', alignItems: 'center', gap: 8, fontSize: 13,
          borderBottom: '1px solid var(--color-border-light)',
        }}>
          {sendResult.ok ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
          {sendResult.msg}
        </div>
      )}

      {/* Compose form */}
      {showCompose && (
        <div style={{ padding: 16, borderBottom: '2px solid var(--color-primary)', background: 'var(--color-bg-secondary, #f8fafc)' }}>
          {templates.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 4, color: 'var(--color-text-secondary)' }}>בחר תבנית</label>
              <select
                value={selectedTemplate || ''}
                onChange={e => handleTemplateSelect(Number(e.target.value))}
                style={{
                  width: '100%', padding: '8px 12px', borderRadius: 6,
                  border: '1px solid var(--color-border)', fontSize: 14,
                }}
              >
                <option value="">כתוב מייל חופשי</option>
                {templates.map(t => (
                  <option key={t.id} value={t.id}>
                    {t.name} {t.category && `(${t.category})`}
                  </option>
                ))}
              </select>
            </div>
          )}
          <div style={{ marginBottom: 10 }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 4, color: 'var(--color-text-secondary)' }}>נושא</label>
            <input
              type="text"
              value={subject}
              onChange={e => setSubject(e.target.value)}
              placeholder="נושא המייל..."
              style={{
                width: '100%', padding: '8px 12px', borderRadius: 6,
                border: '1px solid var(--color-border)', fontSize: 14,
                direction: 'rtl',
              }}
            />
          </div>
          <div style={{ marginBottom: 10 }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 4, color: 'var(--color-text-secondary)' }}>תוכן</label>
            <textarea
              value={body}
              onChange={e => setBody(e.target.value)}
              placeholder="תוכן המייל..."
              rows={6}
              style={{
                width: '100%', padding: '8px 12px', borderRadius: 6,
                border: '1px solid var(--color-border)', fontSize: 14,
                resize: 'vertical', direction: 'rtl', fontFamily: 'inherit',
              }}
            />
          </div>
          <div style={{ marginBottom: 10 }}>
            <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 8, color: 'var(--color-text-secondary)' }}>קבצים מצורפים</label>
            <label className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`} style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <Upload size={14} />
              {uploading ? 'מעלה...' : 'העלה קובץ'}
              <input
                type="file"
                multiple
                onChange={handleFileUpload}
                disabled={uploading}
                style={{ display: 'none' }}
              />
            </label>
            {uploadedFiles.length > 0 && (
              <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
                {uploadedFiles.map(file => (
                  <div
                    key={file.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '4px 8px',
                      background: 'white',
                      border: '1px solid var(--color-border)',
                      borderRadius: 4,
                      fontSize: 12,
                    }}
                  >
                    <FileText size={12} />
                    <span style={{ flex: 1 }}>{file.filename}</span>
                    <span style={{ color: 'var(--color-text-muted)' }}>{formatFileSize(file.size_bytes)}</span>
                    <button
                      onClick={() => handleRemoveFile(file.id)}
                      style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        padding: 2,
                        color: 'var(--color-danger)',
                      }}
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <button className={`${s.btn} ${s['btn-ghost']} ${s['btn-sm']}`} onClick={() => setShowCompose(false)}>ביטול</button>
            <button
              className={`${s.btn} ${s['btn-primary']} ${s['btn-sm']}`}
              onClick={handleSend}
              disabled={sending || !subject.trim() || !body.trim()}
            >
              <Send size={14} /> {sending ? 'שולח...' : 'שלח מייל'}
            </button>
          </div>
        </div>
      )}

      {/* Email history */}
      {loading ? (
        <div style={{ padding: 24, textAlign: 'center', color: 'var(--color-text-muted)' }}>טוען...</div>
      ) : emails.length === 0 ? (
        <div className={s['empty-state']}>
          <Mail size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
          <div>לא נשלחו מיילים לליד זה</div>
          {lead.email && (
            <button className={`${s.btn} ${s['btn-primary']} ${s['btn-sm']}`} onClick={() => setShowCompose(true)} style={{ marginTop: 12 }}>
              <Mail size={14} /> שלח מייל ראשון
            </button>
          )}
        </div>
      ) : (
        <div className={s.timeline} style={{ padding: 16 }}>
          {emails.map(email => (
            <div key={email.id} className={s['timeline-item']}>
              <div className={s['timeline-dot']} style={{
                background: email.status === 'נשלח' ? 'var(--color-success, #16a34a)' : email.status === 'נכשל' ? 'var(--color-danger, #dc2626)' : 'var(--color-border)',
              }} />
              <div className={s['timeline-content']}>
                <div className={s['timeline-date']}>
                  {formatDateTime(email.sent_at || email.created_at)}
                  <span style={{
                    marginRight: 8, fontSize: 11, padding: '1px 6px', borderRadius: 4,
                    background: email.status === 'נשלח' ? 'var(--color-success-light, #f0fdf4)' : 'var(--color-danger-light, #fef2f2)',
                    color: email.status === 'נשלח' ? 'var(--color-success, #16a34a)' : 'var(--color-danger, #dc2626)',
                  }}>{email.status}</span>
                </div>
                <div style={{ fontWeight: 600, fontSize: 14, marginTop: 4 }}>{email.subject}</div>
                <div style={{ marginTop: 4, fontSize: 13, color: 'var(--color-text-secondary)', whiteSpace: 'pre-wrap', maxHeight: 100, overflow: 'hidden' }}>
                  {email.body.replace(/<[^>]*>/g, '').substring(0, 200)}
                  {email.body.length > 200 && '...'}
                </div>
                {email.attachments && email.attachments.length > 0 && (
                  <div style={{ marginTop: 8, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                    {email.attachments.map(att => (
                      <div
                        key={att.id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 4,
                          padding: '2px 6px',
                          background: 'var(--color-bg-secondary)',
                          borderRadius: 4,
                          fontSize: 11,
                        }}
                      >
                        <Paperclip size={10} />
                        <span>{att.filename}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default LeadWorkspace
