import { useState, useEffect } from 'react'
import { Filter, Calendar } from 'lucide-react'
import s from '@/styles/shared.module.css'

interface DashboardFiltersProps {
  onFilterChange: (filters: FilterState) => void
  salespeople: Array<{ id: number; name: string }>
}

export interface FilterState {
  fromDate: string
  toDate: string
  cutoffDate: string
  statuses: string[]
  salespersonIds: number[]
  sources: string[]
  daysToFirstCall: number
}

const LEAD_STATUSES = [
  'ליד חדש',
  'ליד בתהליך',
  'חיוג ראשון',
  'ליד ישן',
  'נסלק',
  'תלמיד פעיל',
  'לא רלוונטי',
]

const LEAD_SOURCES = [
  'אתר',
  'פייסבוק',
  'גוגל',
  'הפניה',
  'אירוע',
  'טלפון',
  'אחר',
]

export function DashboardFilters({ onFilterChange, salespeople }: DashboardFiltersProps) {
  const [isOpen, setIsOpen] = useState(false)
  
  // Default: last 30 days, cutoff at 2024-12-01
  const today = new Date().toISOString().split('T')[0]
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  
  const [filters, setFilters] = useState<FilterState>({
    fromDate: thirtyDaysAgo,
    toDate: today,
    cutoffDate: '2024-12-01',
    statuses: [],
    salespersonIds: [],
    sources: [],
    daysToFirstCall: 3,
  })

  useEffect(() => {
    onFilterChange(filters)
  }, [filters, onFilterChange])

  const updateFilter = <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const toggleStatus = (status: string) => {
    setFilters(prev => ({
      ...prev,
      statuses: prev.statuses.includes(status)
        ? prev.statuses.filter(s => s !== status)
        : [...prev.statuses, status]
    }))
  }

  const toggleSalesperson = (id: number) => {
    setFilters(prev => ({
      ...prev,
      salespersonIds: prev.salespersonIds.includes(id)
        ? prev.salespersonIds.filter(spId => spId !== id)
        : [...prev.salespersonIds, id]
    }))
  }

  const toggleSource = (source: string) => {
    setFilters(prev => ({
      ...prev,
      sources: prev.sources.includes(source)
        ? prev.sources.filter(s => s !== source)
        : [...prev.sources, source]
    }))
  }

  const resetFilters = () => {
    setFilters({
      fromDate: thirtyDaysAgo,
      toDate: today,
      cutoffDate: '2024-12-01',
      statuses: [],
      salespersonIds: [],
      sources: [],
      daysToFirstCall: 3,
    })
  }

  const activeFilterCount = 
    filters.statuses.length + 
    filters.salespersonIds.length + 
    filters.sources.length +
    (filters.cutoffDate !== '2024-12-01' ? 1 : 0)

  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
        <button
          className={`${s.btn} ${s['btn-secondary']}`}
          onClick={() => setIsOpen(!isOpen)}
          style={{ display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <Filter size={16} />
          פילטרים
          {activeFilterCount > 0 && (
            <span style={{
              background: 'var(--color-primary)',
              color: 'white',
              borderRadius: '50%',
              width: 20,
              height: 20,
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 11,
              fontWeight: 600,
            }}>
              {activeFilterCount}
            </span>
          )}
        </button>

        {activeFilterCount > 0 && (
          <button
            className={`${s.btn} ${s['btn-ghost']}`}
            onClick={resetFilters}
            style={{ fontSize: 12 }}
          >
            איפוס
          </button>
        )}
      </div>

      {isOpen && (
        <div className={s.card} style={{ padding: 20 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 20 }}>
            {/* Date Range */}
            <div>
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                <Calendar size={16} />
                טווח תאריכים
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div className={s['form-group']}>
                  <label className={s['form-label']}>מתאריך</label>
                  <input
                    type="date"
                    className={s.input}
                    value={filters.fromDate}
                    onChange={e => updateFilter('fromDate', e.target.value)}
                    dir="ltr"
                  />
                </div>
                <div className={s['form-group']}>
                  <label className={s['form-label']}>עד תאריך</label>
                  <input
                    type="date"
                    className={s.input}
                    value={filters.toDate}
                    onChange={e => updateFilter('toDate', e.target.value)}
                    dir="ltr"
                  />
                </div>
                <div className={s['form-group']}>
                  <label className={s['form-label']}>תאריך cutoff (לידים ישנים)</label>
                  <input
                    type="date"
                    className={s.input}
                    value={filters.cutoffDate}
                    onChange={e => updateFilter('cutoffDate', e.target.value)}
                    dir="ltr"
                  />
                  <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                    לידים לפני תאריך זה לא ייכללו בחישובים
                  </span>
                </div>
              </div>
            </div>

            {/* Statuses */}
            <div>
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>סטטוסים</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {LEAD_STATUSES.map(status => (
                  <label key={status} style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={filters.statuses.includes(status)}
                      onChange={() => toggleStatus(status)}
                    />
                    <span style={{ fontSize: 13 }}>{status}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Salespeople */}
            <div>
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>אנשי מכירות</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 200, overflowY: 'auto' }}>
                {salespeople.map(sp => (
                  <label key={sp.id} style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={filters.salespersonIds.includes(sp.id)}
                      onChange={() => toggleSalesperson(sp.id)}
                    />
                    <span style={{ fontSize: 13 }}>{sp.name}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Sources */}
            <div>
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>מקורות</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {LEAD_SOURCES.map(source => (
                  <label key={source} style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={filters.sources.includes(source)}
                      onChange={() => toggleSource(source)}
                    />
                    <span style={{ fontSize: 13 }}>{source}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Settings */}
            <div>
              <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>הגדרות</h4>
              <div className={s['form-group']}>
                <label className={s['form-label']}>ימים עד חיוג ראשון (הזנחה)</label>
                <input
                  type="number"
                  className={s.input}
                  value={filters.daysToFirstCall}
                  onChange={e => updateFilter('daysToFirstCall', parseInt(e.target.value) || 3)}
                  min="1"
                  max="30"
                />
                <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                  לידים ללא חיוג ראשון תוך {filters.daysToFirstCall} ימים ייחשבו כמוזנחים
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
