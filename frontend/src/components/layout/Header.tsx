import { useState, useEffect, useRef, useCallback, type FC, type FormEvent } from 'react'
import {
  Menu,
  Plus,
  Bell,
  UserPlus,
  GraduationCap,
  CheckSquare,
  LogOut,
  User,
  AtSign,
  Pin,
  MessageCircle,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useModal } from '@/components/ui/Modal'
import { useToast } from '@/components/ui/Toast'
import { api } from '@/lib/api'
import styles from './Header.module.css'
import clsx from 'clsx'
import s from '@/styles/shared.module.css'

/* ── Notification types ── */
interface ChatNotification {
  id: number
  type: 'mention' | 'pin'
  thread_id: number
  sender_name: string
  sender_avatar?: string | null
  content: string
  created_at?: string | null
}

interface NotificationsResponse {
  notifications: ChatNotification[]
  unread_count: number
}

/* ── NotificationBell component ── */
function NotificationBell() {
  const [open, setOpen] = useState(false)
  const [notifications, setNotifications] = useState<ChatNotification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const ref = useRef<HTMLDivElement>(null)

  const fetchNotifications = useCallback(async () => {
    try {
      const data = await api.get<NotificationsResponse>('/chat/notifications')
      setNotifications(data.notifications)
      setUnreadCount(data.unread_count)
    } catch {}
  }, [])

  // Fetch on mount and every 30s
  useEffect(() => {
    fetchNotifications()
    const interval = setInterval(fetchNotifications, 30000)
    return () => clearInterval(interval)
  }, [fetchNotifications])

  // Close on outside click
  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const formatTime = (dateStr?: string | null) => {
    if (!dateStr) return ''
    try {
      const d = new Date(dateStr)
      const now = new Date()
      const diffMs = now.getTime() - d.getTime()
      const diffMin = Math.floor(diffMs / 60000)
      if (diffMin < 1) return 'עכשיו'
      if (diffMin < 60) return `לפני ${diffMin} דק׳`
      const diffH = Math.floor(diffMin / 60)
      if (diffH < 24) return `לפני ${diffH} שע׳`
      return d.toLocaleDateString('he-IL', { day: 'numeric', month: 'short' })
    } catch { return '' }
  }

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button
        className={styles['header__action-btn']}
        aria-label="התראות"
        onClick={() => { setOpen(v => !v); if (!open) fetchNotifications() }}
      >
        <Bell size={18} strokeWidth={1.5} />
        {unreadCount > 0 && (
          <span className={styles.header__badge}>
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className={styles['header__notif-dropdown']}>
          <div className={styles['header__notif-header']}>
            <span>התראות צ׳אט</span>
            {unreadCount > 0 && (
              <span className={styles['header__notif-count']}>{unreadCount} חדשות</span>
            )}
          </div>
          <div className={styles['header__notif-list']}>
            {notifications.length === 0 ? (
              <div className={styles['header__notif-empty']}>
                <MessageCircle size={24} strokeWidth={1} />
                <span>אין התראות חדשות</span>
              </div>
            ) : notifications.map(n => (
              <div key={n.id} className={styles['header__notif-item']} onClick={() => setOpen(false)}>
                <div className={styles['header__notif-icon']}>
                  {n.type === 'mention' ? <AtSign size={14} /> : <Pin size={14} />}
                </div>
                <div className={styles['header__notif-content']}>
                  <div className={styles['header__notif-sender']}>
                    {n.sender_name}
                    <span className={styles['header__notif-type']}>
                      {n.type === 'mention' ? 'הזכיר אותך' : 'הצמיד הודעה'}
                    </span>
                  </div>
                  <div className={styles['header__notif-text']}>{n.content}</div>
                  <div className={styles['header__notif-time']}>{formatTime(n.created_at)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Quick forms for header actions ── */
function QuickLeadForm({ onSubmit }: { onSubmit: (data: Record<string, unknown>) => void }) {
  const [form, setForm] = useState({ full_name: '', phone: '', source_type: 'manual' })
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setForm(p => ({ ...p, [k]: e.target.value }))
  const handle = (e: FormEvent) => { e.preventDefault(); onSubmit(form) }
  return (
    <form onSubmit={handle} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>שם *</label>
          <input className={s.input} value={form.full_name} onChange={set('full_name')} required />
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>טלפון *</label>
          <input className={s.input} value={form.phone} onChange={set('phone')} required dir="ltr" />
        </div>
      </div>
      <div className={s['form-group']}>
        <label className={s['form-label']}>מקור</label>
        <select className={s.select} value={form.source_type} onChange={set('source_type')}>
          <option value="manual">ידני</option>
          <option value="yemot">ימות המשיח</option>
          <option value="elementor">אלמנטור</option>
          <option value="referral">הפניה</option>
        </select>
      </div>
      <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>צור ליד</button>
    </form>
  )
}

function QuickConvertForm({ onSubmit }: { onSubmit: (leadId: number) => void }) {
  const [leadId, setLeadId] = useState('')
  return (
    <form onSubmit={e => { e.preventDefault(); onSubmit(Number(leadId)) }} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className={s['form-group']}>
        <label className={s['form-label']}>מזהה ליד</label>
        <input className={s.input} type="number" value={leadId} onChange={e => setLeadId(e.target.value)} required dir="ltr" />
      </div>
      <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>המר לתלמיד</button>
    </form>
  )
}

function QuickTaskForm({ onSubmit }: { onSubmit: (data: Record<string, unknown>) => void }) {
  const [form, setForm] = useState({ title: '', priority: 2 })
  return (
    <form onSubmit={e => { e.preventDefault(); onSubmit(form) }} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className={s['form-group']}>
        <label className={s['form-label']}>כותרת *</label>
        <input className={s.input} value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} required />
      </div>
      <div className={s['form-group']}>
        <label className={s['form-label']}>עדיפות</label>
        <select className={s.select} value={form.priority} onChange={e => setForm(p => ({ ...p, priority: Number(e.target.value) }))}>
          <option value={1}>נמוך</option>
          <option value={2}>רגיל</option>
          <option value={3}>גבוה</option>
          <option value={4}>דחוף</option>
        </select>
      </div>
      <button type="submit" className={`${s.btn} ${s['btn-primary']}`}>צור משימה</button>
    </form>
  )
}

interface HeaderProps {
  onToggleSidebar: () => void
}

export const Header: FC<HeaderProps> = ({ onToggleSidebar }) => {
  const { user, logout } = useAuth()
  const [scrolled, setScrolled] = useState(false)
  const [showQuickAdd, setShowQuickAdd] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const quickAddRef = useRef<HTMLDivElement>(null)
  const userMenuRef = useRef<HTMLDivElement>(null)

  // Track scroll for shadow
  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 2)
    window.addEventListener('scroll', handler, { passive: true })
    return () => window.removeEventListener('scroll', handler)
  }, [])

  // Close quick-add on outside click
  useEffect(() => {
    if (!showQuickAdd) return
    const handler = (e: MouseEvent) => {
      if (quickAddRef.current && !quickAddRef.current.contains(e.target as Node)) {
        setShowQuickAdd(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [showQuickAdd])

  // Close user menu on outside click
  useEffect(() => {
    if (!showUserMenu) return
    const handler = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setShowUserMenu(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [showUserMenu])

  // Keyboard shortcut: Escape to close quick-add
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setShowQuickAdd(false)
      }
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [])

  const { openModal, closeModal } = useModal()
  const toast = useToast()

  const handleQuickAction = useCallback((action: string) => {
    setShowQuickAdd(false)
    if (action === 'new-lead') {
      openModal({
        title: 'ליד חדש',
        size: 'lg',
        content: <QuickLeadForm onSubmit={async (data) => {
          try {
            await api.post('leads', data)
            toast.success('ליד נוצר בהצלחה')
            closeModal()
          } catch (err: unknown) { toast.error((err as { message?: string }).message ?? 'שגיאה') }
        }} />,
      })
    } else if (action === 'new-student') {
      openModal({
        title: 'המרת ליד לתלמיד',
        size: 'sm',
        content: <QuickConvertForm onSubmit={async (leadId) => {
          try {
            await api.post('students/convert', { lead_id: leadId })
            toast.success('ליד הומר לתלמיד')
            closeModal()
          } catch (err: unknown) { toast.error((err as { message?: string }).message ?? 'שגיאה') }
        }} />,
      })
    } else if (action === 'new-task') {
      openModal({
        title: 'משימה חדשה',
        size: 'md',
        content: <QuickTaskForm onSubmit={async (data) => {
          try {
            await api.post('leads/tasks', data)
            toast.success('משימה נוצרה')
            closeModal()
          } catch (err: unknown) { toast.error((err as { message?: string }).message ?? 'שגיאה') }
        }} />,
      })
    }
  }, [openModal, closeModal, toast])

  return (
    <>
      <header className={clsx(styles.header, scrolled && styles.scrolled)}>
        {/* Hamburger — mobile */}
        <button
          className={styles.header__hamburger}
          onClick={onToggleSidebar}
          aria-label="פתח תפריט"
        >
          <Menu size={20} strokeWidth={1.5} />
        </button>

        {/* Brand */}
        <div className={styles.header__brand}>
          <img src="/logo.png" alt="קניין הוראה" className={styles.header__logo} />
          <div className={styles.header__text}>
            <span className={styles.header__title}>קניין הוראה</span>
            <span className={styles.header__subtitle}>ניהול שיווק ולמידה</span>
          </div>
        </div>

        <div className={styles.header__spacer} />

        {/* Actions */}
        <div className={styles.header__actions}>
          {/* Quick add */}
          <div ref={quickAddRef} style={{ position: 'relative' }}>
            <button
              className={styles['header__action-btn']}
              onClick={() => setShowQuickAdd(v => !v)}
              aria-label="פעולה מהירה"
            >
              <Plus size={18} strokeWidth={1.5} />
            </button>

            {showQuickAdd && (
              <div className={styles.header__dropdown}>
                <button
                  className={styles['header__dropdown-item']}
                  onClick={() => handleQuickAction('new-lead')}
                >
                  <UserPlus size={16} strokeWidth={1.5} />
                  ליד חדש
                </button>
                <button
                  className={styles['header__dropdown-item']}
                  onClick={() => handleQuickAction('new-student')}
                >
                  <GraduationCap size={16} strokeWidth={1.5} />
                  תלמיד חדש
                </button>
                <button
                  className={styles['header__dropdown-item']}
                  onClick={() => handleQuickAction('new-task')}
                >
                  <CheckSquare size={16} strokeWidth={1.5} />
                  משימה חדשה
                </button>
              </div>
            )}
          </div>

          {/* Notifications */}
          <NotificationBell />

          {/* User avatar and menu */}
          <div className={styles.header__user} ref={userMenuRef}>
            <button 
              className={styles.header__avatar}
              onClick={() => setShowUserMenu(!showUserMenu)}
            >
              {user?.avatar_url ? (
                <img 
                  src={user.avatar_url} 
                  alt={user.full_name}
                  className={styles['header__avatar-img']}
                />
              ) : (
                <span className={styles['header__avatar-circle']}>
                  {user?.full_name?.split(' ').map(n => n[0]).join('') || 'U'}
                </span>
              )}
              <span className={styles['header__avatar-name']}>
                {user?.full_name || 'משתמש'}
              </span>
            </button>

            {showUserMenu && (
              <div className={styles['header__user-menu']}>
                <div className={styles['header__user-info']}>
                  <div className={styles['header__user-name']}>{user?.full_name}</div>
                  <div className={styles['header__user-email']}>{user?.email}</div>
                  <div className={styles['header__user-role']}>
                    {user?.role_name === 'admin' && 'מנהל מערכת'}
                    {user?.role_name === 'manager' && 'מנהל'}
                    {user?.role_name === 'salesperson' && 'איש מכירות'}
                    {user?.role_name === 'editor' && 'עורך'}
                    {user?.role_name === 'viewer' && 'צופה'}
                    {user?.role_name === 'pending' && 'ממתין לאישור'}
                  </div>
                </div>
                
                <div className={styles['header__user-actions']}>
                  <button 
                    className={styles['header__user-action']}
                    onClick={() => {
                      setShowUserMenu(false)
                      // Navigate to profile (TODO: implement)
                    }}
                  >
                    <User size={16} />
                    פרופיל אישי
                  </button>
                  
                  <button 
                    className={`${styles['header__user-action']} ${styles['header__user-action--danger']}`}
                    onClick={() => {
                      setShowUserMenu(false)
                      logout()
                    }}
                  >
                    <LogOut size={16} />
                    התנתק
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

    </>
  )
}
