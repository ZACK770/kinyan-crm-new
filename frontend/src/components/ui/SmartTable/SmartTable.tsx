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

import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { Inbox, ChevronUp, ChevronDown, Download } from 'lucide-react'
import * as XLSX from 'xlsx'
import type { SmartTableProps, SmartColumn, Filter, FilterMode, SavedFilter, TableState } from './types'
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

  // Shift-click selection tracking
  const lastSelectedIndexRef = useRef<number | null>(null)
  // State
  const [filters, setFilters] = useState<Filter[]>([])
  const [filterMode, setFilterMode] = useState<FilterMode>('and')
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
        setFilterMode(savedState.filterMode || 'and')
        setVisibleColumns(savedState.visibleColumns?.length ? savedState.visibleColumns : defaultVisible)
        setColumnOrder(savedState.columnOrder?.length ? savedState.columnOrder : defaultOrder)
        setSortBy(savedState.sortBy || null)
        setSortDir(savedState.sortDir || 'asc')
        if (savedState.pageSize) setPageSize(savedState.pageSize)
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
  }, [columns, storageKey, defaultPgSize])

  // Save state to storage
  useEffect(() => {
    if (!storageKey || !visibleColumns.length) return

    const state: TableState = {
      filters,
      filterMode,
      visibleColumns,
      columnOrder,
      sortBy,
      sortDir,
      pageSize,
    }
    saveTableState(storageKey, state)
  }, [filters, filterMode, visibleColumns, columnOrder, sortBy, sortDir, pageSize, storageKey])

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
    return applyFilters(data, filters, columnsInfo, filterMode)
  }, [data, filters, filterMode, columns])

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
  const toggleRowSelection = (rowKey: string | number, event?: React.MouseEvent) => {
    const currentIndex = paginatedData.findIndex(row => keyExtractor(row) === rowKey)
    const newSelected = new Set(selectedRows)

    if (event?.shiftKey && lastSelectedIndexRef.current !== null && currentIndex !== -1) {
      const start = Math.min(lastSelectedIndexRef.current, currentIndex)
      const end = Math.max(lastSelectedIndexRef.current, currentIndex)
      for (let index = start; index <= end; index++) {
        newSelected.add(keyExtractor(paginatedData[index]))
      }
    } else {
      if (newSelected.has(rowKey)) {
        newSelected.delete(rowKey)
      } else {
        newSelected.add(rowKey)
      }
    }

    lastSelectedIndexRef.current = currentIndex
    setSelectedRows(newSelected)
    setIsAllSelected(newSelected.size === paginatedData.length && paginatedData.length > 0)
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

  // Skeleton row count for loading state
  const skeletonRowCount = Math.min(pageSize, 15)

  // Empty state (only when NOT loading)
  if (!loading && !data.length) {
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
      {/* Toolbar — always visible */}
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
            filterMode={filterMode}
            savedFilters={savedFilters}
            activeSavedFilterId={activeSavedFilterId}
            onFiltersChange={setFilters}
            onFilterModeChange={setFilterMode}
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
          <button
            className={`${shared.btn} ${shared['btn-secondary']} ${shared['btn-sm']}`}
            onClick={() => exportToExcel(sortedData, displayColumns, storageKey)}
            disabled={loading || sortedData.length === 0}
            title="ייצוא לאקסל"
          >
            <Download size={14} />
            <span>Excel</span>
          </button>
          {toolbarExtra}
          {loading ? (
            <span className={s.resultCount}>טוען...</span>
          ) : (
            <span className={s.resultCount}>
              {sortedData.length !== data.length && <>{sortedData.length} מתוך </>}
              {data.length} תוצאות
            </span>
          )}
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
            {loading ? (
              Array.from({ length: skeletonRowCount }).map((_, rowIdx) => (
                <tr key={`skeleton-${rowIdx}`}>
                  {(onDelete || onBulkUpdate || bulkActions.length > 0) && (
                    <td className={s.checkboxCell}>
                      <div className={s.skeletonBox} style={{ width: 16, height: 16, borderRadius: 3 }} />
                    </td>
                  )}
                  {displayColumns.map((col, colIdx) => (
                    <td key={col.key}>
                      <div
                        className={s.skeleton}
                        style={{
                          width: col.type === 'select'
                            ? '70%'
                            : col.type === 'datetime' || col.type === 'date'
                              ? '60%'
                              : `${55 + ((rowIdx + colIdx) % 4) * 12}%`,
                          animationDelay: `${(rowIdx * 0.05) + (colIdx * 0.03)}s`,
                        }}
                      />
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              paginatedData.map(row => {
                const rowKey = keyExtractor(row)
                const isSelected = selectedRows.has(rowKey)

                return (
                  <tr
                    key={rowKey}
                    className={`${onRowClick ? shared.clickable : ''} ${isSelected ? s.selectedRow : ''} ${rowClassName ? rowClassName(row) : ''}`}
                    onClick={() => onRowClick?.(row)}
                  >
                    {(onDelete || onBulkUpdate || bulkActions.length > 0) && (
                      <td className={s.checkboxCell} onClick={e => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => {}}
                          onClick={(e) => toggleRowSelection(rowKey, e as unknown as React.MouseEvent)}
                          className={s.checkbox}
                        />
                      </td>
                    )}
                    {displayColumns.map(col => (
                      <td
                        key={col.key}
                        className={col.className}
                      >
                        {renderCell(row, col, onUpdate ? (v) => handleCellUpdate(row, col.key, v) : undefined)}
                      </td>
                    ))}
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination — always show during loading for consistent layout */}
      {(totalItems > 0 || loading) && (
        <TablePagination
          totalItems={loading ? 0 : totalItems}
          currentPage={loading ? 1 : safePage}
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

// Export data to Excel
function exportToExcel<T>(data: T[], columns: SmartColumn<T>[], storageKey?: string) {
  const rows = data.map(row => {
    const result: Record<string, unknown> = {}
    for (const col of columns) {
      if (col.key === '_actions') continue
      const rawValue = (row as Record<string, unknown>)[col.key]
      result[col.header] = formatDisplayValue(rawValue, col)
    }
    return result
  })

  const worksheet = XLSX.utils.json_to_sheet(rows)
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Data')
  const fileName = `${storageKey || 'table'}-${new Date().toISOString().slice(0, 10)}.xlsx`
  XLSX.writeFile(workbook, fileName)
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
    return column.render(row, onUpdate ? (v) => onUpdate(v) : () => { })
  }

  // View-only render
  if (column.renderView) {
    return column.renderView(row)
  }

  // Actions column or non-editable - just show value
  if (column.editable === false || column.key === '_actions' || !onUpdate) {
    return formatDisplayValue(value, column)
  }

  // Inline editable cell
  return (
    <InlineEditCell
      value={value}
      type={column.type}
      options={column.options}
      displayValue={column.displayValue ? column.displayValue(row) : formatDisplayValue(value, column)}
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
