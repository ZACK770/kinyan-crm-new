import { useEffect, useState, useCallback, type FormEvent } from 'react'
import {
  Plus,
  CheckSquare,
  Eye,
  Pencil,
  AlertTriangle,
  FileText,
  ArrowRight,
} from 'lucide-react'
import { BackButton } from '@/components/ui/BackButton'
import { api } from '@/lib/api'
import { getStatus, getPriority, formatDate, formatDateTime } from '@/lib/status'
import { useToast } from '@/components/ui/Toast'
import { useModal } from '@/components/ui/Modal'
import { SmartTable, type SmartColumn } from '@/components/ui/SmartTable'
import type { SalesTask, Salesperson } from '@/types'
import s from '@/styles/shared.module.css'

interface User { id: number; name: string; email: string }
interface TaskReport { id: number; description: string | null; duration: string | null; created_at: string | null }

function Badge({ entity, value }: { entity: string; value?: string }) {
  const { label, color } = getStatus(entity, value)
  return <span className={`${s.badge} ${s[`badge-${color}`]}`}>{label}</span>
}

function PriorityBadge({ value }: { value?: number }) {
  const { label, color } = getPriority(value)
  return <span className={`${s.badge} ${s[`badge-${color}`]}`}>{label}</span>
}

const TASK_STATUS_OPTIONS = [
  { value: 'חדש', label: 'חדש' },
  { value: 'בטיפול', label: 'בטיפול' },
  { value: 'הושלם', label: 'הושלם' },
  { value: 'בוטל', label: 'בוטל' },
]

const TASK_TYPE_OPTIONS = [
  { value: 'sales', label: 'מכירות' },
  { value: 'class_management', label: 'ניהול כיתות' },
  { value: 'shipping', label: 'משלוחים' },
  { value: 'general', label: 'כללי' },
]

const PRIORITY_OPTIONS = [
  { value: 0, label: 'ללא' },
  { value: 1, label: 'נמוך' },
  { value: 2, label: 'רגיל' },
  { value: 3, label: 'גבוה' },
]

