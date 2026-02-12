import { useEffect, useState, useCallback, type FormEvent } from 'react'
import { Plus, CheckSquare, ArrowRight } from 'lucide-react'
import { api } from '@/lib/api'
import { getStatus, getPriority, formatDate } from '@/lib/status'
import { useToast } from '@/components/ui/Toast'
import { SmartTable, type SmartColumn } from '@/components/ui/SmartTable'
import type { SalesTask, Salesperson } from '@/types'
import s from '@/styles/shared.module.css'

function Badge({ entity, value }: { entity: string; value?: string }) {
  const { label, color } = getStatus(entity, value)
  return <span className={`${s.badge} ${s[`badge-${color}`]}`}>{label}</span>
}

function PriorityBadge({ value }: { value?: number }) {
  const { label, color } = getPriority(value)
  return <span className={`${s.badge} ${s[`badge-${color}`]}`}>{label}</span>
}

/* ── Task Form ── */
function TaskForm({
  salespersons,
  onSubmit,
  onCancel,
}: {
  salespersons: Salesperson[]
  onSubmit: (data: Record<string, unknown>) => void
  onCancel?: () => void
}) {
  const [form, setForm] = useState({
    title: '',
    description: '',
    salesperson_id: '',
    lead_id: '',
    student_id: '',
    priority: '2',
    due_date: '',
  })
  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [key]: e.target.value }))

  const handle = (e: FormEvent) => {
    e.preventDefault()
    const data: Record<string, unknown> = { title: form.title, priority: Number(form.priority) }
    if (form.description) data.description = form.description
    if (form.salesperson_id) data.salesperson_id = Number(form.salesperson_id)
    if (form.lead_id) data.lead_id = Number(form.lead_id)
    if (form.student_id) data.student_id = Number(form.student_id)
    if (form.due_date) data.due_date = form.due_date
    onSubmit(data)
  }

  return (
    <form onSubmit={handle} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className={s['form-group']}>
        <label className={s['form-label']}>כותרת *</label>
        <input className={s.input} value={form.title} onChange={set('title')} required />
      </div>
      <div className={s['form-group']}>
        <label className={s['form-label']}>תיאור</label>
        <textarea className={s.textarea} value={form.description} onChange={set('description')} rows={3} />
      </div>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>איש מכירות</label>
          <select className={s.select} value={form.salesperson_id} onChange={set('salesperson_id')}>
            <option value="">— בחר —</option>
            {salespersons.map(sp => <option key={sp.id} value={sp.id}>{sp.name}</option>)}
          </select>
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>עדיפות</label>
          <select className={s.select} value={form.priority} onChange={set('priority')}>
            <option value="1">נמוך</option>
            <option value="2">רגיל</option>
            <option value="3">גבוה</option>
            <option value="4">דחוף</option>
          </select>
        </div>
      </div>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>מזהה ליד</label>
          <input className={s.input} type="number" value={form.lead_id} onChange={set('lead_id')} dir="ltr" />
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>תאריך יעד</label>
          <input className={s.input} type="date" value={form.due_date} onChange={set('due_date')} dir="ltr" />
        </div>
      </div>
      <div style={{ display: 'flex', gap: 8, paddingTop: 8 }}>
        <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>צור משימה</button>
        {onCancel && (
          <button type="button" className={`${s.btn} ${s['btn-secondary']}`} onClick={onCancel}>ביטול</button>
        )}
      </div>
    </form>
  )
}

/* ══════════════════════════════════════════════════════════════
   Tasks Page
   ══════════════════════════════════════════════════════════════ */
