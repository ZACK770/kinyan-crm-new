import { useEffect, useState, useCallback, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
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
    send_reminder: true,
  })
  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [key]: e.target.value }))

  const handle = (e: FormEvent) => {
    e.preventDefault()
    const data: Record<string, unknown> = { title: form.title, priority: Number(form.priority), send_reminder: form.send_reminder }
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
      <div className={s['form-group']}>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={form.send_reminder}
            onChange={e => setForm(prev => ({ ...prev, send_reminder: e.target.checked }))}
            style={{ width: 18, height: 18 }}
          />
          <span className={s['form-label']} style={{ margin: 0 }}>שלח מייל תזכורת לשעת המשימה</span>
        </label>
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
  const navigate = useNavigate()

  const [tasks, setTasks] = useState<SalesTask[]>([])
  const [salespersons, setSalespersons] = useState<Salesperson[]>([])
  const [loading, setLoading] = useState(true)

  // Workspace view state
  type ViewMode = 'list' | 'create'
  const [viewMode, setViewMode] = useState<ViewMode>('list')

  const backToList = () => setViewMode('list')

  const handleRowClick = (task: SalesTask) => {
    // If task is linked to a lead, navigate to lead with tasks tab
    if (task.lead_id) {
      navigate(`/leads/${task.lead_id}?tab=tasks`)
    } else {
      toast.info('משימה זו לא מקושרת לליד')
    }
  }

  const fetchTasks = useCallback(async () => {
    setLoading(true)
    try {
      // Get tasks from the dedicated tasks endpoint
      const data = await api.get<SalesTask[]>('tasks/').catch(() => [] as SalesTask[])
      setTasks(data)
    } catch {
      setTasks([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchTasks() }, [fetchTasks])
  useEffect(() => {
    api.get<Salesperson[]>('dashboard/salespeople/list').catch(() => []).then(data => {
      if (Array.isArray(data)) setSalespersons(data as Salesperson[])
    })
  }, [])

  const openCreate = () => {
    setViewMode('create')
  }

  const columns: SmartColumn<SalesTask>[] = [
    {
      key: 'title',
      header: 'כותרת',
      type: 'text',
      sortable: true,
      filterable: true,
    },
    {
      key: 'status',
      header: 'סטטוס',
      type: 'select',
      options: [
        { value: 'חדש', label: 'חדש' },
        { value: 'בטיפול', label: 'בטיפול' },
        { value: 'הושלם', label: 'הושלם' },
        { value: 'בוטל', label: 'בוטל' },
      ],
      renderView: r => <Badge entity="task" value={r.status} />,
      sortable: true,
      filterable: true,
    },
    {
      key: 'priority',
      header: 'עדיפות',
      type: 'select',
      options: [
        { value: 0, label: 'רגיל' },
        { value: 1, label: 'נמוך' },
        { value: 2, label: 'גבוה' },
        { value: 3, label: 'דחוף' },
      ],
      renderView: r => <PriorityBadge value={r.priority} />,
      sortable: true,
      filterable: true,
    },
    {
      key: 'salesperson_id',
      header: 'איש מכירות',
      type: 'select',
      options: salespersons.map(sp => ({ value: sp.id, label: sp.name })),
      renderView: r => salespersons.find(sp => sp.id === r.salesperson_id)?.name ?? '—',
      sortable: true,
      filterable: true,
    },
    {
      key: 'lead.full_name',
      header: 'שם ליד',
      type: 'text',
      renderView: r => (r as any).lead?.full_name ?? '—',
      sortable: false,
      filterable: true,
    },
    {
      key: 'lead.phone',
      header: 'טלפון ליד',
      type: 'text',
      renderView: r => (r as any).lead?.phone ?? '—',
      sortable: false,
      filterable: true,
    },
    {
      key: 'lead.email',
      header: 'מייל ליד',
      type: 'text',
      renderView: r => (r as any).lead?.email ?? '—',
      sortable: false,
      filterable: true,
      hiddenByDefault: true,
    },
    {
      key: 'due_date',
      header: 'יעד',
      type: 'datetime',
      renderView: r => formatDate(r.due_date),
      className: s.muted,
      sortable: true,
      filterable: true,
    },
    {
      key: 'created_at',
      header: 'תאריך יצירה',
      type: 'datetime',
      renderView: r => formatDate(r.created_at),
      className: s.muted,
      sortable: true,
      filterable: true,
    },
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
                await api.post('tasks/', data)
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
          onRowClick={handleRowClick}
          storageKey="tasks_table_v1"
          searchPlaceholder="חיפוש לפי כותרת..."
          searchFields={[
            { key: 'title', label: 'כותרת', weight: 3 },
          ]}
        />
      </div>
    </div>
  )
}
