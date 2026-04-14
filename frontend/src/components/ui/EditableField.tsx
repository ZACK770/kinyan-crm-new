import { useState, useRef, useEffect, type ReactNode } from 'react'
import { Loader2, Pencil, Plus, Check } from 'lucide-react'
import s from '@/styles/shared.module.css'

/* ══════════════════════════════════════════════════════════════
   EditableField — Click-to-edit inline field
   ═══════════════════════════════════════════════════════════════
   UX Pattern: Auto-save on blur
   - Click to edit → field becomes input
   - Auto-save when: blur, Enter (text), Tab
   - Escape: cancel changes (revert to original)
   - No explicit save/cancel buttons needed
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

// SaveStatus indicator states
type SaveStatus = 'idle' | 'saving' | 'saved'

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
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const savedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

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

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (savedTimerRef.current) clearTimeout(savedTimerRef.current)
    }
  }, [])

  const startEditing = () => {
    if (disabled || saveStatus === 'saving') return
    setEditValue(String(value ?? ''))
    setIsEditing(true)
    setSaveStatus('idle')
  }

  const cancel = () => {
    setEditValue(String(value ?? ''))
    setIsEditing(false)
  }

  const save = async () => {
    // No changes? Just close
    if (editValue === String(value ?? '')) {
      setIsEditing(false)
      return
    }

    setSaveStatus('saving')
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

      // Show saved indicator briefly
      setSaveStatus('saved')
      savedTimerRef.current = setTimeout(() => {
        setSaveStatus('idle')
      }, 1500)
    } catch (err) {
      console.error('Failed to save:', err)
      setSaveStatus('idle')
      // Keep editing open on error
    }
  }

  const handleBlur = (e: React.FocusEvent) => {
    // Don't save if clicking the "create new" button
    const relatedTarget = e.relatedTarget as HTMLElement
    if (relatedTarget?.closest('[data-create-entity]')) {
      return
    }
    // Auto-save on blur
    save()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && type !== 'textarea') {
      e.preventDefault()
      save()
    } else if (e.key === 'Escape') {
      e.preventDefault()
      cancel()
    }
  }

  // For selects, save immediately on change (better UX)
  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newValue = e.target.value
    setEditValue(newValue)
    // For selects, auto-save on selection (no need to blur)
    setTimeout(() => {
      if (!isEditing) return
      save()
    }, 50)
  }

  // Displayed value (when not editing)
  const display = displayValue ?? value ?? placeholder

  // Save status icon
  const StatusIcon = () => {
    if (saveStatus === 'saving') {
      return <Loader2 size={12} className={s['editable-field__status']} style={{ animation: 'spin 1s linear infinite' }} />
    }
    if (saveStatus === 'saved') {
      return <Check size={12} className={s['editable-field__status']} style={{ color: 'var(--color-success, #16a34a)' }} />
    }
    return null
  }

  // Editing UI — simplified, no save/cancel buttons
  if (isEditing) {
    return (
      <div
        ref={containerRef}
        className={`${s['editable-field']} ${s['editable-field--editing']} ${className}`}
      >
        <span className={s['editable-field__label']}>
          {label}
          <StatusIcon />
        </span>
        <div className={s['editable-field__edit-row']}>
          {type === 'textarea' ? (
            <textarea
              ref={inputRef as React.RefObject<HTMLTextAreaElement>}
              className={s.textarea}
              value={editValue}
              onChange={e => setEditValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onBlur={handleBlur}
              rows={3}
              dir={dir}
              disabled={saveStatus === 'saving'}
            />
          ) : type === 'select' || type === 'entity-select' ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1 }}>
              <select
                ref={inputRef as React.RefObject<HTMLSelectElement>}
                className={s.select}
                value={editValue}
                onChange={handleSelectChange}
                onKeyDown={handleKeyDown}
                onBlur={handleBlur}
                disabled={saveStatus === 'saving'}
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
                  data-create-entity
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
              onBlur={handleBlur}
              dir={dir}
              disabled={saveStatus === 'saving'}
            />
          )}
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
      <span className={s['editable-field__label']}>
        {label}
        <StatusIcon />
      </span>
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
