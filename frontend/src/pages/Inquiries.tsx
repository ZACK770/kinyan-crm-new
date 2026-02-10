import { useEffect, useState, useCallback, type FormEvent } from 'react'
import { Plus, Inbox, Eye, MessageSquarePlus } from 'lucide-react'
import { api } from '@/lib/api'
import { getStatus, formatDateTime } from '@/lib/status'
import { useModal } from '@/components/ui/Modal'
import { useToast } from '@/components/ui/Toast'
import { DataTable, type Column } from '@/components/ui/DataTable'
import type { Inquiry, InquiryResponse } from '@/types'
import s from '@/styles/shared.module.css'

function Badge({ entity, value }: { entity: string; value?: string }) {
  const { label, color } = getStatus(entity, value)
  return <span className={`${s.badge} ${s[`badge-${color}`]}`}>{label}</span>
}

/* ── Create Inquiry Form ── */
function InquiryForm({ onSubmit }: { onSubmit: (data: Record<string, unknown>) => void }) {
  const [form, setForm] = useState({
    subject: '',
    inquiry_type: 'general',
    phone: '',
    notes: '',
  })
  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [key]: e.target.value }))

  const handle = (e: FormEvent) => {
    e.preventDefault()
    const data: Record<string, unknown> = { subject: form.subject, inquiry_type: form.inquiry_type }
    if (form.phone) data.phone = form.phone
    if (form.notes) data.notes = form.notes
    onSubmit(data)
  }

  return (
    <form onSubmit={handle} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className={s['form-group']}>
        <label className={s['form-label']}>נושא *</label>
        <input className={s.input} value={form.subject} onChange={set('subject')} required />
      </div>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>סוג</label>
          <select className={s.select} value={form.inquiry_type} onChange={set('inquiry_type')}>
            <option value="general">כללי</option>
            <option value="complaint">תלונה</option>
            <option value="question">שאלה</option>
            <option value="request">בקשה</option>
            <option value="feedback">משוב</option>
          </select>
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>טלפון</label>
          <input className={s.input} value={form.phone} onChange={set('phone')} dir="ltr" />
        </div>
      </div>
      <div className={s['form-group']}>
        <label className={s['form-label']}>הערות</label>
        <textarea className={s.textarea} value={form.notes} onChange={set('notes')} rows={3} />
      </div>
      <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>צור פנייה</button>
    </form>
  )
}

/* ── Response Form ── */
function ResponseForm({ onSubmit }: { onSubmit: (text: string) => void }) {
  const [text, setText] = useState('')
  return (
    <form onSubmit={e => { e.preventDefault(); if (text.trim()) onSubmit(text.trim()) }} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div className={s['form-group']}>
        <label className={s['form-label']}>תגובה</label>
        <textarea className={s.textarea} value={text} onChange={e => setText(e.target.value)} rows={4} required />
      </div>
      <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>שלח תגובה</button>
    </form>
  )
}

