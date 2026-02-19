import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  type FC,
  type ReactNode,
} from 'react'
import { X, Megaphone, Flame, PartyPopper, AlertTriangle, Trophy } from 'lucide-react'
import { api } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import styles from './PopupAnnouncement.module.css'
import clsx from 'clsx'

/* ============================================================
   Types
   ============================================================ */

interface PopupData {
  id: number
  title: string
  body?: string | null
  image_url?: string | null
  cta_text?: string | null
  cta_link?: string | null
  theme: string
  animation: string
  target_audience: string
  min_permission_level: number
  is_active: boolean
  start_at?: string | null
  end_at?: string | null
  show_count: number
  priority: number
}

interface PopupContextType {
  checkNow: () => void
}

const PopupContext = createContext<PopupContextType | null>(null)

export function usePopupAnnouncements(): PopupContextType {
  const ctx = useContext(PopupContext)
  if (!ctx) throw new Error('usePopupAnnouncements must be used within PopupAnnouncementProvider')
  return ctx
}

/* ============================================================
   Theme icons
   ============================================================ */

const THEME_ICONS: Record<string, FC<{ size?: number }>> = {
  default: Megaphone,
  success: Trophy,
  warning: AlertTriangle,
  fire: Flame,
  celebration: PartyPopper,
}


/* ============================================================
   Single Popup Display
   ============================================================ */

const PopupDisplay: FC<{
  popup: PopupData
  onDismiss: () => void
}> = ({ popup, onDismiss }) => {
  const [exiting, setExiting] = useState(false)

  const handleDismiss = useCallback(() => {
    setExiting(true)
    setTimeout(onDismiss, 300)
  }, [onDismiss])

  const handleCta = useCallback(() => {
    if (popup.cta_link) {
      window.open(popup.cta_link, '_blank', 'noopener')
    }
    handleDismiss()
  }, [popup.cta_link, handleDismiss])

  const themeClass = styles[`theme-${popup.theme}`] || styles['theme-default']
  const animClass = styles[popup.animation] || styles.slideUp
  const Icon = THEME_ICONS[popup.theme] || THEME_ICONS.default

  return (
    <div
      className={clsx(styles.overlay, animClass, themeClass, exiting && styles.exiting)}
      onClick={(e) => { if (e.target === e.currentTarget) handleDismiss() }}
    >
      <div className={styles.card}>
        {/* Celebration confetti */}
        {popup.theme === 'celebration' && (
          <div className={styles.confetti}>
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className={styles.confettiPiece} />
            ))}
          </div>
        )}

        {/* Accent bar */}
        <div className={styles.accentBar} />

        {/* Close button */}
        <button className={styles.closeBtn} onClick={handleDismiss} aria-label="סגירה">
          <X size={16} strokeWidth={2} />
        </button>

        {/* Image */}
        {popup.image_url && (
          <div className={styles.imageWrapper}>
            <img src={popup.image_url} alt="" className={styles.image} />
            <div className={styles.imageGradient} />
          </div>
        )}

        {/* Content */}
        <div className={styles.content}>
          {!popup.image_url && (
            <div className={styles.themeIcon}>
              <Icon size={26} />
            </div>
          )}
          <h2 className={styles.title}>{popup.title}</h2>
          {popup.body && <p className={styles.body}>{popup.body}</p>}
        </div>

        {/* Actions */}
        <div className={styles.actions}>
          {popup.cta_text && (
            <button className={styles.ctaBtn} onClick={handleCta}>
              {popup.cta_text}
            </button>
          )}
          <button className={styles.dismissBtn} onClick={handleDismiss}>
            הבנתי, תודה
          </button>
        </div>
      </div>
    </div>
  )
}

/* ============================================================
   Provider — polls for active popups
   ============================================================ */

const POLL_INTERVAL = 60 * 60 * 1000 // 1 hour

export const PopupAnnouncementProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth()
  const [queue, setQueue] = useState<PopupData[]>([])
  const [currentPopup, setCurrentPopup] = useState<PopupData | null>(null)
  const [isPreview, setIsPreview] = useState(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const mountedRef = useRef(true)

  const fetchPopups = useCallback(async () => {
    if (!mountedRef.current) return
    try {
      const data = await api.get<PopupData[]>('/popups/active')
      if (!mountedRef.current) return
      if (data.length > 0) {
        setQueue(data)
      }
    } catch {
      // silently ignore — user might not be authenticated yet
    }
  }, [])

  // Show next popup from queue
  useEffect(() => {
    if (!currentPopup && queue.length > 0) {
      setCurrentPopup(queue[0])
      setIsPreview(false)
      setQueue(prev => prev.slice(1))
    }
  }, [currentPopup, queue])

  // Start polling when authenticated
  useEffect(() => {
    if (!isAuthenticated) return

    // Initial fetch after a short delay (let the app settle)
    const initialTimeout = setTimeout(fetchPopups, 2000)

    // Periodic polling
    timerRef.current = setInterval(fetchPopups, POLL_INTERVAL)

    return () => {
      clearTimeout(initialTimeout)
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [isAuthenticated, fetchPopups])

  // Listen for preview events from admin page
  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail as PopupData
      if (detail) {
        setCurrentPopup(detail)
        setIsPreview(true)
      }
    }
    window.addEventListener('popup-preview', handler)
    return () => window.removeEventListener('popup-preview', handler)
  }, [])

  // Cleanup
  useEffect(() => {
    mountedRef.current = true
    return () => { mountedRef.current = false }
  }, [])

  const handleDismiss = useCallback(async () => {
    if (!currentPopup) return
    if (!isPreview) {
      try {
        await api.post(`/popups/${currentPopup.id}/dismiss`)
      } catch {
        // ignore dismiss errors
      }
    }
    setCurrentPopup(null)
    setIsPreview(false)
  }, [currentPopup, isPreview])

  const checkNow = useCallback(() => {
    fetchPopups()
  }, [fetchPopups])

  return (
    <PopupContext.Provider value={{ checkNow }}>
      {children}
      {currentPopup && (
        <PopupDisplay popup={currentPopup} onDismiss={handleDismiss} />
      )}
    </PopupContext.Provider>
  )
}
