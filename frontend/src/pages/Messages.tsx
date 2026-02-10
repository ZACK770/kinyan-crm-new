import { Send } from 'lucide-react'
import s from '@/styles/shared.module.css'

/* ══════════════════════════════════════════════════════════════
   Messages Page — placeholder with structure ready
   ══════════════════════════════════════════════════════════════ */
export function MessagesPage() {
  return (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>הודעות</h1>
      </div>

      <div className={s.card}>
        <div className={s.empty} style={{ padding: 60 }}>
          <span className={s['empty-icon']}><Send size={48} strokeWidth={1.5} /></span>
          <span className={s['empty-text']} style={{ fontSize: 15, fontWeight: 500 }}>מערכת הודעות</span>
          <span className={s['empty-text']}>
            מודול שליחת SMS, וואטסאפ ואימייל — ייפתח בקרוב
          </span>
        </div>
      </div>
    </div>
  )
}
