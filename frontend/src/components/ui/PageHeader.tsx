/**
 * Generic Page Header with Create Button
 * Consistent header across all entity pages
 */
import { Plus, RefreshCw } from 'lucide-react'
import s from '@/styles/shared.module.css'

interface PageHeaderProps {
  title: string
  createLabel?: string
  onCreate?: () => void
  onRefresh?: () => void
  loading?: boolean
  children?: React.ReactNode  // For filters
}

export function PageHeader({ 
  title, 
  createLabel, 
  onCreate, 
  onRefresh, 
  loading = false,
  children 
}: PageHeaderProps) {
  return (
    <div className={s['page-header']}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <h1 className={s['page-title']}>{title}</h1>
        {onRefresh && (
          <button 
            className={`${s.btn} ${s['btn-ghost']} ${s['btn-sm']}`}
            onClick={onRefresh}
            disabled={loading}
            title="רענון"
          >
            <RefreshCw size={16} strokeWidth={1.5} className={loading ? 'spin' : ''} />
          </button>
        )}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {children}
        {onCreate && createLabel && (
          <button className={`${s.btn} ${s['btn-primary']}`} onClick={onCreate}>
            <Plus size={18} strokeWidth={2} />
            {createLabel}
          </button>
        )}
      </div>
    </div>
  )
}
