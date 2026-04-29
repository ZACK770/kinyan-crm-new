import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '@/contexts/AuthContext'
import { App } from './App'
import { ToastProvider } from './components/ui/Toast'
import { ModalProvider } from './components/ui/Modal'
import { ErrorBoundary } from './components/ui/ErrorBoundary'
import { TaskReminderProvider } from './components/ui/TaskReminderProvider'
import './styles/globals.css'

// Global version marker - helps verify cache/deployment
console.log('[VERSION] Kinyan CRM Frontend v1.3.3 - 2026-04-29 23:00 - Fixed all circular dependencies in ChatWidget')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <ToastProvider>
            <ModalProvider>
              <TaskReminderProvider>
                <App />
              </TaskReminderProvider>
            </ModalProvider>
          </ToastProvider>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>
)
