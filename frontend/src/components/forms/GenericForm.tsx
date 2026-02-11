/**
 * Generic Form Component
 * Renders a form based on schema definition with entity-linked dropdowns
 */
import { useState, type FormEvent, type ChangeEvent, useMemo } from 'react'
import { Plus } from 'lucide-react'
import { useEntityData } from '@/hooks/useEntityData'
import type { EntityFormSchema, FormField, FormSection } from './formSchemas'
import { buildInitialState, entityRefRoutes } from './formSchemas'
import s from '@/styles/shared.module.css'

interface GenericFormProps {
  schema: EntityFormSchema
  initial?: Record<string, unknown>
  onSubmit: (data: Record<string, unknown>) => void | Promise<void>
  isEdit?: boolean
  loading?: boolean
}

export function GenericForm({ schema, initial, onSubmit, isEdit = false, loading = false }: GenericFormProps) {
  const { courses, campaigns, salespeople, loading: refLoading } = useEntityData()
  const [form, setForm] = useState(() => buildInitialState(schema, initial))
  const [submitting, setSubmitting] = useState(false)

  // Get entity options for dropdowns
  const entityOptions = useMemo(() => ({
    courses: courses.map(c => ({ value: String(c.id), label: c.name })),
    campaigns: campaigns.map(c => ({ value: String(c.id), label: c.name })),
    salespeople: salespeople.map(sp => ({ value: String(sp.id), label: sp.name })),
  }), [courses, campaigns, salespeople])

  // Get selected course price (for display)
  const selectedCourse = useMemo(() => {
    const courseId = form.course_id as number | undefined
    if (!courseId) return null
    return courses.find(c => c.id === courseId) ?? null
  }, [courses, form.course_id])

  const handleChange = (key: string, type: string) => (
    e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    let value: unknown = e.target.value
    
    if (type === 'boolean') {
      value = (e.target as HTMLInputElement).checked
    } else if (type === 'number' || type === 'entity-select') {
      const strVal = e.target.value
      value = strVal ? Number(strVal) : null
    } else if (type === 'currency') {
      const numVal = parseFloat(e.target.value)
      value = isNaN(numVal) ? '' : numVal
    }
    
    setForm(prev => ({ ...prev, [key]: value }))
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    
    try {
      // Clean data before submit
      const data: Record<string, unknown> = {}
      for (const [key, value] of Object.entries(form)) {
        if (value !== '' && value !== null && value !== undefined) {
          data[key] = value
        }
      }
      await onSubmit(data)
    } finally {
      setSubmitting(false)
    }
  }

  const renderField = (field: FormField) => {
    const value = form[field.key]
    
    switch (field.type) {
      case 'text':
      case 'email':
      case 'tel':
        return (
          <input
            className={s.input}
            type={field.type === 'tel' ? 'tel' : field.type}
            value={String(value ?? '')}
            onChange={handleChange(field.key, field.type)}
            required={field.required}
            placeholder={field.placeholder}
            dir={field.dir}
          />
        )
        
      case 'number':
        return (
          <input
            className={s.input}
            type="number"
            value={String(value ?? '')}
            onChange={handleChange(field.key, field.type)}
            required={field.required}
            dir="ltr"
          />
        )
        
      case 'currency':
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <input
              className={s.input}
              type="number"
              step="0.01"
              value={String(value ?? '')}
              onChange={handleChange(field.key, field.type)}
              required={field.required}
              dir="ltr"
              style={{ flex: 1 }}
            />
            <span style={{ color: 'var(--text-muted)' }}>₪</span>
          </div>
        )
        
      case 'date':
        return (
          <input
            className={s.input}
            type="date"
            value={String(value ?? '')}
            onChange={handleChange(field.key, field.type)}
            required={field.required}
            dir="ltr"
          />
        )
        
      case 'textarea':
        return (
          <textarea
            className={s.textarea}
            value={String(value ?? '')}
            onChange={handleChange(field.key, field.type)}
            required={field.required}
            rows={3}
          />
        )
        
      case 'boolean':
        return (
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={Boolean(value)}
              onChange={handleChange(field.key, field.type)}
            />
            <span>{field.label}</span>
          </label>
        )
        
      case 'select':
        return (
          <select
            className={s.select}
            value={String(value ?? '')}
            onChange={handleChange(field.key, field.type)}
            required={field.required}
          >
            <option value="">— בחר —</option>
            {field.options?.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        )
        
      case 'entity-select':
        const options = field.entityRef ? entityOptions[field.entityRef] : []
        const createRoute = field.entityRef ? entityRefRoutes[field.entityRef] : null
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <select
              className={s.select}
              value={String(value ?? '')}
              onChange={handleChange(field.key, field.type)}
              required={field.required}
              disabled={refLoading}
              style={{ flex: 1 }}
            >
              <option value="">— {refLoading ? 'טוען...' : 'בחר'} —</option>
              {options.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            {createRoute && (
              <button
                type="button"
                className={`${s.btn} ${s['btn-icon']} ${s['btn-ghost']}`}
                title="צור חדש"
                onClick={() => window.open(`${createRoute}?create=true`, '_blank')}
                style={{ flexShrink: 0, padding: 6 }}
              >
                <Plus size={16} />
              </button>
            )}
          </div>
        )
        
      default:
        return null
    }
  }

  const renderSection = (section: FormSection, idx: number) => {
    // Group fields into rows (halfWidth = 2 per row)
    const rows: FormField[][] = []
    let currentRow: FormField[] = []
    
    for (const field of section.fields) {
      if (field.halfWidth) {
        currentRow.push(field)
        if (currentRow.length === 2) {
          rows.push(currentRow)
          currentRow = []
        }
      } else {
        if (currentRow.length > 0) {
          rows.push(currentRow)
          currentRow = []
        }
        rows.push([field])
      }
    }
    if (currentRow.length > 0) {
      rows.push(currentRow)
    }

    return (
      <div key={idx} style={{ marginBottom: 20 }}>
        {section.title && (
          <h4 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)' }}>
            {section.title}
          </h4>
        )}
        {rows.map((rowFields, rowIdx) => (
          <div 
            key={rowIdx} 
            className={rowFields.length > 1 ? s['form-row'] : undefined}
            style={rowFields.length === 1 ? { marginBottom: 16 } : undefined}
          >
            {rowFields.map(field => (
              <div key={field.key} className={s['form-group']}>
                {field.type !== 'boolean' && (
                  <label className={s['form-label']}>
                    {field.label}{field.required && ' *'}
                  </label>
                )}
                {renderField(field)}
              </div>
            ))}
          </div>
        ))}
      </div>
    )
  }

  const isFormLoading = loading || submitting || refLoading

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {schema.sections.map(renderSection)}
      
      {/* Show course price if course selected */}
      {selectedCourse && 'price' in selectedCourse && (
        <div className={s['detail-row']} style={{ background: 'var(--bg-accent)', padding: '8px 12px', borderRadius: 6 }}>
          <span className={s['detail-key']}>מחיר הקורס</span>
          <span className={s['detail-value']} style={{ fontWeight: 600 }}>
            ₪{(selectedCourse as { price?: number }).price?.toLocaleString() ?? '—'}
          </span>
        </div>
      )}
      
      <div style={{ display: 'flex', justifyContent: 'flex-start', gap: 8, paddingTop: 12 }}>
        <button 
          type="submit" 
          className={`${s.btn} ${s['btn-primary']}`}
          disabled={isFormLoading}
        >
          {isFormLoading ? 'שומר...' : (isEdit ? schema.editSubmitLabel : schema.submitLabel)}
        </button>
      </div>
    </form>
  )
}
