import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '@/contexts/AuthContext'
import { App } from './App'
import { ToastProvider } from './components/ui/Toast'
import { ModalProvider } from './components/ui/Modal'
import { ErrorBoundary } from './components/ui/ErrorBoundary'
import { PopupAnnouncementProvider } from './components/ui/PopupAnnouncement'
import './styles/globals.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <ToastProvider>
            <ModalProvider>
              <PopupAnnouncementProvider>
                <App />
              </PopupAnnouncementProvider>
            </ModalProvider>
          </ToastProvider>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>
)
