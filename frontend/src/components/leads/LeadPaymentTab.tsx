import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import { CreditCard, CheckCircle2, XCircle, Calculator, Tag, AlertCircle } from 'lucide-react'
import type { Lead, Course, Payment } from '@/types'
import { formatCurrency, formatDateTime } from '@/lib/status'
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
  
  // Card details (inline - no dialog)
  const [cardNumber, setCardNumber] = useState('')
  const [expiry, setExpiry] = useState('')
  const [cvv, setCvv] = useState('')
  const [comments, setComments] = useState('')
  const [paymentType, setPaymentType] = useState<'RAGIL' | 'HK'>('HK')
  const [isProcessing, setIsProcessing] = useState(false)
  const [chargeResult, setChargeResult] = useState<any>(null)
  
  // Payment status
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatus | null>(null)
  
  // Errors
  const [error, setError] = useState<string | null>(null)

  const selectedCourse = courses.find(c => c.id === selectedCourseId)

  // Derived amounts
  const numPayments = Number(paymentsCount) || 1
  const finalPrice = pricing?.final_price ?? 0
  const monthlyAmount = numPayments > 0 ? Math.round((finalPrice / numPayments) * 100) / 100 : finalPrice

  // Load course defaults when selected
  useEffect(() => {
    if (selectedCourse) {
      setPrice(String(selectedCourse.price ?? ''))
      setPaymentsCount(String(selectedCourse.payments_count ?? 1))
      setPaymentDay('15')
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

  // Save course selection (returns true on success)
  const handleSelectCourse = async (): Promise<boolean> => {
    if (!selectedCourseId) {
      setError('יש לבחור קורס')
      return false
    }
    
    setError(null)
    try {
      await api.post(`/leads/${lead.id}/select-course`, {
        course_id: selectedCourseId,
        price: Number(price),
        payments_count: numPayments,
        payment_day: Number(paymentDay),
      })
      
      // Update discount if provided
      if (Number(discountAmount) > 0) {
        await api.patch(`/leads/${lead.id}/update-discount`, {
          discount_amount: Number(discountAmount),
          installments_override: numPayments,
        })
      }
      
      onUpdate()
      return true
    } catch (err) {
      const message = err instanceof Error ? err.message : 'שגיאה בשמירת קורס'
      setError(message)
      return false
    }
  }

  // Format card number with spaces
  const handleCardNumberChange = (value: string) => {
    const cleaned = value.replace(/\s/g, '')
    const formatted = cleaned.match(/.{1,4}/g)?.join(' ') || cleaned
    setCardNumber(formatted)
  }

  // Format expiry as MM/YY
  const handleExpiryChange = (value: string) => {
    const cleaned = value.replace(/\D/g, '')
    if (cleaned.length >= 2) {
      setExpiry(cleaned.slice(0, 2) + '/' + cleaned.slice(2, 4))
    } else {
      setExpiry(cleaned)
    }
  }

  // Direct charge submit
  const handleCharge = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Save course first
    const saved = await handleSelectCourse()
    if (!saved) return

    setIsProcessing(true)
    setError(null)
    setChargeResult(null)
    
    try {
      const cleanCardNumber = cardNumber.replace(/\s/g, '')
      const cleanExpiry = expiry.replace(/\D/g, '')
      
      if (cleanCardNumber.length < 13 || cleanCardNumber.length > 16) {
        throw new Error('מספר כרטיס לא תקין (13-16 ספרות)')
      }
      if (cleanExpiry.length !== 4) {
        throw new Error('תוקף לא תקין (MMYY)')
      }
      if (cvv.length < 3 || cvv.length > 4) {
        throw new Error('CVV לא תקין (3-4 ספרות)')
      }
      
      const amount = paymentType === 'HK' ? monthlyAmount : finalPrice
      if (!amount || amount <= 0) {
        throw new Error('סכום לא תקין')
      }
      
      const payload: any = {
        card_number: cleanCardNumber,
        expiry: cleanExpiry,
        cvv: cvv,
        amount: amount,
        installments: numPayments,
        payment_type: paymentType,
        comments: comments || undefined
      }
      
      const response = await api.post<any>(`/leads/${lead.id}/charge-card-direct`, payload)
      
      setChargeResult(response)
      toast.success(`סליקה הצליחה! אישור: ${response.confirmation || response.keva_id}`)
      onUpdate()
      
    } catch (err: any) {
      const errorMsg = err?.message || err?.response?.data?.detail || 'שגיאה בסליקה'
      setError(errorMsg)
      toast.error(errorMsg)
    } finally {
      setIsProcessing(false)
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
                      {isCalculating ? '...' : formatCurrency(finalPrice)}
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

            {pricing && numPayments > 0 && (
              <div className={ps.monthlyPayment}>
                <Calculator size={14} />
                <span>תשלום חודשי: <strong>{formatCurrency(monthlyAmount)}</strong></span>
              </div>
            )}
          </>
        )}
      </div>

      {/* Inline Payment Form */}
      {selectedCourse && pricing && (
        <div className={ps.card}>
          <h3 className={ps.cardTitle}>
            <CreditCard size={16} />
            סליקה
          </h3>

          {chargeResult ? (
            <div style={{
              background: '#d4edda',
              border: '1px solid #c3e6cb',
              borderRadius: '8px',
              padding: '20px',
              textAlign: 'center'
            }}>
              <CheckCircle2 size={48} style={{ color: '#155724', margin: '0 auto 15px' }} />
              <h3 style={{ color: '#155724', marginBottom: '15px', fontSize: '20px' }}>
                הסליקה הושלמה בהצלחה!
              </h3>
              <div style={{ fontSize: '14px', color: '#155724', textAlign: 'right' }}>
                {chargeResult.confirmation && (
                  <div style={{ padding: '8px 0', borderBottom: '1px solid #c3e6cb' }}>
                    <strong>מספר אישור:</strong> {chargeResult.confirmation}
                  </div>
                )}
                {chargeResult.keva_id && (
                  <div style={{ padding: '8px 0', borderBottom: '1px solid #c3e6cb' }}>
                    <strong>מזהה הוראת קבע:</strong> {chargeResult.keva_id}
                  </div>
                )}
                <div style={{ padding: '8px 0', borderBottom: '1px solid #c3e6cb' }}>
                  <strong>סכום:</strong> {formatCurrency(chargeResult.amount)}
                </div>
                <div style={{ padding: '8px 0' }}>
                  <strong>תשלומים:</strong> {chargeResult.installments}
                </div>
              </div>
            </div>
          ) : (
            <form onSubmit={handleCharge}>
              {/* Payment Type Selection */}
              <div className={s['form-group']}>
                <label className={s['form-label']}>סוג תשלום</label>
                <div style={{ display: 'flex', gap: '15px', marginTop: '8px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                    <input
                      type="radio"
                      name="paymentType"
                      value="HK"
                      checked={paymentType === 'HK'}
                      onChange={() => setPaymentType('HK')}
                      disabled={isProcessing}
                    />
                    <span>הוראת קבע (חודשי)</span>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                    <input
                      type="radio"
                      name="paymentType"
                      value="RAGIL"
                      checked={paymentType === 'RAGIL'}
                      onChange={() => setPaymentType('RAGIL')}
                      disabled={isProcessing}
                    />
                    <span>חיוב רגיל (תשלומים)</span>
                  </label>
                </div>
                <div style={{ marginTop: '8px', padding: '10px', background: paymentType === 'HK' ? '#e8f5e9' : '#e3f2fd', borderRadius: '6px', border: `1px solid ${paymentType === 'HK' ? '#4caf50' : '#2196f3'}`, fontSize: '13px', color: '#555' }}>
                  {paymentType === 'HK'
                    ? `הוראת קבע: ${formatCurrency(monthlyAmount)} x ${numPayments} חודשים = ${formatCurrency(finalPrice)}`
                    : `חיוב רגיל: ${formatCurrency(finalPrice)} מחולק ל-${numPayments} תשלומים של ${formatCurrency(monthlyAmount)}`
                  }
                </div>
              </div>

              {/* Card Number */}
              <div className={s['form-group']}>
                <label className={s['form-label']}>מספר כרטיס אשראי</label>
                <input
                  type="text"
                  className={s.input}
                  value={cardNumber}
                  onChange={e => handleCardNumberChange(e.target.value)}
                  placeholder="4580 1234 5678 9012"
                  maxLength={19}
                  required
                  disabled={isProcessing}
                  style={{ direction: 'ltr', textAlign: 'left' }}
                />
              </div>

              {/* Expiry & CVV */}
              <div className={s['form-row']}>
                <div className={s['form-group']}>
                  <label className={s['form-label']}>תוקף (MM/YY)</label>
                  <input
                    type="text"
                    className={s.input}
                    value={expiry}
                    onChange={e => handleExpiryChange(e.target.value)}
                    placeholder="12/26"
                    maxLength={5}
                    required
                    disabled={isProcessing}
                    style={{ direction: 'ltr', textAlign: 'left' }}
                  />
                </div>
                <div className={s['form-group']}>
                  <label className={s['form-label']}>CVV</label>
                  <input
                    type="text"
                    className={s.input}
                    value={cvv}
                    onChange={e => setCvv(e.target.value.replace(/\D/g, ''))}
                    placeholder="123"
                    maxLength={4}
                    required
                    disabled={isProcessing}
                    style={{ direction: 'ltr', textAlign: 'left' }}
                  />
                </div>
              </div>

              {/* Comments */}
              <div className={s['form-group']}>
                <label className={s['form-label']}>הערות</label>
                <input
                  type="text"
                  className={s.input}
                  value={comments}
                  onChange={e => setComments(e.target.value)}
                  placeholder="תיאור התשלום (אופציונלי)"
                  disabled={isProcessing}
                />
              </div>

              {/* Warning + Submit */}
              <div style={{
                background: '#fff3cd',
                border: '1px solid #ffc107',
                borderRadius: '8px',
                padding: '10px 12px',
                marginTop: '12px',
                display: 'flex',
                gap: '8px',
                alignItems: 'center',
                fontSize: '13px',
                color: '#856404'
              }}>
                <AlertCircle size={16} style={{ flexShrink: 0 }} />
                <span>פעולה זו תבצע חיוב אמיתי של כרטיס אשראי</span>
              </div>

              <button
                type="submit"
                className={`${s.btn} ${s['btn-primary']}`}
                disabled={isProcessing}
                style={{ marginTop: '12px', width: '100%', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
              >
                <CreditCard size={16} />
                {isProcessing ? 'מעבד...' : 'בצע סליקה'}
              </button>
            </form>
          )}
        </div>
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
