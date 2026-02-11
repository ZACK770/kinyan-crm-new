import { useState } from 'react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import { CreditCard, X, AlertCircle, CheckCircle2 } from 'lucide-react'
import s from '@/styles/shared.module.css'

interface DirectChargeDialogProps {
  leadId: number
  leadName: string
  defaultAmount?: number
  defaultInstallments?: number
  onClose: () => void
  onSuccess: () => void
}

export function DirectChargeDialog({
  leadId,
  leadName,
  defaultAmount,
  defaultInstallments = 1,
  onClose,
  onSuccess
}: DirectChargeDialogProps) {
  const toast = useToast()
  
  const [cardNumber, setCardNumber] = useState('')
  const [expiry, setExpiry] = useState('')
  const [cvv, setCvv] = useState('')
  const [comments, setComments] = useState('')
  const [paymentType, setPaymentType] = useState<'RAGIL' | 'HK'>('RAGIL')
  
  // Use props directly - no local state needed
  const amount = defaultAmount || 0
  const installments = defaultInstallments
  
  const [isProcessing, setIsProcessing] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    setIsProcessing(true)
    setError(null)
    setResult(null)
    
    try {
      // Clean card number and expiry
      const cleanCardNumber = cardNumber.replace(/\s/g, '')
      const cleanExpiry = expiry.replace(/\D/g, '')
      
      // Validate
      if (cleanCardNumber.length < 13 || cleanCardNumber.length > 16) {
        throw new Error('מספר כרטיס לא תקין (13-16 ספרות)')
      }
      if (cleanExpiry.length !== 4) {
        throw new Error('תוקף לא תקין (MMYY)')
      }
      if (cvv.length < 3 || cvv.length > 4) {
        throw new Error('CVV לא תקין (3-4 ספרות)')
      }
      if (!amount || amount <= 0) {
        throw new Error('סכום לא תקין')
      }
      
      const response = await api.post<any>(`/leads/${leadId}/charge-card-direct`, {
        card_number: cleanCardNumber,
        expiry: cleanExpiry,
        cvv: cvv,
        amount: amount,
        installments: installments,
        payment_type: paymentType,
        comments: comments || undefined
      })
      
      setResult(response)
      toast.success(`סליקה הצליחה! אישור: ${response.confirmation}`)
      
      // Wait a bit before closing to show success
      setTimeout(() => {
        onSuccess()
        onClose()
      }, 2000)
      
    } catch (err: any) {
      const errorMsg = err?.message || err?.response?.data?.detail || 'שגיאה בסליקה'
      setError(errorMsg)
      toast.error(errorMsg)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className={s.modalOverlay} onClick={onClose}>
      <div className={s.modal} onClick={e => e.stopPropagation()} style={{ maxWidth: '600px' }}>
        <div className={s.modalHeader}>
          <h2 className={s.modalTitle}>
            <CreditCard size={20} />
            סליקת כרטיס אשראי ישירה
          </h2>
          <button className={s.modalClose} onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className={s.modalBody}>
          {/* Warning */}
          <div style={{
            background: '#fff3cd',
            border: '1px solid #ffc107',
            borderRadius: '8px',
            padding: '12px',
            marginBottom: '20px',
            display: 'flex',
            gap: '10px',
            alignItems: 'flex-start'
          }}>
            <AlertCircle size={20} style={{ color: '#856404', flexShrink: 0, marginTop: '2px' }} />
            <div style={{ fontSize: '14px', color: '#856404' }}>
              <strong>שים לב:</strong> פעולה זו תבצע חיוב אמיתי של כרטיס אשראי דרך נדרים פלוס.
              <br />
              <strong>ליד:</strong> {leadName}
            </div>
          </div>

          {!result ? (
            <form onSubmit={handleSubmit}>
              {/* Card Number */}
              <div className={s['form-group']}>
                <label className={s['form-label']}>מספר כרטיס אשראי *</label>
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
                  <label className={s['form-label']}>תוקף (MM/YY) *</label>
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
                  <label className={s['form-label']}>CVV *</label>
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

              {/* Payment Type Selection */}
              <div className={s['form-group']}>
                <label className={s['form-label']}>סוג תשלום *</label>
                <div style={{ display: 'flex', gap: '15px', marginTop: '8px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                    <input
                      type="radio"
                      name="paymentType"
                      value="RAGIL"
                      checked={paymentType === 'RAGIL'}
                      onChange={() => setPaymentType('RAGIL')}
                      disabled={isProcessing}
                    />
                    <span>חיוב רגיל (חד-פעמי)</span>
                  </label>
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
                </div>
                {paymentType === 'HK' && (
                  <small style={{ fontSize: '12px', color: '#ff9800', display: 'block', marginTop: '6px' }}>
                    ⚠️ הוראת קבע - הכרטיס יחויב באופן אוטומטי כל חודש
                  </small>
                )}
              </div>

              {/* Amount & Installments - READ ONLY */}
              <div className={s['form-row']}>
                <div className={s['form-group']}>
                  <label className={s['form-label']}>סכום (₪) *</label>
                  <input
                    type="text"
                    className={s.input}
                    value={`₪${amount}`}
                    readOnly
                    disabled
                    style={{ background: '#f5f5f5', cursor: 'not-allowed' }}
                  />
                  <small style={{ fontSize: '12px', color: '#666', display: 'block', marginTop: '4px' }}>
                    מחיר נלקח אוטומטית מהקורס שנבחר
                  </small>
                </div>
                <div className={s['form-group']}>
                  <label className={s['form-label']}>תשלומים *</label>
                  <input
                    type="text"
                    className={s.input}
                    value={installments}
                    readOnly
                    disabled
                    style={{ background: '#f5f5f5', cursor: 'not-allowed' }}
                  />
                  <small style={{ fontSize: '12px', color: '#666', display: 'block', marginTop: '4px' }}>
                    מספר תשלומים נלקח אוטומטית מהקורס
                  </small>
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

              {/* Error */}
              {error && (
                <div style={{
                  background: '#f8d7da',
                  border: '1px solid #f5c6cb',
                  borderRadius: '8px',
                  padding: '12px',
                  marginTop: '15px',
                  color: '#721c24',
                  fontSize: '14px'
                }}>
                  <strong>שגיאה:</strong> {error}
                </div>
              )}

              {/* Submit */}
              <div className={s.modalFooter} style={{ marginTop: '20px' }}>
                <button
                  type="button"
                  className={`${s.btn} ${s['btn-secondary']}`}
                  onClick={onClose}
                  disabled={isProcessing}
                >
                  ביטול
                </button>
                <button
                  type="submit"
                  className={`${s.btn} ${s['btn-primary']}`}
                  disabled={isProcessing}
                >
                  {isProcessing ? 'מעבד...' : 'בצע סליקה'}
                </button>
              </div>
            </form>
          ) : (
            /* Success Result */
            <div>
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
                  <div style={{ padding: '8px 0', borderBottom: '1px solid #c3e6cb' }}>
                    <strong>מספר אישור:</strong> {result.confirmation}
                  </div>
                  <div style={{ padding: '8px 0', borderBottom: '1px solid #c3e6cb' }}>
                    <strong>מזהה עסקה:</strong> {result.transaction_id}
                  </div>
                  <div style={{ padding: '8px 0', borderBottom: '1px solid #c3e6cb' }}>
                    <strong>סכום:</strong> ₪{result.amount}
                  </div>
                  <div style={{ padding: '8px 0', borderBottom: '1px solid #c3e6cb' }}>
                    <strong>תשלומים:</strong> {result.installments}
                  </div>
                  {result.card_last_4 && (
                    <div style={{ padding: '8px 0', borderBottom: '1px solid #c3e6cb' }}>
                      <strong>4 ספרות אחרונות:</strong> {result.card_last_4}
                    </div>
                  )}
                  {result.receipt_number && (
                    <div style={{ padding: '8px 0' }}>
                      <strong>מספר קבלה:</strong> {result.receipt_number}
                    </div>
                  )}
                </div>
              </div>
              
              <div className={s.modalFooter} style={{ marginTop: '20px' }}>
                <button
                  className={`${s.btn} ${s['btn-primary']}`}
                  onClick={() => {
                    onSuccess()
                    onClose()
                  }}
                >
                  סגור
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
