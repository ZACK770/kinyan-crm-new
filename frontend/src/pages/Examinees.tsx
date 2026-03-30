import { useEffect, useState, useCallback } from 'react'
import { Plus, Phone } from 'lucide-react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import { SmartTable, type SmartColumn } from '@/components/ui/SmartTable'
import type { Examinee } from '@/types'
import s from '@/styles/shared.module.css'

export function ExamineesPage() {
  const toast = useToast()

  const [examinees, setExaminees] = useState<Examinee[]>([])
  const [loading, setLoading] = useState(true)

  const columns: SmartColumn<Examinee>[] = [
    {
      key: 'id',
      header: 'ID',
      width: 80,
      sortable: true,
      type: 'number',
    },
    {
      key: 'full_name',
      header: 'שם',
      type: 'text',
      editable: true,
      sortable: true,
    },
    {
      key: 'phone',
      header: 'טלפון',
      type: 'text',
      editable: true,
      sortable: true,
    },
    {
      key: 'id_number',
      header: 'ת"ז',
      type: 'text',
      editable: true,
      sortable: true,
    },
    {
      key: 'email',
      header: 'אימייל',
      type: 'text',
      editable: true,
      sortable: true,
    },
    {
      key: 'source',
      header: 'מקור',
      type: 'text',
      editable: true,
      sortable: true,
    },
    {
      key: 'student_id',
      header: 'תלמיד #',
      type: 'number',
      editable: true,
      sortable: true,
    },
    {
      key: 'created_at',
      header: 'נוצר',
      type: 'date',
      sortable: true,
    },
    {
      key: 'updated_at',
      header: 'עודכן',
      type: 'date',
      sortable: true,
    },
  ]

  const fetchExaminees = useCallback(async () => {
    setLoading(true)
    try {
      const all: Examinee[] = []
      let offset = 0
      const batchSize = 1000
      while (true) {
        const batch = await api.get<Examinee[]>(`examinees?limit=${batchSize}&offset=${offset}`)
        all.push(...batch)
        if (batch.length < batchSize) break
        offset += batchSize
      }
      setExaminees(all)
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בטעינת נבחנים')
    } finally {
      setLoading(false)
    }
  }, [toast])

  const serverSearch = useCallback(async (query: string): Promise<Examinee[]> => {
    const results = await api.get<Examinee[]>(`examinees?search=${encodeURIComponent(query)}&limit=20`)
    return results
  }, [])

  useEffect(() => {
    fetchExaminees()
  }, [fetchExaminees])

  const handleInlineUpdate = async (row: Examinee, field: string, value: unknown) => {
    try {
      const payload: Record<string, unknown> = { [field]: value }
      const result = await api.patch<{ id: number; status: string; updated_at?: string }>(`examinees/${row.id}`, payload)
      toast.success('עודכן בהצלחה')
      const serverUpdates: Record<string, unknown> = { ...payload }
      if (result?.updated_at) serverUpdates.updated_at = result.updated_at
      setExaminees(prev => prev.map(p => p.id === row.id ? { ...p, ...serverUpdates } : p))
    } catch (err) {
      toast.error('שגיאה בעדכון')
      throw err
    }
  }

  const handleBulkUpdate = async (selected: Examinee[], field: string, value: unknown) => {
    try {
      const ids = selected.map(x => x.id)
      await api.post('examinees/bulk-update', { ids, field, value })
      toast.success(`עודכנו ${ids.length} נבחנים`)
      fetchExaminees()
    } catch {
      toast.error('שגיאה בעדכון מרובה')
    }
  }

  const handleBulkDelete = async (selected: Examinee[]) => {
    try {
      const ids = selected.map(x => x.id)
      await api.post('examinees/bulk-delete', { ids })
      toast.success(`נמחקו ${ids.length} נבחנים`)
      fetchExaminees()
    } catch {
      toast.error('שגיאה במחיקה')
    }
  }

  return (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>נבחנים</h1>
        <div className={s['page-actions']}>
          <button
            className={`${s.btn} ${s['btn-primary']}`}
            onClick={() => toast.info('בשלב זה יצירה נעשית דרך ה-DB / תהליך אוטומטי')}
          >
            <Plus size={16} strokeWidth={1.5} /> נבחן חדש
          </button>
        </div>
      </div>

      <div className={s.card}>
        <SmartTable
          columns={columns}
          data={examinees}
          loading={loading}
          emptyText="לא נמצאו נבחנים"
          emptyIcon={<Phone size={40} strokeWidth={1.5} />}
          onUpdate={handleInlineUpdate}
          onDelete={handleBulkDelete}
          onBulkUpdate={handleBulkUpdate}
          keyExtractor={(row) => row.id}
          storageKey="examinees_table_v1"
          searchPlaceholder='חיפוש נבחן לפי שם, טלפון, ת"ז, אימייל...'
          searchFields={[
            { key: 'full_name', label: 'שם', weight: 3 },
            { key: 'phone', label: 'טלפון', weight: 2 },
            { key: 'id_number', label: 'ת"ז', weight: 2 },
            { key: 'email', label: 'אימייל', weight: 1 },
            { key: 'source', label: 'מקור', weight: 1 },
          ]}
          onServerSearch={serverSearch}
          defaultPageSize={100}
          pageSizeOptions={[50, 100, 200]}
          bulkActions={[]}
        />
      </div>
    </div>
  )
}
