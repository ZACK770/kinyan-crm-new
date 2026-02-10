import { useState, useCallback, type ReactNode } from 'react'
import {
  X,
  Phone,
  Mail,
  MapPin,
  Calendar,
  User,
  MessageSquarePlus,
  UserCheck,
  ArrowLeft,
  CreditCard,
  ListTodo,
  MessageCircle,
  FileText,
  History,
} from 'lucide-react'
import { api } from '@/lib/api'
import { getStatus, formatDate, formatDateTime } from '@/lib/status'
import { EditableField, type SelectOption } from '@/components/ui/EditableField'
import type { Lead, LeadInteraction, Salesperson, Course, Campaign } from '@/types'
import s from '@/styles/shared.module.css'

/* ══════════════════════════════════════════════════════════════
   Lead Workspace — Full workspace view for lead management
   Features:
   - Inline editable fields (click to edit)
   - Linked entities tabs (interactions, tasks, payments)
   - Conversion flow
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

interface LeadWorkspaceProps {
  lead: Lead
  salespersons: Salesperson[]
  campaigns: Campaign[]
  courses: Course[]
  onClose: () => void
  onUpdate: () => void
  onAddInteraction: () => void
  onConvert: () => void
}

type TabId = 'interactions' | 'tasks' | 'payments' | 'inquiries'

export function LeadWorkspace({
  lead,
  salespersons,
  campaigns,
  courses,
  onClose,
  onUpdate,
  onAddInteraction,
  onConvert,
}: LeadWorkspaceProps) {
  const [activeTab, setActiveTab] = useState<TabId>('interactions')
  
  // Inline save handler
  const saveField = useCallback(async (field: string, value: string | number | null) => {
    try {
      await api(`/leads/${lead.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ [field]: value }),
      })
      onUpdate()
    } catch (err) {
      console.error('Failed to update field:', err)
      throw err
    }
  }, [lead.id, onUpdate])

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

  const isConverted = lead.status === 'converted' || lead.student_id

  // Find related names for display
  const salesperson = salespersons.find(sp => sp.id === lead.salesperson_id)
  const campaign = campaigns.find(c => c.id === lead.campaign_id)

  return (
    <div className={s.workspace}>
      {/* Left Sidebar — Lead Details */}
      <div className={s.workspace__sidebar}>
        {/* Header */}
        <div className={s.workspace__header}>
          <div className={s.workspace__title}>
            <span>{lead.full_name} {lead.family_name ?? ''}</span>
            <Badge entity="leads" value={lead.status} />
          </div>
          <button className={`${s.btn} ${s['btn-ghost']} ${s['btn-icon']}`} onClick={onClose} title="חזור">
            <ArrowLeft size={18} />
          </button>
        </div>

        {/* Converted badge */}
        {isConverted && lead.student_id && (
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
              הומר לתלמיד #{lead.student_id}
            </span>
          </div>
        )}

        {/* Quick Actions */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {!isConverted && (
            <button className={`${s.btn} ${s['btn-primary']} ${s['btn-sm']}`} onClick={onConvert}>
              <UserCheck size={14} /> המר לתלמיד
            </button>
          )}
          <button className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`} onClick={onAddInteraction}>
            <MessageSquarePlus size={14} /> הוסף פעילות
          </button>
        </div>

        {/* Contact Info */}
        <div>
          <h4 style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 8, textTransform: 'uppercase' }}>
            פרטי קשר
          </h4>
          <div className={s['field-grid']}>
            <EditableField
              label="שם פרטי"
              value={lead.full_name}
              onSave={v => saveField('full_name', v)}
            />
            <EditableField
              label="שם משפחה"
              value={lead.family_name}
              onSave={v => saveField('family_name', v)}
            />
            <EditableField
              label="טלפון"
              value={lead.phone}
              dir="ltr"
              onSave={v => saveField('phone', v)}
            />
            <EditableField
              label="טלפון נוסף"
              value={lead.phone2}
              dir="ltr"
              onSave={v => saveField('phone2', v)}
            />
            <EditableField
              label="אימייל"
              value={lead.email}
              dir="ltr"
              onSave={v => saveField('email', v)}
            />
            <EditableField
              label="עיר"
              value={lead.city}
              onSave={v => saveField('city', v)}
            />
          </div>
          <div className={`${s['field-grid']} ${s['field-grid--single']}`}>
            <EditableField
              label="כתובת"
              value={lead.address}
              onSave={v => saveField('address', v)}
            />
            <EditableField
              label="תעודת זהות"
              value={lead.id_number}
              dir="ltr"
              onSave={v => saveField('id_number', v)}
            />
          </div>
        </div>

        {/* Sales Info */}
        <div>
          <h4 style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 8, textTransform: 'uppercase' }}>
            שיוך מכירות
          </h4>
          <div className={`${s['field-grid']} ${s['field-grid--single']}`}>
            <EditableField
              label="סטטוס"
              value={lead.status}
              displayValue={<Badge entity="leads" value={lead.status} />}
              type="select"
              options={STATUS_OPTIONS}
              onSave={v => saveField('status', v)}
              disabled={isConverted}
            />
            <EditableField
              label="איש מכירות"
              value={lead.salesperson_id}
              displayValue={salesperson?.name}
              type="entity-select"
              options={salespersonOptions}
              onSave={v => saveField('salesperson_id', v)}
            />
          </div>
        </div>

        {/* Source Info */}
        <div>
          <h4 style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 8, textTransform: 'uppercase' }}>
            מקור הגעה
          </h4>
          <div className={`${s['field-grid']} ${s['field-grid--single']}`}>
            <EditableField
              label="מקור"
              value={lead.source_type}
              type="select"
              options={SOURCE_OPTIONS}
              onSave={v => saveField('source_type', v)}
            />
            <EditableField
              label="קמפיין"
              value={lead.campaign_id}
              displayValue={campaign?.name}
              type="entity-select"
              options={campaignOptions}
              onSave={v => saveField('campaign_id', v)}
            />
            <EditableField
              label="שם מקור"
              value={lead.source_name}
              onSave={v => saveField('source_name', v)}
            />
            <EditableField
              label="הודעה מהמקור"
              value={lead.source_message}
              type="textarea"
              onSave={v => saveField('source_message', v)}
            />
          </div>
        </div>

        {/* Course Interest */}
        <div>
          <h4 style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 8, textTransform: 'uppercase' }}>
            התעניינות
          </h4>
          <div className={`${s['field-grid']} ${s['field-grid--single']}`}>
            <EditableField
              label="קורס מבוקש"
              value={(lead as Record<string, unknown>).course_id as number | undefined}
              displayValue={courses.find(c => c.id === (lead as Record<string, unknown>).course_id)?.name}
              type="entity-select"
              options={courseOptions}
              onSave={v => saveField('course_id', v)}
            />
          </div>
        </div>

        {/* Notes */}
        <div>
          <h4 style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: 8, textTransform: 'uppercase' }}>
            הערות
          </h4>
          <EditableField
            label="הערות"
            value={lead.notes}
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
          <div>נוצר: {formatDateTime(lead.created_at)}</div>
          {lead.updated_at && <div>עודכן: {formatDateTime(lead.updated_at)}</div>}
          {lead.conversion_date && <div>הומר: {formatDateTime(lead.conversion_date)}</div>}
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
            count={lead.interactions?.length}
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
              interactions={lead.interactions || []} 
              onAdd={onAddInteraction}
            />
          )}
          {activeTab === 'tasks' && (
            <TasksTab leadId={lead.id} />
          )}
          {activeTab === 'payments' && (
            <PaymentsTab leadId={lead.id} />
          )}
          {activeTab === 'inquiries' && (
            <InquiriesTab leadId={lead.id} />
          )}
        </div>
      </div>
    </div>
  )
}

// Tab button component
function TabButton({ 
  id, 
  active, 
  onClick, 
  icon, 
  label, 
  count 
}: { 
  id: string
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
  onAdd: () => void
}) {
  if (interactions.length === 0) {
    return (
      <div className={s['empty-state']}>
        <MessageCircle size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
        <div>אין פעילות עדיין</div>
        <button className={`${s.btn} ${s['btn-primary']} ${s['btn-sm']}`} onClick={onAdd} style={{ marginTop: 12 }}>
          <MessageSquarePlus size={14} /> הוסף פעילות ראשונה
        </button>
      </div>
    )
  }

  return (
    <div className={s.workspace__section_content}>
      <div style={{ padding: '8px 16px', borderBottom: '1px solid var(--color-border-light)', display: 'flex', justifyContent: 'flex-end' }}>
        <button className={`${s.btn} ${s['btn-primary']} ${s['btn-sm']}`} onClick={onAdd}>
          <MessageSquarePlus size={14} /> הוסף פעילות
        </button>
      </div>
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
function TasksTab({ leadId }: { leadId: number }) {
  return (
    <div className={s['empty-state']}>
      <ListTodo size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
      <div>אין משימות מקושרות</div>
      <div style={{ fontSize: 12, marginTop: 4 }}>משימות מכירות קשורות לליד יופיעו כאן</div>
    </div>
  )
}

// Payments Tab (placeholder - to be expanded)
function PaymentsTab({ leadId }: { leadId: number }) {
  return (
    <div className={s['empty-state']}>
      <CreditCard size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
      <div>אין תשלומים</div>
      <div style={{ fontSize: 12, marginTop: 4 }}>תשלומים קשורים לליד יופיעו כאן</div>
    </div>
  )
}

// Inquiries Tab (placeholder - to be expanded)
function InquiriesTab({ leadId }: { leadId: number }) {
  return (
    <div className={s['empty-state']}>
      <MessageCircle size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
      <div>אין פניות נכנסות</div>
      <div style={{ fontSize: 12, marginTop: 4 }}>פניות נכנסות מהליד יופיעו כאן</div>
    </div>
  )
}

export default LeadWorkspace
