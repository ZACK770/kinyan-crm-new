import { UserCheck } from 'lucide-react'
import s from '@/styles/shared.module.css'

/* ══════════════════════════════════════════════════════════════
   Lecturers Page — placeholder with structure ready
   ══════════════════════════════════════════════════════════════ */
export function LecturersPage() {
  return (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>מרצים</h1>
      </div>

      <div className={s.card}>
        <div className={s.empty} style={{ padding: 60 }}>
          <span className={s['empty-icon']}><UserCheck size={48} strokeWidth={1.5} /></span>
          <span className={s['empty-text']} style={{ fontSize: 15, fontWeight: 500 }}>ניהול מרצים</span>
          <span className={s['empty-text']}>
            מודול ניהול מרצים ומשתלמים — ייפתח בקרוב
          </span>
        </div>
      </div>
    </div>
  )
}
