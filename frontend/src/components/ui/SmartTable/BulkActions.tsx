/* ============================================================
   BulkActions — Bulk operations for selected rows
   ============================================================ */

import { useState, useRef, useEffect } from 'react'
import { Check, Trash2, Edit3, X, ChevronDown } from 'lucide-react'
import type { BulkAction, SmartColumn, FieldType } from './types'
import s from './SmartTable.module.css'
import shared from '@/styles/shared.module.css'

interface Props<T> {
  selectedRows: T[]
  bulkActions: BulkAction<T>[]
  columns: SmartColumn<T>[]
  onClearSelection: () => void
  onBulkUpdate?: (rows: T[], field: string, value: unknown) => Promise<void>
  onDelete?: (rows: T[]) => Promise<void>
}

export function BulkActions<T>({
  selectedRows,
  bulkActions,
  columns,
  onClearSelection,
  onBulkUpdate,
  onDelete,
}: Props<T>) {
  const [showUpdatePanel, setShowUpdatePanel] = useState(false)
  const [selectedField, setSelectedField] = useState('')
  const [updateValue, setUpdateValue] = useState<unknown>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [showActionsMenu, setShowActionsMenu] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  // Close menu on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowActionsMenu(false)
      }
    }
    if (showActionsMenu) {
      document.addEventListener('mousedown', handleClick)
      return () => document.removeEventListener('mousedown', handleClick)
    }
  }, [showActionsMenu])

  if (selectedRows.length === 0) return null

  const editableColumns = columns.filter(c => c.editable !== false && c.key !== '_actions')

  const handleBulkUpdate = async () => {
    if (!selectedField || !onBulkUpdate) return
    
    setIsProcessing(true)
    try {
      await onBulkUpdate(selectedRows, selectedField, updateValue)
      setShowUpdatePanel(false)
      setSelectedField('')
      setUpdateValue(null)
      onClearSelection()
    } catch (error) {
      console.error('Bulk update failed:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleBulkDelete = async () => {
    if (!onDelete) return
    if (!confirm(`למחוק ${selectedRows.length} פריטים?`)) return
    
    setIsProcessing(true)
    try {
      await onDelete(selectedRows)
      onClearSelection()
    } catch (error) {
      console.error('Bulk delete failed:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleCustomAction = async (action: BulkAction<T>) => {
    setIsProcessing(true)
    try {
      await action.action(selectedRows)
      setShowActionsMenu(false)
    } catch (error) {
      console.error('Bulk action failed:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  const getSelectedColumn = () => columns.find(c => c.key === selectedField)

  const renderValueInput = () => {
    const column = getSelectedColumn()
    if (!column) return null

    const type = column.type
    const options = column.options || []

    if (type === 'select' && options.length) {
      return (
        <select 
          className={`${shared.select} ${shared['select-sm']}`}
          value={String(updateValue ?? '')}
          onChange={e => setUpdateValue(e.target.value || null)}
        >
          <option value="">— בחר ערך —</option>
          {options.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      )
    }

    if (type === 'boolean') {
      return (
        <select 
          className={`${shared.select} ${shared['select-sm']}`}
          value={updateValue === true ? 'true' : updateValue === false ? 'false' : ''}
          onChange={e => setUpdateValue(e.target.value === 'true' ? true : e.target.value === 'false' ? false : null)}
        >
          <option value="">— בחר —</option>
          <option value="true">כן</option>
          <option value="false">לא</option>
        </select>
      )
    }

    if (type === 'number' || type === 'currency') {
      return (
        <input
          type="number"
          className={`${shared.input} ${shared['input-sm']}`}
          value={String(updateValue ?? '')}
          onChange={e => setUpdateValue(e.target.value ? Number(e.target.value) : null)}
          placeholder="ערך..."
          dir="ltr"
        />
      )
    }

    if (type === 'date' || type === 'datetime') {
      return (
        <input
          type="date"
          className={`${shared.input} ${shared['input-sm']}`}
          value={String(updateValue ?? '')}
          onChange={e => setUpdateValue(e.target.value || null)}
        />
      )
    }

    // Default: text input
    return (
      <input
        type="text"
        className={`${shared.input} ${shared['input-sm']}`}
        value={String(updateValue ?? '')}
        onChange={e => setUpdateValue(e.target.value || null)}
        placeholder="ערך..."
      />
    )
  }

  return (
    <div className={s.bulkActionsBar}>
      <div className={s.bulkActionsInfo}>
        <span className={s.selectedCount}>{selectedRows.length}</span>
        <span>נבחרו</span>
        <button 
          className={s.clearSelectionBtn}
          onClick={onClearSelection}
          title="בטל בחירה"
        >
          <X size={14} />
        </button>
      </div>

      <div className={s.bulkActionsButtons}>
        {/* Update field button */}
        {onBulkUpdate && (
          <button
            className={`${shared.btn} ${shared['btn-secondary']} ${shared['btn-sm']}`}
            onClick={() => setShowUpdatePanel(!showUpdatePanel)}
          >
            <Edit3 size={14} />
            עדכון שדה
          </button>
        )}

        {/* Delete button */}
        {onDelete && (
          <button
            className={`${shared.btn} ${shared['btn-danger']} ${shared['btn-sm']}`}
            onClick={handleBulkDelete}
            disabled={isProcessing}
          >
            <Trash2 size={14} />
            מחק
          </button>
        )}

        {/* Custom actions dropdown */}
        {bulkActions.length > 0 && (
          <div className={s.actionsMenuWrapper} ref={menuRef}>
            <button
              className={`${shared.btn} ${shared['btn-secondary']} ${shared['btn-sm']}`}
              onClick={() => setShowActionsMenu(!showActionsMenu)}
            >
              פעולות נוספות
              <ChevronDown size={14} />
            </button>

            {showActionsMenu && (
              <div className={s.actionsMenu}>
                {bulkActions.map(action => (
                  <button
                    key={action.id}
                    className={s.actionMenuItem}
                    onClick={() => handleCustomAction(action)}
                    disabled={isProcessing}
                  >
                    {action.icon}
                    {action.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Update field panel */}
      {showUpdatePanel && (
        <div className={s.updatePanel}>
          <div className={s.updatePanelContent}>
            <select
              className={`${shared.select} ${shared['select-sm']}`}
              value={selectedField}
              onChange={e => {
                setSelectedField(e.target.value)
                setUpdateValue(null)
              }}
            >
              <option value="">— בחר שדה —</option>
              {editableColumns.map(col => (
                <option key={col.key} value={col.key}>{col.header}</option>
              ))}
            </select>

            {selectedField && (
              <>
                {renderValueInput()}
                <button
                  className={`${shared.btn} ${shared['btn-primary']} ${shared['btn-sm']}`}
                  onClick={handleBulkUpdate}
                  disabled={isProcessing || updateValue === null}
                >
                  <Check size={14} />
                  עדכן {selectedRows.length} פריטים
                </button>
              </>
            )}

            <button
              className={`${shared.btn} ${shared['btn-ghost']} ${shared['btn-sm']}`}
              onClick={() => {
                setShowUpdatePanel(false)
                setSelectedField('')
                setUpdateValue(null)
              }}
            >
              ביטול
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
