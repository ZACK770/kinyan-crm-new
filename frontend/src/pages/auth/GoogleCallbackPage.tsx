import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useToast } from '@/components/ui/Toast'
import { api } from '@/lib/api'
import type { AuthResponse } from '@/types/auth'
import styles from './Auth.module.css'

export function GoogleCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { refreshUser } = useAuth()
  const { error: showError } = useToast()
  const [status, setStatus] = useState<'loading' | 'error'>('loading')

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code')
      const error = searchParams.get('error')

      if (error) {
        setStatus('error')
        showError('ההתחברות עם Google בוטלה')
        setTimeout(() => navigate('/auth/login'), 2000)
        return
      }

      if (!code) {
        setStatus('error')
        showError('קוד אימות חסר')
        setTimeout(() => navigate('/auth/login'), 2000)
        return
      }

      try {
        const response = await api.post<AuthResponse>('/auth/google/callback', { code })
        
        // Save token and user data
        localStorage.setItem('kinyan_auth_token', response.access_token)
        api.setAuthToken(response.access_token)
        
        // Refresh user data
        await refreshUser()

        // Check if user is pending approval
        if (response.user.role_name === 'pending' || response.user.permission_level === 0) {
          navigate('/welcome')
        } else {
          navigate('/')
        }
      } catch (err) {
        setStatus('error')
        const message = err instanceof Error ? err.message : 'שגיאה באימות Google'
        showError(message)
        setTimeout(() => navigate('/auth/login'), 2000)
      }
    }

    handleCallback()
  }, [searchParams, navigate, refreshUser, showError])

  return (
    <div className={styles.authContainer}>
      <div className={styles.authCard}>
        <div className={styles.authHeader}>
          {status === 'loading' ? (
            <>
              <h1>מתחבר עם Google...</h1>
              <p>אנא המתן</p>
            </>
          ) : (
            <>
              <h1>שגיאה בהתחברות</h1>
              <p>מנתב לדף התחברות...</p>
            </>
          )}
        </div>
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div className="spinner"></div>
        </div>
      </div>
    </div>
  )
}
