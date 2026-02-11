/* ============================================================
   SmartSearch — Inline search with dropdown results
   ============================================================
   Reusable component for SmartTable. Shows instant search results
   in neat cards as the user types. No modal needed.
   ============================================================ */

import { useState, useRef, useEffect, useMemo, useCallback } from 'react'
import { Search, X } from 'lucide-react'
import type { SmartColumn, SelectOption, SearchFieldConfig } from './types'
import s from './SmartTable.module.css'

interface SmartSearchProps<T> {
  data: T[]
  columns: SmartColumn<T>[]
  /** Which fields to search in, with labels and optional weights */
  searchFields?: SearchFieldConfig[]
  /** Max results to show in dropdown */
  maxResults?: number
  onSelect: (row: T) => void
  placeholder?: string
  /** Called when search text changes — parent can use for additional filtering */
  onSearchChange?: (query: string) => void
}

export function SmartSearch<T>({
  data,
  columns,
  searchFields,
  maxResults = 8,
  onSelect,
  placeholder = 'חיפוש...',
  onSearchChange,
}: SmartSearchProps<T>) {
  const [query, setQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const [highlightIndex, setHighlightIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Determine searchable fields
  const fields = useMemo(() => {
    if (searchFields?.length) return searchFields
    // Default: all text/select columns that are filterable
    return columns
      .filter(c => c.filterable !== false && (c.type === 'text' || c.type === 'select'))
      .map(c => ({ key: c.key, label: c.header, weight: 1 }))
  }, [searchFields, columns])

  // Build a lookup for select options (value -> label)
  const selectLookup = useMemo(() => {
    const lookup: Record<string, Record<string, string>> = {}
    columns.forEach(col => {
      if (col.type === 'select' && col.options?.length) {
        lookup[col.key] = {}
        col.options.forEach((opt: SelectOption) => {
          lookup[col.key][String(opt.value)] = opt.label
        })
      }
    })
    return lookup
  }, [columns])

  // Search results
  const results = useMemo(() => {
    if (!query.trim()) return []

    const q = query.trim().toLowerCase()
    const scored: { row: T; score: number }[] = []

    for (const row of data) {
      let totalScore = 0
      const rec = row as Record<string, unknown>

      for (const field of fields) {
        const rawVal = rec[field.key]
        if (rawVal === null || rawVal === undefined) continue

        let strVal = String(rawVal).toLowerCase()

        // For select fields, also search in the label
        if (selectLookup[field.key]) {
          const label = selectLookup[field.key][String(rawVal)]
          if (label) strVal = `${strVal} ${label.toLowerCase()}`
        }

        const weight = field.weight ?? 1

        if (strVal === q) {
          totalScore += 10 * weight // Exact match
        } else if (strVal.startsWith(q)) {
          totalScore += 5 * weight // Starts with
        } else if (strVal.includes(q)) {
          totalScore += 2 * weight // Contains
        }
      }

      if (totalScore > 0) {
        scored.push({ row, score: totalScore })
      }
    }

    // Sort by score descending
    scored.sort((a, b) => b.score - a.score)
    return scored.slice(0, maxResults)
  }, [query, data, fields, selectLookup, maxResults])

  // Notify parent of search change
  useEffect(() => {
    onSearchChange?.(query)
  }, [query, onSearchChange])

  // Close dropdown on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      const target = e.target as Node
      if (
        dropdownRef.current && !dropdownRef.current.contains(target) &&
        inputRef.current && !inputRef.current.contains(target)
      ) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  // Reset highlight when results change
  useEffect(() => {
    setHighlightIndex(-1)
  }, [results])

  // Keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!isOpen || !results.length) {
      if (e.key === 'Escape') {
        setQuery('')
        setIsOpen(false)
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightIndex(prev => (prev + 1) % results.length)
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightIndex(prev => (prev - 1 + results.length) % results.length)
        break
      case 'Enter':
        e.preventDefault()
        if (highlightIndex >= 0 && highlightIndex < results.length) {
          handleSelect(results[highlightIndex].row)
        }
        break
      case 'Escape':
        setIsOpen(false)
        setQuery('')
        break
    }
  }, [isOpen, results, highlightIndex])

  const handleSelect = (row: T) => {
    onSelect(row)
    setQuery('')
    setIsOpen(false)
    inputRef.current?.blur()
  }

  // Get the primary display fields for the result card
  const getCardFields = (row: T) => {
    const rec = row as Record<string, unknown>
    const cardFields: { label: string; value: string }[] = []

    for (const col of columns) {
      if (col.key === '_actions') continue
      const val = rec[col.key]
      if (val === null || val === undefined || val === '') continue

      let displayVal = String(val)
      if (selectLookup[col.key]) {
        displayVal = selectLookup[col.key][String(val)] ?? displayVal
      }
      if (col.type === 'datetime' || col.type === 'date') {
        try {
          displayVal = new Date(val as string).toLocaleDateString('he-IL')
        } catch { /* keep original */ }
      }

      cardFields.push({ label: col.header, value: displayVal })
      if (cardFields.length >= 5) break // Limit fields shown
    }

    return cardFields
  }

  // Highlight matching text
  const highlightText = (text: string) => {
    if (!query.trim()) return text
    const q = query.trim()
    const idx = text.toLowerCase().indexOf(q.toLowerCase())
    if (idx === -1) return text
    return (
      <>
        {text.slice(0, idx)}
        <mark className={s.searchHighlight}>{text.slice(idx, idx + q.length)}</mark>
        {text.slice(idx + q.length)}
      </>
    )
  }

  return (
    <div className={s.smartSearch}>
      <div className={s.searchInputWrapper}>
        <Search size={16} className={s.searchIcon} />
        <input
          ref={inputRef}
          type="text"
          className={s.searchInput}
          placeholder={placeholder}
          value={query}
          onChange={e => {
            setQuery(e.target.value)
            setIsOpen(true)
          }}
          onFocus={() => {
            if (query.trim()) setIsOpen(true)
          }}
          onKeyDown={handleKeyDown}
          dir="auto"
        />
        {query && (
          <button
            className={s.searchClear}
            onClick={() => {
              setQuery('')
              setIsOpen(false)
              inputRef.current?.focus()
            }}
            type="button"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Dropdown results */}
      {isOpen && query.trim() && (
        <div ref={dropdownRef} className={s.searchDropdown}>
          {results.length === 0 ? (
            <div className={s.searchNoResults}>
              לא נמצאו תוצאות עבור "{query}"
            </div>
          ) : (
            <>
              <div className={s.searchResultsHeader}>
                {results.length} תוצאות
              </div>
              {results.map(({ row }, idx) => {
                const cardFields = getCardFields(row)
                const isHighlighted = idx === highlightIndex

                return (
                  <div
                    key={idx}
                    className={`${s.searchResultCard} ${isHighlighted ? s.searchResultHighlighted : ''}`}
                    onClick={() => handleSelect(row)}
                    onMouseEnter={() => setHighlightIndex(idx)}
                  >
                    {cardFields.map((f, i) => (
                      <div key={i} className={i === 0 ? s.searchResultPrimary : s.searchResultField}>
                        {i > 0 && <span className={s.searchFieldLabel}>{f.label}:</span>}
                        <span className={i === 0 ? s.searchResultName : s.searchResultValue}>
                          {highlightText(f.value)}
                        </span>
                      </div>
                    ))}
                  </div>
                )
              })}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default SmartSearch
