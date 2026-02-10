import { useEffect, useState, useCallback, type FormEvent } from 'react'
import { Plus, TrendingDown } from 'lucide-react'
import { api } from '@/lib/api'
import { formatDate, formatCurrency } from '@/lib/status'
import { useModal } from '@/components/ui/Modal'
import { useToast } from '@/components/ui/Toast'
import { DataTable, type Column } from '@/components/ui/DataTable'
import type { Expense } from '@/types'
import s from '@/styles/shared.module.css'

/* ── Expense Form ── */
function ExpenseForm({ onSubmit }: { onSubmit: (data: Record<string, unknown>) => void }) {
  const [form, setForm] = useState({
    description: '',
    category: '',
    amount: '',
    vendor: '',
    expense_date: '',
    notes: '',
  })
  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [key]: e.target.value }))

  const handle = (e: FormEvent) => {
    e.preventDefault()
    const data: Record<string, unknown> = {
      description: form.description,
      amount: Number(form.amount),
    }
    if (form.category) data.category = form.category
    if (form.vendor) data.vendor = form.vendor
    if (form.expense_date) data.expense_date = form.expense_date
    if (form.notes) data.notes = form.notes
    onSubmit(data)
  }

  return (
    <form onSubmit={handle} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className={s['form-group']}>
        <label className={s['form-label']}>תיאור *</label>
        <input className={s.input} value={form.description} onChange={set('description')} required />
      </div>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>סכום *</label>
          <input className={s.input} type="number" step="0.01" value={form.amount} onChange={set('amount')} required dir="ltr" />
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>קטגוריה</label>
          <select className={s.select} value={form.category} onChange={set('category')}>
            <option value="">— בחר —</option>
            <option value="marketing">שיווק</option>
            <option value="salary">שכר</option>
            <option value="rent">שכירות</option>
            <option value="software">תוכנה</option>
            <option value="supplies">ציוד</option>
            <option value="travel">נסיעות</option>
            <option value="other">אחר</option>
          </select>
        </div>
      </div>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>ספק</label>
          <input className={s.input} value={form.vendor} onChange={set('vendor')} />
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>תאריך</label>
          <input className={s.input} type="date" value={form.expense_date} onChange={set('expense_date')} dir="ltr" />
        </div>
      </div>
      <div className={s['form-group']}>
        <label className={s['form-label']}>הערות</label>
        <textarea className={s.textarea} value={form.notes} onChange={set('notes')} rows={2} />
      </div>
      <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>שמור הוצאה</button>
    </form>
  )
}

/* ══════════════════════════════════════════════════════════════
   Expenses Page
   ══════════════════════════════════════════════════════════════ */
export function ExpensesPage() {
  const { openModal, closeModal } = useModal()
  const toast = useToast()

  const [expenses, setExpenses] = useState<Expense[]>([])
  const [total, setTotal] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchExpenses = useCallback(async () => {
    setLoading(true)
    try {
      const [data, totalData] = await Promise.all([
        api.get<Expense[]>('expenses?limit=200'),
        api.get<{ total: number }>('expenses/total'),
      ])
      setExpenses(data)
      setTotal(totalData.total)
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה')
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => { fetchExpenses() }, [fetchExpenses])

  const openCreate = () => {
    openModal({
      title: 'הוצאה חדשה',
      size: 'md',
      content: (
        <ExpenseForm
          onSubmit={async data => {
            try {
              await api.post('expenses', data)
              toast.success('הוצאה נוצרה')
              closeModal()
              fetchExpenses()
            } catch (err: unknown) { toast.error((err as { message?: string }).message ?? 'שגיאה') }
          }}
        />
      ),
    })
  }

  const columns: Column<Expense>[] = [
    { key: 'description', header: 'תיאור' },
    { key: 'category', header: 'קטגוריה', render: r => r.category ?? '—' },
    { key: 'amount', header: 'סכום', render: r => formatCurrency(r.amount) },
    { key: 'vendor', header: 'ספק', render: r => r.vendor ?? '—' },
    { key: 'expense_date', header: 'תאריך', render: r => formatDate(r.expense_date ?? r.created_at), className: s.muted },
  ]

  return (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>הוצאות</h1>
        <div className={s['page-actions']}>
          {total != null && (
            <span style={{ fontSize: 14, color: 'var(--color-text-secondary)', marginLeft: 12 }}>
              סה"כ: <strong>{formatCurrency(total)}</strong>
            </span>
          )}
          <button className={`${s.btn} ${s['btn-primary']}`} onClick={openCreate}>
            <Plus size={16} strokeWidth={1.5} /> הוצאה חדשה
          </button>
        </div>
      </div>

      <div className={s.card}>
        <DataTable
          columns={columns}
          data={expenses}
          loading={loading}
          emptyText="אין הוצאות"
          emptyIcon={<TrendingDown size={40} strokeWidth={1.5} />}
          keyExtractor={r => r.id}
        />
      </div>
    </div>
  )
}
