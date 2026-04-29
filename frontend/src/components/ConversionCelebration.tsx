import { useEffect, useState, useCallback } from 'react'
import { X, ChevronLeft, ChevronRight, Check } from 'lucide-react'
import { api } from '@/lib/api'
import { formatDateTime } from '@/lib/status'

interface Conversion {
  id: number
  full_name: string
  family_name: string | null
  phone: string
  payment_completed_date: string | null
  payment_completed_amount: number | null
  payment_completed_method: string | null
  payment_reference: string | null
  salesperson_name: string | null
  course_name: string | null
  selected_price: number | null
}

// LocalStorage key for tracking viewed conversions
const VIEWED_CONVERSIONS_KEY = 'viewed_conversions'

export function ConversionCelebration() {
  const [conversions, setConversions] = useState<Conversion[]>([])
  const [unviewedConversions, setUnviewedConversions] = useState<Conversion[]>([])
  const [showCelebration, setShowCelebration] = useState(false)
  const [showSidebar, setShowSidebar] = useState(false)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [fireworksActive, setFireworksActive] = useState(false)

  // Get viewed conversions from localStorage
  const getViewedConversions = useCallback((): Set<number> => {
    try {
      const stored = localStorage.getItem(VIEWED_CONVERSIONS_KEY)
      return stored ? new Set(JSON.parse(stored)) : new Set()
    } catch {
      return new Set()
    }
  }, [])

  // Mark conversion as viewed
  const markAsViewed = useCallback((conversionId: number) => {
    const viewed = getViewedConversions()
    viewed.add(conversionId)
    localStorage.setItem(VIEWED_CONVERSIONS_KEY, JSON.stringify([...viewed]))
    
    // Update unviewed list
    setUnviewedConversions(prev => prev.filter(c => c.id !== conversionId))
    
    // If no more unviewed, hide celebration
    if (unviewedConversions.filter(c => c.id !== conversionId).length === 0) {
      setShowCelebration(false)
    }
  }, [getViewedConversions, unviewedConversions])

  // Fetch recent conversions
  const fetchConversions = useCallback(async () => {
    try {
      const data = await api.get<Conversion[]>('leads/recent-conversions?limit=10')
      setConversions(data)
      
      const viewed = getViewedConversions()
      const unviewed = data.filter(c => !viewed.has(c.id))
      setUnviewedConversions(unviewed)
      
      // Show celebration if there are new unviewed conversions
      if (unviewed.length > 0 && !showCelebration) {
        setShowCelebration(true)
        setFireworksActive(true)
        setCurrentIndex(0)
        
        // Auto-hide fireworks after 5 seconds
        setTimeout(() => setFireworksActive(false), 5000)
      }
    } catch (err) {
      console.error('Failed to fetch conversions:', err)
    }
  }, [getViewedConversions, showCelebration])

  // Initial fetch and polling
  useEffect(() => {
    fetchConversions()
    
    // Poll every 30 seconds for new conversions
    const interval = setInterval(fetchConversions, 30000)
    
    return () => clearInterval(interval)
  }, [fetchConversions])

  // Handle navigation in sidebar
  const handleNext = () => {
    if (currentIndex < unviewedConversions.length - 1) {
      setCurrentIndex(prev => prev + 1)
    }
  }

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1)
    }
  }

  // Mark current as viewed and move to next
  const handleMarkViewed = () => {
    const current = unviewedConversions[currentIndex]
    if (current) {
      markAsViewed(current.id)
      
      // Move to next or close if last
      if (currentIndex < unviewedConversions.length - 1) {
        setCurrentIndex(prev => prev + 1)
      } else {
        setShowSidebar(false)
      }
    }
  }

  // Mark all as viewed
  const handleMarkAllViewed = () => {
    unviewedConversions.forEach(c => markAsViewed(c.id))
    setShowCelebration(false)
    setShowSidebar(false)
  }

  // Don't render if no unviewed conversions and celebration not active
  if (unviewedConversions.length === 0 && !showCelebration && !showSidebar) {
    return null
  }

  const currentConversion = unviewedConversions[currentIndex]

  return (
    <>
      {/* Fireworks Animation Overlay */}
      {fireworksActive && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          pointerEvents: 'none',
          zIndex: 9999,
          overflow: 'hidden'
        }}>
          <FireworksCanvas />
        </div>
      )}

      {/* Celebration Banner */}
      {showCelebration && !showSidebar && (
        <div style={{
          position: 'fixed',
          top: 20,
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          padding: '16px 24px',
          borderRadius: 12,
          boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
          zIndex: 10000,
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          animation: 'slideDown 0.5s ease-out',
          cursor: 'pointer'
        }}
        onClick={() => setShowSidebar(true)}
        >
          <div style={{ fontSize: '24px' }}>
            🎉
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 16 }}>
              יש {unviewedConversions.length} סליקות חדשות!
            </div>
            <div style={{ fontSize: 14, opacity: 0.9 }}>
              לחץ לצפייה בפרטים
            </div>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleMarkAllViewed()
            }}
            style={{
              background: 'rgba(255,255,255,0.2)',
              border: 'none',
              color: 'white',
              padding: '8px 12px',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: 12
            }}
          >
            סגור הכל
          </button>
        </div>
      )}

      {/* Sidebar with Conversion Cards */}
      {showSidebar && unviewedConversions.length > 0 && currentConversion && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          bottom: 0,
          width: 380,
          background: 'white',
          boxShadow: '4px 0 24px rgba(0,0,0,0.15)',
          zIndex: 10001,
          display: 'flex',
          flexDirection: 'column',
          animation: 'slideInLeft 0.3s ease-out'
        }}>
          {/* Header */}
          <div style={{
            padding: '20px',
            borderBottom: '1px solid #e5e7eb',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white'
          }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: 18 }}>
                סליקות חדשות
              </div>
              <div style={{ fontSize: 13, opacity: 0.9 }}>
                {currentIndex + 1} מתוך {unviewedConversions.length}
              </div>
            </div>
            <button
              onClick={() => setShowSidebar(false)}
              style={{
                background: 'none',
                border: 'none',
                color: 'white',
                cursor: 'pointer',
                padding: 4
              }}
            >
              <X size={24} />
            </button>
          </div>

          {/* Conversion Card */}
          <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
            <div style={{
              background: 'linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%)',
              borderRadius: 12,
              padding: '20px',
              marginBottom: 16,
              border: '2px solid #667eea'
            }}>
              {/* Customer Info */}
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 4 }}>
                  {currentConversion.full_name} {currentConversion.family_name}
                </div>
                <div style={{ color: '#666', fontSize: 14, direction: 'ltr', textAlign: 'left' }}>
                  {currentConversion.phone}
                </div>
              </div>

              {/* Payment Details */}
              <div style={{
                background: 'white',
                borderRadius: 8,
                padding: '16px',
                marginBottom: 16
              }}>
                <div style={{ fontSize: 12, color: '#666', marginBottom: 8, fontWeight: 600 }}>
                  פרטי הסליקה
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <div style={{ fontSize: 11, color: '#999', marginBottom: 2 }}>סכום</div>
                    <div style={{ fontWeight: 700, fontSize: 20, color: '#10b981' }}>
                      ₪{currentConversion.payment_completed_amount?.toFixed(2) || '0.00'}
                    </div>
                  </div>
                  
                  <div>
                    <div style={{ fontSize: 11, color: '#999', marginBottom: 2 }}>שיטת תשלום</div>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>
                      {currentConversion.payment_completed_method || '—'}
                    </div>
                  </div>
                </div>

                {currentConversion.payment_reference && (
                  <div style={{ marginTop: 12 }}>
                    <div style={{ fontSize: 11, color: '#999', marginBottom: 2 }}>אסמכתא</div>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>
                      {currentConversion.payment_reference}
                    </div>
                  </div>
                )}

                {currentConversion.payment_completed_date && (
                  <div style={{ marginTop: 12 }}>
                    <div style={{ fontSize: 11, color: '#999', marginBottom: 2 }}>תאריך סליקה</div>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>
                      {formatDateTime(currentConversion.payment_completed_date)}
                    </div>
                  </div>
                )}
              </div>

              {/* Course Info */}
              {currentConversion.course_name && (
                <div style={{
                  background: 'white',
                  borderRadius: 8,
                  padding: '16px',
                  marginBottom: 16
                }}>
                  <div style={{ fontSize: 12, color: '#666', marginBottom: 8, fontWeight: 600 }}>
                    קורס
                  </div>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>
                    {currentConversion.course_name}
                  </div>
                  {currentConversion.selected_price && (
                    <div style={{ marginTop: 4, fontSize: 14, color: '#666' }}>
                      מחיר: ₪{currentConversion.selected_price.toFixed(2)}
                    </div>
                  )}
                </div>
              )}

              {/* Salesperson Info */}
              {currentConversion.salesperson_name && (
                <div style={{
                  background: 'white',
                  borderRadius: 8,
                  padding: '16px'
                }}>
                  <div style={{ fontSize: 12, color: '#666', marginBottom: 8, fontWeight: 600 }}>
                    איש מכירות
                  </div>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>
                    {currentConversion.salesperson_name}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Footer with Navigation */}
          <div style={{
            padding: '16px 20px',
            borderTop: '1px solid #e5e7eb',
            display: 'flex',
            gap: 12
          }}>
            <button
              onClick={handlePrev}
              disabled={currentIndex === 0}
              style={{
                flex: 1,
                padding: '12px',
                borderRadius: 8,
                border: '1px solid #e5e7eb',
                background: 'white',
                cursor: currentIndex === 0 ? 'not-allowed' : 'pointer',
                opacity: currentIndex === 0 ? 0.5 : 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8
              }}
            >
              <ChevronRight size={18} />
              הקודם
            </button>

            <button
              onClick={handleMarkViewed}
              style={{
                flex: 2,
                padding: '12px',
                borderRadius: 8,
                border: 'none',
                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                color: 'white',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8
              }}
            >
              <Check size={18} />
              סמן כנצפה
            </button>

            <button
              onClick={handleNext}
              disabled={currentIndex === unviewedConversions.length - 1}
              style={{
                flex: 1,
                padding: '12px',
                borderRadius: 8,
                border: '1px solid #e5e7eb',
                background: 'white',
                cursor: currentIndex === unviewedConversions.length - 1 ? 'not-allowed' : 'pointer',
                opacity: currentIndex === unviewedConversions.length - 1 ? 0.5 : 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8
              }}
            >
              הבא
              <ChevronLeft size={18} />
            </button>
          </div>
        </div>
      )}

      <style>{`
        @keyframes slideDown {
          from {
            transform: translateX(-50%) translateY(-100px);
            opacity: 0;
          }
          to {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
          }
        }

        @keyframes slideInLeft {
          from {
            transform: translateX(-100%);
          }
          to {
            transform: translateX(0);
          }
        }
      `}</style>
    </>
  )
}

