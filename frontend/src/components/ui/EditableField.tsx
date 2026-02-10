import { useState, useRef, useEffect, type ReactNode } from 'react'
import { Check, X, Pencil, Plus } from 'lucide-react'
import s from '@/styles/shared.module.css'

/* ══════════════════════════════════════════════════════════════
   EditableField — Click-to-edit inline field
   Supports: text, textarea, select, entity-select
   ══════════════════════════════════════════════════════════════ */

export type FieldType = 'text' | 'textarea' | 'select' | 'entity-select'

export interface SelectOption {
  value: string | number
  label: string
}

export interface EditableFieldProps {
  label: string
  value: string | number | null | undefined
  displayValue?: ReactNode // Custom display (e.g., badge, formatted date)
  type?: FieldType
  options?: SelectOption[]
  placeholder?: string
  dir?: 'rtl' | 'ltr'
  onSave: (value: string | number | null) => Promise<void> | void
  disabled?: boolean
  className?: string
  entityCreatePath?: string  // Route path to open in new tab for creating new entity
}

export function EditableField({
  label,
  value,
  displayValue,
  type = 'text',
  options = [],
  placeholder = '—',
  dir,
  onSave,
  disabled = false,
  className = '',
  entityCreatePath,
}: EditableFieldProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(String(value ?? ''))
  const [isSaving, setIsSaving] = useState(false)
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>(null)

  // Focus input when entering edit mode
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      if (inputRef.current instanceof HTMLInputElement || inputRef.current instanceof HTMLTextAreaElement) {
        inputRef.current.select()
      }
    }
  }, [isEditing])

  // Sync editValue when value changes externally
  useEffect(() => {
    if (!isEditing) {
      setEditValue(String(value ?? ''))
    }
  }, [value, isEditing])

  const startEditing = () => {
    if (disabled) return
    setEditValue(String(value ?? ''))
    setIsEditing(true)
  }

  const cancel = () => {
    setEditValue(String(value ?? ''))
    setIsEditing(false)
  }

  const save = async () => {
    if (editValue === String(value ?? '')) {
      setIsEditing(false)
      return
    }

    setIsSaving(true)
    try {
      // Convert to appropriate type
      let finalValue: string | number | null = editValue
      if (editValue === '' || editValue === undefined) {
        finalValue = null
      } else if (type === 'entity-select' && editValue) {
        finalValue = Number(editValue)
      }
      
      await onSave(finalValue)
      setIsEditing(false)
    } catch (err) {
      console.error('Failed to save:', err)
    } finally {
      setIsSaving(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && type !== 'textarea') {
      e.preventDefault()
      save()
    } else if (e.key === 'Escape') {
      cancel()
    }
  }

  // Displayed value (when not editing)
  const display = displayValue ?? value ?? placeholder

  // Editing UI
  if (isEditing) {
    return (
      <div className={`${s['editable-field']} ${s['editable-field--editing']} ${className}`}>
        <span className={s['editable-field__label']}>{label}</span>
        <div className={s['editable-field__edit-row']}>
          {type === 'textarea' ? (
            <textarea
              ref={inputRef as React.RefObject<HTMLTextAreaElement>}
              className={s.textarea}
              value={editValue}
              onChange={e => setEditValue(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={3}
              dir={dir}
              disabled={isSaving}
            />
          ) : type === 'select' || type === 'entity-select' ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1 }}>
              <select
                ref={inputRef as React.RefObject<HTMLSelectElement>}
                className={s.select}
                value={editValue}
                onChange={e => setEditValue(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isSaving}
                style={{ flex: 1 }}
              >
                <option value="">— בחר —</option>
                {options.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              {type === 'entity-select' && entityCreatePath && (
                <button
                  type="button"
                  className={`${s.btn} ${s['btn-icon']} ${s['btn-ghost']}`}
                  title="צור חדש"
                  onClick={() => window.open(`${entityCreatePath}?create=true`, '_blank')}
                  style={{ flexShrink: 0, padding: 4 }}
                >
                  <Plus size={14} />
                </button>
              )}
            </div>
          ) : (
            <input
              ref={inputRef as React.RefObject<HTMLInputElement>}
              type="text"
              className={s.input}
              value={editValue}
              onChange={e => setEditValue(e.target.value)}
              onKeyDown={handleKeyDown}
              dir={dir}
              disabled={isSaving}
            />
          )}
          <div className={s['editable-field__actions']}>
            <button
              type="button"
              className={`${s.btn} ${s['btn-icon']} ${s['btn-success']}`}
              onClick={save}
              disabled={isSaving}
              title="שמור"
            >
              <Check size={14} />
            </button>
            <button
              type="button"
              className={`${s.btn} ${s['btn-icon']} ${s['btn-ghost']}`}
              onClick={cancel}
              disabled={isSaving}
              title="בטל"
            >
              <X size={14} />
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Display UI (clickable to edit)
  return (
    <div
      className={`${s['editable-field']} ${disabled ? s['editable-field--disabled'] : ''} ${className}`}
      onClick={startEditing}
      role={disabled ? undefined : 'button'}
      tabIndex={disabled ? undefined : 0}
      onKeyDown={e => { if (e.key === 'Enter') startEditing() }}
    >
      <span className={s['editable-field__label']}>{label}</span>
      <span className={s['editable-field__value']}>
        {display}
        {!disabled && (
          <Pencil size={12} className={s['editable-field__icon']} />
        )}
      </span>
    </div>
  )
}

export default EditableField
