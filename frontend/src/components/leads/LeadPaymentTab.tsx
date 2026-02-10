import { useState, useEffect } from 'react'
import { api } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import { CreditCard, CheckCircle2, XCircle, Link, Copy } from 'lucide-react'
import type { Lead, Product, LeadPaymentStatus, Payment } from '@/types'
import { formatCurrency, formatDateTime } from '@/lib/status'
import s from '@/styles/shared.module.css'
import ps from './LeadPaymentTab.module.css'

interface LeadPaymentTabProps {
  lead: Lead
  products: Product[]
  onUpdate: () => void
}

/* ══════════════════════════════════════════════════════════════
   Product Selector Component
   ══════════════════════════════════════════════════════════════ */
function ProductSelector({ lead, products, onUpdate }: LeadPaymentTabProps) {
  const { toast } = useToast()
  const [selectedProductId, setSelectedProductId] = useState<number | ''>(lead.selected_product_id ?? '')
  const [price, setPrice] = useState('')
  const [paymentsCount, setPaymentsCount] = useState('1')

  const selectedProduct = products.find(p => p.id === selectedProductId)

  useEffect(() => {
    if (selectedProduct) {
      setPrice(String(selectedProduct.price ?? ''))
      setPaymentsCount(String(selectedProduct.payments_count ?? '1'))
    }
  }, [selectedProduct])

  const handleSelectProduct = async () => {
    if (!selectedProductId) return
    try {
      await api.post(`/leads/${lead.id}/select-product`, {
        product_id: selectedProductId,
        price: Number(price),
        payments_count: Number(paymentsCount),
      })
      toast.success('מוצר נבחר בהצלחה')
      onUpdate()
    } catch (err) {
      toast.error('שגיאה בבחירת מוצר')
    }
  }

  return (
    <div className={ps.card}>
      <h3 className={ps.cardTitle}>בחירת מוצר ותנאי תשלום</h3>
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
          <div className={s['form-row']}>
            <div className={s['form-group']}>
              <label className={s['form-label']}>מחיר</label>
              <input
                className={s.input}
                type="number"
                value={price}
                onChange={e => setPrice(e.target.value)}
              />
            </div>
            <div className={s['form-group']}>
              <label className={s['form-label']}>מספר תשלומים</label>
              <input
                className={s.input}
                type="number"
                value={paymentsCount}
                onChange={e => setPaymentsCount(e.target.value)}
              />
            </div>
          </div>
          <button
            className={`${s.btn} ${s['btn-primary']}`}
            onClick={handleSelectProduct}
          >
            שמור מוצר
          </button>
        </>
      )}
    </div>
  )
}

/* ══════════════════════════════════════════════════════════════
   Payment Link Generator Component
   ══════════════════════════════════════════════════════════════ */
function PaymentLink({ lead, onUpdate }: { lead: Lead, onUpdate: () => void }) {
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)

  const handleCreateLink = async () => {
    setIsLoading(true)
    try {
      await api.post(`/leads/${lead.id}/create-payment-link`, {
        amount: 250, // Example: should come from selected product
        installments: 1,
      })
      toast.success('לינק תשלום נוצר ונשלח')
      onUpdate()
    } catch (err) {
      toast.error('שגיאה ביצירת לינק')
    } finally {
      setIsLoading(false)
    }
  }

  const copyLink = () => {
    if (lead.nedarim_payment_link) {
      navigator.clipboard.writeText(lead.nedarim_payment_link)
      toast.info('הלינק הועתק')
    }
  }

  return (
    <div className={ps.card}>
      <h3 className={ps.cardTitle}>סליקה</h3>
      {lead.nedarim_payment_link ? (
        <div className={ps.linkDisplay}>
          <input className={s.input} value={lead.nedarim_payment_link} readOnly />
          <button className={`${s.btn} ${s['btn-secondary']}`} onClick={copyLink}>
            <Copy size={14} />
          </button>
        </div>
      ) : (
        <button
          className={`${s.btn} ${s['btn-primary']}`}
          onClick={handleCreateLink}
          disabled={isLoading}
        >
          <CreditCard size={16} /> {isLoading ? 'יוצר לינק...' : 'צור לינק לתשלום ראשון'}
        </button>
      )}
      <div className={ps.status}>
        {lead.first_payment ? (
          <span className={ps.paid}><CheckCircle2 size={14} /> תשלום ראשון בוצע</span>
        ) : (
          <span className={ps.pending}><XCircle size={14} /> ממתין לתשלום</span>
        )}
      </div>
    </div>
  )
}

/* ══════════════════════════════════════════════════════════════
   Payment History Component
   ══════════════════════════════════════════════════════════════ */
function PaymentHistory({ payments }: { payments: Payment[] }) {
  if (!payments || payments.length === 0) {
    return (
      <div className={ps.card}>
        <h3 className={ps.cardTitle}>היסטוריית תשלומים</h3>
        <p>אין עדיין תשלומים עבור ליד זה.</p>
      </div>
    )
  }

  return (
    <div className={ps.card}>
      <h3 className={ps.cardTitle}>היסטוריית תשלומים</h3>
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
          {payments.map(p => (
            <tr key={p.id}>
              <td>{formatDateTime(p.payment_date || p.created_at)}</td>
              <td>{formatCurrency(p.amount)}</td>
              <td>{p.status}</td>
              <td>{p.reference}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* ══════════════════════════════════════════════════════════════
   Main Tab Component
   ══════════════════════════════════════════════════════════════ */
export function LeadPaymentTab({ lead, products, onUpdate }: LeadPaymentTabProps) {
  const [status, setStatus] = useState<LeadPaymentStatus | null>(null)

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await api.get<LeadPaymentStatus>(`/leads/${lead.id}/payment-status`)
        setStatus(data)
      } catch (err) {
        console.error('Failed to fetch payment status', err)
      }
    }
    fetchStatus()
  }, [lead.id])

  if (!status) {
    return <div>טוען נתוני תשלום...</div>
  }

  return (
    <div className={ps.paymentTab}>
      <ProductSelector lead={lead} products={products} onUpdate={onUpdate} />
      <PaymentLink lead={lead} onUpdate={onUpdate} />
      <PaymentHistory payments={status.payments} />
    </div>
  )
}
