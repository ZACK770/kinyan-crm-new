import { useEffect, useState, useCallback, type FormEvent } from 'react'
import { Megaphone, Plus, Pencil, Eye } from 'lucide-react'
import { api } from '@/lib/api'
import { formatDate } from '@/lib/status'
import { useModal } from '@/components/ui/Modal'
import { useToast } from '@/components/ui/Toast'
import { DataTable, type Column } from '@/components/ui/DataTable'
import type { Campaign, Course } from '@/types'
import s from '@/styles/shared.module.css'

/* ── Campaign Form ── */
function CampaignForm({
  initial,
  courses,
  onSubmit,
}: {
  initial?: Partial<Campaign>
  courses: Course[]
  onSubmit: (data: Record<string, unknown>) => void
}) {
  const [form, setForm] = useState({
    name: initial?.name ?? '',
    course_id: initial?.course_id ?? '',
    platforms: initial?.platforms ?? '',
    start_date: initial?.start_date?.split('T')[0] ?? '',
    end_date: initial?.end_date?.split('T')[0] ?? '',
    is_active: initial?.is_active ?? true,
  })

  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [key]: e.target.type === 'checkbox' ? (e.target as HTMLInputElement).checked : e.target.value }))

  const handle = (e: FormEvent) => {
    e.preventDefault()
    const data: Record<string, unknown> = { ...form }
    if (data.course_id) data.course_id = Number(data.course_id)
    else delete data.course_id
    Object.keys(data).forEach(k => { if (data[k] === '') delete data[k] })
    onSubmit(data)
  }

  return (
    <form onSubmit={handle} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className={s['form-group']}>
        <label className={s['form-label']}>שם הקמפיין *</label>
        <input className={s.input} value={form.name} onChange={set('name')} required />
      </div>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>קורס</label>
          <select className={s.select} value={form.course_id} onChange={set('course_id')}>
            <option value="">— בחר קורס —</option>
            {courses.map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>פלטפורמות</label>
          <input className={s.input} value={form.platforms} onChange={set('platforms')} placeholder="פייסבוק, גוגל..." />
        </div>
      </div>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>תאריך התחלה</label>
          <input className={s.input} type="date" value={form.start_date} onChange={set('start_date')} dir="ltr" />
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>תאריך סיום</label>
          <input className={s.input} type="date" value={form.end_date} onChange={set('end_date')} dir="ltr" />
        </div>
      </div>
      <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
        <input type="checkbox" checked={form.is_active} onChange={set('is_active')} />
        <span>פעיל</span>
      </label>
      <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>
        {initial?.id ? 'עדכן' : 'צור קמפיין'}
      </button>
    </form>
  )
}

/* ══════════════════════════════════════════════════════════════
   Campaigns Page
   ══════════════════════════════════════════════════════════════ */
export function CampaignsPage() {
  const { openModal, closeModal } = useModal()
  const toast = useToast()

  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [courses, setCourses] = useState<Course[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<Course[]>('courses').catch(() => []).then(setCourses)
  }, [])

  const fetchCampaigns = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get<Campaign[]>('campaigns')
      setCampaigns(data)
    } catch {
      setCampaigns([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchCampaigns() }, [fetchCampaigns])

  /* ── Create ── */
  const openCreate = () => {
    openModal({
      title: 'קמפיין חדש',
      size: 'md',
      content: (
        <CampaignForm
          courses={courses}
          onSubmit={async data => {
            try {
              await api.post('campaigns', data)
              toast.success('קמפיין נוצר בהצלחה')
              closeModal()
              fetchCampaigns()
            } catch (err: unknown) {
              toast.error((err as { message?: string }).message ?? 'שגיאה')
            }
          }}
        />
      ),
    })
  }

  /* ── Edit ── */
  const openEdit = (campaign: Campaign) => {
    openModal({
      title: `עריכת קמפיין — ${campaign.name}`,
      size: 'md',
      content: (
        <CampaignForm
          initial={campaign}
          courses={courses}
          onSubmit={async data => {
            try {
              await api.patch(`campaigns/${campaign.id}`, data)
              toast.success('קמפיין עודכן')
              closeModal()
              fetchCampaigns()
            } catch (err: unknown) {
              toast.error((err as { message?: string }).message ?? 'שגיאה')
            }
          }}
        />
      ),
    })
  }

  const columns: Column<Campaign>[] = [
    { key: 'name', header: 'שם הקמפיין' },
    { key: 'platforms', header: 'פלטפורמות', render: r => r.platforms ?? '—' },
    {
      key: 'is_active',
      header: 'סטטוס',
      render: r => (
        <span className={`${s.badge} ${r.is_active ? s['badge-green'] : s['badge-gray']}`}>
          {r.is_active ? 'פעיל' : 'לא פעיל'}
        </span>
      ),
    },
    { key: 'start_date', header: 'התחלה', render: r => formatDate(r.start_date), className: s.muted },
    { key: 'end_date', header: 'סיום', render: r => formatDate(r.end_date), className: s.muted },
    {
      key: '_actions',
      header: '',
      render: r => (
        <button className={`${s.btn} ${s['btn-ghost']} ${s['btn-xs']}`} onClick={e => { e.stopPropagation(); openEdit(r) }} title="עריכה">
          <Pencil size={14} strokeWidth={1.5} />
        </button>
      ),
    },
  ]

  return (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>קמפיינים</h1>
        <button className={`${s.btn} ${s['btn-primary']}`} onClick={openCreate}>
          <Plus size={16} strokeWidth={1.5} /> קמפיין חדש
        </button>
      </div>
      <div className={s.card}>
        <DataTable
          columns={columns}
          data={campaigns}
          loading={loading}
          emptyText="אין קמפיינים"
          emptyIcon={<Megaphone size={40} strokeWidth={1.5} />}
          keyExtractor={r => r.id}
        />
      </div>
    </div>
  )
}