export function TasksPage() {
  const toast = useToast()

  const [tasks, setTasks] = useState<SalesTask[]>([])
  const [salespersons, setSalespersons] = useState<Salesperson[]>([])
  const [loading, setLoading] = useState(true)

  // Workspace view state
  type ViewMode = 'list' | 'create'
  const [viewMode, setViewMode] = useState<ViewMode>('list')

  const backToList = () => setViewMode('list')

  const fetchTasks = useCallback(async () => {
    setLoading(true)
    try {
      // Tasks may be returned through dashboard salespeople endpoint or a dedicated one
      // For now we attempt to get from a general tasks endpoint
      const data = await api.get<SalesTask[]>('leads/tasks').catch(() => [] as SalesTask[])
      setTasks(data)
    } catch {
      setTasks([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchTasks() }, [fetchTasks])
  useEffect(() => {
    api.get<Salesperson[]>('dashboard/salespeople').catch(() => []).then(data => {
      if (Array.isArray(data)) setSalespersons(data as Salesperson[])
    })
  }, [])

  const openCreate = () => {
    setViewMode('create')
  }

  const handleInlineUpdate = async (row: SalesTask, field: string, value: unknown) => {
    try {
      await api.patch(`leads/tasks/${row.id}`, { [field]: value })
      setTasks(prev => prev.map(t => t.id === row.id ? { ...t, [field]: value } : t))
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בעדכון')
      throw err
    }
  }

  const columns: SmartColumn<SalesTask>[] = [
    { key: 'id', header: '#', type: 'number', width: 60, editable: false },
    { key: 'title', header: 'כותרת', type: 'text' },
    {
      key: 'status', header: 'סטטוס', type: 'select',
      options: [
        { value: 'new', label: 'חדש' },
        { value: 'in_progress', label: 'בביצוע' },
        { value: 'completed', label: 'הושלם' },
        { value: 'cancelled', label: 'בוטל' },
      ],
      renderView: r => <Badge entity="task" value={r.status} />,
    },
    {
      key: 'priority', header: 'עדיפות', type: 'select',
      options: [
        { value: 1, label: 'נמוך' },
        { value: 2, label: 'רגיל' },
        { value: 3, label: 'גבוה' },
        { value: 4, label: 'דחוף' },
      ],
      renderView: r => <PriorityBadge value={r.priority} />,
    },
    {
      key: 'salesperson_id', header: 'איש מכירות', type: 'select',
      options: salespersons.map(sp => ({ value: sp.id, label: sp.name })),
      renderView: r => salespersons.find(sp => sp.id === r.salesperson_id)?.name ?? '—',
    },
    { key: 'due_date', header: 'יעד', type: 'date', renderView: r => formatDate(r.due_date), className: s.muted },
    { key: 'created_at', header: 'נוצר', type: 'date', editable: false, renderView: r => formatDate(r.created_at), className: s.muted },
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
            <h1 className={s['page-title']} style={{ fontSize: '1.2rem' }}>משימה חדשה</h1>
          </div>
        </div>
        <div className={s.card} style={{ padding: 24, maxWidth: 600 }}>
          <TaskForm
            salespersons={salespersons}
            onSubmit={async data => {
              try {
                await api.post('leads/tasks', data)
                toast.success('משימה נוצרה')
                fetchTasks()
                backToList()
              } catch (err: unknown) { toast.error((err as { message?: string }).message ?? 'שגיאה ביצירת משימה') }
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
        <h1 className={s['page-title']}>משימות</h1>
        <div className={s['page-actions']}>
          <button className={`${s.btn} ${s['btn-primary']}`} onClick={openCreate}>
            <Plus size={16} strokeWidth={1.5} /> משימה חדשה
          </button>
        </div>
      </div>

      <div className={s.card}>
        <SmartTable
          columns={columns}
          data={tasks}
          loading={loading}
          emptyText="אין משימות"
          emptyIcon={<CheckSquare size={40} strokeWidth={1.5} />}
          keyExtractor={r => r.id}
          storageKey="tasks_table"
          onUpdate={handleInlineUpdate}
          searchFields={[
            { key: 'title', label: 'כותרת', weight: 3 },
          ]}
          searchPlaceholder="חיפוש משימות..."
        />
      </div>
    </div>
  )
}
