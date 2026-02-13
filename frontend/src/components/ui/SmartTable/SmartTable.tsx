/* ============================================================
   SmartTable — Feature-rich data table component
   ============================================================
   Features:
   - Smart filtering with operators per field type
   - Saved filter presets
   - Column visibility and reordering
   - Inline editing with auto-save
   - Bulk selection and actions
   - Sorting
   - Pagination (optional)
   ============================================================ */

import { useState, useEffect, useMemo, useCallback } from 'react'
import { Inbox, ChevronUp, ChevronDown } from 'lucide-react'
import type { SmartTableProps, SmartColumn, Filter, SavedFilter, TableState } from './types'
import { FilterPanel } from './FilterPanel'
import { ColumnManager } from './ColumnManager'
import { BulkActions } from './BulkActions'
import { InlineEditCell } from './InlineEditCell'
import { SmartSearch } from './SmartSearch'
import { TablePagination } from './TablePagination'
import { 
  generateId, 
  applyFilters, 
  loadTableState, 
  saveTableState, 
  loadSavedFilters, 
  saveSavedFilters 
} from './filterUtils'
import s from './SmartTable.module.css'
import shared from '@/styles/shared.module.css'

export function SmartTable<T>({
  data,
  columns,
  keyExtractor,
  loading = false,
  emptyText = 'אין נתונים להצגה',
  emptyIcon,
  onRowClick,
  onUpdate,
  onDelete,
  onBulkUpdate,
  bulkActions = [],
  storageKey,
  searchFields,
  searchPlaceholder,
  onSearchSelect,
  onServerSearch,
  defaultPageSize,
  pageSizeOptions,
  className,
  toolbarExtra,
  rowClassName,
}: SmartTableProps<T>) {
  // Search & Pagination props with defaults
  const searchSelect = onSearchSelect ?? onRowClick
  const defaultPgSize = defaultPageSize ?? 100
  const pgSizeOpts = pageSizeOptions ?? [50, 100, 200]

  // State
  const [filters, setFilters] = useState<Filter[]>([])
  const [savedFilters, setSavedFilters] = useState<SavedFilter[]>([])
  const [activeSavedFilterId, setActiveSavedFilterId] = useState<string | null>(null)
  const [visibleColumns, setVisibleColumns] = useState<string[]>([])
  const [columnOrder, setColumnOrder] = useState<string[]>([])
  const [sortBy, setSortBy] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [selectedRows, setSelectedRows] = useState<Set<string | number>>(new Set())
  const [isAllSelected, setIsAllSelected] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(defaultPgSize)

  // Initialize state from storage or defaults
  useEffect(() => {
    // Set default visible columns
    const defaultVisible = columns
      .filter(c => !c.hiddenByDefault)
      .map(c => c.key)
    
    const defaultOrder = columns.map(c => c.key)

    if (storageKey) {
      // Load saved state
      const savedState = loadTableState(storageKey)
      if (savedState) {
        setFilters(savedState.filters || [])
        setVisibleColumns(savedState.visibleColumns?.length ? savedState.visibleColumns : defaultVisible)
        setColumnOrder(savedState.columnOrder?.length ? savedState.columnOrder : defaultOrder)
        setSortBy(savedState.sortBy || null)
        setSortDir(savedState.sortDir || 'asc')
      } else {
        setVisibleColumns(defaultVisible)
        setColumnOrder(defaultOrder)
      }

      // Load saved filters
      const savedFiltersList = loadSavedFilters(storageKey)
      setSavedFilters(savedFiltersList)
    } else {
      setVisibleColumns(defaultVisible)
      setColumnOrder(defaultOrder)
    }
  }, [columns, storageKey])

  // Save state to storage
  useEffect(() => {
    if (!storageKey || !visibleColumns.length) return

    const state: TableState = {
      filters,
      visibleColumns,
      columnOrder,
      sortBy,
      sortDir,
    }
    saveTableState(storageKey, state)
  }, [filters, visibleColumns, columnOrder, sortBy, sortDir, storageKey])

  // Get ordered and visible columns
  const displayColumns = useMemo(() => {
    return [...columns]
      .filter(c => visibleColumns.includes(c.key))
      .sort((a, b) => {
        const aIndex = columnOrder.indexOf(a.key)
        const bIndex = columnOrder.indexOf(b.key)
        if (aIndex === -1 && bIndex === -1) return 0
        if (aIndex === -1) return 1
        if (bIndex === -1) return -1
        return aIndex - bIndex
      })
  }, [columns, visibleColumns, columnOrder])

  // Apply filters to data
  const filteredData = useMemo(() => {
    const columnsInfo = columns.map(c => ({ key: c.key, type: c.type }))
    return applyFilters(data, filters, columnsInfo)
  }, [data, filters, columns])

  // Apply sorting
  const sortedData = useMemo(() => {
    if (!sortBy) return filteredData

    const column = columns.find(c => c.key === sortBy)
    if (!column) return filteredData

    return [...filteredData].sort((a, b) => {
      const aVal = (a as Record<string, unknown>)[sortBy]
      const bVal = (b as Record<string, unknown>)[sortBy]

      let comparison = 0

      if (aVal === null || aVal === undefined) comparison = 1
      else if (bVal === null || bVal === undefined) comparison = -1
      else if (column.type === 'number' || column.type === 'currency') {
        comparison = Number(aVal) - Number(bVal)
      } else if (column.type === 'date' || column.type === 'datetime') {
        comparison = new Date(aVal as string).getTime() - new Date(bVal as string).getTime()
      } else {
        comparison = String(aVal).localeCompare(String(bVal), 'he')
      }

      return sortDir === 'asc' ? comparison : -comparison
    })
  }, [filteredData, sortBy, sortDir, columns])

  // Paginate data
  const totalItems = sortedData.length
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize))
  const safePage = Math.min(currentPage, totalPages)

  const paginatedData = useMemo(() => {
    const start = (safePage - 1) * pageSize
    return sortedData.slice(start, start + pageSize)
  }, [sortedData, safePage, pageSize])

  // Reset to page 1 when filters/sorting/data change
  useEffect(() => {
    setCurrentPage(1)
  }, [filters, sortBy, sortDir, data.length])

  const handlePageSizeChange = (size: number) => {
    setPageSize(size)
    setCurrentPage(1)
  }

  // Handle filter save
  const handleSaveFilter = useCallback((name: string, currentFilters: Filter[]) => {
    const newFilter: SavedFilter = {
      id: generateId(),
      name,
      filters: currentFilters,
      columns: visibleColumns,
      columnOrder,
      createdAt: new Date().toISOString(),
    }
    const updated = [...savedFilters, newFilter]
    setSavedFilters(updated)
    setActiveSavedFilterId(newFilter.id)
    if (storageKey) {
      saveSavedFilters(storageKey, updated)
    }
  }, [savedFilters, visibleColumns, columnOrder, storageKey])

  // Handle filter load
  const handleLoadFilter = useCallback((savedFilter: SavedFilter) => {
    setFilters(savedFilter.filters)
    if (savedFilter.columns?.length) setVisibleColumns(savedFilter.columns)
    if (savedFilter.columnOrder?.length) setColumnOrder(savedFilter.columnOrder)
    setActiveSavedFilterId(savedFilter.id)
  }, [])

  // Handle filter delete
  const handleDeleteSavedFilter = useCallback((id: string) => {
    const updated = savedFilters.filter(f => f.id !== id)
    setSavedFilters(updated)
    if (activeSavedFilterId === id) setActiveSavedFilterId(null)
    if (storageKey) {
      saveSavedFilters(storageKey, updated)
    }
  }, [savedFilters, activeSavedFilterId, storageKey])

  // Handle sorting
  const handleSort = (columnKey: string) => {
    const column = columns.find(c => c.key === columnKey)
    if (!column || column.sortable === false) return

    if (sortBy === columnKey) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(columnKey)
      setSortDir('asc')
    }
  }

  // Handle row selection
  const toggleRowSelection = (rowKey: string | number) => {
    const newSelected = new Set(selectedRows)
    if (newSelected.has(rowKey)) {
      newSelected.delete(rowKey)
    } else {
      newSelected.add(rowKey)
    }
    setSelectedRows(newSelected)
    setIsAllSelected(newSelected.size === sortedData.length && sortedData.length > 0)
  }

  const toggleSelectAll = () => {
    if (isAllSelected) {
      setSelectedRows(new Set())
      setIsAllSelected(false)
    } else {
      setSelectedRows(new Set(paginatedData.map(keyExtractor)))
      setIsAllSelected(true)
    }
  }

  const clearSelection = () => {
    setSelectedRows(new Set())
    setIsAllSelected(false)
  }

  // Get selected row objects
  const selectedRowObjects = useMemo(() => {
    return sortedData.filter(row => selectedRows.has(keyExtractor(row)))
  }, [sortedData, selectedRows, keyExtractor])

  // Handle inline update
  const handleCellUpdate = async (row: T, field: string, value: unknown) => {
    if (!onUpdate) return
    await onUpdate(row, field, value)
  }

  // Handle bulk update
  const handleBulkUpdate = async (rows: T[], field: string, value: unknown) => {
    if (!onBulkUpdate) return
    await onBulkUpdate(rows, field, value)
  }

  // Loading state
  if (loading) {
    return <div className={shared.loading}>טוען נתונים...</div>
  }

  // Empty state
  if (!data.length) {
    return (
      <div className={shared.empty}>
        <span className={shared['empty-icon']}>
          {emptyIcon || <Inbox size={40} strokeWidth={1.5} />}
        </span>
        <span className={shared['empty-text']}>{emptyText}</span>
      </div>
    )
  }

  return (
    <div className={`${s.smartTable} ${className || ''}`}>
      {/* Toolbar */}
      <div className={s.toolbar}>
        <div className={s.toolbarLeft}>
          <SmartSearch
            data={data}
            columns={columns}
            searchFields={searchFields}
            onSelect={(row) => searchSelect?.(row)}
            placeholder={searchPlaceholder ?? 'חיפוש...'}
            onServerSearch={onServerSearch}
          />
          <FilterPanel
            columns={columns}
            filters={filters}
            savedFilters={savedFilters}
            activeSavedFilterId={activeSavedFilterId}
            onFiltersChange={setFilters}
            onSaveFilter={handleSaveFilter}
            onLoadFilter={handleLoadFilter}
            onDeleteSavedFilter={handleDeleteSavedFilter}
          />
          <ColumnManager
            columns={columns}
            visibleColumns={visibleColumns}
            columnOrder={columnOrder}
            onVisibilityChange={setVisibleColumns}
            onOrderChange={setColumnOrder}
          />
        </div>
        <div className={s.toolbarRight}>
          {toolbarExtra}
          <span className={s.resultCount}>
            {sortedData.length !== data.length && <>{sortedData.length} מתוך </>}
            {data.length} תוצאות
          </span>
        </div>
      </div>

      {/* Bulk actions bar */}
      <BulkActions
        selectedRows={selectedRowObjects}
        bulkActions={bulkActions}
        columns={columns}
        onClearSelection={clearSelection}
        onBulkUpdate={onBulkUpdate ? handleBulkUpdate : undefined}
        onDelete={onDelete}
      />

      {/* Table */}
      <div className={shared['table-wrapper']}>
        <table className={shared.table}>
          <thead>
            <tr>
              {/* Selection checkbox */}
              {(onDelete || onBulkUpdate || bulkActions.length > 0) && (
                <th className={s.checkboxCell}>
                  <input
                    type="checkbox"
                    checked={isAllSelected}
                    onChange={toggleSelectAll}
                    className={s.checkbox}
                  />
                </th>
              )}
              {displayColumns.map(col => {
                const isSorted = sortBy === col.key
                const isSortable = col.sortable !== false

                return (
                  <th
                    key={col.key}
                    className={`${isSortable ? shared.sortable : ''} ${isSorted ? s.sorted : ''}`}
                    onClick={() => isSortable && handleSort(col.key)}
                    style={{ width: col.width, minWidth: col.minWidth }}
                  >
                    <span className={s.headerContent}>
                      {col.header}
                      {isSortable && (
                        <span className={s.sortIcon}>
                          {isSorted && sortDir === 'asc' && <ChevronUp size={14} />}
                          {isSorted && sortDir === 'desc' && <ChevronDown size={14} />}
                        </span>
                      )}
                    </span>
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {paginatedData.map(row => {
              const rowKey = keyExtractor(row)
              const isSelected = selectedRows.has(rowKey)

              return (
                <tr
                  key={rowKey}
                  className={`${onRowClick ? shared.clickable : ''} ${isSelected ? s.selectedRow : ''} ${rowClassName ? rowClassName(row) : ''}`}
                  onClick={() => onRowClick?.(row)}
                >
                  {/* Selection checkbox */}
                  {(onDelete || onBulkUpdate || bulkActions.length > 0) && (
                    <td className={s.checkboxCell} onClick={e => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleRowSelection(rowKey)}
                        className={s.checkbox}
                      />
                    </td>
                  )}
                  {displayColumns.map(col => (
                    <td 
                      key={col.key} 
                      className={col.className}
                      onClick={e => {
                        // Stop propagation for editable cells
                        if (col.editable !== false && onUpdate) {
                          e.stopPropagation()
                        }
                      }}
                    >
                      {renderCell(row, col, onUpdate ? (v) => handleCellUpdate(row, col.key, v) : undefined)}
                    </td>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalItems > 0 && (
        <TablePagination
          totalItems={totalItems}
          currentPage={safePage}
          pageSize={pageSize}
          pageSizeOptions={pgSizeOpts}
          onPageChange={setCurrentPage}
          onPageSizeChange={handlePageSizeChange}
        />
      )}

      {/* Filtered results notice */}
      {filters.length > 0 && sortedData.length === 0 && (
        <div className={s.noResults}>
          <span>לא נמצאו תוצאות התואמות לסינון</span>
          <button 
            className={`${shared.btn} ${shared['btn-ghost']} ${shared['btn-sm']}`}
            onClick={() => setFilters([])}
          >
            נקה סינון
          </button>
        </div>
      )}
    </div>
  )
}

// Render a single cell
function renderCell<T>(
  row: T,
  column: SmartColumn<T>,
  onUpdate?: (value: unknown) => Promise<void>
) {
  const value = (row as Record<string, unknown>)[column.key]

  // Custom render function takes priority (always)
  if (column.render) {
    return column.render(row, onUpdate ? (v) => onUpdate(v) : () => {})
  }

  // View-only render (only if not editable)
  if (column.renderView && (column.editable === false || !onUpdate)) {
    return column.renderView(row)
  }

  // Actions column or non-editable - just show value
  if (column.editable === false || column.key === '_actions' || !onUpdate) {
    return formatDisplayValue(value, column)
  }

  // Inline editable cell — use renderView as display if available
  const customDisplay = column.renderView ? column.renderView(row) : undefined
  return (
    <InlineEditCell
      value={value}
      type={column.type}
      options={column.options}
      displayValue={customDisplay ?? formatDisplayValue(value, column)}
      onSave={onUpdate}
    />
  )
}

// Format value for display
function formatDisplayValue<T>(value: unknown, column: SmartColumn<T>): React.ReactNode {
  if (value === null || value === undefined || value === '') return '—'

  if (column.type === 'select' && column.options?.length) {
    const opt = column.options.find(o => String(o.value) === String(value))
    return opt?.label ?? String(value)
  }

  if (column.type === 'boolean') {
    return value === true ? 'כן' : value === false ? 'לא' : '—'
  }

  if (column.type === 'currency') {
    return new Intl.NumberFormat('he-IL', { style: 'currency', currency: 'ILS' }).format(Number(value))
  }

  if (column.type === 'date') {
    try {
      return new Date(value as string).toLocaleDateString('he-IL')
    } catch {
      return String(value)
    }
  }

  if (column.type === 'datetime') {
    try {
      return new Date(value as string).toLocaleString('he-IL')
    } catch {
      return String(value)
    }
  }

  return String(value)
}

export default SmartTable
