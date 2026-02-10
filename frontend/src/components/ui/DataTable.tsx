import { type ReactNode } from 'react'
import { Inbox } from 'lucide-react'
import s from '@/styles/shared.module.css'

export interface Column<T> {
  key: string
  header: string
  render?: (row: T) => ReactNode
  className?: string
}

interface Props<T> {
  columns: Column<T>[]
  data: T[]
  loading?: boolean
  emptyText?: string
  emptyIcon?: ReactNode
  onRowClick?: (row: T) => void
  keyExtractor: (row: T) => string | number
}

export function DataTable<T>({
  columns,
  data,
  loading,
  emptyText,
  emptyIcon,
  onRowClick,
  keyExtractor,
}: Props<T>) {
  if (loading) {
    return <div className={s.loading}>טוען נתונים...</div>
  }

  if (!data.length) {
    return (
      <div className={s.empty}>
        <span className={s['empty-icon']}>
          {emptyIcon || <Inbox size={40} strokeWidth={1.5} />}
        </span>
        <span className={s['empty-text']}>{emptyText || 'אין נתונים להצגה'}</span>
      </div>
    )
  }

  return (
    <div className={s['table-wrapper']}>
      <table className={s.table}>
        <thead>
          <tr>
            {columns.map(col => (
              <th key={col.key}>{col.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map(row => (
            <tr
              key={keyExtractor(row)}
              className={onRowClick ? s.clickable : undefined}
              onClick={() => onRowClick?.(row)}
            >
              {columns.map(col => (
                <td key={col.key} className={col.className || undefined}>
                  {col.render
                    ? col.render(row)
                    : ((row as Record<string, unknown>)[col.key] as ReactNode)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
