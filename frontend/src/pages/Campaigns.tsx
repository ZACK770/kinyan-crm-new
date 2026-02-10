import { useEffect, useState, useCallback } from 'react'
import { Megaphone } from 'lucide-react'
import { api } from '@/lib/api'
import { formatDate } from '@/lib/status'
import { DataTable, type Column } from '@/components/ui/DataTable'
import type { Campaign } from '@/types'
import s from '@/styles/shared.module.css'

/* ══════════════════════════════════════════════════════════════
   Campaigns Page
   ══════════════════════════════════════════════════════════════ */
export function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)

  const fetchCampaigns = useCallback(async () => {
    setLoading(true)
    try {
      // Try fetching campaigns — endpoint may not exist yet
      const data = await api.get<Campaign[]>('leads/campaigns').catch(() => [] as Campaign[])
      setCampaigns(data)
    } catch {
      setCampaigns([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchCampaigns() }, [fetchCampaigns])

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
  ]

  return (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>קמפיינים</h1>
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
