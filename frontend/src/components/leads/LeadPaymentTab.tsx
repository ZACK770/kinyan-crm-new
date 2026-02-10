import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import { CreditCard, CheckCircle2, XCircle, Copy, Calculator, Tag } from 'lucide-react'
import type { Lead, Product, Payment } from '@/types'
import { formatCurrency, formatDateTime } from '@/lib/status'
import s from '@/styles/shared.module.css'
import ps from './LeadPaymentTab.module.css'

interface LeadPaymentTabProps {
  lead: Lead
  products: Product[]
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
export function LeadPaymentTab({ lead, products, onUpdate }: LeadPaymentTabProps) {
  const toast = useToast()
  
  // Product selection state
  const [selectedProductId, setSelectedProductId] = useState<number | ''>(lead.selected_product_id ?? '')
  const [price, setPrice] = useState('')
  const [paymentsCount, setPaymentsCount] = useState('1')
  const [paymentDay, setPaymentDay] = useState('15')
  const [discountAmount, setDiscountAmount] = useState('0')
  
  // Calculated pricing (real-time)
  const [pricing, setPricing] = useState<PricingCalculation | null>(null)
  const [isCalculating, setIsCalculating] = useState(false)
  
  // Payment link state
  const [isCreatingLink, setIsCreatingLink] = useState(false)
  
  // Payment status
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatus | null>(null)
  
  // Errors
  const [error, setError] = useState<string | null>(null)

  const selectedProduct = products.find(p => p.id === selectedProductId)

  // Load product defaults when selected
  useEffect(() => {
    if (selectedProduct) {
      setPrice(String(selectedProduct.price ?? ''))
      setPaymentsCount(String(selectedProduct.payments_count ?? '1'))
      setPaymentDay('15') // Default
      setDiscountAmount('0')
    }
  }, [selectedProduct])

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
      if (!selectedProductId || !price) {
        setPricing(null)
        return
      }

      setIsCalculating(true)
      try {
        const data = await api.post<PricingCalculation>(`/leads/${lead.id}/calculate-pricing`, {
          product_id: selectedProductId,
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
  }, [selectedProductId, price, discountAmount, lead.id])

  // Save product selection
  const handleSelectProduct = async () => {
    if (!selectedProductId) {
      setError('יש לבחור מוצר')
      return
    }
    
    setError(null)
    try {
      await api.post(`/leads/${lead.id}/select-product`, {
        product_id: selectedProductId,
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
      
      toast.success('מוצר ותמחור נשמרו בהצלחה')
      onUpdate()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'שגיאה בשמירת מוצר'
      setError(message)
    }
  }

  // Create payment link
  const handleCreateLink = async () => {
    if (!lead.selected_product_id) {
      setError('יש לבחור ולשמור מוצר קודם')
      return
    }

    setIsCreatingLink(true)
    setError(null)
    try {
      await api.post(`/leads/${lead.id}/create-payment-link`, {})
      toast.success('לינק תשלום נוצר בהצלחה')
      onUpdate()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'שגיאה ביצירת לינק'
      setError(message)
    } finally {
      setIsCreatingLink(false)
    }
  }

  const copyLink = () => {
    if (lead.nedarim_payment_link) {
      navigator.clipboard.writeText(lead.nedarim_payment_link)
      toast.info('הלינק הועתק ללוח')
    }
  }

  if (!paymentStatus) {
    return <div>טוען נתוני תשלום...</div>
  }

  return (
    <div className={ps.paymentTab}>
      {/* Product Selection & Pricing */}
      <div className={ps.card}>
        <h3 className={ps.cardTitle}>
          <Tag size={16} />
          בחירת מוצר ותמחור
        </h3>
        
        {error && (
          <div className={ps.errorBox}>
            <XCircle size={14} />
            {error}
          </div>
        )}

        <div className={s['form-group']}>
          <label className={s['form-label']}>מוצר</label>
          <select
            className={s.select}
            value={selectedProductId}
            onChange={e => setSelectedProductId(Number(e.target.value))}
          >
            <option value="">— בחר מוצר —</option>
            {products.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </div>

        {selectedProduct && (
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
              onClick={handleSelectProduct}
              disabled={!selectedProductId}
            >
              שמור מוצר ותמחור
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
        {lead.nedarim_payment_link ? (
          <>
            <div className={ps.linkDisplay}>
              <input className={s.input} value={lead.nedarim_payment_link} readOnly />
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
          <button
            className={`${s.btn} ${s['btn-primary']}`}
            onClick={handleCreateLink}
            disabled={isCreatingLink || !lead.selected_product_id}
          >
            <CreditCard size={16} /> {isCreatingLink ? 'יוצר לינק...' : 'צור לינק תשלום'}
          </button>
        )}
      </div>

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
