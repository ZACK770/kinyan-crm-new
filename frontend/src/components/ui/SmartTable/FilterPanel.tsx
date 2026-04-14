/* ============================================================
   FilterPanel — Smart filtering UI with presets
   ============================================================ */

import { useState, useEffect, useRef } from 'react'
import { Filter as FilterIcon, X, Plus, Save, Trash2, ChevronDown, Calendar } from 'lucide-react'
import type { Filter, SmartColumn, SavedFilter, FilterOperator, FieldType } from './types'
import {
  generateId,
  getOperatorsForType,
  operatorLabels,
  operatorNeedsValue,
  operatorNeedsSecondValue
} from './filterUtils'
import s from './SmartTable.module.css'
import shared from '@/styles/shared.module.css'

interface Props<T> {
  columns: SmartColumn<T>[]
  filters: Filter[]
  savedFilters: SavedFilter[]
  activeSavedFilterId: string | null
  onFiltersChange: (filters: Filter[]) => void
  onSaveFilter: (name: string, filters: Filter[]) => void
  onLoadFilter: (savedFilter: SavedFilter) => void
  onDeleteSavedFilter: (id: string) => void
}

export function FilterPanel<T>({
  columns,
  filters,
  savedFilters,
  activeSavedFilterId,
  onFiltersChange,
  onSaveFilter,
  onLoadFilter,
  onDeleteSavedFilter,
}: Props<T>) {
  const [isOpen, setIsOpen] = useState(false)
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [saveFilterName, setSaveFilterName] = useState('')
  const [showSavedDropdown, setShowSavedDropdown] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowSavedDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const filterableColumns = columns.filter(c => c.filterable !== false)

  const addFilter = () => {
    const firstCol = filterableColumns[0]
    if (!firstCol) return

    const operators = getOperatorsForType(firstCol.type)
    const newFilter: Filter = {
      id: generateId(),
      field: firstCol.key,
      operator: operators[0],
      value: null,
    }
    onFiltersChange([...filters, newFilter])
  }

  const updateFilter = (id: string, updates: Partial<Filter>) => {
    onFiltersChange(filters.map(f => f.id === id ? { ...f, ...updates } : f))
  }

  const removeFilter = (id: string) => {
    onFiltersChange(filters.filter(f => f.id !== id))
  }

  const clearAllFilters = () => {
    onFiltersChange([])
  }

  const handleSaveFilter = () => {
    if (!saveFilterName.trim()) return
    onSaveFilter(saveFilterName.trim(), filters)
    setSaveFilterName('')
    setShowSaveDialog(false)
  }

  const handleFieldChange = (filterId: string, fieldKey: string) => {
    const column = columns.find(c => c.key === fieldKey)
    if (!column) return

    const operators = column.filterOperators || getOperatorsForType(column.type)
    updateFilter(filterId, {
      field: fieldKey,
      operator: operators[0],
      value: null,
      value2: undefined,
    })
  }

  const getColumnType = (fieldKey: string): FieldType => {
    return columns.find(c => c.key === fieldKey)?.type || 'text'
  }

  const getColumnOperators = (fieldKey: string): FilterOperator[] => {
    const column = columns.find(c => c.key === fieldKey)
    return column?.filterOperators || getOperatorsForType(column?.type || 'text')
  }

  const getColumnOptions = (fieldKey: string) => {
    return columns.find(c => c.key === fieldKey)?.options || []
  }

  const activeSavedFilter = savedFilters.find(f => f.id === activeSavedFilterId)

  return (
    <div className={s.filterPanel}>
      {/* Toggle button */}
      <button
        className={`${shared.btn} ${shared['btn-secondary']} ${shared['btn-sm']} ${filters.length ? s.filterActive : ''}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        <FilterIcon size={14} />
        <span>סינון</span>
        {filters.length > 0 && (
          <span className={s.filterCount}>{filters.length}</span>
        )}
      </button>

      {/* Saved filters dropdown */}
      {savedFilters.length > 0 && (
        <div className={s.savedFiltersWrapper} ref={dropdownRef}>
          <button
            className={`${shared.btn} ${shared['btn-ghost']} ${shared['btn-sm']}`}
            onClick={() => setShowSavedDropdown(!showSavedDropdown)}
          >
            {activeSavedFilter ? activeSavedFilter.name : 'פילטרים שמורים'}
            <ChevronDown size={14} />
          </button>

          {showSavedDropdown && (
            <div className={s.savedFiltersDropdown}>
              {savedFilters.map(sf => (
                <div key={sf.id} className={s.savedFilterItem}>
                  <button
                    className={`${s.savedFilterBtn} ${sf.id === activeSavedFilterId ? s.active : ''}`}
                    onClick={() => {
                      onLoadFilter(sf)
                      setShowSavedDropdown(false)
                    }}
                  >
                    {sf.name}
                  </button>
                  <button
                    className={s.savedFilterDelete}
                    onClick={(e) => {
                      e.stopPropagation()
                      onDeleteSavedFilter(sf.id)
                    }}
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Filter panel content */}
      {isOpen && (
        <div className={s.filterPanelContent}>
          <div className={s.filterPanelHeader}>
            <span>סינון מתקדם</span>
            <div className={s.filterPanelActions}>
              {filters.length > 0 && (
                <>
                  <button
                    className={`${shared.btn} ${shared['btn-ghost']} ${shared['btn-xs']}`}
                    onClick={() => setShowSaveDialog(true)}
                  >
                    <Save size={12} /> שמור
                  </button>
                  <button
                    className={`${shared.btn} ${shared['btn-ghost']} ${shared['btn-xs']}`}
                    onClick={clearAllFilters}
                  >
                    <Trash2 size={12} /> נקה
                  </button>
                </>
              )}
              <button
                className={`${shared.btn} ${shared['btn-ghost']} ${shared['btn-xs']}`}
                onClick={() => setIsOpen(false)}
              >
                <X size={14} />
              </button>
            </div>
          </div>

          {/* Save filter dialog */}
          {showSaveDialog && (
            <div className={s.saveFilterDialog}>
              <input
                className={`${shared.input} ${shared['input-sm']}`}
                placeholder="שם הפילטר..."
                value={saveFilterName}
                onChange={e => setSaveFilterName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSaveFilter()}
                autoFocus
              />
              <button
                className={`${shared.btn} ${shared['btn-primary']} ${shared['btn-sm']}`}
                onClick={handleSaveFilter}
                disabled={!saveFilterName.trim()}
              >
                שמור
              </button>
              <button
                className={`${shared.btn} ${shared['btn-ghost']} ${shared['btn-sm']}`}
                onClick={() => setShowSaveDialog(false)}
              >
                ביטול
              </button>
            </div>
          )}

          {/* Filter rows */}
          <div className={s.filterRows}>
            {filters.map((filter, index) => {
              const fieldType = getColumnType(filter.field)
              const operators = getColumnOperators(filter.field)
              const options = getColumnOptions(filter.field)
              const needsValue = operatorNeedsValue(filter.operator)
              const needsSecondValue = operatorNeedsSecondValue(filter.operator)

              return (
                <div key={filter.id} className={s.filterRow}>
                  {index > 0 && <span className={s.filterAnd}>וגם</span>}

                  {/* Field selector */}
                  <select
                    className={`${shared.select} ${shared['select-sm']}`}
                    value={filter.field}
                    onChange={e => handleFieldChange(filter.id, e.target.value)}
                  >
                    {filterableColumns.map(col => (
                      <option key={col.key} value={col.key}>{col.header}</option>
                    ))}
                  </select>

                  {/* Operator selector */}
                  <select
                    className={`${shared.select} ${shared['select-sm']}`}
                    value={filter.operator}
                    onChange={e => updateFilter(filter.id, {
                      operator: e.target.value as FilterOperator,
                      value: operatorNeedsValue(e.target.value as FilterOperator) ? filter.value : null,
                    })}
                  >
                    {operators.map(op => (
                      <option key={op} value={op}>{operatorLabels[op]}</option>
                    ))}
                  </select>

                  {/* Value input */}
                  {needsValue && (
                    <FilterValueInput
                      type={fieldType}
                      value={filter.value}
                      options={options}
                      onChange={v => updateFilter(filter.id, { value: v })}
                    />
                  )}

                  {/* Second value for "between" */}
                  {needsSecondValue && (
                    <>
                      <span className={s.filterTo}>עד</span>
                      <FilterValueInput
                        type={fieldType}
                        value={filter.value2 ?? null}
                        options={options}
                        onChange={v => updateFilter(filter.id, { value2: v })}
                      />
                    </>
                  )}

                  {/* Remove button */}
                  <button
                    className={s.filterRemove}
                    onClick={() => removeFilter(filter.id)}
                  >
                    <X size={14} />
                  </button>
                </div>
              )
            })}
          </div>

          {/* Add filter button */}
          <button
            className={`${shared.btn} ${shared['btn-ghost']} ${shared['btn-sm']}`}
            onClick={addFilter}
          >
            <Plus size={14} /> הוסף תנאי
          </button>
        </div>
      )}
    </div>
  )
}

/* ── Filter Value Input Component ── */
interface FilterValueInputProps {
  type: FieldType
  value: string | number | boolean | null
  options?: { value: string | number; label: string }[]
  onChange: (value: string | number | null) => void
}

function FilterValueInput({ type, value, options, onChange }: FilterValueInputProps) {
  if (type === 'select' && options?.length) {
    return (
      <select
        className={`${shared.select} ${shared['select-sm']}`}
        value={String(value ?? '')}
        onChange={e => onChange(e.target.value || null)}
      >
        <option value="">— בחר —</option>
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    )
  }

  if (type === 'date' || type === 'datetime') {
    return (
      <div className={s.dateInputWrapper}>
        <input
          type="date"
          className={`${shared.input} ${shared['input-sm']}`}
          value={String(value ?? '')}
          onChange={e => onChange(e.target.value || null)}
        />
        <Calendar size={14} className={s.dateIcon} />
      </div>
    )
  }

  if (type === 'number' || type === 'currency') {
    return (
      <input
        type="number"
        className={`${shared.input} ${shared['input-sm']}`}
        value={String(value ?? '')}
        onChange={e => onChange(e.target.value ? Number(e.target.value) : null)}
        dir="ltr"
        style={{ width: 120 }}
      />
    )
  }

  // Default: text input
  return (
    <input
      type="text"
      className={`${shared.input} ${shared['input-sm']}`}
      value={String(value ?? '')}
      onChange={e => onChange(e.target.value || null)}
      placeholder="ערך..."
      style={{ minWidth: 120 }}
    />
  )
}
