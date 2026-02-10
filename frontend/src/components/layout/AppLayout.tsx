import { useState, type FC, type ReactNode } from 'react'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import styles from './AppLayout.module.css'
import clsx from 'clsx'

interface AppLayoutProps {
  children: ReactNode
}

export const AppLayout: FC<AppLayoutProps> = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className={styles.layout}>
      <Header
        onToggleSidebar={() => setMobileOpen((v) => !v)}
      />

      <Sidebar
        collapsed={sidebarCollapsed}
        mobileOpen={mobileOpen}
        onToggleCollapse={() => setSidebarCollapsed((v) => !v)}
        onCloseMobile={() => setMobileOpen(false)}
      />

      <main
        className={clsx(
          styles.main,
          sidebarCollapsed && styles['sidebar-collapsed'],
        )}
      >
        {children}
      </main>
    </div>
  )
}
