import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import { CreditCard, CheckCircle2, XCircle, Copy, Calculator, Tag } from 'lucide-react'
import type { Lead, Course, Payment } from '@/types'
import { formatCurrency, formatDateTime } from '@/lib/status'
import { DirectChargeDialog } from './DirectChargeDialog'
import s from '@/styles/shared.module.css'
import ps from './LeadPaymentTab.module.css'

interface LeadPaymentTabProps {
  lead: Lead
  courses: Course[]
  onUpdate: () => void
}

interface PricingCalculation {
  original_price: number
  discount_amount: number
  final_price: number
  payments_count: number
  monthly_payment: number
}

interface PaymentStatus {
  lead_id: number
  first_payment: boolean
  nedarim_payment_link: string | null
  payments: Payment[]
}

/* ══════════════════════════════════════════════════════════════
   Main Payment Tab Component - Merged & Enhanced
   ══════════════════════════════════════════════════════════════ */
export function LeadPaymentTab({ lead, courses, onUpdate }: LeadPaymentTabProps) {
  const toast = useToast()

  // Course selection state
  const [selectedCourseId, setSelectedCourseId] = useState<number | ''>(lead.selected_course_id ?? '')
  const [price, setPrice] = useState('')
  const [paymentsCount, setPaymentsCount] = useState('1')
  const [paymentDay, setPaymentDay] = useState('15')
  const [discountAmount, setDiscountAmount] = useState('0')

  // Calculated pricing (real-time)
  const [pricing, setPricing] = useState<PricingCalculation | null>(null)
  const [isCalculating, setIsCalculating] = useState(false)

  // Payment link state
  const [isCreatingLink, setIsCreatingLink] = useState(false)
  const [createdPaymentLink, setCreatedPaymentLink] = useState<string | null>(null)

  // Direct charge dialog
  const [showDirectChargeDialog, setShowDirectChargeDialog] = useState(false)

  // Payment status
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatus | null>(null)

  // Errors
  const [error, setError] = useState<string | null>(null)

  const selectedCourse = courses.find(c => c.id === selectedCourseId)

  // Load course defaults when selected
  useEffect(() => {
    if (selectedCourse) {
      console.log('Selected course:', selectedCourse)
      console.log('Course price:', selectedCourse.price)
      console.log('Course payments_count:', selectedCourse.payments_count)
      setPrice(String(selectedCourse.price ?? ''))
      setPaymentsCount(String(selectedCourse.payments_count ?? 1))
      setPaymentDay('15') // Default
      setDiscountAmount('0')
    }
  }, [selectedCourse])

  // Fetch payment status
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await api.get<PaymentStatus>(`/leads/${lead.id}/payment-status`)
        setPaymentStatus(data)
      } catch (err) {
        console.error('Failed to fetch payment status', err)
      }
    }
    fetchStatus()
  }, [lead.id])

  // Real-time pricing calculation
  useEffect(() => {
    const calculatePricing = async () => {
      if (!selectedCourseId || !price) {
        setPricing(null)
        return
      }

      setIsCalculating(true)
      try {
        const data = await api.post<PricingCalculation>(`/leads/${lead.id}/calculate-pricing`, {
          course_id: selectedCourseId,
          discount_amount: Number(discountAmount) || 0,
        })
        setPricing(data)
        setError(null)
      } catch (err) {
        console.error('Failed to calculate pricing:', err)
        setPricing(null)
      } finally {
        setIsCalculating(false)
      }
    }

    const timer = setTimeout(calculatePricing, 300) // Debounce
    return () => clearTimeout(timer)
  }, [selectedCourseId, price, discountAmount, lead.id])

  // Save course selection
  const handleSelectCourse = async () => {
    if (!selectedCourseId) {
      setError('יש לבחור קורס')
      return
    }

    setError(null)
    try {
      await api.post(`/leads/${lead.id}/select-course`, {
        course_id: selectedCourseId,
        price: Number(price),
        payments_count: Number(paymentsCount),
        payment_day: Number(paymentDay),
      })

      // Update discount if provided
      if (Number(discountAmount) > 0) {
        await api.patch(`/leads/${lead.id}/update-discount`, {
          discount_amount: Number(discountAmount),
          installments_override: Number(paymentsCount),
        })
      }

      toast.success('קורס ותמחור נשמרו בהצלחה')
      onUpdate()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'שגיאה בשמירת קורס'
      setError(message)
    }
  }

  // Create payment link
  const handleCreateLink = async () => {
    if (!selectedCourseId) {
      setError('יש לבחור ולשמור קורס קודם')
      return
    }

    setIsCreatingLink(true)
    setError(null)
    try {
      const result = await api.post<any>(`/leads/${lead.id}/create-payment-link`, {})
      console.log('=== Payment Link Response ===')
      console.log('Full result:', JSON.stringify(result, null, 2))
      console.log('result.payment_link:', result.payment_link)
      console.log('result.nedarim_payment_link:', result.nedarim_payment_link)

      const paymentLink = result.payment_link || result.nedarim_payment_link
      console.log('Extracted payment link:', paymentLink)
      console.log('Type of paymentLink:', typeof paymentLink)

      if (paymentLink) {
        setCreatedPaymentLink(paymentLink)
        console.log('✓ Set createdPaymentLink state to:', paymentLink)
        toast.success('לינק תשלום נוצר בהצלחה')
      } else {
        console.error('✗ No payment link found in response!')
        console.error('Available keys:', Object.keys(result))
        toast.error('לינק נוצר אך לא נמצא בתגובה')
      }
      onUpdate()
    } catch (err: any) {
      console.error('Payment link error:', err)
      const message = err?.message || 'שגיאה ביצירת לינק'
      setError(message)
      toast.error(message)
    } finally {
      setIsCreatingLink(false)
    }
  }

  const copyLink = () => {
    const link = createdPaymentLink || lead.nedarim_payment_link
    if (link) {
      navigator.clipboard.writeText(link)
      toast.info('הלינק הועתק ללוח')
    }
  }

  if (!paymentStatus) {
    return <div>טוען נתוני תשלום...</div>
  }

  return (
    <div className={ps.paymentTab}>
      {/* Course Selection & Pricing */}
      <div className={ps.card}>
        <h3 className={ps.cardTitle}>
          <Tag size={16} />
          בחירת קורס ותמחור
        </h3>

        {error && (
          <div className={ps.errorBox}>
            <XCircle size={14} />
            {error}
          </div>
        )}

        <div className={s['form-group']}>
          <label className={s['form-label']}>קורס</label>
          <select
            className={s.select}
            value={selectedCourseId}
            onChange={e => setSelectedCourseId(Number(e.target.value))}
          >
            <option value="">— בחר קורס —</option>
            {courses.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>

        {selectedCourse && (
          <>
            {/* Pricing Section */}
            <div className={ps.pricingSection}>
              <div className={ps.priceRow}>
                <span className={ps.priceLabel}>מחיר מקורי:</span>
                <span className={ps.priceValue}>{formatCurrency(Number(price))}</span>
              </div>

              <div className={s['form-group']}>
                <label className={s['form-label']}>הנחה (₪)</label>
                <input
                  className={s.input}
                  type="number"
                  min="0"
                  value={discountAmount}
                  onChange={e => setDiscountAmount(e.target.value)}
                  placeholder="0"
                />
              </div>

              {pricing && (
                <>
                  <div className={ps.divider} />
                  <div className={ps.priceRow}>
                    <span className={ps.priceLabel}>מחיר סופי:</span>
                    <span className={ps.priceFinal}>
                      {isCalculating ? '...' : formatCurrency(pricing.final_price)}
                    </span>
                  </div>
                </>
              )}
            </div>

            {/* Installments Section */}
            <div className={s['form-row']}>
              <div className={s['form-group']}>
                <label className={s['form-label']}>מספר תשלומים</label>
                <input
                  className={s.input}
                  type="number"
                  min="1"
                  value={paymentsCount}
                  onChange={e => setPaymentsCount(e.target.value)}
                />
              </div>
              <div className={s['form-group']}>
                <label className={s['form-label']}>יום חיוב בחודש</label>
                <input
                  className={s.input}
                  type="number"
                  min="1"
                  max="28"
                  value={paymentDay}
                  onChange={e => setPaymentDay(e.target.value)}
                />
              </div>
            </div>

            {pricing && (
              <div className={ps.monthlyPayment}>
                <Calculator size={14} />
                <span>תשלום חודשי: <strong>{formatCurrency(pricing.monthly_payment)}</strong></span>
              </div>
            )}

            <button
              className={`${s.btn} ${s['btn-primary']}`}
              onClick={handleSelectCourse}
              disabled={!selectedCourseId}
            >
              שמור קורס ותמחור
            </button>
          </>
        )}
      </div>

      {/* Payment Link Section */}
      <div className={ps.card}>
        <h3 className={ps.cardTitle}>
          <CreditCard size={16} />
          סליקה
        </h3>
        {(createdPaymentLink || lead.nedarim_payment_link) ? (
          <>
            <div className={ps.linkDisplay}>
              <input className={s.input} value={createdPaymentLink || lead.nedarim_payment_link} readOnly />
              <button className={`${s.btn} ${s['btn-secondary']}`} onClick={copyLink}>
                <Copy size={14} /> העתק
              </button>
            </div>
            <div className={ps.status}>
              {lead.first_payment ? (
                <span className={ps.paid}><CheckCircle2 size={14} /> תשלום ראשון בוצע</span>
              ) : (
                <span className={ps.pending}><XCircle size={14} /> ממתין לתשלום</span>
              )}
            </div>
          </>
        ) : (
          <div style={{ display: 'flex', gap: '10px', flexDirection: 'column' }}>
            <button
              className={`${s.btn} ${s['btn-primary']}`}
              onClick={() => setShowDirectChargeDialog(true)}
              disabled={!selectedCourseId}
              style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
            >
              <CreditCard size={16} /> סלוק כרטיס אשראי ישירות
            </button>
            <button
              className={`${s.btn} ${s['btn-secondary']}`}
              onClick={handleCreateLink}
              disabled={isCreatingLink || !selectedCourseId}
            >
              <CreditCard size={16} /> {isCreatingLink ? 'יוצר לינק...' : 'או צור לינק תשלום'}
            </button>
          </div>
        )}
      </div>

      {/* Direct Charge Dialog */}
      {showDirectChargeDialog && (
        <DirectChargeDialog
          leadId={lead.id}
          leadName={lead.full_name}
          defaultAmount={pricing?.final_price || (selectedCourse?.price ? Number(selectedCourse.price) : undefined)}
          defaultInstallments={Number(paymentsCount) || 1}
          onClose={() => setShowDirectChargeDialog(false)}
          onSuccess={() => {
            onUpdate()
            setShowDirectChargeDialog(false)
          }}
        />
      )}

      {/* Payment History Section */}
      <div className={ps.card}>
        <h3 className={ps.cardTitle}>היסטוריית תשלומים</h3>
        {!paymentStatus.payments || paymentStatus.payments.length === 0 ? (
          <p style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>אין עדיין תשלומים עבור ליד זה.</p>
        ) : (
          <table className={s.table}>
            <thead>
              <tr>
                <th>תאריך</th>
                <th>סכום</th>
                <th>סטטוס</th>
                <th>אסמכתא</th>
              </tr>
            </thead>
            <tbody>
              {paymentStatus.payments.map(p => (
                <tr key={p.id}>
                  <td>{formatDateTime(p.payment_date || p.created_at)}</td>
                  <td>{formatCurrency(p.amount)}</td>
                  <td>{p.status}</td>
                  <td>{p.reference || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
