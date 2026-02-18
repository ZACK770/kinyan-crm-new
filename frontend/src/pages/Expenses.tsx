import { useEffect, useState, useCallback, type FormEvent } from 'react'
import { Plus, TrendingDown } from 'lucide-react'
import { BackButton } from '@/components/ui/BackButton'
import { api } from '@/lib/api'
import { formatDate, formatCurrency } from '@/lib/status'
import { useToast } from '@/components/ui/Toast'
import { SmartTable, type SmartColumn } from '@/components/ui/SmartTable'
import type { Expense } from '@/types'
import s from '@/styles/shared.module.css'

/* ── Expense Form ── */
function ExpenseForm({ onSubmit, onCancel }: { onSubmit: (data: Record<string, unknown>) => void; onCancel?: () => void }) {
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
      <div style={{ display: 'flex', gap: 8, paddingTop: 8 }}>
        <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>שמור הוצאה</button>
        {onCancel && (
          <button type="button" className={`${s.btn} ${s['btn-secondary']}`} onClick={onCancel}>ביטול</button>
        )}
      </div>
    </form>
  )
}

/* ══════════════════════════════════════════════════════════════
   Expenses Page
   ══════════════════════════════════════════════════════════════ */
export function ExpensesPage() {
  const toast = useToast()

  const [expenses, setExpenses] = useState<Expense[]>([])
  const [total, setTotal] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  // Workspace view state
  type ViewMode = 'list' | 'create'
  const [viewMode, setViewMode] = useState<ViewMode>('list')

  const backToList = () => setViewMode('list')

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
    setViewMode('create')
  }

  const columns: SmartColumn<Expense>[] = [
    { key: 'id', header: '#', type: 'number', width: 60, editable: false },
    { key: 'description', header: 'תיאור', type: 'text' },
    { 
      key: 'category', header: 'קטגוריה', type: 'select',
      options: [
        { value: 'marketing', label: 'שיווק' },
        { value: 'salary', label: 'שכר' },
        { value: 'rent', label: 'שכירות' },
        { value: 'software', label: 'תוכנה' },
        { value: 'supplies', label: 'ציוד' },
        { value: 'travel', label: 'נסיעות' },
        { value: 'other', label: 'אחר' },
      ],
      renderView: r => r.category ?? '—'
    },
    { key: 'amount', header: 'סכום', type: 'currency', renderView: r => formatCurrency(r.amount) },
    { key: 'vendor', header: 'ספק', type: 'text', renderView: r => r.vendor ?? '—' },
    { key: 'notes', header: 'הערות', type: 'text', hiddenByDefault: true, renderView: r => r.notes ?? '—' },
    { key: 'expense_date', header: 'תאריך', type: 'date', renderView: r => formatDate(r.expense_date ?? r.created_at), className: s.muted },
  ]

  // Show workspace for create
  if (viewMode === 'create') {
    return (
      <div>
        <div className={s['page-header']}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <BackButton onClick={backToList} label="חזרה להוצאות" />
            <h1 className={s['page-title']} style={{ fontSize: '1.2rem' }}>הוצאה חדשה</h1>
          </div>
        </div>
        <div className={s.card} style={{ padding: 24, maxWidth: 600 }}>
          <ExpenseForm
            onSubmit={async data => {
              try {
                await api.post('expenses', data)
                toast.success('הוצאה נוצרה')
                fetchExpenses()
                backToList()
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
        <SmartTable
          columns={columns}
          data={expenses}
          loading={loading}
          emptyText="אין הוצאות"
          emptyIcon={<TrendingDown size={40} strokeWidth={1.5} />}
          keyExtractor={r => r.id}
          storageKey="expenses_table"
          searchFields={[
            { key: 'description', label: 'תיאור', weight: 3 },
            { key: 'vendor', label: 'ספק', weight: 2 },
            { key: 'category', label: 'קטגוריה', weight: 1 },
          ]}
          searchPlaceholder="חיפוש הוצאות..."
        />
      </div>
    </div>
  )
}
