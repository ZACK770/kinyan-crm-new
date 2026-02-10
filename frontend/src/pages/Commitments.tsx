import { useState } from 'react'
import { FileText, Search } from 'lucide-react'
import { api } from '@/lib/api'
import { getStatus, formatDate, formatCurrency } from '@/lib/status'
import { useToast } from '@/components/ui/Toast'
import { DataTable, type Column } from '@/components/ui/DataTable'
import type { Commitment } from '@/types'
import s from '@/styles/shared.module.css'

function Badge({ entity, value }: { entity: string; value?: string }) {
  const { label, color } = getStatus(entity, value)
  return <span className={`${s.badge} ${s[`badge-${color}`]}`}>{label}</span>
}

/* ══════════════════════════════════════════════════════════════
   Commitments Page
   ══════════════════════════════════════════════════════════════ */
export function CommitmentsPage() {
  const toast = useToast()

  const [commitments, setCommitments] = useState<Commitment[]>([])
  const [loading, setLoading] = useState(false)
  const [studentId, setStudentId] = useState('')

  const fetchCommitments = async (sid?: string) => {
    const id = sid ?? studentId
    if (!id) return
    setLoading(true)
    try {
      const data = await api.get<Commitment[]>(`finance/commitments/student/${id}`)
      setCommitments(data)
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה')
      setCommitments([])
    } finally {
      setLoading(false)
    }
  }

  const columns: Column<Commitment>[] = [
    { key: 'id', header: '#' },
    { key: 'total_amount', header: 'סה"כ', render: r => formatCurrency(r.total_amount) },
    { key: 'paid_amount', header: 'שולם', render: r => formatCurrency(r.paid_amount) },
    { key: 'remaining', header: 'יתרה', render: r => formatCurrency(r.remaining) },
    { key: 'installments', header: 'תשלומים', render: r => r.installments ?? '—' },
    { key: 'status', header: 'סטטוס', render: r => <Badge entity="commitment" value={r.status} /> },
    { key: 'start_date', header: 'התחלה', render: r => formatDate(r.start_date), className: s.muted },
  ]

  return (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>התחייבויות</h1>
      </div>

      <div className={s.card}>
        <div className={s.toolbar}>
          <div style={{ display: 'flex', gap: 4, maxWidth: 300 }}>
            <input
              className={`${s.input} ${s['input-sm']}`}
              placeholder="מזהה תלמיד..."
              value={studentId}
              onChange={e => setStudentId(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && fetchCommitments()}
              dir="ltr"
              style={{ flex: 1 }}
            />
            <button className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`} onClick={() => fetchCommitments()}>
              <Search size={14} strokeWidth={1.5} />
            </button>
          </div>
        </div>

        {!studentId && !commitments.length && !loading ? (
          <div className={s.empty}>
            <span className={s['empty-icon']}><FileText size={40} strokeWidth={1.5} /></span>
            <span className={s['empty-text']}>הזן מזהה תלמיד כדי לצפות בהתחייבויות</span>
          </div>
        ) : (
          <DataTable
            columns={columns}
            data={commitments}
            loading={loading}
            emptyText="אין התחייבויות"
            emptyIcon={<FileText size={40} strokeWidth={1.5} />}
            keyExtractor={r => r.id}
          />
        )}
      </div>
    </div>
  )
}
