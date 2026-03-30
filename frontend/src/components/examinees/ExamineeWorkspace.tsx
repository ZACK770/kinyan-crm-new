import { useState, useCallback, useMemo, type ReactNode, type FormEvent, useEffect } from 'react'
import {
  History,
  ClipboardList,
  FileCheck2,
  CreditCard,
  Save,
  ChevronDown,
  Trash2,
  Phone,
} from 'lucide-react'
import { BackButton } from '@/components/ui/BackButton'
import { api } from '@/lib/api'
import { formatDateTime } from '@/lib/status'
import { EditableField, type SelectOption } from '@/components/ui/EditableField'
import { useModal } from '@/components/ui/Modal'
import { useToast } from '@/components/ui/Toast'
import s from '@/styles/shared.module.css'
import type { Examinee, Collection } from '@/types'

type TabId = 'history' | 'registrations' | 'submissions' | 'collections'

const INITIAL_FORM = {
  full_name: '',
  phone: '',
  id_number: '',
  email: '',
  source: 'external_exam_product',
  student_id: '',
}

const SOURCE_OPTIONS: SelectOption[] = [
  { value: 'external_exam_product', label: 'מוצר מבחנים חיצוני' },
  { value: 'manual', label: 'ידני' },
]

interface ExamineeSubmission {
  id: number
  exam_id: number
  exam_name: string
  exam_date: string | null
  exam_type: string
  submitted_at: string | null
  score: number | null
  status: string
  student_notes: string | null
  internal_notes: string | null
}

interface ExamListItem {
  id: number
  name: string
  exam_type: string
  exam_date: string | null
  course_id: number
}

function TabButton({
  active,
  icon,
  label,
  count,
  onClick,
}: {
  active: boolean
  icon: ReactNode
  label: string
  count?: number
  onClick: () => void
}) {
  return (
    <button
      type="button"
      className={`${s.btn} ${s['btn-ghost']}`}
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '10px 12px',
        borderBottom: active ? '2px solid var(--color-primary)' : '2px solid transparent',
        borderRadius: 0,
      }}
    >
      {icon}
      <span>{label}</span>
      {typeof count === 'number' && (
        <span
          style={{
            fontSize: 12,
            padding: '1px 8px',
            background: 'var(--bg-accent)',
            borderRadius: 999,
          }}
        >
          {count}
        </span>
      )}
    </button>
  )
}

function EmptyState({ title }: { title: string }) {
  return (
    <div className={s.empty} style={{ padding: 40 }}>
      <span className={s['empty-text']}>{title}</span>
    </div>
  )
}

function HistoryTab({ examineeId }: { examineeId: number }) {
  const toast = useToast()
  const [loading, setLoading] = useState(true)
  const [items, setItems] = useState<any[]>([])

  useEffect(() => {
    let isMounted = true
    setLoading(true)
    api.get<any[]>(`/api/audit-logs/entity/examinees/${examineeId}?limit=50`)
      .then(data => { if (isMounted) setItems(data || []) })
      .catch(() => toast.error('שגיאה בטעינת היסטוריה'))
      .finally(() => { if (isMounted) setLoading(false) })
    return () => { isMounted = false }
  }, [examineeId, toast])

  if (loading) return <div style={{ color: 'var(--color-text-muted)' }}>טוען היסטוריה...</div>
  if (!items.length) return <EmptyState title="אין עדיין היסטוריה" />

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {items.map((x) => (
        <div key={x.id} style={{ padding: 12, border: '1px solid var(--color-border-light)', borderRadius: 8 }}>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{formatDateTime(x.created_at)}</div>
          <div style={{ fontSize: 13, fontWeight: 600 }}>{x.description || x.action}</div>
          {x.user_name && <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>ע"י: {x.user_name}</div>}
        </div>
      ))}
    </div>
  )
}

