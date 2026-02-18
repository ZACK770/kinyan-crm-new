import { useState, useEffect, useCallback, type FormEvent } from 'react'
import { UserCheck, Plus } from 'lucide-react'
import { BackButton } from '@/components/ui/BackButton'
import { api } from '@/lib/api'
import { formatDate } from '@/lib/status'
import { useToast } from '@/components/ui/Toast'
import { SmartTable, type SmartColumn } from '@/components/ui/SmartTable'
import s from '@/styles/shared.module.css'

/* ══════════════════════════════════════════════════════════════
   Lecturers Page — ניהול מרצים
   ══════════════════════════════════════════════════════════════ */

interface Lecturer {
  id: number
  name: string
  specialty?: string
  phone?: string
  email?: string
  notes?: string
  created_at?: string
}

/* ── Lecturer Form ── */
function LecturerForm({ initial, onSubmit, onCancel }: {
  initial?: Partial<Lecturer>
  onSubmit: (data: Record<string, unknown>) => void
  onCancel?: () => void
}) {
  const [form, setForm] = useState({
    name: initial?.name ?? '',
    specialty: initial?.specialty ?? '',
    phone: initial?.phone ?? '',
    email: initial?.email ?? '',
    notes: initial?.notes ?? '',
  })
  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [key]: e.target.value }))

  const handle = (e: FormEvent) => {
    e.preventDefault()
    onSubmit(form)
  }

  return (
    <form onSubmit={handle} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className={s['form-group']}>
        <label className={s['form-label']}>שם מרצה *</label>
        <input className={s.input} value={form.name} onChange={set('name')} required placeholder="שם מלא" />
      </div>
      <div className={s['form-group']}>
        <label className={s['form-label']}>התמחות</label>
        <input className={s.input} value={form.specialty} onChange={set('specialty')} placeholder="תחום התמחות" />
      </div>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>טלפון</label>
          <input className={s.input} type="tel" value={form.phone} onChange={set('phone')} placeholder="050-1234567" />
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>אימייל</label>
          <input className={s.input} type="email" value={form.email} onChange={set('email')} placeholder="email@example.com" />
        </div>
      </div>
      <div className={s['form-group']}>
        <label className={s['form-label']}>הערות</label>
        <textarea className={s.textarea} value={form.notes} onChange={set('notes')} rows={3} />
      </div>
      <div style={{ display: 'flex', gap: 8, paddingTop: 8 }}>
        <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>
          {initial?.id ? 'עדכן' : 'צור מרצה'}
        </button>
        {onCancel && (
          <button type="button" className={`${s.btn} ${s['btn-secondary']}`} onClick={onCancel}>ביטול</button>
        )}
      </div>
    </form>
  )
}

export function LecturersPage() {
  const toast = useToast()
  const [lecturers, setLecturers] = useState<Lecturer[]>([])
  const [loading, setLoading] = useState(true)

  type ViewMode = 'list' | 'create' | 'edit'
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [selectedLecturer, setSelectedLecturer] = useState<Lecturer | null>(null)

  const backToList = () => { setSelectedLecturer(null); setViewMode('list') }

  const fetchLecturers = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get<Lecturer[]>('/lecturers')
      setLecturers(data)
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בטעינת מרצים')
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => { fetchLecturers() }, [fetchLecturers])

  const handleInlineUpdate = async (row: Lecturer, field: string, value: unknown) => {
    try {
      await api.patch(`/lecturers/${row.id}`, { [field]: value })
      setLecturers(prev => prev.map(l => l.id === row.id ? { ...l, [field]: value } : l))
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בעדכון')
      throw err
    }
  }

  const columns: SmartColumn<Lecturer>[] = [
    { key: 'id', header: '#', type: 'number', width: 60, editable: false },
    { key: 'name', header: 'שם', type: 'text' },
    { key: 'specialty', header: 'התמחות', type: 'text', renderView: r => r.specialty ?? '—' },
    { key: 'phone', header: 'טלפון', type: 'text', renderView: r => r.phone ?? '—' },
    { key: 'email', header: 'אימייל', type: 'text', renderView: r => r.email ?? '—' },
    { key: 'notes', header: 'הערות', type: 'text', hiddenByDefault: true, renderView: r => r.notes ?? '—' },
    { key: 'created_at', header: 'נוצר', type: 'date', editable: false, renderView: r => formatDate(r.created_at), className: s.muted },
  ]

  if (viewMode === 'create' || (viewMode === 'edit' && selectedLecturer)) {
    return (
      <div>
        <div className={s['page-header']}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <BackButton onClick={backToList} label="חזרה למרצים" />
            <h1 className={s['page-title']} style={{ fontSize: '1.2rem' }}>
              {selectedLecturer ? `עריכת מרצה — ${selectedLecturer.name}` : 'מרצה חדש'}
            </h1>
          </div>
        </div>
        <div className={s.card} style={{ padding: 24, maxWidth: 600 }}>
          <LecturerForm
            initial={selectedLecturer ?? undefined}
            onSubmit={async data => {
              try {
                if (selectedLecturer) {
                  await api.patch(`/lecturers/${selectedLecturer.id}`, data)
                  toast.success('מרצה עודכן')
                } else {
                  await api.post('/lecturers', data)
                  toast.success('מרצה נוצר בהצלחה')
                }
                fetchLecturers()
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
        <h1 className={s['page-title']}>מרצים</h1>
        <button className={`${s.btn} ${s['btn-primary']}`} onClick={() => setViewMode('create')}>
          <Plus size={16} strokeWidth={1.5} /> מרצה חדש
        </button>
      </div>

      <div className={s.card}>
        <SmartTable
          columns={columns}
          data={lecturers}
          loading={loading}
          emptyText="אין מרצים"
          emptyIcon={<UserCheck size={40} strokeWidth={1.5} />}
          keyExtractor={r => r.id}
          storageKey="lecturers_table"
          onUpdate={handleInlineUpdate}
          onRowClick={r => { setSelectedLecturer(r); setViewMode('edit') }}
          searchFields={[
            { key: 'name', label: 'שם', weight: 3 },
            { key: 'specialty', label: 'התמחות', weight: 2 },
            { key: 'phone', label: 'טלפון', weight: 1 },
            { key: 'email', label: 'אימייל', weight: 1 },
          ]}
          searchPlaceholder="חיפוש מרצים..."
        />
      </div>
    </div>
  )
}
