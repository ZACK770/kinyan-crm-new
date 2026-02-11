/* ============================================================
   ColumnManager — Column visibility and reordering
   ============================================================ */

import { useState, useRef, useEffect } from 'react'
import { Settings2, Eye, EyeOff, GripVertical, X } from 'lucide-react'
import type { SmartColumn } from './types'
import s from './SmartTable.module.css'
import shared from '@/styles/shared.module.css'

interface Props<T> {
  columns: SmartColumn<T>[]
  visibleColumns: string[]
  columnOrder: string[]
  onVisibilityChange: (visibleColumns: string[]) => void
  onOrderChange: (columnOrder: string[]) => void
}

export function ColumnManager<T>({
  columns,
  visibleColumns,
  columnOrder,
  onVisibilityChange,
  onOrderChange,
}: Props<T>) {
  const [isOpen, setIsOpen] = useState(false)
  const [draggedItem, setDraggedItem] = useState<string | null>(null)
  const panelRef = useRef<HTMLDivElement>(null)

  // Close on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClick)
      return () => document.removeEventListener('mousedown', handleClick)
    }
  }, [isOpen])

  // Get ordered columns list
  const orderedColumns = [...columns].sort((a, b) => {
    const aIndex = columnOrder.indexOf(a.key)
    const bIndex = columnOrder.indexOf(b.key)
    if (aIndex === -1 && bIndex === -1) return 0
    if (aIndex === -1) return 1
    if (bIndex === -1) return -1
    return aIndex - bIndex
  })

  const toggleColumn = (key: string) => {
    if (visibleColumns.includes(key)) {
      // Don't allow hiding all columns
      if (visibleColumns.length <= 1) return
      onVisibilityChange(visibleColumns.filter(k => k !== key))
    } else {
      onVisibilityChange([...visibleColumns, key])
    }
  }

  const showAllColumns = () => {
    onVisibilityChange(columns.map(c => c.key))
  }

  const handleDragStart = (e: React.DragEvent, key: string) => {
    setDraggedItem(key)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', key)
    // Add dragging class after a frame
    requestAnimationFrame(() => {
      const elem = e.currentTarget as HTMLElement
      elem.classList.add(s.dragging)
    })
  }

  const handleDragEnd = (e: React.DragEvent) => {
    setDraggedItem(null)
    const elem = e.currentTarget as HTMLElement
    elem.classList.remove(s.dragging)
  }

  const handleDragOver = (e: React.DragEvent, overKey: string) => {
    e.preventDefault()
    if (!draggedItem || draggedItem === overKey) return

    const currentOrder = [...columnOrder]
    // Ensure all columns are in the order
    columns.forEach(c => {
      if (!currentOrder.includes(c.key)) {
        currentOrder.push(c.key)
      }
    })

    const dragIndex = currentOrder.indexOf(draggedItem)
    const overIndex = currentOrder.indexOf(overKey)

    if (dragIndex === -1 || overIndex === -1) return

    // Reorder
    currentOrder.splice(dragIndex, 1)
    currentOrder.splice(overIndex, 0, draggedItem)

    onOrderChange(currentOrder)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDraggedItem(null)
  }

  const hiddenCount = columns.length - visibleColumns.length

  return (
    <div className={s.columnManager} ref={panelRef}>
      <button 
        className={`${shared.btn} ${shared['btn-ghost']} ${shared['btn-sm']}`}
        onClick={() => setIsOpen(!isOpen)}
        title="הגדרות עמודות"
      >
        <Settings2 size={14} />
        <span>עמודות</span>
        {hiddenCount > 0 && (
          <span className={s.hiddenCount}>-{hiddenCount}</span>
        )}
      </button>

      {isOpen && (
        <div className={s.columnManagerPanel}>
          <div className={s.columnManagerHeader}>
            <span>ניהול עמודות</span>
            <button 
              className={`${shared.btn} ${shared['btn-ghost']} ${shared['btn-xs']}`}
              onClick={() => setIsOpen(false)}
            >
              <X size={14} />
            </button>
          </div>

          <div className={s.columnManagerActions}>
            <button 
              className={`${shared.btn} ${shared['btn-ghost']} ${shared['btn-xs']}`}
              onClick={showAllColumns}
            >
              הצג הכל
            </button>
          </div>

          <div className={s.columnList}>
            {orderedColumns.map(column => {
              const isVisible = visibleColumns.includes(column.key)
              const isOnlyVisible = isVisible && visibleColumns.length === 1

              return (
                <div
                  key={column.key}
                  className={`${s.columnItem} ${draggedItem === column.key ? s.dragging : ''}`}
                  draggable
                  onDragStart={e => handleDragStart(e, column.key)}
                  onDragEnd={handleDragEnd}
                  onDragOver={e => handleDragOver(e, column.key)}
                  onDrop={handleDrop}
                >
                  <div className={s.columnDragHandle}>
                    <GripVertical size={14} />
                  </div>
                  
                  <span className={s.columnLabel}>{column.header}</span>
                  
                  <button
                    className={`${s.columnVisibility} ${isVisible ? s.visible : s.hidden}`}
                    onClick={() => toggleColumn(column.key)}
                    disabled={isOnlyVisible}
                    title={isVisible ? 'הסתר עמודה' : 'הצג עמודה'}
                  >
                    {isVisible ? <Eye size={14} /> : <EyeOff size={14} />}
                  </button>
                </div>
              )
            })}
          </div>

          <div className={s.columnManagerHint}>
            גרור כדי לשנות סדר
          </div>
        </div>
      )}
    </div>
  )
}
