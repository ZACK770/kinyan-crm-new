/* ============================================================
   SmartTable Type Definitions
   ============================================================ */

import type { ReactNode } from 'react'

// Filter operator types based on field type
export type TextOperator = 'contains' | 'equals' | 'startsWith' | 'endsWith' | 'isEmpty' | 'isNotEmpty'
export type NumberOperator = 'equals' | 'gt' | 'gte' | 'lt' | 'lte' | 'between' | 'isEmpty' | 'isNotEmpty'
export type DateOperator = 
  | 'equals' | 'before' | 'after' | 'between' 
  | 'today' | 'yesterday' | 'thisWeek' | 'lastWeek' | 'thisMonth' | 'lastMonth' 
  | 'last7Days' | 'last30Days' | 'thisYear' | 'isEmpty' | 'isNotEmpty'
export type SelectOperator = 'equals' | 'notEquals' | 'in' | 'isEmpty' | 'isNotEmpty'
export type BooleanOperator = 'isTrue' | 'isFalse'

export type FilterOperator = TextOperator | NumberOperator | DateOperator | SelectOperator | BooleanOperator

// Column field types
export type FieldType = 'text' | 'number' | 'date' | 'datetime' | 'select' | 'boolean' | 'currency'

// Filter definition
export interface Filter {
  id: string
  field: string
  operator: FilterOperator
  value: string | number | boolean | null
  value2?: string | number | null // For 'between' operator
}

// Saved filter preset
export interface SavedFilter {
  id: string
  name: string
  filters: Filter[]
  columns: string[] // Visible column keys
  columnOrder: string[] // Column order
  createdAt: string
}

// Select option for dropdowns
export interface SelectOption {
  value: string | number
  label: string
}

// Column definition
export interface SmartColumn<T> {
  key: string
  header: string
  type: FieldType
  render?: (row: T, onUpdate: (value: unknown) => void) => ReactNode
  renderView?: (row: T) => ReactNode // Display-only render (no editing)
  options?: SelectOption[] // For select type
  editable?: boolean // Allow inline editing (default true)
  sortable?: boolean // Allow sorting (default true)
  filterable?: boolean // Allow filtering (default true)
  hiddenByDefault?: boolean // Start hidden
  width?: string | number
  minWidth?: number
  className?: string
  // Custom filter options (override default operators)
  filterOperators?: FilterOperator[]
}

// Bulk action definition
export interface BulkAction<T> {
  id: string
  label: string
  icon?: ReactNode
  variant?: 'primary' | 'secondary' | 'danger'
  // Action can be a simple callback or open a form
  action: (selectedRows: T[]) => void | Promise<void>
  // Or specify a field update action
  fieldUpdate?: {
    field: string
    label: string
    type: FieldType
    options?: SelectOption[]
  }
}

// SmartTable props
export interface SmartTableProps<T> {
  // Data
  data: T[]
  columns: SmartColumn<T>[]
  keyExtractor: (row: T) => string | number
  
  // State
  loading?: boolean
  emptyText?: string
  emptyIcon?: ReactNode
  
  // Events
  onRowClick?: (row: T) => void
  onUpdate?: (row: T, field: string, value: unknown) => Promise<void>
  onDelete?: (rows: T[]) => Promise<void>
  onBulkUpdate?: (rows: T[], field: string, value: unknown) => Promise<void>
  
  // Features
  bulkActions?: BulkAction<T>[]
  storageKey?: string // For persisting filters/columns to localStorage
  
  // UI customization
  className?: string
  toolbarExtra?: ReactNode // Extra toolbar content
}

// Filter panel state
export interface FilterPanelState {
  isOpen: boolean
  filters: Filter[]
  savedFilters: SavedFilter[]
  activeSavedFilterId: string | null
}

// Column manager state
export interface ColumnManagerState {
  isOpen: boolean
  visibleColumns: string[]
  columnOrder: string[]
}

// Table state (for persistence)
export interface TableState {
  filters: Filter[]
  visibleColumns: string[]
  columnOrder: string[]
  sortBy: string | null
  sortDir: 'asc' | 'desc'
}
