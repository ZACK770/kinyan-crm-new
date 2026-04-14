import { type FC } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  BookOpen,
  CreditCard,
  Receipt,
  FileText,
  Megaphone,
  CheckSquare,
  Inbox,
  Send,
  UserCheck,
  TrendingDown,
  PanelRightClose,
  PanelRightOpen,
  Shield,
  ScrollText,
  Calendar,
  MapPin,
  Upload,
  UserCog,
  Activity,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import clsx from 'clsx'
import styles from './Sidebar.module.css'

interface SidebarProps {
  collapsed: boolean
  mobileOpen: boolean
  onToggleCollapse: () => void
  onCloseMobile: () => void
}

interface NavItem {
  to: string
  label: string
  icon: FC<{ size?: number; strokeWidth?: number }>
}

const NAV_SECTIONS: { items: NavItem[] }[] = [
  {
    items: [
      { to: '/', label: 'דשבורד', icon: LayoutDashboard },
      { to: '/leads', label: 'לידים', icon: Users },
      { to: '/students', label: 'תלמידים', icon: GraduationCap },
      { to: '/courses', label: 'קורסים', icon: BookOpen },
      { to: '/tracks', label: 'מסלולים', icon: Calendar },
      { to: '/entry-points', label: 'נקודות כניסה', icon: MapPin },
    ],
  },
  {
    items: [
      { to: '/payments', label: 'תשלומים', icon: CreditCard },
      { to: '/collections', label: 'גביה', icon: Receipt },
      { to: '/commitments', label: 'התחייבויות', icon: FileText },
    ],
  },
  {
    items: [
      { to: '/campaigns', label: 'קמפיינים', icon: Megaphone },
      { to: '/tasks', label: 'משימות', icon: CheckSquare },
      { to: '/inquiries', label: 'פניות', icon: Inbox },
      { to: '/messages', label: 'הודעות', icon: Send },
    ],
  },
  {
    items: [
      { to: '/lecturers', label: 'מרצים', icon: UserCheck },
      { to: '/expenses', label: 'הוצאות', icon: TrendingDown },
    ],
  },
]

// Admin-only navigation items
const ADMIN_NAV_ITEMS: NavItem[] = [
  { to: '/admin/users', label: 'ניהול משתמשים', icon: Shield },
  { to: '/admin/import-leads', label: 'ייבוא לידים', icon: Upload },
]

// Manager+ navigation items
const MANAGER_NAV_ITEMS: NavItem[] = [
  { to: '/admin/sales-assignment', label: 'שיוך לידים', icon: UserCog },
  { to: '/admin/webhook-logs', label: 'לוגים Webhooks', icon: Activity },
  { to: '/admin/audit-logs', label: 'יומן פעילות', icon: ScrollText },
]

export const Sidebar: FC<SidebarProps> = ({
  collapsed,
  mobileOpen,
  onToggleCollapse,
  onCloseMobile,
}) => {
  const { user } = useAuth()
  const location = useLocation()

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div className={styles.sidebar__backdrop} onClick={onCloseMobile} />
      )}

      <aside
        className={clsx(
          styles.sidebar,
          collapsed && styles.collapsed,
          mobileOpen && styles['mobile-open'],
        )}
      >
        <nav className={styles.sidebar__nav}>
          {NAV_SECTIONS.map((section, sIdx) => (
            <div key={sIdx}>
              {sIdx > 0 && <div className={styles.sidebar__divider} />}
              <div className={styles.sidebar__section}>
                {section.items.map((item) => {
                  const Icon = item.icon
                  const isActive =
                    item.to === '/'
                      ? location.pathname === '/'
                      : location.pathname.startsWith(item.to)

                  return (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      className={clsx(
                        styles.sidebar__item,
                        isActive && styles.active,
                      )}
                      onClick={onCloseMobile}
                    >
                      <span className={styles.sidebar__icon}>
                        <Icon size={20} strokeWidth={1.5} />
                      </span>
                      <span className={styles.sidebar__label}>
                        {item.label}
                      </span>
                      {collapsed && (
                        <span className={styles.sidebar__tooltip}>
                          {item.label}
                        </span>
                      )}
                    </NavLink>
                  )
                })}
              </div>
            </div>
          ))}

          {/* Admin section - only for admin users */}
          {user?.role_name === 'admin' && (
            <>
              <div className={styles.sidebar__divider} />
              <div className={styles.sidebar__section}>
                <div className={styles.sidebar__section_title}>
                  {!collapsed && <span>ניהול מערכת</span>}
                </div>
                {ADMIN_NAV_ITEMS.map((item) => {
                  const Icon = item.icon
                  const isActive = location.pathname.startsWith(item.to)

                  return (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      className={clsx(
                        styles.sidebar__item,
                        isActive && styles.active,
                      )}
                      onClick={onCloseMobile}
                    >
                      <span className={styles.sidebar__icon}>
                        <Icon size={20} strokeWidth={1.5} />
                      </span>
                      <span className={styles.sidebar__label}>
                        {item.label}
                      </span>
                      {collapsed && (
                        <span className={styles.sidebar__tooltip}>
                          {item.label}
                        </span>
                      )}
                    </NavLink>
                  )
                })}
              </div>
            </>
          )}

          {/* Manager+ section - for manager and admin */}
          {(user?.role_name === 'admin' || user?.role_name === 'manager') && (
            <>
              {user?.role_name !== 'admin' && <div className={styles.sidebar__divider} />}
              <div className={styles.sidebar__section}>
                {user?.role_name !== 'admin' && (
                  <div className={styles.sidebar__section_title}>
                    {!collapsed && <span>ניהול מערכת</span>}
                  </div>
                )}
                {MANAGER_NAV_ITEMS.map((item) => {
                  const Icon = item.icon
                  const isActive = location.pathname.startsWith(item.to)

                  return (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      className={clsx(
                        styles.sidebar__item,
                        isActive && styles.active,
                      )}
                      onClick={onCloseMobile}
                    >
                      <span className={styles.sidebar__icon}>
                        <Icon size={20} strokeWidth={1.5} />
                      </span>
                      <span className={styles.sidebar__label}>
                        {item.label}
                      </span>
                      {collapsed && (
                        <span className={styles.sidebar__tooltip}>
                          {item.label}
                        </span>
                      )}
                    </NavLink>
                  )
                })}
              </div>
            </>
          )}
        </nav>

        {/* Collapse toggle — desktop only */}
        <button
          className={styles.sidebar__toggle}
          onClick={onToggleCollapse}
          aria-label={collapsed ? 'הרחב תפריט' : 'כווץ תפריט'}
        >
          {collapsed ? (
            <PanelRightOpen size={18} strokeWidth={1.5} />
          ) : (
            <PanelRightClose size={18} strokeWidth={1.5} />
          )}
        </button>
      </aside>
    </>
  )
}