function RegistrationsTab({ examineeId, onRegistered }: { examineeId: number; onRegistered: () => void }) {
  const toast = useToast()
  const [loading, setLoading] = useState(true)
  const [exams, setExams] = useState<ExamListItem[]>([])
  const [selectedExamId, setSelectedExamId] = useState<string>('')
  const [isRegistering, setIsRegistering] = useState(false)

  useEffect(() => {
    let isMounted = true
    setLoading(true)
    api.get<ExamListItem[]>('/api/exams?limit=500')
      .then(data => { if (isMounted) setExams(data || []) })
      .catch(() => toast.error('שגיאה בטעינת מבחנים'))
      .finally(() => { if (isMounted) setLoading(false) })
    return () => { isMounted = false }
  }, [toast])

  const handleRegister = async () => {
    if (!selectedExamId) return
    setIsRegistering(true)
    try {
      await api.post(`examinees/${examineeId}/registrations`, { exam_id: Number(selectedExamId) })
      toast.success('נרשם למבחן')
      setSelectedExamId('')
      onRegistered()
    } catch (err: any) {
      toast.error(err?.message ?? 'שגיאה ברישום למבחן')
    } finally {
      setIsRegistering(false)
    }
  }

  if (loading) return <div style={{ color: 'var(--color-text-muted)' }}>טוען מבחנים...</div>
  if (!exams.length) return <EmptyState title="אין עדיין מבחנים" />

  return (
    <div>
      <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', marginBottom: 14, flexWrap: 'wrap' }}>
        <div className={s['form-group']} style={{ minWidth: 280 }}>
          <label className={s['form-label']}>בחר מבחן לרישום</label>
          <select className={s.select} value={selectedExamId} onChange={e => setSelectedExamId(e.target.value)}>
            <option value="">— בחר —</option>
            {exams.map(e => (
              <option key={e.id} value={String(e.id)}>
                {e.name}{e.exam_date ? ` — ${e.exam_date}` : ''}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          className={`${s.btn} ${s['btn-primary']}`}
          disabled={!selectedExamId || isRegistering}
          onClick={handleRegister}
        >
          {isRegistering ? 'רושם...' : 'רשום למבחן'}
        </button>
      </div>
      <table className={s.table}>
        <thead>
          <tr>
            <th>מבחן</th>
            <th>סוג</th>
            <th>תאריך</th>
            <th>קורס</th>
          </tr>
        </thead>
        <tbody>
          {exams.map(e => (
            <tr key={e.id}>
              <td>{e.name}</td>
              <td>{e.exam_type}</td>
              <td>{e.exam_date || '—'}</td>
              <td>{e.course_id}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function SubmissionsTab({ examineeId }: { examineeId: number }) {
  const toast = useToast()
  const [loading, setLoading] = useState(true)
  const [items, setItems] = useState<ExamineeSubmission[]>([])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get<ExamineeSubmission[]>(`examinees/${examineeId}/submissions`)
      setItems(data || [])
    } catch {
      toast.error('שגיאה בטעינת הגשות')
    } finally {
      setLoading(false)
    }
  }, [examineeId, toast])

  useEffect(() => {
    load()
  }, [load])

  if (loading) return <div style={{ color: 'var(--color-text-muted)' }}>טוען הגשות...</div>
  if (!items.length) return <EmptyState title="עדיין אין תוצאות" />

  return (
    <table className={s.table}>
      <thead>
        <tr>
          <th>מבחן</th>
          <th>תאריך</th>
          <th>סטטוס</th>
          <th>ציון</th>
          <th>הוגש</th>
        </tr>
      </thead>
      <tbody>
        {items.map(x => (
          <tr key={x.id}>
            <td>{x.exam_name}</td>
            <td>{x.exam_date || '—'}</td>
            <td>{x.status}</td>
            <td>{x.score ?? '—'}</td>
            <td>{x.submitted_at ? formatDateTime(x.submitted_at) : '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function CollectionsTab({ studentId }: { studentId: number }) {
  const toast = useToast()
  const [loading, setLoading] = useState(true)
  const [items, setItems] = useState<Collection[]>([])

  useEffect(() => {
    let isMounted = true
    setLoading(true)
    api.get<Collection[]>(`/api/collections/student/${studentId}?limit=200`)
      .then(data => { if (isMounted) setItems(data || []) })
      .catch(() => toast.error('שגיאה בטעינת גביה'))
      .finally(() => { if (isMounted) setLoading(false) })
    return () => { isMounted = false }
  }, [studentId, toast])

  if (loading) return <div style={{ color: 'var(--color-text-muted)' }}>טוען גביה...</div>
  if (!items.length) return <EmptyState title="אין עדיין גביה" />

  return (
    <table className={s.table}>
      <thead>
        <tr>
          <th>תאריך יעד</th>
          <th>סכום</th>
          <th>סטטוס</th>
          <th>הערות</th>
        </tr>
      </thead>
      <tbody>
        {items.map(c => (
          <tr key={c.id}>
            <td>{c.due_date}</td>
            <td>{c.amount}</td>
            <td>{c.status}</td>
            <td>{c.notes || '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

interface ExamineeWorkspaceProps {
  examinee?: Examinee | null
  onClose: () => void
  onUpdate: () => void
  onCreate?: (examinee: Examinee) => void
  onDelete?: () => void
}

export function ExamineeWorkspace({
  examinee,
  onClose,
  onUpdate,
  onCreate,
  onDelete,
}: ExamineeWorkspaceProps) {
  const isCreateMode = !examinee
  const toast = useToast()
  const { confirm } = useModal()

  const [activeTab, setActiveTab] = useState<TabId>('submissions')
  const [isSaving, setIsSaving] = useState(false)

  const [form, setForm] = useState(INITIAL_FORM)

  const isDirty = useMemo(() => {
    if (!isCreateMode) return false
    return Object.keys(INITIAL_FORM).some(
      key => (form as any)[key] !== (INITIAL_FORM as any)[key]
    )
  }, [isCreateMode, form])

  const updateForm = (field: string, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }))
  }

  const saveField = useCallback(async (field: string, value: string | number | null) => {
    if (!examinee) return
    await api.patch(`/examinees/${examinee.id}`, { [field]: value })
    onUpdate()
  }, [examinee?.id, onUpdate])

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
  }, [confirm, isDirty, onClose])

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault()
    if (!form.phone.trim()) return

    setIsSaving(true)
    try {
      const data: Record<string, unknown> = { ...form }
      if (data.student_id) data.student_id = Number(data.student_id)
      else delete data.student_id
      Object.keys(data).forEach(k => { if (data[k] === '') delete data[k] })

      const result = await api.post<{ id: number }>('examinees', data)
      const full = await api.get<Examinee>(`examinees/${result.id}`)
      toast.success('נבחן נוצר בהצלחה')
      onCreate?.(full)
    } catch (err: any) {
      const msg = err?.message || 'שגיאה ביצירת נבחן'
      toast.error(msg)
    } finally {
      setIsSaving(false)
    }
  }

  if (isCreateMode) {
    return (
      <div className={s.workspace}>
        <form onSubmit={handleCreate} className={s.workspace__sidebar}>
          <div className={s.workspace__header}>
            <BackButton onClick={handleClose} label="חזרה לנבחנים" />
            <div className={s.workspace__title}>
              <span>{form.full_name || 'נבחן חדש'}</span>
            </div>
          </div>

          <CollapsibleSection id="create-contact" title="פרטי נבחן">
            <div className={s['field-grid']}>
              <EditableField label="שם" value={form.full_name} onSave={v => { updateForm('full_name', String(v ?? '')); return Promise.resolve() }} />
              <EditableField label="טלפון *" value={form.phone} dir="ltr" onSave={v => { updateForm('phone', String(v ?? '')); return Promise.resolve() }} />
              <EditableField label='ת"ז' value={form.id_number} dir="ltr" onSave={v => { updateForm('id_number', String(v ?? '')); return Promise.resolve() }} />
              <EditableField label="אימייל" value={form.email} dir="ltr" onSave={v => { updateForm('email', String(v ?? '')); return Promise.resolve() }} />
            </div>
            <div className={`${s['field-grid']} ${s['field-grid--single']}`}>
              <EditableField
                label="מקור"
                value={form.source || null}
                type="select"
                options={SOURCE_OPTIONS}
                onSave={v => { updateForm('source', String(v ?? '')); return Promise.resolve() }}
              />
              <EditableField
                label="תלמיד # (אופציונלי)"
                value={form.student_id || null}
                dir="ltr"
                onSave={v => { updateForm('student_id', String(v ?? '')); return Promise.resolve() }}
              />
            </div>
          </CollapsibleSection>

          <div style={{ display: 'flex', gap: 12, paddingTop: 16, borderTop: '1px solid var(--color-border-light)' }}>
            <button type="submit" className={`${s.btn} ${s['btn-primary']}`} disabled={isSaving || !form.phone.trim()}>
              <Save size={16} /> {isSaving ? 'שומר...' : 'צור נבחן'}
            </button>
            <button type="button" className={`${s.btn} ${s['btn-ghost']}`} onClick={handleClose}>
              ביטול
            </button>
          </div>
        </form>

        <div className={s.workspace__main}>
          <div className={s.tabs}>
            <TabButton active icon={<History size={14} />} label="היסטוריה" onClick={() => {}} />
            <TabButton active={false} icon={<ClipboardList size={14} />} label="רישום למבחנים" onClick={() => {}} />
            <TabButton active={false} icon={<FileCheck2 size={14} />} label="הגשות ותוצאות" onClick={() => {}} />
            <TabButton active={false} icon={<CreditCard size={14} />} label="גביה" onClick={() => {}} />
          </div>
          <div className={s.workspace__section}>
            <div className={s['empty-state']}>
              <Phone size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
              <div>שמור את הנבחן כדי לנהל רישומים/הגשות/גביה</div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={s.workspace}>
      <div className={s.workspace__sidebar}>
        <div className={s.workspace__header}>
          <BackButton onClick={onClose} label="חזרה לנבחנים" />
          <div className={s.workspace__title}>
            <span>{examinee!.full_name || `נבחן #${examinee!.id}`}</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {onDelete && (
            <button
              className={`${s.btn} ${s['btn-danger']} ${s['btn-sm']}`}
              onClick={onDelete}
              style={{ background: 'var(--color-danger, #dc2626)', color: 'white' }}
            >
              <Trash2 size={14} /> מחק נבחן
            </button>
          )}
        </div>

        <CollapsibleSection id="edit-contact" title="פרטי נבחן">
          <div className={s['field-grid']}>
            <EditableField label="שם" value={examinee!.full_name} onSave={v => saveField('full_name', v)} />
            <EditableField label="טלפון" value={examinee!.phone} dir="ltr" onSave={v => saveField('phone', v)} />
            <EditableField label='ת"ז' value={examinee!.id_number} dir="ltr" onSave={v => saveField('id_number', v)} />
            <EditableField label="אימייל" value={examinee!.email} dir="ltr" onSave={v => saveField('email', v)} />
          </div>
          <div className={`${s['field-grid']} ${s['field-grid--single']}`}>
            <EditableField
              label="מקור"
              value={examinee!.source || null}
              type="select"
              options={SOURCE_OPTIONS}
              onSave={v => saveField('source', v)}
            />
            <EditableField
              label="תלמיד #"
              value={examinee!.student_id}
              dir="ltr"
              onSave={v => {
                const raw = v === null || v === undefined || v === '' ? null : Number(v)
                return saveField('student_id', raw)
              }}
            />
          </div>
        </CollapsibleSection>

        <div style={{
          marginTop: 'auto',
          paddingTop: 16,
          borderTop: '1px solid var(--color-border-light)',
          fontSize: 11,
          color: 'var(--color-text-muted)',
        }}>
          {examinee!.created_at && <div>נוצר: {formatDateTime(examinee!.created_at)}</div>}
          {examinee!.updated_at && <div>עודכן: {formatDateTime(examinee!.updated_at)}</div>}
        </div>
      </div>

      <div className={s.workspace__main}>
        <div className={s.tabs}>
          <TabButton
            active={activeTab === 'history'}
            onClick={() => setActiveTab('history')}
            icon={<History size={14} />}
            label="היסטוריה"
          />
          <TabButton
            active={activeTab === 'registrations'}
            onClick={() => setActiveTab('registrations')}
            icon={<ClipboardList size={14} />}
            label="רישום למבחנים"
          />
          <TabButton
            active={activeTab === 'submissions'}
            onClick={() => setActiveTab('submissions')}
            icon={<FileCheck2 size={14} />}
            label="הגשות ותוצאות"
          />
          <TabButton
            active={activeTab === 'collections'}
            onClick={() => setActiveTab('collections')}
            icon={<CreditCard size={14} />}
            label="גביה"
          />
        </div>

        <div className={s.workspace__section}>
          {activeTab === 'history' && (
            <HistoryTab examineeId={examinee!.id} />
          )}
          {activeTab === 'registrations' && (
            <RegistrationsTab
              examineeId={examinee!.id}
              onRegistered={() => {
                setActiveTab('submissions')
              }}
            />
          )}
          {activeTab === 'submissions' && (
            <SubmissionsTab examineeId={examinee!.id} />
          )}
          {activeTab === 'collections' && (
            examinee!.student_id
              ? <CollectionsTab studentId={examinee!.student_id} />
              : <EmptyState title="אין תלמיד משויך — לא ניתן להציג גביה" />
          )}
        </div>
      </div>
    </div>
  )
}
