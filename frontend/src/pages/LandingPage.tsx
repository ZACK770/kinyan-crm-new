import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useToast } from '@/components/ui/Toast'
import { Users, CreditCard, BarChart3, Zap, ArrowLeft, X, LogIn } from 'lucide-react'
import styles from './Landing.module.css'

/* ============================================================
   Login Modal (inline)
   ============================================================ */
function LoginModal({ onClose }: { onClose: () => void }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { login } = useAuth()
  const { success: showSuccess } = useToast()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !password.trim()) {
      setError('אנא מלא את כל השדות')
      return
    }
    setError('')
    setLoading(true)
    try {
      await login({ email: email.trim(), password })
      showSuccess('התחברת בהצלחה')
      navigate('/', { replace: true })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'שגיאה בהתחברות')
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleLogin = async () => {
    try {
      const response = await fetch('/api/auth/google/login-url')
      if (!response.ok) throw new Error('Failed to get Google login URL')
      const data = await response.json()
      window.location.href = data.url
    } catch {
      setError('שגיאה בהתחברות עם Google')
    }
  }

  // Close on Escape
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onClose])

  return (
    <div className={styles.modalOverlay} onClick={(e) => { if (e.target === e.currentTarget) onClose() }}>
      <div className={styles.modalCard}>
        <button className={styles.modalClose} onClick={onClose} aria-label="סגור">
          <X size={20} />
        </button>

        <div className={styles.modalHeader}>
          <div className={styles.modalLogo}>
            <span className={styles.logoAccent}>Ne</span>xus
          </div>
          <p className={styles.modalTitle}>כניסה למערכת</p>
        </div>

        {error && <div className={styles.modalError}>{error}</div>}

        <form onSubmit={handleSubmit} className={styles.modalForm}>
          <div className={styles.modalField}>
            <label htmlFor="modal-email">כתובת מייל</label>
            <input
              id="modal-email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              required
              placeholder="your@email.com"
            />
          </div>

          <div className={styles.modalField}>
            <label htmlFor="modal-password">סיסמה</label>
            <input
              id="modal-password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              required
              placeholder="••••••••"
            />
          </div>

          <button type="submit" className={styles.modalSubmit} disabled={loading}>
            {loading ? 'מתחבר...' : 'התחבר'}
          </button>
        </form>

        <div className={styles.modalDivider}>
          <span>או</span>
        </div>

        <button onClick={handleGoogleLogin} className={styles.googleButton} disabled={loading}>
          <svg className={styles.googleIcon} viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
          </svg>
          התחבר עם Google
        </button>

        <div className={styles.modalLinks}>
          <Link to="/auth/forgot-password">שכחת סיסמה?</Link>
          <span> • </span>
          <Link to="/auth/register">אין לך חשבון? הירשם</Link>
        </div>
      </div>
    </div>
  )
}

/* ============================================================
   Landing Page
   ============================================================ */
