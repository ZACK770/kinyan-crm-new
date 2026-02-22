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

// Filter combination mode
export type FilterMode = 'and' | 'or'

// Filter definition
export interface Filter {
  id: string
  field: string
  operator: FilterOperator
  value: string | number | boolean | null
  value2?: string | number | null // For 'between' operator
  values?: (string | number)[] // For multi-value equals/notEquals
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

// Search field configuration
export interface SearchFieldConfig {
  key: string
  label: string
  /** Weight for ranking (higher = more important). Default 1 */
  weight?: number
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
  
  // Search
  searchFields?: SearchFieldConfig[] // Fields to search in (defaults to all text/select)
  searchPlaceholder?: string
  onSearchSelect?: (row: T) => void // Called when a search result is clicked
  onServerSearch?: (query: string) => Promise<T[]> // Server-side search (searches ALL data, not just loaded)
  
  // Pagination
  defaultPageSize?: number // Default items per page (default: 100)
  pageSizeOptions?: number[] // Available page sizes (default: [50, 100, 200])
  
  // UI customization
  className?: string
  toolbarExtra?: ReactNode // Extra toolbar content
  rowClassName?: (row: T) => string // Dynamic row class based on data
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
  filterMode: FilterMode
  visibleColumns: string[]
  columnOrder: string[]
  sortBy: string | null
  sortDir: 'asc' | 'desc'
  pageSize?: number
}
