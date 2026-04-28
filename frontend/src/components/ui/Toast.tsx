import {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
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
  onClick?: () => void
}

interface ToastOptions {
  duration?: number
  onClick?: () => void
}

interface ToastContextType {
  success: (title: string, message?: string, options?: ToastOptions) => void
  error: (title: string, message?: string, options?: ToastOptions) => void
  warning: (title: string, message?: string, options?: ToastOptions) => void
  info: (title: string, message?: string, options?: ToastOptions) => void
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

  const handleClick = () => {
    if (item.onClick) {
      item.onClick()
    }
    onDismiss(item.id)
  }

  return (
    <div
      className={clsx(styles.toast, styles[item.type], item.exiting && styles.exiting)}
      onClick={handleClick}
      role="alert"
      style={item.onClick ? { cursor: 'pointer' } : undefined}
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

  const addToast = useCallback((type: ToastType, title: string, message?: string, options?: ToastOptions) => {
    const id = `toast-${++idRef.current}`
    const duration = options?.duration ?? DURATIONS[type]
    const newToast: ToastItem = { id, type, title, message, duration, onClick: options?.onClick }

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

  // IMPORTANT: Memoize ctx to prevent infinite re-render loops!
  // Without useMemo, ctx changes every render, causing useCallback deps to change,
  // which triggers useEffect, which fetches, which on error shows toast, which re-renders...
  const ctx: ToastContextType = useMemo(() => ({
    success: (title, message, options) => addToast('success', title, message, options),
    error: (title, message, options) => addToast('error', title, message, options),
    warning: (title, message, options) => addToast('warning', title, message, options),
    info: (title, message, options) => addToast('info', title, message, options),
  }), [addToast])

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
