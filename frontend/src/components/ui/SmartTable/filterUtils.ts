/* ============================================================
   SmartTable Filter Utilities
   ============================================================ */

import type { Filter, FilterOperator, FieldType, FilterMode, SavedFilter, TableState } from './types'

// Generate unique ID
export const generateId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`

// Operator labels (Hebrew)
export const operatorLabels: Record<FilterOperator, string> = {
  // Text
  contains: 'מכיל',
  equals: 'שווה ל',
  startsWith: 'מתחיל ב',
  endsWith: 'מסתיים ב',
  isEmpty: 'ריק',
  isNotEmpty: 'לא ריק',
  // Number
  gt: 'גדול מ',
  gte: 'גדול או שווה',
  lt: 'קטן מ',
  lte: 'קטן או שווה',
  between: 'בין',
  // Select
  notEquals: 'שונה מ',
  in: 'אחד מ',
  // Boolean
  isTrue: 'כן',
  isFalse: 'לא',
  // Date
  before: 'לפני',
  after: 'אחרי',
  today: 'היום',
  yesterday: 'אתמול',
  thisWeek: 'השבוע',
  lastWeek: 'שבוע שעבר',
  thisMonth: 'החודש הנוכחי',
  lastMonth: 'חודש שעבר',
  last7Days: '7 ימים אחרונים',
  last30Days: '30 ימים אחרונים',
  thisYear: 'השנה',
}

// Get operators for field type
export function getOperatorsForType(type: FieldType): FilterOperator[] {
  switch (type) {
    case 'text':
      return ['contains', 'equals', 'startsWith', 'endsWith', 'isEmpty', 'isNotEmpty']
    case 'number':
    case 'currency':
      return ['equals', 'gt', 'gte', 'lt', 'lte', 'between', 'isEmpty', 'isNotEmpty']
    case 'date':
    case 'datetime':
      return [
        'today', 'yesterday', 'thisWeek', 'lastWeek', 'thisMonth', 'lastMonth',
        'last7Days', 'last30Days', 'thisYear',
        'equals', 'before', 'after', 'between', 'isEmpty', 'isNotEmpty'
      ]
    case 'select':
      return ['equals', 'notEquals', 'in', 'isEmpty', 'isNotEmpty']
    case 'boolean':
      return ['isTrue', 'isFalse']
    default:
      return ['contains', 'equals', 'isEmpty', 'isNotEmpty']
  }
}

// Check if operator needs a value input
export function operatorNeedsValue(operator: FilterOperator): boolean {
  return !['isEmpty', 'isNotEmpty', 'today', 'yesterday', 'thisWeek', 'lastWeek',
    'thisMonth', 'lastMonth', 'last7Days', 'last30Days', 'thisYear',
    'isTrue', 'isFalse'].includes(operator)
}

// Check if operator needs second value (between)
export function operatorNeedsSecondValue(operator: FilterOperator): boolean {
  return operator === 'between'
}

// Get date range for date operators
function getDateRange(operator: FilterOperator): { start: Date; end: Date } | null {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())

  switch (operator) {
    case 'today':
      return { start: today, end: new Date(today.getTime() + 86400000 - 1) }
    case 'yesterday': {
      const yesterday = new Date(today.getTime() - 86400000)
      return { start: yesterday, end: new Date(today.getTime() - 1) }
    }
    case 'thisWeek': {
      const dayOfWeek = today.getDay()
      const startOfWeek = new Date(today.getTime() - dayOfWeek * 86400000)
      return { start: startOfWeek, end: now }
    }
    case 'lastWeek': {
      const dayOfWeek = today.getDay()
      const startOfThisWeek = new Date(today.getTime() - dayOfWeek * 86400000)
      const startOfLastWeek = new Date(startOfThisWeek.getTime() - 7 * 86400000)
      return { start: startOfLastWeek, end: new Date(startOfThisWeek.getTime() - 1) }
    }
    case 'thisMonth': {
      const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
      return { start: startOfMonth, end: now }
    }
    case 'lastMonth': {
      const startOfThisMonth = new Date(now.getFullYear(), now.getMonth(), 1)
      const startOfLastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1)
      return { start: startOfLastMonth, end: new Date(startOfThisMonth.getTime() - 1) }
    }
    case 'last7Days': {
      const start = new Date(today.getTime() - 7 * 86400000)
      return { start, end: now }
    }
    case 'last30Days': {
      const start = new Date(today.getTime() - 30 * 86400000)
      return { start, end: now }
    }
    case 'thisYear': {
      const startOfYear = new Date(now.getFullYear(), 0, 1)
      return { start: startOfYear, end: now }
    }
    default:
      return null
  }
}

// Apply a single filter to a row
export function applyFilter<T>(row: T, filter: Filter, type: FieldType): boolean {
  const value = (row as Record<string, unknown>)[filter.field]
  const filterValue = filter.value
  const filterValue2 = filter.value2

  // Handle empty checks
  if (filter.operator === 'isEmpty') {
    return value === null || value === undefined || value === ''
  }
  if (filter.operator === 'isNotEmpty') {
    return value !== null && value !== undefined && value !== ''
  }

  // Handle boolean
  if (type === 'boolean') {
    if (filter.operator === 'isTrue') return value === true
    if (filter.operator === 'isFalse') return value === false
  }

  // Handle text
  if (type === 'text') {
    const strValue = String(value ?? '').toLowerCase()
    const strFilter = String(filterValue ?? '').toLowerCase()

    switch (filter.operator) {
      case 'contains': return strValue.includes(strFilter)
      case 'equals': return strValue === strFilter
      case 'startsWith': return strValue.startsWith(strFilter)
      case 'endsWith': return strValue.endsWith(strFilter)
      default: return true
    }
  }

  // Handle number/currency
  if (type === 'number' || type === 'currency') {
    const numValue = Number(value)
    const numFilter = Number(filterValue)
    const numFilter2 = Number(filterValue2)

    if (isNaN(numValue)) return String(filter.operator) === 'isEmpty'

    switch (filter.operator) {
      case 'equals': return numValue === numFilter
      case 'gt': return numValue > numFilter
      case 'gte': return numValue >= numFilter
      case 'lt': return numValue < numFilter
      case 'lte': return numValue <= numFilter
      case 'between': return numValue >= numFilter && numValue <= numFilter2
      default: return true
    }
  }

  // Handle date/datetime
  if (type === 'date' || type === 'datetime') {
    const dateValue = value ? new Date(value as string) : null

    // Check preset date ranges
    const dateRange = getDateRange(filter.operator)
    if (dateRange && dateValue) {
      return dateValue >= dateRange.start && dateValue <= dateRange.end
    }

    const filterDate = filterValue ? new Date(filterValue as string) : null
    const filterDate2 = filterValue2 ? new Date(filterValue2 as string) : null

    if (!dateValue) return false

    switch (filter.operator) {
      case 'equals':
        if (!filterDate) return false
        return dateValue.toDateString() === filterDate.toDateString()
      case 'before':
        if (!filterDate) return false
        return dateValue < filterDate
      case 'after':
        if (!filterDate) return false
        return dateValue > filterDate
      case 'between':
        if (!filterDate || !filterDate2) return false
        return dateValue >= filterDate && dateValue <= filterDate2
      default: return true
    }
  }

  // Handle select
  if (type === 'select') {
    const strValue = String(value ?? '')
    const strFilter = String(filterValue ?? '')
    const filterValues = filter.values?.map(v => String(v)) ?? []

    switch (filter.operator) {
      case 'equals':
        return filterValues.length > 0 ? filterValues.includes(strValue) : strValue === strFilter
      case 'notEquals':
        return filterValues.length > 0 ? !filterValues.includes(strValue) : strValue !== strFilter
      case 'in': {
        const values = strFilter.split(',').map(v => v.trim())
        return values.includes(strValue)
      }
      default: return true
    }
  }

  return true
}

// Apply all filters to data
export function applyFilters<T>(
  data: T[],
  filters: Filter[],
  columns: { key: string; type: FieldType }[],
  filterMode: FilterMode = 'and'
): T[] {
  if (!filters.length) return data

  return data.filter(row => {
    const matcher = filterMode === 'or' ? filters.some.bind(filters) : filters.every.bind(filters)
    return matcher(filter => {
      const column = columns.find(c => c.key === filter.field)
      if (!column) return true
      return applyFilter(row, filter, column.type)
    })
  })
}

// Storage helpers
export function loadTableState(key: string): TableState | null {
  try {
    const stored = localStorage.getItem(`smarttable_${key}`)
    if (!stored) return null
    return JSON.parse(stored)
  } catch {
    return null
  }
}

export function saveTableState(key: string, state: TableState): void {
  try {
    localStorage.setItem(`smarttable_${key}`, JSON.stringify(state))
  } catch {
    // Ignore storage errors
  }
}

export function loadSavedFilters(key: string): SavedFilter[] {
  try {
    const stored = localStorage.getItem(`smarttable_filters_${key}`)
    if (!stored) return []
    return JSON.parse(stored)
  } catch {
    return []
  }
}

export function saveSavedFilters(key: string, filters: SavedFilter[]): void {
  try {
    localStorage.setItem(`smarttable_filters_${key}`, JSON.stringify(filters))
  } catch {
    // Ignore storage errors
  }
}
