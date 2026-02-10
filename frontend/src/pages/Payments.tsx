import { useState, type FormEvent } from 'react'
import { Plus, CreditCard, Search, ArrowRight } from 'lucide-react'
import { api } from '@/lib/api'
import { getStatus, formatDate, formatCurrency } from '@/lib/status'
import { useToast } from '@/components/ui/Toast'
import { DataTable, type Column } from '@/components/ui/DataTable'
import type { Payment } from '@/types'
import s from '@/styles/shared.module.css'

function Badge({ entity, value }: { entity: string; value?: string }) {
  const { label, color } = getStatus(entity, value)
  return <span className={`${s.badge} ${s[`badge-${color}`]}`}>{label}</span>
}

/* ── Payment Form ── */
function PaymentForm({ onSubmit, onCancel }: { onSubmit: (data: Record<string, unknown>) => void; onCancel?: () => void }) {
  const [form, setForm] = useState({
    student_id: '',
    amount: '',
    payment_method: 'credit_card',
    transaction_type: 'payment',
    reference: '',
    status: 'paid',
  })
  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(prev => ({ ...prev, [key]: e.target.value }))

  const handle = (e: FormEvent) => {
    e.preventDefault()
    const data: Record<string, unknown> = {
      student_id: Number(form.student_id),
      amount: Number(form.amount),
      payment_method: form.payment_method,
      transaction_type: form.transaction_type,
      status: form.status,
    }
    if (form.reference) data.reference = form.reference
    onSubmit(data)
  }

  return (
    <form onSubmit={handle} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>מזהה תלמיד *</label>
          <input className={s.input} type="number" value={form.student_id} onChange={set('student_id')} required dir="ltr" />
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>סכום *</label>
          <input className={s.input} type="number" step="0.01" value={form.amount} onChange={set('amount')} required dir="ltr" />
        </div>
      </div>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>אמצעי תשלום</label>
          <select className={s.select} value={form.payment_method} onChange={set('payment_method')}>
            <option value="credit_card">כרטיס אשראי</option>
            <option value="bank_transfer">העברה בנקאית</option>
            <option value="cash">מזומן</option>
            <option value="check">צ'ק</option>
            <option value="nedarim">נדרים פלוס</option>
          </select>
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>סוג עסקה</label>
          <select className={s.select} value={form.transaction_type} onChange={set('transaction_type')}>
            <option value="payment">תשלום</option>
            <option value="refund">החזר</option>
            <option value="charge">חיוב</option>
          </select>
        </div>
      </div>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>סטטוס</label>
          <select className={s.select} value={form.status} onChange={set('status')}>
            <option value="paid">שולם</option>
            <option value="pending">ממתין</option>
            <option value="partial">חלקי</option>
          </select>
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>אסמכתא</label>
          <input className={s.input} value={form.reference} onChange={set('reference')} dir="ltr" />
        </div>
      </div>
      <div style={{ display: 'flex', gap: 8, paddingTop: 8 }}>
        <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>שמור תשלום</button>
        {onCancel && (
          <button type="button" className={`${s.btn} ${s['btn-secondary']}`} onClick={onCancel}>ביטול</button>
        )}
      </div>
    </form>
  )
}

/* ══════════════════════════════════════════════════════════════
   Payments Page
   ══════════════════════════════════════════════════════════════ */
export function PaymentsPage() {
  const toast = useToast()

  const [payments, setPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(false)
  const [studentId, setStudentId] = useState('')

  // Workspace view state
  type ViewMode = 'list' | 'create'
  const [viewMode, setViewMode] = useState<ViewMode>('list')

  const backToList = () => setViewMode('list')

  const fetchPayments = async (sid?: string) => {
    const id = sid ?? studentId
    if (!id) return
    setLoading(true)
    try {
      const data = await api.get<Payment[]>(`finance/payments/student/${id}`)
      setPayments(data)
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה')
      setPayments([])
    } finally {
      setLoading(false)
    }
  }

  const openCreate = () => {
    setViewMode('create')
  }

  const columns: Column<Payment>[] = [
    { key: 'id', header: '#', render: r => r.id },
    { key: 'amount', header: 'סכום', render: r => formatCurrency(r.amount) },
    { key: 'payment_method', header: 'אמצעי', render: r => r.payment_method ?? '—' },
    { key: 'status', header: 'סטטוס', render: r => <Badge entity="payment" value={r.status} /> },
    { key: 'reference', header: 'אסמכתא', render: r => r.reference ?? '—', className: s.mono },
    { key: 'payment_date', header: 'תאריך', render: r => formatDate(r.payment_date ?? r.created_at), className: s.muted },
  ]

  // Show workspace for create
  if (viewMode === 'create') {
    return (
      <div>
        <div className={s['page-header']}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button className={`${s.btn} ${s['btn-ghost']}`} onClick={backToList} style={{ padding: '6px 10px' }}>
              <ArrowRight size={18} /> חזרה לרשימה
            </button>
            <h1 className={s['page-title']} style={{ fontSize: '1.2rem' }}>תשלום חדש</h1>
          </div>
        </div>
        <div className={s.card} style={{ padding: 24, maxWidth: 600 }}>
          <PaymentForm
            onSubmit={async data => {
              try {
                await api.post('finance/payments', data)
                toast.success('תשלום נוצר בהצלחה')
                backToList()
                if (studentId) fetchPayments()
              } catch (err: unknown) { toast.error((err as { message?: string }).message ?? 'שגיאה') }
            }}
            onCancel={backToList}
          />
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>תשלומים</h1>
        <div className={s['page-actions']}>
          <button className={`${s.btn} ${s['btn-primary']}`} onClick={openCreate}>
            <Plus size={16} strokeWidth={1.5} /> תשלום חדש
          </button>
        </div>
      </div>

      <div className={s.card}>
        <div className={s.toolbar}>
          <div style={{ display: 'flex', gap: 4, maxWidth: 300 }}>
            <input
              className={`${s.input} ${s['input-sm']}`}
              placeholder="מזהה תלמיד..."
              value={studentId}
              onChange={e => setStudentId(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && fetchPayments()}
              dir="ltr"
              style={{ flex: 1 }}
            />
            <button className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`} onClick={() => fetchPayments()}>
              <Search size={14} strokeWidth={1.5} />
            </button>
          </div>
        </div>

        {!studentId && !payments.length && !loading ? (
          <div className={s.empty}>
            <span className={s['empty-icon']}><CreditCard size={40} strokeWidth={1.5} /></span>
            <span className={s['empty-text']}>הזן מזהה תלמיד כדי לצפות בתשלומים</span>
          </div>
        ) : (
          <DataTable
            columns={columns}
            data={payments}
            loading={loading}
            emptyText="לא נמצאו תשלומים"
            emptyIcon={<CreditCard size={40} strokeWidth={1.5} />}
            keyExtractor={r => r.id}
          />
        )}
      </div>
    </div>
  )
}
