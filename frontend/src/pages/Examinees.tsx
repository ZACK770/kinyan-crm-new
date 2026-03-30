import { useEffect, useState, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Plus, Phone } from 'lucide-react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import { SmartTable, type SmartColumn } from '@/components/ui/SmartTable'
import { ExamineeWorkspace } from '@/components/examinees'
import type { Examinee } from '@/types'
import s from '@/styles/shared.module.css'

export function ExamineesPage() {
  const toast = useToast()

  const [examinees, setExaminees] = useState<Examinee[]>([])
  const [loading, setLoading] = useState(true)

  type ViewMode = 'list' | 'create'
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [selectedExaminee, setSelectedExaminee] = useState<Examinee | null>(null)
  const [loadingWorkspace, setLoadingWorkspace] = useState(false)
  const [searchParams, setSearchParams] = useSearchParams()

  useEffect(() => {
    if (searchParams.get('create') === 'true') {
      setViewMode('create')
      setSelectedExaminee(null)
      setSearchParams({}, { replace: true })
    } else if (searchParams.get('examinee')) {
      const examineeId = Number(searchParams.get('examinee'))
      if (examineeId && !isNaN(examineeId) && selectedExaminee?.id !== examineeId) {
        setLoadingWorkspace(true)
        api.get<Examinee>(`examinees/${examineeId}`)
          .then(ex => {
            setSelectedExaminee(ex)
            setViewMode('list')
          })
          .catch(() => {
            toast.error('נבחן לא נמצא')
            setSearchParams({}, { replace: true })
          })
          .finally(() => setLoadingWorkspace(false))
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams])

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

  const openCreate = () => {
    setSelectedExaminee(null)
    setViewMode('create')
  }

  const openExamineeWorkspace = async (row: Examinee) => {
    try {
      const full = await api.get<Examinee>(`examinees/${row.id}`)
      setSelectedExaminee(full)
      setViewMode('list')
      setSearchParams({ examinee: String(row.id) }, { replace: true })
    } catch {
      toast.error('שגיאה בטעינת פרטי נבחן')
    }
  }

  const backToList = () => {
    setSelectedExaminee(null)
    setViewMode('list')
    setSearchParams({}, { replace: true })
  }

  const refreshSelected = async () => {
    if (!selectedExaminee) return
    try {
      const fresh = await api.get<Examinee>(`examinees/${selectedExaminee.id}`)
      setSelectedExaminee(fresh)
    } catch {
      // ignore
    }
  }

  const handleDeleteOne = async (ex: Examinee) => {
    const shouldDelete = window.confirm(`האם אתה בטוח שברצונך למחוק את הנבחן ${ex.full_name || ex.phone}? פעולה זו בלתי הפיכה.`)
    if (!shouldDelete) return
    try {
      await api.delete(`examinees/${ex.id}`)
      toast.success('נבחן נמחק בהצלחה')
      fetchExaminees()
      if (selectedExaminee?.id === ex.id) backToList()
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה במחיקה')
    }
  }

  const handleCreated = async (newEx: Examinee) => {
    fetchExaminees()
    setSelectedExaminee(newEx)
    setViewMode('list')
    setSearchParams({ examinee: String(newEx.id) }, { replace: true })
  }

  const serverSearch = useCallback(async (query: string): Promise<Examinee[]> => {
    const results = await api.get<Examinee[]>(`examinees?search=${encodeURIComponent(query)}&limit=20`)
    return results
  }, [])

  useEffect(() => {
    fetchExaminees()
  }, [fetchExaminees])

  if (viewMode === 'create') {
    return (
      <ExamineeWorkspace
        examinee={null}
        onClose={backToList}
        onUpdate={() => {}}
        onCreate={handleCreated}
      />
    )
  }

  if (selectedExaminee) {
    return (
      <ExamineeWorkspace
        examinee={selectedExaminee}
        onClose={backToList}
        onUpdate={refreshSelected}
        onDelete={() => handleDeleteOne(selectedExaminee)}
      />
    )
  }

  if (loadingWorkspace) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 80, color: 'var(--color-text-muted)' }}>
        טוען מרחב עבודה...
      </div>
    )
  }

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
            onClick={openCreate}
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
          onRowClick={openExamineeWorkspace}
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
