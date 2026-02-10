import { useState, type FormEvent } from 'react'
import { X, Save, BookOpen } from 'lucide-react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import { EditableField } from '@/components/ui/EditableField'
import type { Course, CourseModule } from '@/types'
import { formatDate } from '@/lib/status'
import s from '@/styles/shared.module.css'

/* ══════════════════════════════════════════════════════════════
   Course Workspace — Full workspace view for course management
   ═══════════════════════════════════════════════════════════════
   Supports both CREATE and EDIT modes:
   - CREATE: course is null, shows form with fields
   - EDIT: course is provided, inline editable fields (auto-save on blur)
   
   Unified view for consistency with LeadWorkspace
   ══════════════════════════════════════════════════════════════ */

interface CourseWorkspaceProps {
  course?: Course | null
  onClose: () => void
  onUpdate: () => void
  onCreate?: (course: Course) => void
}

const EMPTY_FORM = {
  name: '',
  description: '',
  semester: '',
  total_sessions: '',
  start_date: '',
  end_date: '',
  price: '',
  payments_count: '1',
  is_active: true,
}

export function CourseWorkspace({
  course,
  onClose,
  onUpdate,
  onCreate,
}: CourseWorkspaceProps) {
  const isCreateMode = !course
  const toast = useToast()
  const [isSaving, setIsSaving] = useState(false)
  
  // Create mode: form state
  const [formData, setFormData] = useState(EMPTY_FORM)
  
  // Edit mode: modules data
  const [modules, setModules] = useState<CourseModule[]>([])
  const [modulesLoaded, setModulesLoaded] = useState(false)

  // Load modules for edit mode
  useState(() => {
    if (course?.id && !modulesLoaded) {
      api.get<Course & { modules?: CourseModule[] }>(`courses/${course.id}`)
        .then(full => {
          setModules(full.modules || [])
          setModulesLoaded(true)
        })
        .catch(() => {})
    }
  })

  /* ── CREATE MODE: Form handlers ── */
  const setField = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setFormData(prev => ({ 
      ...prev, 
      [key]: e.target.type === 'checkbox' ? (e.target as HTMLInputElement).checked : e.target.value 
    }))

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault()
    setIsSaving(true)
    try {
      const data: Record<string, unknown> = { ...formData }
      if (data.total_sessions) data.total_sessions = Number(data.total_sessions)
      else delete data.total_sessions
      if (data.price) data.price = Number(data.price)
      else delete data.price
      if (data.payments_count) data.payments_count = Number(data.payments_count)
      else delete data.payments_count
      Object.keys(data).forEach(k => { if (data[k] === '') delete data[k] })
      
      const created = await api.post<Course>('courses', data)
      toast.success('קורס נוצר בהצלחה')
      onCreate?.(created)
      onClose()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'שגיאה ביצירת קורס'
      toast.error(message)
    } finally {
      setIsSaving(false)
    }
  }

  /* ── EDIT MODE: Inline edit handlers ── */
  const handleInlineEdit = async (field: string, value: unknown) => {
    if (!course) return
    
    try {
      await api.patch(`courses/${course.id}`, { [field]: value })
      toast.success('שדה עודכן')
      onUpdate()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'שגיאה בעדכון'
      toast.error(message)
    }
  }

  /* ── RENDER: CREATE MODE ── */
  if (isCreateMode) {
    return (
      <div className={s.workspace}>
        <div className={s['workspace-header']}>
          <h2 className={s['workspace-title']}>
            <BookOpen size={20} />
            קורס חדש
          </h2>
          <button className={`${s.btn} ${s['btn-ghost']}`} onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className={s['workspace-body']}>
          <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Basic Info */}
            <div className={s['form-section']}>
              <h3 className={s['section-title']}>פרטים בסיסיים</h3>
              
              <div className={s['form-group']}>
                <label className={s['form-label']}>שם הקורס *</label>
                <input 
                  className={s.input} 
                  value={formData.name} 
                  onChange={setField('name')} 
                  required 
                  placeholder="לדוגמה: איסור והיתר"
                />
              </div>

              <div className={s['form-group']}>
                <label className={s['form-label']}>תיאור</label>
                <textarea 
                  className={s.textarea} 
                  value={formData.description} 
                  onChange={setField('description')} 
                  rows={3}
                  placeholder="תיאור כללי של הקורס"
                />
              </div>

              <div className={s['form-row']}>
                <div className={s['form-group']}>
                  <label className={s['form-label']}>סמסטר</label>
                  <input 
                    className={s.input} 
                    value={formData.semester} 
                    onChange={setField('semester')}
                    placeholder="לדוגמה: סמסטר א׳ תשפ״ה"
                  />
                </div>
                <div className={s['form-group']}>
                  <label className={s['form-label']}>סה"כ שיעורים</label>
                  <input 
                    className={s.input} 
                    type="number" 
                    value={formData.total_sessions} 
                    onChange={setField('total_sessions')} 
                    dir="ltr"
                    placeholder="0"
                  />
                </div>
              </div>
            </div>

            {/* Pricing */}
            <div className={s['form-section']}>
              <h3 className={s['section-title']}>תמחור</h3>
              
              <div className={s['form-row']}>
                <div className={s['form-group']}>
                  <label className={s['form-label']}>מחיר (₪)</label>
                  <input 
                    className={s.input} 
                    type="number" 
                    step="0.01"
                    value={formData.price} 
                    onChange={setField('price')} 
                    dir="ltr"
                    placeholder="0.00"
                  />
                </div>
                <div className={s['form-group']}>
                  <label className={s['form-label']}>מספר תשלומים</label>
                  <input 
                    className={s.input} 
                    type="number" 
                    min="1"
                    value={formData.payments_count} 
                    onChange={setField('payments_count')} 
                    dir="ltr"
                  />
                </div>
              </div>
            </div>

            {/* Dates */}
            <div className={s['form-section']}>
              <h3 className={s['section-title']}>תאריכים</h3>
              
              <div className={s['form-row']}>
                <div className={s['form-group']}>
                  <label className={s['form-label']}>תאריך התחלה</label>
                  <input 
                    className={s.input} 
                    type="date" 
                    value={formData.start_date} 
                    onChange={setField('start_date')} 
                    dir="ltr" 
                  />
                </div>
                <div className={s['form-group']}>
                  <label className={s['form-label']}>תאריך סיום</label>
                  <input 
                    className={s.input} 
                    type="date" 
                    value={formData.end_date} 
                    onChange={setField('end_date')} 
                    dir="ltr" 
                  />
                </div>
              </div>
            </div>

            {/* Status */}
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
              <input 
                type="checkbox" 
                checked={formData.is_active} 
                onChange={setField('is_active')} 
              />
              <span>קורס פעיל</span>
            </label>

            {/* Actions */}
            <div style={{ display: 'flex', gap: 8, paddingTop: 16, borderTop: '1px solid var(--border)' }}>
              <button 
                type="submit" 
                className={`${s.btn} ${s['btn-primary']}`}
                disabled={isSaving}
              >
                <Save size={16} />
                {isSaving ? 'שומר...' : 'צור קורס'}
              </button>
              <button 
                type="button" 
                className={`${s.btn} ${s['btn-secondary']}`} 
                onClick={onClose}
              >
                ביטול
              </button>
            </div>
          </form>
        </div>
      </div>
    )
  }

  /* ── RENDER: EDIT MODE ── */
  return (
    <div className={s.workspace}>
      <div className={s['workspace-header']}>
        <h2 className={s['workspace-title']}>
          <BookOpen size={20} />
          {course.name}
        </h2>
        <button className={`${s.btn} ${s['btn-ghost']}`} onClick={onClose}>
          <X size={18} />
        </button>
      </div>

      <div className={s['workspace-body']}>
        {/* Basic Info */}
        <div className={s['detail-section']}>
          <h3 className={s['section-title']}>פרטים בסיסיים</h3>
          
          <EditableField
            label="שם הקורס"
            value={course.name}
            onSave={val => handleInlineEdit('name', val)}
          />
          
          <EditableField
            label="תיאור"
            value={course.description || ''}
            onSave={val => handleInlineEdit('description', val)}
            type="textarea"
          />
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <EditableField
              label="סמסטר"
              value={course.semester || ''}
              onSave={val => handleInlineEdit('semester', val)}
            />
            
            <EditableField
              label="סה״כ שיעורים"
              value={String(course.total_sessions || '')}
              onSave={val => handleInlineEdit('total_sessions', val ? Number(val) : null)}
              dir="ltr"
            />
          </div>
        </div>

        {/* Pricing */}
        <div className={s['detail-section']}>
          <h3 className={s['section-title']}>תמחור</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <EditableField
              label="מחיר (₪)"
              value={String(course.price || '')}
              onSave={val => handleInlineEdit('price', val ? Number(val) : null)}
              dir="ltr"
            />
            
            <EditableField
              label="מספר תשלומים"
              value={String(course.payments_count || 1)}
              onSave={val => handleInlineEdit('payments_count', val ? Number(val) : 1)}
              dir="ltr"
            />
          </div>
        </div>

        {/* Dates */}
        <div className={s['detail-section']}>
          <h3 className={s['section-title']}>תאריכים</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <EditableField
              label="תאריך התחלה"
              value={course.start_date?.split('T')[0] || ''}
              onSave={val => handleInlineEdit('start_date', val)}
              dir="ltr"
            />
            
            <EditableField
              label="תאריך סיום"
              value={course.end_date?.split('T')[0] || ''}
              onSave={val => handleInlineEdit('end_date', val)}
              dir="ltr"
            />
          </div>
        </div>

        {/* Status */}
        <div className={s['detail-section']}>
          <h3 className={s['section-title']}>סטטוס</h3>
          
          <EditableField
            label="פעיל"
            value={course.is_active ? 'כן' : 'לא'}
            onSave={val => handleInlineEdit('is_active', val === 'כן')}
            type="select"
            options={[
              { value: 'כן', label: 'פעיל' },
              { value: 'לא', label: 'לא פעיל' },
            ]}
          />
        </div>

        {/* Modules */}
        {modulesLoaded && (
          <div className={s['detail-section']}>
            <h3 className={s['section-title']}>מודולים</h3>
            
            {modules.length > 0 ? (
              <div className={s['table-wrapper']}>
                <table className={s.table}>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>שם</th>
                      <th>מס׳ שיעורים</th>
                      <th>שעות</th>
                      <th>תאריך התחלה</th>
                      <th>שעות</th>
                    </tr>
                  </thead>
                  <tbody>
                    {modules
                      .sort((a, b) => a.module_order - b.module_order)
                      .map(m => (
                        <tr key={m.id}>
                          <td>{m.module_order}</td>
                          <td>{m.name}</td>
                          <td>{m.sessions_count ?? '—'}</td>
                          <td>{m.hours_estimate ?? '—'}</td>
                          <td className={s.muted}>{formatDate(m.start_date)}</td>
                          <td className={s.muted}>
                            {m.start_time && m.end_time ? `${m.start_time}–${m.end_time}` : '—'}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className={s['empty-state']}>
                <span className={s['empty-text']}>לא הוגדרו מודולים</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