/* ── Inquiry Detail ── */
function InquiryDetail({
  inquiry,
  responses,
  onAddResponse,
  onChangeStatus,
}: {
  inquiry: Inquiry
  responses: InquiryResponse[]
  onAddResponse: () => void
  onChangeStatus: (status: string) => void
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>נושא</span>
          <span className={s['detail-value']}>{inquiry.subject}</span>
        </div>
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>סוג</span>
          <span className={s['detail-value']}>{inquiry.inquiry_type}</span>
        </div>
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>סטטוס</span>
          <span className={s['detail-value']}>
            <Badge entity="inquiry" value={inquiry.status} />
          </span>
        </div>
        {inquiry.phone && (
          <div className={s['detail-row']}>
            <span className={s['detail-key']}>טלפון</span>
            <span className={s['detail-value']} dir="ltr">{inquiry.phone}</span>
          </div>
        )}
        {inquiry.notes && (
          <div className={s['detail-row']}>
            <span className={s['detail-key']}>הערות</span>
            <span className={s['detail-value']}>{inquiry.notes}</span>
          </div>
        )}
        <div className={s['detail-row']}>
          <span className={s['detail-key']}>נוצר</span>
          <span className={s['detail-value']}>{formatDateTime(inquiry.created_at)}</span>
        </div>
      </div>

      {/* Status actions */}
      <div style={{ display: 'flex', gap: 8 }}>
        {inquiry.status !== 'in_progress' && (
          <button className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`} onClick={() => onChangeStatus('in_progress')}>
            העבר לטיפול
          </button>
        )}
        {inquiry.status !== 'closed' && (
          <button className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`} onClick={() => onChangeStatus('closed')}>
            סגור פנייה
          </button>
        )}
      </div>

      {/* Responses */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h4 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>תגובות</h4>
          <button className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`} onClick={onAddResponse}>
            <MessageSquarePlus size={14} strokeWidth={1.5} /> הוסף
          </button>
        </div>
        {responses.length ? (
          <div className={s.timeline}>
            {responses.map(r => (
              <div key={r.id} className={s['timeline-item']}>
                <span className={s['timeline-dot']} />
                <div className={s['timeline-content']}>
                  <div className={s['timeline-date']}>
                    {formatDateTime(r.created_at)} {r.responded_by && `· ${r.responded_by}`}
                  </div>
                  <div className={s['timeline-text']}>{r.response_text}</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className={s.empty} style={{ padding: 20 }}>
            <span className={s['empty-text']}>אין תגובות עדיין</span>
          </div>
        )}
      </div>
    </div>
  )
}

/* ══════════════════════════════════════════════════════════════
   Inquiries Page
   ══════════════════════════════════════════════════════════════ */
export function InquiriesPage() {
  const { openModal, closeModal } = useModal()
  const toast = useToast()

  const [inquiries, setInquiries] = useState<Inquiry[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')

  const fetchInquiries = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get<Inquiry[]>('inquiries')
      setInquiries(statusFilter ? data.filter(i => i.status === statusFilter) : data)
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה')
    } finally {
      setLoading(false)
    }
  }, [statusFilter, toast])

  useEffect(() => { fetchInquiries() }, [fetchInquiries])

  const openCreate = () => {
    openModal({
      title: 'פנייה חדשה',
      size: 'md',
      content: (
        <InquiryForm
          onSubmit={async data => {
            try {
              await api.post('inquiries', data)
              toast.success('פנייה נוצרה')
              closeModal()
              fetchInquiries()
            } catch (err: unknown) { toast.error((err as { message?: string }).message ?? 'שגיאה') }
          }}
        />
      ),
    })
  }

  const openDetail = async (inq: Inquiry) => {
    try {
      const full = await api.get<Inquiry & { responses?: InquiryResponse[] }>(`inquiries/${inq.id}`)
      showDetailModal(full)
    } catch { toast.error('שגיאה') }
  }

  const showDetailModal = (full: Inquiry & { responses?: InquiryResponse[] }) => {
    openModal({
      title: full.subject,
      size: 'lg',
      content: (
        <InquiryDetail
          inquiry={full}
          responses={full.responses ?? []}
          onAddResponse={() => {
            closeModal()
            openAddResponse(full)
          }}
          onChangeStatus={async newStatus => {
            try {
              await api.patch(`inquiries/${full.id}/status`, { status: newStatus })
              toast.success('סטטוס עודכן')
              closeModal()
              fetchInquiries()
            } catch (err: unknown) { toast.error((err as { message?: string }).message ?? 'שגיאה') }
          }}
        />
      ),
    })
  }

  const openAddResponse = (inq: Inquiry & { responses?: InquiryResponse[] }) => {
    openModal({
      title: 'הוספת תגובה',
      size: 'md',
      content: (
        <ResponseForm
          onSubmit={async text => {
            try {
              await api.post(`inquiries/${inq.id}/responses`, { response_text: text })
              toast.success('תגובה נוספה')
              closeModal()
              // Refresh detail
              const fresh = await api.get<Inquiry & { responses?: InquiryResponse[] }>(`inquiries/${inq.id}`)
              showDetailModal(fresh)
            } catch (err: unknown) { toast.error((err as { message?: string }).message ?? 'שגיאה') }
          }}
        />
      ),
    })
  }

  const columns: Column<Inquiry>[] = [
    { key: 'id', header: '#' },
    { key: 'subject', header: 'נושא' },
    { key: 'inquiry_type', header: 'סוג' },
    { key: 'status', header: 'סטטוס', render: r => <Badge entity="inquiry" value={r.status} /> },
    { key: 'handled_by', header: 'מטפל', render: r => r.handled_by ?? '—' },
    { key: 'created_at', header: 'תאריך', render: r => formatDateTime(r.created_at), className: s.muted },
    {
      key: '_actions',
      header: '',
      render: r => (
        <button className={`${s.btn} ${s['btn-ghost']} ${s['btn-xs']}`} onClick={e => { e.stopPropagation(); openDetail(r) }}>
          <Eye size={14} strokeWidth={1.5} />
        </button>
      ),
    },
  ]

  return (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>פניות</h1>
        <div className={s['page-actions']}>
          <button className={`${s.btn} ${s['btn-primary']}`} onClick={openCreate}>
            <Plus size={16} strokeWidth={1.5} /> פנייה חדשה
          </button>
        </div>
      </div>

      <div className={s.card}>
        <div className={s.toolbar}>
          <select className={`${s.select} ${s['select-sm']}`} value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
            <option value="">כל הסטטוסים</option>
            <option value="new">חדש</option>
            <option value="in_progress">בטיפול</option>
            <option value="closed">סגור</option>
          </select>
        </div>
        <DataTable
          columns={columns}
          data={inquiries}
          loading={loading}
          emptyText="לא נמצאו פניות"
          emptyIcon={<Inbox size={40} strokeWidth={1.5} />}
          onRowClick={openDetail}
          keyExtractor={r => r.id}
        />
      </div>
    </div>
  )
}
