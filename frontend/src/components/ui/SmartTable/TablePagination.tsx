/* ============================================================
   TablePagination — Configurable pagination for SmartTable
   ============================================================
   Supports page size selection (100/200) and page navigation.
   Reusable across all table entities.
   ============================================================ */

import { useMemo } from 'react'
import { ChevronRight, ChevronLeft, ChevronsRight, ChevronsLeft } from 'lucide-react'
import s from './SmartTable.module.css'

export interface TablePaginationProps {
  totalItems: number
  currentPage: number
  pageSize: number
  pageSizeOptions?: number[]
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
}

export function TablePagination({
  totalItems,
  currentPage,
  pageSize,
  pageSizeOptions = [50, 100, 200],
  onPageChange,
  onPageSizeChange,
}: TablePaginationProps) {
  const totalPages = useMemo(() => Math.max(1, Math.ceil(totalItems / pageSize)), [totalItems, pageSize])

  // Ensure current page is valid
  const safePage = Math.min(currentPage, totalPages)

  const startItem = (safePage - 1) * pageSize + 1
  const endItem = Math.min(safePage * pageSize, totalItems)

  // Generate page numbers to show
  const pageNumbers = useMemo(() => {
    const pages: (number | 'ellipsis')[] = []
    const maxVisible = 5

    if (totalPages <= maxVisible + 2) {
      for (let i = 1; i <= totalPages; i++) pages.push(i)
    } else {
      pages.push(1)

      if (safePage > 3) pages.push('ellipsis')

      const start = Math.max(2, safePage - 1)
      const end = Math.min(totalPages - 1, safePage + 1)

      for (let i = start; i <= end; i++) pages.push(i)

      if (safePage < totalPages - 2) pages.push('ellipsis')

      pages.push(totalPages)
    }

    return pages
  }, [totalPages, safePage])

  if (totalItems === 0) return null

  return (
    <div className={s.pagination}>
      {/* Page size selector */}
      <div className={s.paginationRight}>
        <span className={s.paginationLabel}>הצג</span>
        <div className={s.pageSizeSelector}>
          {pageSizeOptions.map(size => (
            <button
              key={size}
              className={`${s.pageSizeBtn} ${pageSize === size ? s.pageSizeBtnActive : ''}`}
              onClick={() => onPageSizeChange(size)}
            >
              {size}
            </button>
          ))}
        </div>
        <span className={s.paginationLabel}>שורות</span>
      </div>

      {/* Info */}
      <div className={s.paginationCenter}>
        <span className={s.paginationInfo}>
          {startItem}–{endItem} מתוך {totalItems}
        </span>
      </div>

      {/* Page navigation */}
      <div className={s.paginationLeft}>
        <button
          className={s.pageBtn}
          onClick={() => onPageChange(1)}
          disabled={safePage === 1}
          title="עמוד ראשון"
        >
          <ChevronsRight size={16} />
        </button>
        <button
          className={s.pageBtn}
          onClick={() => onPageChange(safePage - 1)}
          disabled={safePage === 1}
          title="עמוד קודם"
        >
          <ChevronRight size={16} />
        </button>

        {pageNumbers.map((p, idx) =>
          p === 'ellipsis' ? (
            <span key={`e${idx}`} className={s.pageEllipsis}>…</span>
          ) : (
            <button
              key={p}
              className={`${s.pageBtn} ${p === safePage ? s.pageBtnActive : ''}`}
              onClick={() => onPageChange(p)}
            >
              {p}
            </button>
          )
        )}

        <button
          className={s.pageBtn}
          onClick={() => onPageChange(safePage + 1)}
          disabled={safePage === totalPages}
          title="עמוד הבא"
        >
          <ChevronLeft size={16} />
        </button>
        <button
          className={s.pageBtn}
          onClick={() => onPageChange(totalPages)}
          disabled={safePage === totalPages}
          title="עמוד אחרון"
        >
          <ChevronsLeft size={16} />
        </button>
      </div>
    </div>
  )
}

export default TablePagination
