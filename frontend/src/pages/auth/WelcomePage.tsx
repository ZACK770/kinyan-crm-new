import { useAuth } from '@/contexts/AuthContext'
import { Link } from 'react-router-dom'
import styles from './Auth.module.css'

export function WelcomePage() {
  const { user, logout } = useAuth()

  if (!user) {
    return (
      <div className={styles.authContainer}>
        <div className={styles.authCard}>
          <h1>גישה מוגבלת</h1>
          <p>אנא התחבר כדי לראות עמוד זה</p>
          <Link to="/auth/login" className={styles.primaryButton}>
            התחבר
          </Link>
        </div>
      </div>
    )
  }

  if (user.role_name !== 'pending') {
    // אם המשתמש כבר מאושר, הפנה לדשבורד
    window.location.href = '/'
    return null
  }

  return (
    <div className={styles.authContainer}>
      <div className={styles.authCard}>
        <div className={styles.welcomeHeader}>
          <div className={styles.welcomeIcon}>⏳</div>
          <h1>ברוך הבא, {user.full_name}!</h1>
          <p>החשבון שלך נרשם בהצלחה</p>
        </div>

        <div className={styles.welcomeContent}>
          <div className={styles.statusCard}>
            <h3>סטטוס החשבון</h3>
            <div className={styles.statusBadge + ' ' + styles.pending}>
              ממתין לאישור
            </div>
            <p>החשבון שלך ממתין לאישור מנהל המערכת. תקבל הודעה במייל כאשר החשבון יאושר.</p>
          </div>

          <div className={styles.infoSection}>
            <h3>פרטי החשבון</h3>
            <div className={styles.userInfo}>
              <div>
                <strong>מייל:</strong> {user.email}
              </div>
              <div>
                <strong>תאריך הרשמה:</strong> {new Date(user.created_at).toLocaleDateString('he-IL')}
              </div>
            </div>
          </div>

          <div className={styles.nextSteps}>
            <h3>מה הלאה?</h3>
            <ul>
              <li>מנהל המערכת יבדוק את בקשת ההרשמה שלך</li>
              <li>תקבל הודעה במייל על אישור החשבון</li>
              <li>לאחר האישור תוכל להתחבר ולהשתמש במערכת</li>
            </ul>
          </div>

          <div className={styles.contactInfo}>
            <h3>צריך עזרה?</h3>
            <p>אם יש לך שאלות או בעיות, אנא פנה למנהל המערכת.</p>
          </div>

          <button 
            onClick={logout}
            className={styles.logoutButton}
          >
            התנתק
          </button>
        </div>
      </div>
    </div>
  )
}