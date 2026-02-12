import { useEffect, useState, useCallback } from 'react'
import { Receipt, CheckCircle, XCircle } from 'lucide-react'
import { api } from '@/lib/api'
import { getStatus, formatDate, formatCurrency } from '@/lib/status'
import { useModal } from '@/components/ui/Modal'
import { useToast } from '@/components/ui/Toast'
import { SmartTable, type SmartColumn } from '@/components/ui/SmartTable'
import type { Collection } from '@/types'
import s from '@/styles/shared.module.css'

function Badge({ entity, value }: { entity: string; value?: string }) {
  const { label, color } = getStatus(entity, value)
  return <span className={`${s.badge} ${s[`badge-${color}`]}`}>{label}</span>
}

/* ══════════════════════════════════════════════════════════════
   Collections Page
   ══════════════════════════════════════════════════════════════ */
export function CollectionsPage() {
  const { confirm } = useModal()
  const toast = useToast()

  const [items, setItems] = useState<Collection[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'pending' | 'overdue'>('pending')

  const fetchItems = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get<Collection[]>(`collections/${tab}`)
      setItems(data)
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה')
    } finally {
      setLoading(false)
    }
  }, [tab, toast])

  useEffect(() => { fetchItems() }, [fetchItems])

  const markCollected = async (item: Collection) => {
    const ok = await confirm({ title: 'אישור גביה', message: `לסמן גביה של ${formatCurrency(item.amount)}?` })
    if (!ok) return
    try {
      await api.post(`collections/${item.id}/collected`)
      toast.success('נגבה בהצלחה')
      fetchItems()
    } catch (err: unknown) { toast.error((err as { message?: string }).message ?? 'שגיאה') }
  }

  const markFailed = async (item: Collection) => {
    const ok = await confirm({ title: 'סימון ככישלון', message: 'לסמן גביה זו ככושלת?', danger: true })
    if (!ok) return
    try {
      await api.post(`collections/${item.id}/failed`)
      toast.warning('סומן ככישלון')
      fetchItems()
    } catch (err: unknown) { toast.error((err as { message?: string }).message ?? 'שגיאה') }
  }

  const columns: SmartColumn<Collection>[] = [
    { key: 'id', header: '#', type: 'number', width: 60, editable: false },
    { key: 'student_name', header: 'תלמיד', type: 'text', editable: false, renderView: r => (r as any).student_name ?? `תלמיד #${r.student_id}` },
    { key: 'amount', header: 'סכום', type: 'currency', editable: false, renderView: r => formatCurrency(r.amount) },
    { key: 'due_date', header: 'תאריך יעד', type: 'date', editable: false, renderView: r => formatDate(r.due_date), className: s.muted },
    {
      key: 'status', header: 'סטטוס', type: 'select', editable: false,
      options: [
        { value: 'pending', label: 'ממתין' },
        { value: 'collected', label: 'נגבה' },
        { value: 'failed', label: 'נכשל' },
        { value: 'overdue', label: 'באיחור' },
      ],
      renderView: r => <Badge entity="collection" value={r.status} />,
    },
    { key: 'payment_method', header: 'אמצעי', type: 'text', editable: false, renderView: r => (r as any).payment_method ?? '—' },
    {
      key: '_actions', header: 'פעולות', type: 'text', editable: false, sortable: false, filterable: false,
      renderView: r => (
        <div style={{ display: 'flex', gap: 4 }}>
          <button className={`${s.btn} ${s['btn-ghost']} ${s['btn-xs']}`} onClick={() => markCollected(r)} title="נגבה">
            <CheckCircle size={14} strokeWidth={1.5} />
          </button>
          <button className={`${s.btn} ${s['btn-ghost']} ${s['btn-xs']}`} onClick={() => markFailed(r)} title="נכשל">
            <XCircle size={14} strokeWidth={1.5} />
          </button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>גביה</h1>
      </div>

      <div className={s.card}>
        <div className={s.toolbar}>
          <div className={s.tabs}>
            <button className={`${s.tab} ${tab === 'pending' ? s.active : ''}`} onClick={() => setTab('pending')}>
              ממתינים
            </button>
            <button className={`${s.tab} ${tab === 'overdue' ? s.active : ''}`} onClick={() => setTab('overdue')}>
              באיחור
            </button>
          </div>
        </div>

        <SmartTable
          columns={columns}
          data={items}
          loading={loading}
          emptyText={tab === 'pending' ? 'אין גביות ממתינות' : 'אין גביות באיחור'}
          emptyIcon={<Receipt size={40} strokeWidth={1.5} />}
          keyExtractor={r => r.id}
          storageKey="collections_table"
          searchFields={[
            { key: 'student_name', label: 'תלמיד', weight: 3 },
          ]}
          searchPlaceholder="חיפוש גביות..."
        />
      </div>
    </div>
  )
}
