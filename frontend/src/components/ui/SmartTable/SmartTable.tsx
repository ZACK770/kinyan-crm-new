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
  operatorNeedsValue,
  operatorNeedsSecondValue,
  loadSavedFilters, 
  saveSavedFilters 
} from './filterUtils'
import s from './SmartTable.module.css'
import shared from '@/styles/shared.module.css'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui'

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
  const toast = useToast()

  // Search & Pagination props with defaults
  const searchSelect = onSearchSelect ?? onRowClick
  const defaultPgSize = defaultPageSize ?? 100
  const pgSizeOpts = pageSizeOptions ?? [50, 100, 200]

  // Shift-click selection tracking
  const lastSelectedIndexRef = useRef<number | null>(null)

  const serverPersistTimeoutRef = useRef<number | null>(null)

  const [canPublishGlobal, setCanPublishGlobal] = useState(false)
  const [isPublishingGlobal, setIsPublishingGlobal] = useState(false)

  // State
  const [filters, setFilters] = useState<Filter[]>([])
  const [filterMode, setFilterMode] = useState<FilterMode>('and')
  const [userSavedFilters, setUserSavedFilters] = useState<SavedFilter[]>([])
  const [globalSavedFilters, setGlobalSavedFilters] = useState<SavedFilter[]>([])
  const [activeSavedFilterId, setActiveSavedFilterId] = useState<string | null>(null)
  const [visibleColumns, setVisibleColumns] = useState<string[]>([])
  const [columnOrder, setColumnOrder] = useState<string[]>([])
  const [sortBy, setSortBy] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [selectedRows, setSelectedRows] = useState<Set<string | number>>(new Set())
  const [isAllSelected, setIsAllSelected] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(defaultPgSize)

  // Track if we're in the middle of clearing filters to prevent reload
  const [isClearingFilters, setIsClearingFilters] = useState(false)

  // Clear filters properly - resets active filter and updates state
  const handleClearFilters = useCallback(() => {
    setIsClearingFilters(true)
    setFilters([])
    setActiveSavedFilterId(null)
    // Reset flag after a short delay to allow state to settle
    setTimeout(() => setIsClearingFilters(false), 100)
  }, [])

  // Initialize state from storage or defaults
  useEffect(() => {
    // Set default visible columns
    const defaultVisible = columns
      .filter(c => !c.hiddenByDefault)
      .map(c => c.key)
    
    const defaultOrder = columns.map(c => c.key)

    if (!storageKey) {
      setVisibleColumns(defaultVisible)
      setColumnOrder(defaultOrder)
      return
    }

    ;(async () => {
      try {
        const me = await api.get<{ permission_level: number }>('/auth/me')
        setCanPublishGlobal(Number(me?.permission_level) >= 40)
      } catch {
        setCanPublishGlobal(false)
      }
    })()

    // Load local cached state first (fast)
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

    const savedFiltersList = loadSavedFilters(storageKey)
    setUserSavedFilters(savedFiltersList)

    // Then load from server (source-of-truth, sync between devices)
    let cancelled = false
    ;(async () => {
      // Skip server load if we're in the middle of clearing filters
      if (isClearingFilters) return
      
      try {
        const res = await api.get<{ storage_key: string; data: any }>(
          `/users/me/saved-table-prefs?storage_key=${encodeURIComponent(storageKey)}`
        )
        if (cancelled) return
        const data = res?.data
        if (!data) return

        const serverTableState = data.tableState as TableState | undefined
        const serverSavedFilters = data.savedFilters as SavedFilter[] | undefined

        if (serverTableState) {
          // Only apply saved filters if they're valid (not empty/null values)
          const validFilters = (serverTableState.filters || []).filter((f: any) => {
            if (!f.field || !f.operator) return false
            // Operators that don't require a value are valid even with null/empty value
            if (!operatorNeedsValue(f.operator)) return true

            // Operators that require a value must have one
            if (f.value === null || f.value === undefined || f.value === '') return false

            // 'between' requires value2 as well
            if (operatorNeedsSecondValue(f.operator)) {
              return !(f.value2 === null || f.value2 === undefined || f.value2 === '')
            }

            return true
          })
          
          setFilters(validFilters)
          setFilterMode(serverTableState.filterMode || 'and')
          setVisibleColumns(serverTableState.visibleColumns?.length ? serverTableState.visibleColumns : defaultVisible)
          setColumnOrder(serverTableState.columnOrder?.length ? serverTableState.columnOrder : defaultOrder)
          setSortBy(serverTableState.sortBy || null)
          setSortDir(serverTableState.sortDir || 'asc')
          if (serverTableState.pageSize) setPageSize(serverTableState.pageSize)

          // Refresh local cache
          saveTableState(storageKey, serverTableState)
        }

        if (Array.isArray(serverSavedFilters)) {
          setUserSavedFilters(serverSavedFilters)
          saveSavedFilters(storageKey, serverSavedFilters)
        }
      } catch {
        // Ignore server errors; local cache remains
      }
    })()

    ;(async () => {
      // Skip global prefs load if we're in the middle of clearing filters
      if (isClearingFilters) return
      
      try {
        const res = await api.get<{ storage_key: string; data: any }>(
          `/table-prefs/global?storage_key=${encodeURIComponent(storageKey)}`
        )
        if (cancelled) return
        const data = res?.data
        if (!data) return

        const serverGlobalSavedFilters = data.savedFilters as SavedFilter[] | undefined
        if (Array.isArray(serverGlobalSavedFilters)) {
          setGlobalSavedFilters(serverGlobalSavedFilters)
        }

        const serverGlobalTableState = data.tableState as TableState | undefined
        if (serverGlobalTableState && !savedState) {
          // Only apply global filters if they're valid (not empty/null values)
          const validFilters = (serverGlobalTableState.filters || []).filter((f: any) => {
            if (!f.field || !f.operator) return false
            // Operators that don't require a value are valid even with null/empty value
            if (!operatorNeedsValue(f.operator)) return true

            // Operators that require a value must have one
            if (f.value === null || f.value === undefined || f.value === '') return false

            // 'between' requires value2 as well
            if (operatorNeedsSecondValue(f.operator)) {
              return !(f.value2 === null || f.value2 === undefined || f.value2 === '')
            }

            return true
          })
          
          setFilters(validFilters)
          setFilterMode(serverGlobalTableState.filterMode || 'and')
          setVisibleColumns(serverGlobalTableState.visibleColumns?.length ? serverGlobalTableState.visibleColumns : defaultVisible)
          setColumnOrder(serverGlobalTableState.columnOrder?.length ? serverGlobalTableState.columnOrder : defaultOrder)
          setSortBy(serverGlobalTableState.sortBy || null)
          setSortDir(serverGlobalTableState.sortDir || 'asc')
          if (serverGlobalTableState.pageSize) setPageSize(serverGlobalTableState.pageSize)
        }
      } catch {
        // Ignore server errors
      }
    })()

    return () => {
      cancelled = true
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

  // Persist saved filters + table state to server (debounced)
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

    if (serverPersistTimeoutRef.current) {
      window.clearTimeout(serverPersistTimeoutRef.current)
    }

    serverPersistTimeoutRef.current = window.setTimeout(async () => {
      try {
        await api.put(
          `/users/me/saved-table-prefs?storage_key=${encodeURIComponent(storageKey)}`,
          {
            data: {
              tableState: state,
              savedFilters: userSavedFilters,
              updatedAt: new Date().toISOString(),
            },
          }
        )
      } catch {
        // Ignore server errors; local cache remains
      }
    }, 750)

    return () => {
      if (serverPersistTimeoutRef.current) {
        window.clearTimeout(serverPersistTimeoutRef.current)
      }
    }
  }, [filters, filterMode, visibleColumns, columnOrder, sortBy, sortDir, pageSize, userSavedFilters, storageKey])

  const effectiveSavedFilters = useMemo(() => {
    return [...globalSavedFilters, ...userSavedFilters]
  }, [globalSavedFilters, userSavedFilters])

  const handlePublishGlobal = useCallback(async (savedFilterId: string) => {
    if (!storageKey) return

    const source = userSavedFilters.find(f => f.id === savedFilterId)
    if (!source) {
      toast.error('לא ניתן לפרסם', 'בחר פילטר שמור (לא גלובלי) כדי לפרסם')
      return
    }

    const globalId = `g_${savedFilterId}`
    const published: SavedFilter = {
      ...source,
      id: globalId,
    }

    const updatedGlobalSavedFilters = (() => {
      const idx = globalSavedFilters.findIndex(f => f.id === globalId)
      if (idx === -1) return [...globalSavedFilters, published]
      const next = [...globalSavedFilters]
      next[idx] = published
      return next
    })()

    const state: TableState = {
      filters,
      filterMode,
      visibleColumns,
      columnOrder,
      sortBy,
      sortDir,
      pageSize,
    }
    try {
      setIsPublishingGlobal(true)
      await api.put(
        `/table-prefs/global?storage_key=${encodeURIComponent(storageKey)}`,
        {
          data: {
            tableState: state,
            savedFilters: updatedGlobalSavedFilters,
            updatedAt: new Date().toISOString(),
          },
        }
      )
      setGlobalSavedFilters(updatedGlobalSavedFilters)
      setActiveSavedFilterId(globalId)
      toast.success('פורסם לכולם', `הפילטר "${source.name}" פורסם בהצלחה`)
    } catch (e: any) {
      toast.error('שגיאה בפרסום', e?.message || 'לא ניתן לפרסם כרגע')
    } finally {
      setIsPublishingGlobal(false)
    }
  }, [
    storageKey,
    userSavedFilters,
    globalSavedFilters,
    filters,
    filterMode,
    visibleColumns,
    columnOrder,
    sortBy,
    sortDir,
    pageSize,
    toast,
  ])

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
    const updated = [...userSavedFilters, newFilter]
    setUserSavedFilters(updated)
    setActiveSavedFilterId(newFilter.id)
    if (storageKey) {
      saveSavedFilters(storageKey, updated)
    }
  }, [userSavedFilters, visibleColumns, columnOrder, storageKey])

  // Handle filter load
  const handleLoadFilter = useCallback((savedFilter: SavedFilter) => {
    setFilters(savedFilter.filters)
    if (savedFilter.columns?.length) setVisibleColumns(savedFilter.columns)
    if (savedFilter.columnOrder?.length) setColumnOrder(savedFilter.columnOrder)
    setActiveSavedFilterId(savedFilter.id)
  }, [])

  // Handle filter delete
  const handleDeleteSavedFilter = useCallback((id: string) => {
    const updated = userSavedFilters.filter(f => f.id !== id)
    setUserSavedFilters(updated)
    if (activeSavedFilterId === id) setActiveSavedFilterId(null)
    if (storageKey) {
      saveSavedFilters(storageKey, updated)
    }
  }, [userSavedFilters, activeSavedFilterId, storageKey])

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

  // Handle row selection (with shift-click range support)
  const toggleRowSelection = (rowKey: string | number, event?: React.MouseEvent) => {
    const currentIndex = paginatedData.findIndex(row => keyExtractor(row) === rowKey)
    const newSelected = new Set(selectedRows)

    if (event?.shiftKey && lastSelectedIndexRef.current !== null && currentIndex !== -1) {
      // Shift-click: select range
      const start = Math.min(lastSelectedIndexRef.current, currentIndex)
      const end = Math.max(lastSelectedIndexRef.current, currentIndex)
      for (let i = start; i <= end; i++) {
        newSelected.add(keyExtractor(paginatedData[i]))
      }
    } else {
      // Normal click: toggle single
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
            savedFilters={effectiveSavedFilters}
            activeSavedFilterId={activeSavedFilterId}
            onFiltersChange={setFilters}
            onFilterModeChange={setFilterMode}
            onSaveFilter={handleSaveFilter}
            onLoadFilter={handleLoadFilter}
            onDeleteSavedFilter={handleDeleteSavedFilter}
            canPublishGlobal={canPublishGlobal}
            onPublishGlobal={handlePublishGlobal}
            isPublishingGlobal={isPublishingGlobal}
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
              // Skeleton rows while loading
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
                          width: col.type === 'select' ? '70%' : col.type === 'datetime' || col.type === 'date' ? '60%' : `${55 + ((rowIdx + colIdx) % 4) * 12}%`,
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
                    {/* Selection checkbox */}
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
            onClick={handleClearFilters}
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
    const obj: Record<string, unknown> = {}
    for (const col of columns) {
      if (col.key === '_actions') continue
      const value = (row as Record<string, unknown>)[col.key]
      if (col.type === 'select' && col.options?.length) {
        const opt = col.options.find(o => String(o.value) === String(value))
        obj[col.header] = opt?.label ?? (value ?? '')
      } else if (col.type === 'boolean') {
        obj[col.header] = value === true ? 'כן' : value === false ? 'לא' : ''
      } else if (col.type === 'currency') {
        obj[col.header] = value != null ? Number(value) : ''
      } else if (col.type === 'date' && value) {
        try { obj[col.header] = new Date(value as string).toLocaleDateString('he-IL') } catch { obj[col.header] = value }
      } else if (col.type === 'datetime' && value) {
        try { obj[col.header] = new Date(value as string).toLocaleString('he-IL') } catch { obj[col.header] = value }
      } else {
        obj[col.header] = value ?? ''
      }
    }
    return obj
  })

  const ws = XLSX.utils.json_to_sheet(rows)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Data')

  const filename = `${storageKey || 'export'}_${new Date().toISOString().slice(0, 10)}.xlsx`
  XLSX.writeFile(wb, filename)
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
    <div onClick={e => e.stopPropagation()}>
      <InlineEditCell
        value={value}
        type={column.type}
        options={column.options}
        displayValue={customDisplay ?? formatDisplayValue(value, column)}
        onSave={onUpdate}
      />
    </div>
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
