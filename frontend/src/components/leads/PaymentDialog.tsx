import React, { useState, useEffect } from 'react';
import { X, DollarSign, Loader2, CheckCircle2, Plus } from 'lucide-react';

interface Payment {
  id: number;
  amount: number;
  payment_method: string;
  status: string;
  payment_date?: string;
  reference?: string;
  nedarim_transaction_id?: string;
}

interface Props {
  leadId: number;
  onClose: () => void;
  onSuccess: () => void;
}

const PaymentDialog: React.FC<Props> = ({ leadId, onClose, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [totalPaid, setTotalPaid] = useState(0);
  const [totalPrice, setTotalPrice] = useState(0);
  const [showAddForm, setShowAddForm] = useState(false);
  
  const [formData, setFormData] = useState({
    amount: '',
    method: 'אשראי',
    reference: '',
    verified: false
  });

  useEffect(() => {
    fetchPayments();
  }, [leadId]);

  const fetchPayments = async () => {
    try {
      const response = await fetch(`/api/leads/${leadId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (!response.ok) throw new Error('Failed to fetch lead');
      const lead = await response.json();
      
      // Fetch payments
      const paymentsResponse = await fetch(`/api/payments?lead_id=${leadId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (paymentsResponse.ok) {
        const paymentsData = await paymentsResponse.json();
        setPayments(paymentsData.items || []);
        const paid = paymentsData.items?.reduce((sum: number, p: Payment) => 
          p.status === 'שולם' ? sum + p.amount : sum, 0) || 0;
        setTotalPaid(paid);
      }
      
      setTotalPrice(lead.selected_price || 0);
    } catch (err) {
      console.error('Error fetching payments:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      setError('נא להזין סכום תקין');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/leads/${leadId}/conversion/payment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          amount: parseFloat(formData.amount),
          method: formData.method,
          reference: formData.reference || null,
          verified: formData.verified
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'שגיאה ברישום התשלום');
      }

      await fetchPayments();
      setShowAddForm(false);
      setFormData({ amount: '', method: 'אשראי', reference: '', verified: false });
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'שגיאה ברישום התשלום');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
              <DollarSign className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">ניהול תשלומים</h2>
              <p className="text-sm text-gray-600 mt-1">
                נסלק: ₪{totalPaid.toLocaleString()} מתוך ₪{totalPrice.toLocaleString()}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Existing Payments */}
          {payments.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-semibold text-gray-900">תשלומים קיימים</h3>
              {payments.map((payment) => (
                <div
                  key={payment.id}
                  className={`p-4 rounded-lg border-2 ${
                    payment.status === 'שולם'
                      ? 'bg-green-50 border-green-200'
                      : 'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        {payment.status === 'שולם' && (
                          <CheckCircle2 className="w-5 h-5 text-green-600" />
                        )}
                        <span className="font-semibold text-gray-900">
                          ₪{payment.amount.toLocaleString()}
                        </span>
                        <span className="text-sm text-gray-600">• {payment.payment_method}</span>
                      </div>
                      {payment.nedarim_transaction_id && (
                        <p className="text-xs text-gray-500 mt-1">
                          אישור: {payment.nedarim_transaction_id}
                        </p>
                      )}
                      {payment.payment_date && (
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(payment.payment_date).toLocaleDateString('he-IL')}
                        </p>
                      )}
                    </div>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        payment.status === 'שולם'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {payment.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Progress Bar */}
          {totalPrice > 0 && (
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="font-medium text-gray-700">התקדמות תשלום</span>
                <span className="font-bold text-blue-600">
                  {Math.round((totalPaid / totalPrice) * 100)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-blue-500 to-indigo-600 h-full transition-all duration-500"
                  style={{ width: `${Math.min((totalPaid / totalPrice) * 100, 100)}%` }}
                />
              </div>
              <p className="text-xs text-gray-600 mt-2">
                {totalPaid >= totalPrice
                  ? '✅ התשלום הושלם במלואו'
                  : `נותרו לתשלום: ₪${(totalPrice - totalPaid).toLocaleString()}`}
              </p>
            </div>
          )}

          {/* Add Payment Button */}
          {!showAddForm && totalPaid < totalPrice && (
            <button
              onClick={() => setShowAddForm(true)}
              className="w-full px-4 py-3 border-2 border-dashed border-blue-300 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors font-medium flex items-center justify-center gap-2"
            >
              <Plus className="w-5 h-5" />
              הוסף תשלום נוסף
            </button>
          )}

          {/* Add Payment Form */}
          {showAddForm && (
            <form onSubmit={handleSubmit} className="space-y-4 p-4 bg-gray-50 rounded-lg border-2 border-blue-200">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800">
              {error}
            </div>
          )}

          {/* Amount */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              סכום התשלום <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <input
                type="number"
                step="0.01"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="0.00"
                required
                disabled={loading}
              />
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">₪</span>
            </div>
          </div>

          {/* Payment Method */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              שיטת תשלום <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.method}
              onChange={(e) => setFormData({ ...formData, method: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
              disabled={loading}
            >
              <option value="אשראי">אשראי</option>
              <option value="העברה בנקאית">העברה בנקאית</option>
              <option value="מזומן">מזומן</option>
              <option value="צ'ק">צ'ק</option>
              <option value="ביט">ביט</option>
              <option value="פייבוקס">פייבוקס</option>
            </select>
          </div>

          {/* Reference */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              אסמכתא / מספר עסקה
            </label>
            <input
              type="text"
              value={formData.reference}
              onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="לדוגמה: 123456"
              disabled={loading}
            />
          </div>

          {/* Verified Checkbox */}
          <div className="flex items-start gap-3 p-4 bg-blue-50 rounded-lg">
            <input
              type="checkbox"
              id="verified"
              checked={formData.verified}
              onChange={(e) => setFormData({ ...formData, verified: e.target.checked })}
              className="mt-1 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              disabled={loading}
            />
            <label htmlFor="verified" className="text-sm text-gray-700">
              <span className="font-medium">התשלום אושר ע"י נדרים פלוס</span>
              <p className="text-xs text-gray-600 mt-1">
                סמן רק אם קיבלת אישור מנדרים פלוס שהתשלום עבר בהצלחה
              </p>
            </label>
          </div>

              {/* Actions */}
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddForm(false);
                    setFormData({ amount: '', method: 'אשראי', reference: '', verified: false });
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                  disabled={loading}
                >
                  ביטול
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      שומר...
                    </>
                  ) : (
                    'שמור תשלום'
                  )}
                </button>
              </div>
            </form>
          )}

          {/* Close Button */}
          {!showAddForm && (
            <button
              onClick={onClose}
              className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
            >
              סגור
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default PaymentDialog;
