import React, { useState } from 'react';
import { X, DollarSign, Loader2 } from 'lucide-react';

interface Props {
  leadId: number;
  onClose: () => void;
  onSuccess: () => void;
}

const PaymentDialog: React.FC<Props> = ({ leadId, onClose, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    amount: '',
    method: 'אשראי',
    reference: '',
    verified: false
  });

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

      onSuccess();
      onClose();
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
            <h2 className="text-xl font-bold text-gray-900">רישום סליקה</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
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
              onClick={onClose}
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
                'שמור סליקה'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PaymentDialog;
