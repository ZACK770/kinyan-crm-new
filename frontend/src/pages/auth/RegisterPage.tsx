import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useToast } from '@/components/ui/Toast'
import styles from './Auth.module.css'

export function RegisterPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const { error: showError, success: showSuccess } = useToast()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!email.trim() || !password.trim() || !fullName.trim()) {
      showError('אנא מלא את כל השדות החובה')
      return
    }

    if (password !== confirmPassword) {
      showError('הסיסמאות אינן תואמות')
      return
    }

    if (password.length < 6) {
      showError('הסיסמה חייבת להכיל לפחות 6 תווים')
      return
    }

    setLoading(true)
    try {
      await register({
        email: email.trim(),
        password,
        full_name: fullName.trim(),
      })
      showSuccess('נרשמת בהצלחה! החשבון שלך ממתין לאישור מנהל')
      navigate('/welcome')
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'שגיאה בהרשמה'
      showError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.authContainer}>
      <div className={styles.authCard}>
        <div className={styles.authHeader}>
          <h1>הרשמה</h1>
          <p>צור חשבון חדש במערכת CRM</p>
        </div>

        <form onSubmit={handleSubmit} className={styles.authForm}>
          <div className={styles.field}>
            <label htmlFor="fullName">שם מלא *</label>
            <input
              id="fullName"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <div className={styles.field}>
            <label htmlFor="email">כתובת מייל *</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              required
              dir="ltr"
            />
          </div>

          <div className={styles.field}>
            <label htmlFor="password">סיסמה * (לפחות 6 תווים)</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              required
              minLength={6}
              dir="ltr"
            />
          </div>

          <div className={styles.field}>
            <label htmlFor="confirmPassword">אימות סיסמה *</label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={loading}
              required
              dir="ltr"
            />
          </div>

          <button 
            type="submit" 
            className={styles.primaryButton}
            disabled={loading}
          >
            {loading ? 'נרשם...' : 'הירשם'}
          </button>
        </form>

        <div className={styles.authInfo}>
          <p><strong>הערה:</strong> לאחר ההרשמה, החשבון שלך יהיה במצב "ממתין לאישור" עד שמנהל המערכת יפעיל אותו.</p>
        </div>

        <div className={styles.authLinks}>
          <Link to="/auth/login">כבר יש לך חשבון? התחבר</Link>
        </div>
      </div>
    </div>
  )
}