export function LandingPage() {
  const [showLogin, setShowLogin] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const { user } = useAuth()
  const navigate = useNavigate()

  // Redirect logged-in users to dashboard
  useEffect(() => {
    if (user) navigate('/', { replace: true })
  }, [user, navigate])

  // Navbar scroll effect
  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const openLogin = () => setShowLogin(true)

  return (
    <div className={styles.landing}>
      {/* --- Navbar --- */}
      <nav className={`${styles.navbar} ${scrolled ? styles.navbarScrolled : ''}`}>
        <div className={styles.logo}>
          <span className={styles.logoDot} />
          <span>Ne<span className={styles.logoAccent}>x</span>us</span>
        </div>
        <button className={styles.navButton} onClick={openLogin}>
          <LogIn size={16} style={{ marginLeft: '0.4rem' }} />
          כניסה למערכת
        </button>
      </nav>

      {/* --- Hero --- */}
      <section className={styles.hero}>
        <div className={styles.heroGlow} />
        <div className={styles.heroContent}>
          <span className={styles.heroTag}>פלטפורמת CRM חכמה לארגונים</span>
          <h1 className={styles.heroTitle}>
            המערכת שמנהלת לך
            <br />
            את <span className={styles.heroTitleGradient}>הארגון</span>
          </h1>
          <p className={styles.heroSubtitle}>
            ניהול לידים, תלמידים, תשלומים, קורסים ואוטומציות — הכל במקום אחד.
            <br />
            ממשק נקי, חכם ומותאם לעברית.
          </p>
          <button className={styles.heroCta} onClick={openLogin}>
            התחל עכשיו
            <ArrowLeft size={18} />
          </button>
        </div>
      </section>

      {/* --- Features --- */}
      <section className={styles.features}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionTag}>יכולות</span>
          <h2 className={styles.sectionTitle}>הכל מה שצריך, במקום אחד</h2>
          <p className={styles.sectionSubtitle}>
            כלים חכמים שעוזרים לך להתמקד במה שחשוב — לגדול
          </p>
        </div>
        <div className={styles.featuresGrid}>
          <div className={styles.featureCard}>
            <div className={`${styles.featureIcon} ${styles.featureIconBlue}`}>
              <Users size={26} />
            </div>
            <h3 className={styles.featureTitle}>ניהול לידים</h3>
            <p className={styles.featureDesc}>
              מעקב מלא מרגע הפנייה ועד ההמרה. סטטוסים, משימות, היסטוריית פעולות.
            </p>
          </div>
          <div className={styles.featureCard}>
            <div className={`${styles.featureIcon} ${styles.featureIconPurple}`}>
              <CreditCard size={26} />
            </div>
            <h3 className={styles.featureTitle}>תשלומים וגבייה</h3>
            <p className={styles.featureDesc}>
              חיובים אוטומטיים, מעקב התחייבויות, חיבור לנדרים פלוס ועוד.
            </p>
          </div>
          <div className={styles.featureCard}>
            <div className={`${styles.featureIcon} ${styles.featureIconCyan}`}>
              <BarChart3 size={26} />
            </div>
            <h3 className={styles.featureTitle}>דשבורד חכם</h3>
            <p className={styles.featureDesc}>
              נתונים בזמן אמת, גרפים, ביצועי צוות ומשפך המרה — במבט אחד.
            </p>
          </div>
          <div className={styles.featureCard}>
            <div className={`${styles.featureIcon} ${styles.featureIconAmber}`}>
              <Zap size={26} />
            </div>
            <h3 className={styles.featureTitle}>אוטומציות</h3>
            <p className={styles.featureDesc}>
              וובהוקים, שליחת מיילים אוטומטית, חלוקת לידים ומשימות חכמות.
            </p>
          </div>
        </div>
      </section>

      {/* --- How It Works --- */}
      <section className={styles.howItWorks}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionTag}>איך זה עובד</span>
          <h2 className={styles.sectionTitle}>שלושה צעדים פשוטים</h2>
        </div>
        <div className={styles.stepsGrid}>
          <div className={styles.step}>
            <div className={styles.stepNumber}>1</div>
            <h3 className={styles.stepTitle}>הרשמה</h3>
            <p className={styles.stepDesc}>
              פותחים חשבון תוך דקה. מייל וסיסמה או כניסה עם Google.
            </p>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNumber}>2</div>
            <h3 className={styles.stepTitle}>הגדרה</h3>
            <p className={styles.stepDesc}>
              מגדירים קורסים, מסלולים, צוות מכירות ווובהוקים מהאתר.
            </p>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNumber}>3</div>
            <h3 className={styles.stepTitle}>ניהול</h3>
            <p className={styles.stepDesc}>
              הלידים זורמים, הצוות עובד, והמערכת מנהלת הכל אוטומטית.
            </p>
          </div>
        </div>
      </section>

      {/* --- Stats --- */}
      <section className={styles.stats}>
        <div className={styles.statsGrid}>
          <div>
            <p className={styles.statNumber}>10,000+</p>
            <p className={styles.statLabel}>לידים מנוהלים</p>
          </div>
          <div>
            <p className={styles.statNumber}>2,500+</p>
            <p className={styles.statLabel}>תלמידים פעילים</p>
          </div>
          <div>
            <p className={styles.statNumber}>99.9%</p>
            <p className={styles.statLabel}>זמינות שרת</p>
          </div>
        </div>
      </section>

      {/* --- CTA --- */}
      <section className={styles.cta}>
        <h2 className={styles.ctaTitle}>מוכנים להתחיל?</h2>
        <p className={styles.ctaSubtitle}>הצטרפו למאות ארגונים שכבר מנהלים חכם</p>
        <button className={styles.ctaButton} onClick={openLogin}>
          כניסה למערכת
          <ArrowLeft size={18} />
        </button>
      </section>

      {/* --- Footer --- */}
      <footer className={styles.footer}>
        <div className={styles.footerContent}>
          <div className={styles.footerLogo}>
            <span className={styles.logoDot} style={{ display: 'inline-block', marginLeft: '0.4rem' }} />
            Nexus CRM
          </div>
          <p className={styles.footerText}>© {new Date().getFullYear()} Nexus CRM. כל הזכויות שמורות.</p>
        </div>
      </footer>

      {/* --- Login Modal --- */}
      {showLogin && <LoginModal onClose={() => setShowLogin(false)} />}
    </div>
  )
}