// Simple fireworks canvas component
function FireworksCanvas() {
  useEffect(() => {
    const canvas = document.createElement('canvas')
    canvas.style.position = 'fixed'
    canvas.style.top = '0'
    canvas.style.left = '0'
    canvas.style.width = '100%'
    canvas.style.height = '100%'
    canvas.style.pointerEvents = 'none'
    document.body.appendChild(canvas)

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    canvas.width = window.innerWidth
    canvas.height = window.innerHeight

    const particles: Particle[] = []
    const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff', '#ff8800', '#ff0088']

    class Particle {
      x: number
      y: number
      vx: number
      vy: number
      color: string
      life: number
      decay: number

      constructor(x: number, y: number, color: string) {
        this.x = x
        this.y = y
        this.vx = (Math.random() - 0.5) * 10
        this.vy = (Math.random() - 0.5) * 10
        this.color = color
        this.life = 100
        this.decay = Math.random() * 2 + 1
      }

      update() {
        this.x += this.vx
        this.y += this.vy
        this.vy += 0.1 // gravity
        this.life -= this.decay
      }

      draw(ctx: CanvasRenderingContext2D) {
        ctx.globalAlpha = this.life / 100
        ctx.fillStyle = this.color
        ctx.beginPath()
        ctx.arc(this.x, this.y, 3, 0, Math.PI * 2)
        ctx.fill()
      }
    }

    function createFirework(x: number, y: number) {
      const color = colors[Math.floor(Math.random() * colors.length)]
      for (let i = 0; i < 50; i++) {
        particles.push(new Particle(x, y, color))
      }
    }

    function animate() {
      ctx.fillStyle = 'rgba(0, 0, 0, 0.1)'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // Randomly create fireworks
      if (Math.random() < 0.05) {
        createFirework(
          Math.random() * canvas.width,
          Math.random() * canvas.height * 0.6
        )
      }

      for (let i = particles.length - 1; i >= 0; i--) {
        particles[i].update()
        particles[i].draw(ctx)
        if (particles[i].life <= 0) {
          particles.splice(i, 1)
        }
      }

      requestAnimationFrame(animate)
    }

    animate()

    const handleResize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      document.body.removeChild(canvas)
    }
  }, [])

  return null
}
