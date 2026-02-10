import {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
  useEffect,
  type FC,
  type ReactNode,
} from 'react'
import { CheckCircle2, XCircle, AlertTriangle, Info } from 'lucide-react'
import styles from './Toast.module.css'
import clsx from 'clsx'

/* ============================================================
   Types
   ============================================================ */

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface ToastItem {
  id: string
  type: ToastType
  title: string
  message?: string
  duration: number
  exiting?: boolean
}

interface ToastContextType {
  success: (title: string, message?: string) => void
  error: (title: string, message?: string) => void
  warning: (title: string, message?: string) => void
  info: (title: string, message?: string) => void
}

const ToastContext = createContext<ToastContextType | null>(null)

export function useToast(): ToastContextType {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}

/* ============================================================
   Icons by type
   ============================================================ */

const ICONS: Record<ToastType, FC<{ size?: number; strokeWidth?: number }>> = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
}

const DURATIONS: Record<ToastType, number> = {
  success: 3000,
  error: 5000,
  warning: 4000,
  info: 3000,
}

/* ============================================================
   Single Toast Item
   ============================================================ */

const ToastItemComponent: FC<{
  item: ToastItem
  onDismiss: (id: string) => void
}> = ({ item, onDismiss }) => {
  const [progress, setProgress] = useState(100)
  const startRef = useRef(Date.now())

  useEffect(() => {
    const interval = setInterval(() => {
      const elapsed = Date.now() - startRef.current
      const remaining = Math.max(0, 100 - (elapsed / item.duration) * 100)
      setProgress(remaining)
      if (remaining === 0) clearInterval(interval)
    }, 50)
    return () => clearInterval(interval)
  }, [item.duration])

  const Icon = ICONS[item.type]

  return (
    <div
      className={clsx(styles.toast, styles[item.type], item.exiting && styles.exiting)}
      onClick={() => onDismiss(item.id)}
      role="alert"
    >
      <div className={styles.icon}>
        <Icon size={18} strokeWidth={1.5} />
      </div>
      <div className={styles.content}>
        <div className={styles.title}>{item.title}</div>
        {item.message && <div className={styles.message}>{item.message}</div>}
      </div>
      <div className={styles.progress}>
        <div className={styles['progress-bar']} style={{ width: `${progress}%` }} />
      </div>
    </div>
  )
}

/* ============================================================
   Provider
   ============================================================ */

const MAX_VISIBLE = 3

export const ToastProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const idRef = useRef(0)

  const addToast = useCallback((type: ToastType, title: string, message?: string) => {
    const id = `toast-${++idRef.current}`
    const duration = DURATIONS[type]
    const newToast: ToastItem = { id, type, title, message, duration }

    setToasts((prev) => {
      const next = [newToast, ...prev]
      return next.slice(0, MAX_VISIBLE + 2) // keep a small buffer
    })

    // Auto dismiss
    setTimeout(() => dismiss(id), duration)
  }, [])

  const dismiss = useCallback((id: string) => {
    // Mark as exiting for animation
    setToasts((prev) =>
      prev.map((t) => (t.id === id ? { ...t, exiting: true } : t)),
    )
    // Remove after animation
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 200)
  }, [])

  const ctx: ToastContextType = {
    success: (title, message) => addToast('success', title, message),
    error: (title, message) => addToast('error', title, message),
    warning: (title, message) => addToast('warning', title, message),
    info: (title, message) => addToast('info', title, message),
  }

  return (
    <ToastContext.Provider value={ctx}>
      {children}
      <div className={styles.container}>
        {toasts.slice(0, MAX_VISIBLE).map((item) => (
          <ToastItemComponent key={item.id} item={item} onDismiss={dismiss} />
        ))}
      </div>
    </ToastContext.Provider>
  )
}
