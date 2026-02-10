import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type FC,
  type ReactNode,
} from 'react'
import { X } from 'lucide-react'
import styles from './Modal.module.css'
import clsx from 'clsx'

/* ============================================================
   Types
   ============================================================ */

type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | 'full'

interface ModalOptions {
  title: string
  size?: ModalSize
  content: ReactNode
  /** If true, clicking outside won't close */
  persistent?: boolean
  /** Hide close X button */
  hideClose?: boolean
}

interface ConfirmOptions {
  title: string
  message: string
  subtitle?: string
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
}

interface ModalContextType {
  /** Open a modal with custom content */
  openModal: (options: ModalOptions) => void
  /** Close the current modal */
  closeModal: () => void
  /** Show a confirm dialog — returns true/false */
  confirm: (options: ConfirmOptions) => Promise<boolean>
}

const ModalContext = createContext<ModalContextType | null>(null)

export function useModal(): ModalContextType {
  const ctx = useContext(ModalContext)
  if (!ctx) throw new Error('useModal must be used within ModalProvider')
  return ctx
}

/* ============================================================
   Provider
   ============================================================ */

export const ModalProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [modal, setModal] = useState<ModalOptions | null>(null)
  const [confirmState, setConfirmState] = useState<{
    options: ConfirmOptions
    resolve: (value: boolean) => void
  } | null>(null)

  const openModal = useCallback((options: ModalOptions) => {
    setModal(options)
  }, [])

  const closeModal = useCallback(() => {
    setModal(null)
  }, [])

  const confirmFn = useCallback((options: ConfirmOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      setConfirmState({ options, resolve })
    })
  }, [])

  const handleConfirmResult = useCallback(
    (result: boolean) => {
      if (confirmState) {
        confirmState.resolve(result)
        setConfirmState(null)
      }
    },
    [confirmState],
  )

  // ESC handler
  useEffect(() => {
    if (!modal && !confirmState) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (confirmState) handleConfirmResult(false)
        else if (modal && !modal.persistent) closeModal()
      }
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [modal, confirmState, closeModal, handleConfirmResult])

  // Body scroll lock
  useEffect(() => {
    if (modal || confirmState) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [modal, confirmState])

  return (
    <ModalContext.Provider value={{ openModal, closeModal, confirm: confirmFn }}>
      {children}

      {/* Custom Modal */}
      {modal && (
        <div
          className={styles.overlay}
          onClick={(e) => {
            if (e.target === e.currentTarget && !modal.persistent) closeModal()
          }}
        >
          <div className={clsx(styles.dialog, styles[modal.size || 'md'])} role="dialog" aria-modal="true">
            <div className={styles.header}>
              <h2 className={styles.title}>{modal.title}</h2>
              {!modal.hideClose && (
                <button className={styles['close-btn']} onClick={closeModal} aria-label="סגירה">
                  <X size={18} strokeWidth={1.5} />
                </button>
              )}
            </div>
            <div className={styles.body}>{modal.content}</div>
          </div>
        </div>
      )}

      {/* Confirm Modal */}
      {confirmState && (
        <div
          className={styles.overlay}
          onClick={(e) => {
            if (e.target === e.currentTarget) handleConfirmResult(false)
          }}
        >
          <div className={clsx(styles.dialog, styles.sm)} role="alertdialog" aria-modal="true">
            <div className={styles.header}>
              <h2 className={styles.title}>{confirmState.options.title}</h2>
              <button
                className={styles['close-btn']}
                onClick={() => handleConfirmResult(false)}
                aria-label="סגירה"
              >
                <X size={18} strokeWidth={1.5} />
              </button>
            </div>
            <div className={styles.body}>
              <div className={styles['confirm-body']}>
                <p className={styles['confirm-message']}>
                  {confirmState.options.message}
                </p>
                {confirmState.options.subtitle && (
                  <p className={styles['confirm-sub']}>
                    {confirmState.options.subtitle}
                  </p>
                )}
              </div>
            </div>
            <div className={styles.footer}>
              <button
                className={
                  confirmState.options.danger
                    ? styles['btn-danger']
                    : styles['btn-primary']
                }
                onClick={() => handleConfirmResult(true)}
              >
                {confirmState.options.confirmLabel || 'אישור'}
              </button>
              <button
                className={styles['btn-secondary']}
                onClick={() => handleConfirmResult(false)}
              >
                {confirmState.options.cancelLabel || 'ביטול'}
              </button>
            </div>
          </div>
        </div>
      )}
    </ModalContext.Provider>
  )
}
