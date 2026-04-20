import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '@/contexts/AuthContext'
import { App } from './App'
import { ToastProvider } from './components/ui/Toast'
import { ModalProvider } from './components/ui/Modal'
import { ErrorBoundary } from './components/ui/ErrorBoundary'
import './styles/globals.css'

// Global version marker - helps verify cache/deployment
console.log('🚀 Kinyan CRM Frontend v1.3.2 - 2026-04-20 14:06 - EditableField fix for select stale state')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <ToastProvider>
            <ModalProvider>
              <App />
            </ModalProvider>
          </ToastProvider>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>
)
