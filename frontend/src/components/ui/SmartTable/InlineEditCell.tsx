/* ============================================================
   InlineEditCell — Inline editing within table cells
   ============================================================ */

import { useState, useRef, useEffect } from 'react'
import { Check, X, Loader2 } from 'lucide-react'
import type { FieldType } from './types'
import s from './SmartTable.module.css'
import shared from '@/styles/shared.module.css'

interface Props {
  value: unknown
  type: FieldType
  options?: { value: string | number; label: string }[]
  displayValue?: React.ReactNode
  onSave: (value: unknown) => Promise<void>
  disabled?: boolean
}

export function InlineEditCell({
  value,
  type,
  options = [],
  displayValue,
  onSave,
  disabled = false,
}: Props) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState<unknown>(value)
  const [isSaving, setIsSaving] = useState(false)
  const [showSaved, setShowSaved] = useState(false)
  const inputRef = useRef<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>(null)
  const savedTimeoutRef = useRef<ReturnType<typeof setTimeout>>()

  // Sync when value changes
  useEffect(() => {
    if (!isEditing) {
      setEditValue(value)
    }
  }, [value, isEditing])

  // Focus on edit start
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      if (inputRef.current instanceof HTMLInputElement) {
        inputRef.current.select()
      }
    }
  }, [isEditing])

  // Cleanup
  useEffect(() => {
    return () => {
      if (savedTimeoutRef.current) clearTimeout(savedTimeoutRef.current)
    }
  }, [])

  const startEditing = () => {
    if (disabled || isSaving) return
    setEditValue(value)
    setIsEditing(true)
  }

  const cancelEditing = () => {
    setEditValue(value)
    setIsEditing(false)
  }

  const saveValue = async () => {
    // No change - just close
    if (editValue === value) {
      setIsEditing(false)
      return
    }

    setIsSaving(true)
    try {
      await onSave(editValue)
      setIsEditing(false)
      // Show saved indicator
      setShowSaved(true)
      savedTimeoutRef.current = setTimeout(() => setShowSaved(false), 1500)
    } catch (error) {
      console.error('Save failed:', error)
      // Keep editing on error
    } finally {
      setIsSaving(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && type !== 'text') {
      e.preventDefault()
      saveValue()
    } else if (e.key === 'Escape') {
      e.preventDefault()
      cancelEditing()
    }
  }

  const handleBlur = () => {
    // Auto-save on blur
    saveValue()
  }

  // For selects, save immediately on change
  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newValue = e.target.value
    setEditValue(type === 'boolean' ? newValue === 'true' : newValue || null)
    // Delay save slightly to allow blur handling
    setTimeout(() => {
      if (isEditing) saveValue()
    }, 50)
  }

  // Render display value
  const renderDisplay = () => {
    if (isSaving) {
      return (
        <span className={s.inlineCellStatus}>
          <Loader2 size={12} className={s.spinning} />
        </span>
      )
    }
    if (showSaved) {
      return (
        <span className={s.inlineCellSaved}>
          <Check size={12} />
        </span>
      )
    }
    return displayValue ?? formatValue(value, type, options)
  }

  // Display mode
  if (!isEditing) {
    return (
      <div 
        className={`${s.inlineCell} ${disabled ? s.disabled : ''}`}
        onClick={startEditing}
        onKeyDown={e => e.key === 'Enter' && startEditing()}
        tabIndex={disabled ? undefined : 0}
        role={disabled ? undefined : 'button'}
      >
        {renderDisplay()}
      </div>
    )
  }

  // Edit mode
  return (
    <div className={s.inlineCellEdit} onClick={e => e.stopPropagation()}>
      {type === 'select' && options.length > 0 ? (
        <select
          ref={inputRef as React.RefObject<HTMLSelectElement>}
          className={`${shared.select} ${s.inlineSelect}`}
          value={String(editValue ?? '')}
          onChange={handleSelectChange}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          disabled={isSaving}
        >
          <option value="">—</option>
          {options.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      ) : type === 'boolean' ? (
        <select
          ref={inputRef as React.RefObject<HTMLSelectElement>}
          className={`${shared.select} ${s.inlineSelect}`}
          value={editValue === true ? 'true' : editValue === false ? 'false' : ''}
          onChange={handleSelectChange}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          disabled={isSaving}
        >
          <option value="">—</option>
          <option value="true">כן</option>
          <option value="false">לא</option>
        </select>
      ) : type === 'date' || type === 'datetime' ? (
        <input
          ref={inputRef as React.RefObject<HTMLInputElement>}
          type="date"
          className={`${shared.input} ${s.inlineInput}`}
          value={String(editValue ?? '')}
          onChange={e => setEditValue(e.target.value || null)}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          disabled={isSaving}
        />
      ) : type === 'number' || type === 'currency' ? (
        <input
          ref={inputRef as React.RefObject<HTMLInputElement>}
          type="number"
          className={`${shared.input} ${s.inlineInput}`}
          value={String(editValue ?? '')}
          onChange={e => setEditValue(e.target.value ? Number(e.target.value) : null)}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          disabled={isSaving}
          dir="ltr"
        />
      ) : (
        <input
          ref={inputRef as React.RefObject<HTMLInputElement>}
          type="text"
          className={`${shared.input} ${s.inlineInput}`}
          value={String(editValue ?? '')}
          onChange={e => setEditValue(e.target.value || null)}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          disabled={isSaving}
        />
      )}
      {isSaving && <Loader2 size={12} className={s.spinning} />}
    </div>
  )
}

// Format value for display
function formatValue(
  value: unknown, 
  type: FieldType, 
  options: { value: string | number; label: string }[]
): string {
  if (value === null || value === undefined || value === '') return '—'

  if (type === 'select' && options.length) {
    const opt = options.find(o => String(o.value) === String(value))
    return opt?.label ?? String(value)
  }

  if (type === 'boolean') {
    return value === true ? 'כן' : value === false ? 'לא' : '—'
  }

  if (type === 'currency') {
    return new Intl.NumberFormat('he-IL', { style: 'currency', currency: 'ILS' }).format(Number(value))
  }

  if (type === 'date' || type === 'datetime') {
    try {
      const date = new Date(value as string)
      return date.toLocaleDateString('he-IL')
    } catch {
      return String(value)
    }
  }

  return String(value)
}