/* ── Task Form ── */
function TaskForm({
  initial,
  salespersons,
  users,
  onSubmit,
  onCancel,
}: {
  initial?: Partial<SalesTask>
  salespersons: Salesperson[]
  users: User[]
  onSubmit: (data: Record<string, unknown>) => void
  onCancel?: () => void
}) {
  const [form, setForm] = useState({
    title: initial?.title ?? '',
    description: initial?.description ?? '',
    salesperson_id: initial?.salesperson_id ?? '',
    assigned_to_user_id: (initial as Record<string, unknown>)?.assigned_to_user_id ?? '',
    lead_id: initial?.lead_id ?? '',
    student_id: initial?.student_id ?? '',
    priority: initial?.priority ?? 0,
    due_date: initial?.due_date ? String(initial.due_date).slice(0, 10) : '',
    task_type: (initial as Record<string, unknown>)?.task_type ?? 'general',
    status: initial?.status ?? 'חדש',
  })
  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [key]: e.target.value }))

  const handle = (e: FormEvent) => {
    e.preventDefault()
    const data: Record<string, unknown> = {
      title: form.title,
      priority: Number(form.priority),
      task_type: form.task_type,
      status: form.status,
    }
    if (form.description) data.description = form.description
    if (form.salesperson_id) data.salesperson_id = Number(form.salesperson_id)
    if (form.assigned_to_user_id) data.assigned_to_user_id = Number(form.assigned_to_user_id)
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
          <label className={s['form-label']}>סוג משימה</label>
          <select className={s.select} value={String(form.task_type)} onChange={set('task_type')}>
            {TASK_TYPE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>סטטוס</label>
          <select className={s.select} value={form.status} onChange={set('status')}>
            {TASK_STATUS_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
      </div>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>איש מכירות</label>
          <select className={s.select} value={form.salesperson_id} onChange={set('salesperson_id')}>
            <option value="">— ללא —</option>
            {salespersons.map(sp => <option key={sp.id} value={sp.id}>{sp.name}</option>)}
          </select>
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>משתמש אחראי</label>
          <select className={s.select} value={String(form.assigned_to_user_id ?? '')} onChange={set('assigned_to_user_id')}>
            <option value="">— ללא —</option>
            {users.map(u => <option key={u.id} value={u.id}>{u.name || u.email}</option>)}
          </select>
        </div>
      </div>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>עדיפות</label>
          <select className={s.select} value={form.priority} onChange={e => setForm(prev => ({ ...prev, priority: Number(e.target.value) }))}>
            {PRIORITY_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>תאריך יעד</label>
          <input className={s.input} type="date" value={form.due_date} onChange={set('due_date')} dir="ltr" />
        </div>
      </div>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>מזהה ליד</label>
          <input className={s.input} type="number" value={form.lead_id} onChange={set('lead_id')} dir="ltr" />
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>מזהה תלמיד</label>
          <input className={s.input} type="number" value={form.student_id} onChange={set('student_id')} dir="ltr" />
        </div>
      </div>
      <div style={{ display: 'flex', gap: 8, paddingTop: 8 }}>
        <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>
          {initial?.id ? 'עדכן' : 'צור משימה'}
        </button>
        {onCancel && (
          <button type="button" className={`${s.btn} ${s['btn-secondary']}`} onClick={onCancel}>ביטול</button>
        )}
      </div>
    </form>
  )
}

/* ── Task Detail (workspace) ── */
function TaskDetail({
  task,
  salespersons,
  users,
  onBack,
  onUpdate,
}: {
  task: SalesTask & { reports?: TaskReport[]; task_type?: string; assigned_to_user_id?: number }
  salespersons: Salesperson[]
  users: User[]
  onBack: () => void
  onUpdate: () => void
}) {
  const toast = useToast()
  const { openModal, closeModal } = useModal()
  const [reportText, setReportText] = useState('')
  const [reportDuration, setReportDuration] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const sp = salespersons.find(s => s.id === task.salesperson_id)
  const assignedUser = users.find(u => u.id === task.assigned_to_user_id)
  const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== 'הושלם' && task.status !== 'בוטל'
  const taskType = TASK_TYPE_OPTIONS.find(o => o.value === task.task_type)

  const handleAddReport = async () => {
    if (!reportText.trim()) return
    setSubmitting(true)
    try {
      await api.post(`tasks/${task.id}/reports`, {
        description: reportText,
        duration: reportDuration || null,
      })
      toast.success('דיווח נוסף')
      setReportText('')
      setReportDuration('')
      onUpdate()
    } catch {
      toast.error('שגיאה בהוספת דיווח')
    } finally {
      setSubmitting(false)
    }
  }

  const handleEdit = () => {
    openModal({
      title: `עריכת משימה — ${task.title}`,
      size: 'lg',
      content: (
        <TaskForm
          initial={task}
          salespersons={salespersons}
          users={users}
          onSubmit={async data => {
            try {
              await api.patch(`tasks/${task.id}`, data)
              toast.success('משימה עודכנה')
              closeModal()
              onUpdate()
            } catch (err: unknown) {
              toast.error((err as { message?: string }).message ?? 'שגיאה')
            }
          }}
          onCancel={() => closeModal()}
        />
      ),
    })
  }

  return (
    <div>
      <div className={s['page-header']}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <BackButton onClick={onBack} label="חזרה למשימות" />
          <h1 className={s['page-title']} style={{ fontSize: '1.2rem' }}>{task.title}</h1>
          <Badge entity="task" value={task.status} />
          {isOverdue && (
            <span className={`${s.badge} ${s['badge-red']}`}>
              <AlertTriangle size={12} /> באיחור
            </span>
          )}
        </div>
        <div className={s['page-actions']}>
          <button className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`} onClick={handleEdit}>
            <Pencil size={14} /> עריכה
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Details card */}
        <div className={s.card} style={{ padding: 20 }}>
          <h3 style={{ margin: '0 0 16px', fontSize: 14, fontWeight: 600 }}>פרטי משימה</h3>
          <div className={s['detail-row']}>
            <span className={s['detail-key']}>סוג</span>
            <span className={s['detail-value']}>{taskType?.label ?? task.task_type}</span>
          </div>
          <div className={s['detail-row']}>
            <span className={s['detail-key']}>עדיפות</span>
            <span className={s['detail-value']}><PriorityBadge value={task.priority} /></span>
          </div>
          <div className={s['detail-row']}>
            <span className={s['detail-key']}>איש מכירות</span>
            <span className={s['detail-value']}>{sp?.name ?? '—'}</span>
          </div>
          <div className={s['detail-row']}>
            <span className={s['detail-key']}>משתמש אחראי</span>
            <span className={s['detail-value']}>{assignedUser ? (assignedUser.name || assignedUser.email) : '—'}</span>
          </div>
          <div className={s['detail-row']}>
            <span className={s['detail-key']}>תאריך יעד</span>
            <span className={s['detail-value']} style={isOverdue ? { color: 'var(--color-danger)', fontWeight: 600 } : {}}>
              {task.due_date ? formatDate(task.due_date) : '—'}
              {isOverdue && ' ⚠️'}
            </span>
          </div>
          {task.lead_id && (
            <div className={s['detail-row']}>
              <span className={s['detail-key']}>ליד</span>
              <span className={s['detail-value']}>
                <a href={`/leads?lead=${task.lead_id}`} style={{ color: 'var(--color-primary)' }}>
                  #{task.lead_id} <ArrowRight size={12} style={{ display: 'inline' }} />
                </a>
              </span>
            </div>
          )}
          {task.student_id && (
            <div className={s['detail-row']}>
              <span className={s['detail-key']}>תלמיד</span>
              <span className={s['detail-value']}>#{task.student_id}</span>
            </div>
          )}
          {task.description && (
            <div style={{ marginTop: 12, padding: 12, background: 'var(--color-bg-accent)', borderRadius: 8, fontSize: 13, whiteSpace: 'pre-wrap' }}>
              {task.description}
            </div>
          )}
          <div style={{ marginTop: 16, fontSize: 11, color: 'var(--color-text-muted)' }}>
            <div>נוצר: {formatDateTime(task.created_at)}</div>
            {task.completed_at && <div>הושלם: {formatDateTime(task.completed_at)}</div>}
          </div>
        </div>

        {/* Reports card */}
        <div className={s.card} style={{ padding: 20 }}>
          <h3 style={{ margin: '0 0 16px', fontSize: 14, fontWeight: 600 }}>
            <FileText size={14} style={{ display: 'inline', marginLeft: 6 }} />
            דיווחי ביצוע
          </h3>

          {/* Add report form */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16, padding: 12, background: 'var(--color-bg-accent)', borderRadius: 8 }}>
            <textarea
              className={s.textarea}
              placeholder="הוסף דיווח ביצוע..."
              value={reportText}
              onChange={e => setReportText(e.target.value)}
              rows={2}
              style={{ fontSize: 13 }}
            />
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input
                className={s.input}
                placeholder="משך (אופציונלי)"
                value={reportDuration}
                onChange={e => setReportDuration(e.target.value)}
                style={{ flex: 1, fontSize: 12 }}
              />
              <button
                className={`${s.btn} ${s['btn-primary']} ${s['btn-sm']}`}
                onClick={handleAddReport}
                disabled={submitting || !reportText.trim()}
              >
                {submitting ? '...' : 'הוסף'}
              </button>
            </div>
          </div>

          {/* Reports list */}
          {task.reports && task.reports.length > 0 ? (
            <div className={s.timeline}>
              {task.reports.map((r: TaskReport) => (
                <div key={r.id} className={s['timeline-item']}>
                  <span className={s['timeline-dot']} />
                  <div className={s['timeline-content']}>
                    <div className={s['timeline-date']}>
                      {r.created_at ? formatDateTime(r.created_at) : ''}
                      {r.duration && <span> • {r.duration}</span>}
                    </div>
                    <div className={s['timeline-text']}>{r.description}</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: 20, color: 'var(--color-text-muted)', fontSize: 13 }}>
              אין דיווחים עדיין
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/* ══════════════════════════════════════════════════════════════
   Tasks Page
   ══════════════════════════════════════════════════════════════ */
export function TasksPage() {
  const toast = useToast()

  const [tasks, setTasks] = useState<SalesTask[]>([])
  const [salespersons, setSalespersons] = useState<Salesperson[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)

  // View state
  type ViewMode = 'list' | 'create' | 'detail'
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [selectedTask, setSelectedTask] = useState<SalesTask | null>(null)

  const backToList = () => {
    setViewMode('list')
    setSelectedTask(null)
  }

  const fetchTasks = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get<SalesTask[]>('tasks')
      setTasks(data)
    } catch {
      setTasks([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchTasks() }, [fetchTasks])
  useEffect(() => {
    Promise.all([
      api.get<Salesperson[]>('leads/salespersons').catch(() => []),
      api.get<User[]>('users').catch(() => []),
    ]).then(([sp, u]) => {
      setSalespersons(sp)
      setUsers(u)
    })
  }, [])

  const openCreate = () => setViewMode('create')

  const openDetail = async (task: SalesTask) => {
    try {
      const full = await api.get<SalesTask>(`tasks/${task.id}`)
      setSelectedTask(full)
      setViewMode('detail')
    } catch {
      toast.error('שגיאה בטעינת משימה')
    }
  }

  const refreshDetail = async () => {
    if (!selectedTask) return
    try {
      const full = await api.get<SalesTask>(`tasks/${selectedTask.id}`)
      setSelectedTask(full)
      fetchTasks()
    } catch {}
  }

  const handleInlineUpdate = async (row: SalesTask, field: string, value: unknown) => {
    try {
      await api.patch(`tasks/${row.id}`, { [field]: value })
      setTasks(prev => prev.map(t => t.id === row.id ? { ...t, [field]: value } : t))
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בעדכון')
      throw err
    }
  }

  const handleDelete = async (rows: SalesTask[]) => {
    try {
      for (const row of rows) {
        await api.delete(`tasks/${row.id}`)
      }
      toast.success(`נמחקו ${rows.length} משימות`)
      fetchTasks()
    } catch {
      toast.error('שגיאה במחיקה')
    }
  }

  const columns: SmartColumn<SalesTask>[] = [
    { key: 'id', header: '#', type: 'number', width: 60, editable: false },
    {
      key: 'title', header: 'כותרת', type: 'text',
      renderView: r => {
        const isOverdue = r.due_date && new Date(r.due_date) < new Date() && r.status !== 'הושלם' && r.status !== 'בוטל'
        return (
          <span style={{ fontWeight: 500 }}>
            {isOverdue && <AlertTriangle size={12} style={{ color: 'var(--color-danger)', marginLeft: 4, display: 'inline' }} />}
            {r.title}
          </span>
        )
      },
    },
    {
      key: 'status', header: 'סטטוס', type: 'select',
      options: TASK_STATUS_OPTIONS,
      renderView: r => <Badge entity="task" value={r.status} />,
    },
    {
      key: 'task_type', header: 'סוג', type: 'select',
      options: TASK_TYPE_OPTIONS,
      renderView: r => TASK_TYPE_OPTIONS.find(o => o.value === r.task_type)?.label ?? '—',
    },
    {
      key: 'priority', header: 'עדיפות', type: 'select',
      options: PRIORITY_OPTIONS,
      renderView: r => <PriorityBadge value={r.priority} />,
    },
    {
      key: 'salesperson_id', header: 'איש מכירות', type: 'select',
      options: salespersons.map(sp => ({ value: sp.id, label: sp.name })),
      renderView: r => salespersons.find(sp => sp.id === r.salesperson_id)?.name ?? '—',
    },
    {
      key: 'assigned_to_user_id', header: 'משתמש אחראי', type: 'select',
      options: users.map(u => ({ value: u.id, label: u.name || u.email })),
      renderView: r => {
        const u = users.find(u => u.id === r.assigned_to_user_id)
        return u ? (u.name || u.email) : '—'
      },
    },
    {
      key: 'due_date', header: 'יעד', type: 'date',
      renderView: r => {
        if (!r.due_date) return '—'
        const isOverdue = new Date(r.due_date) < new Date() && r.status !== 'הושלם' && r.status !== 'בוטל'
        return (
          <span style={isOverdue ? { color: 'var(--color-danger)', fontWeight: 600 } : {}}>
            {formatDate(r.due_date)}
          </span>
        )
      },
      className: s.muted,
    },
    { key: 'created_at', header: 'נוצר', type: 'date', editable: false, renderView: r => formatDate(r.created_at), className: s.muted },
    {
      key: '_actions', header: '', type: 'text', width: 50, editable: false, sortable: false, filterable: false,
      render: r => (
        <button
          className={`${s.btn} ${s['btn-ghost']} ${s['btn-xs']}`}
          onClick={e => { e.stopPropagation(); openDetail(r) }}
          title="פרטים"
        >
          <Eye size={14} />
        </button>
      ),
    },
  ]

  // Detail view
  if (viewMode === 'detail' && selectedTask) {
    return (
      <TaskDetail
        task={selectedTask as SalesTask & { reports?: TaskReport[]; task_type?: string; assigned_to_user_id?: number }}
        salespersons={salespersons}
        users={users}
        onBack={backToList}
        onUpdate={refreshDetail}
      />
    )
  }

  // Create view
  if (viewMode === 'create') {
    return (
      <div>
        <div className={s['page-header']}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <BackButton onClick={backToList} label="חזרה למשימות" />
            <h1 className={s['page-title']} style={{ fontSize: '1.2rem' }}>משימה חדשה</h1>
          </div>
        </div>
        <div className={s.card} style={{ padding: 24, maxWidth: 600 }}>
          <TaskForm
            salespersons={salespersons}
            users={users}
            onSubmit={async data => {
              try {
                await api.post('tasks', data)
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
          storageKey="tasks_table_v2"
          onUpdate={handleInlineUpdate}
          onDelete={handleDelete}
          onRowClick={openDetail}
          searchFields={[
            { key: 'title', label: 'כותרת', weight: 3 },
            { key: 'description', label: 'תיאור', weight: 1 },
          ]}
          searchPlaceholder="חיפוש משימות..."
          defaultPageSize={100}
          rowClassName={(row) => {
            if (row.status === 'הושלם') return 'row-closed-won'
            if (row.status === 'בוטל') return 'row-closed-lost'
            return ''
          }}
        />
      </div>
    </div>
  )
}
