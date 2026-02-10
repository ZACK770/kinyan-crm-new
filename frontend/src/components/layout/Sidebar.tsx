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
} from 'lucide-react'
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

export const Sidebar: FC<SidebarProps> = ({
  collapsed,
  mobileOpen,
  onToggleCollapse,
  onCloseMobile,
}) => {
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
