import { useEffect, useState, useCallback } from 'react'
import { Check, Package, Clock, History } from 'lucide-react'
import { api } from '@/lib/api'
import { formatDate } from '@/lib/status'
import { useToast } from '@/components/ui/Toast'
import { DataTable, type Column } from '@/components/ui/DataTable'
import s from '@/styles/shared.module.css'

interface Delivery {
  id: number
  lead_id: number
  full_name: string
  address: string | null
  city: string | null
  phone: string
  email: string | null
  is_sent: boolean
  sent_date: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

/* ── Deliveries Page ── */
export function DeliveriesPage() {
  const toast = useToast()
  const [pendingDeliveries, setPendingDeliveries] = useState<Delivery[]>([])
  const [historyDeliveries, setHistoryDeliveries] = useState<Delivery[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'pending' | 'history'>('pending')

  const fetchDeliveries = useCallback(async () => {
    setLoading(true)
    try {
      const [pending, history] = await Promise.all([
        api.get<Delivery[]>('deliveries/pending'),
        api.get<Delivery[]>('deliveries/history')
      ])
      setPendingDeliveries(pending)
      setHistoryDeliveries(history)
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בטעינת משלומים')
    } finally {
      setLoading(false)
    }
  }, [toast])

  useEffect(() => { fetchDeliveries() }, [fetchDeliveries])

  const handleMarkSent = async (deliveryId: number) => {
    if (!confirm('לסמן משלוך זה כנשלח?')) return
    try {
      await api.put(`deliveries/${deliveryId}/mark-sent`)
      toast.success('המשלוך סומן כנשלח')
      fetchDeliveries()
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה')
    }
  }

  const handleAutoCreate = async () => {
    try {
      const result = await api.post('deliveries/auto-create')
      toast.success(`נוצרו ${result.created_count} משלומים חדשים`)
      fetchDeliveries()
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה')
    }
  }

  const pendingColumns: Column<Delivery>[] = [
    { key: 'full_name', header: 'שם מלא' },
    { key: 'address', header: 'כתובת', render: r => r.address || '—' },
    { key: 'city', header: 'עיר', render: r => r.city || '—' },
    { key: 'phone', header: 'טלפון', render: r => r.phone },
    { key: 'email', header: 'מייל', render: r => r.email || '—' },
    {
      key: 'created_at',
      header: 'נוצר בתאריך',
      render: r => formatDate(r.created_at)
    },
    {
      key: 'actions',
      header: 'פעולות',
      render: r => (
        <button
          className={`${s.btn} ${s['btn-sm']} ${s['btn-primary']}`}
          onClick={() => handleMarkSent(r.id)}
        >
          <Check size={16} />
          סמן כנשלח
        </button>
      )
    }
  ]

  const historyColumns: Column<Delivery>[] = [
    { key: 'full_name', header: 'שם מלא' },
    { key: 'address', header: 'כתובת', render: r => r.address || '—' },
    { key: 'city', header: 'עיר', render: r => r.city || '—' },
    { key: 'phone', header: 'טלפון', render: r => r.phone },
    { key: 'email', header: 'מייל', render: r => r.email || '—' },
    {
      key: 'sent_date',
      header: 'תאריך שליחה',
      render: r => r.sent_date ? formatDate(r.sent_date) : '—'
    },
    {
      key: 'created_at',
      header: 'נוצר בתאריך',
      render: r => formatDate(r.created_at)
    }
  ]

  if (loading) {
    return <div className={s.card}>טוען...</div>
  }

  return (
    <div className={s.card}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
          <Package size={24} />
          ניהול משלוחים
        </h1>
        <button
          className={`${s.btn} ${s['btn-secondary']}`}
          onClick={handleAutoCreate}
        >
          צור משלוחים אוטומטית מלידים "נסלק"
        </button>
      </div>

      <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
        <button
          className={`${s.btn} ${activeTab === 'pending' ? s['btn-primary'] : s['btn-secondary']}`}
          onClick={() => setActiveTab('pending')}
        >
          <Clock size={16} />
          ממתינים למשלוח ({pendingDeliveries.length})
        </button>
        <button
          className={`${s.btn} ${activeTab === 'history' ? s['btn-primary'] : s['btn-secondary']}`}
          onClick={() => setActiveTab('history')}
        >
          <History size={16} />
          היסטוריית משלוחים ({historyDeliveries.length})
        </button>
      </div>

      {activeTab === 'pending' ? (
        <>
          {pendingDeliveries.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#666' }}>
              אין משלוחים ממתינים
            </div>
          ) : (
            <DataTable
              data={pendingDeliveries}
              columns={pendingColumns}
              emptyMessage="אין משלוחים ממתינים"
            />
          )}
        </>
      ) : (
        <>
          {historyDeliveries.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#666' }}>
              אין היסטוריית משלוחים
            </div>
          ) : (
            <DataTable
              data={historyDeliveries}
              columns={historyColumns}
              emptyMessage="אין היסטוריית משלוחים"
            />
          )}
        </>
      )}
    </div>
  )
}
