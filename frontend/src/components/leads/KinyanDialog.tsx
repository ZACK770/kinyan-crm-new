import React, { useState } from 'react';
import { X, FileText, Loader2 } from 'lucide-react';

interface Props {
  leadId: number;
  onClose: () => void;
  onSuccess: () => void;
}

const KinyanDialog: React.FC<Props> = ({ leadId, onClose, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    method: 'PDF במייל',
    file_url: '',
    notes: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/leads/${leadId}/conversion/kinyan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          method: formData.method,
          file_url: formData.file_url || null,
          notes: formData.notes || null
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'שגיאה ברישום הקניון');
      }

      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'שגיאה ברישום הקניון');
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
            <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
              <FileText className="w-5 h-5 text-purple-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">רישום קניון/תקנון</h2>
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

          {/* Method */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              שיטת אישור <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.method}
              onChange={(e) => setFormData({ ...formData, method: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
              disabled={loading}
            >
              <option value="PDF במייל">PDF במייל</option>
              <option value="אישור טלפוני">אישור טלפוני</option>
              <option value="IVR ימות המשיח">IVR ימות המשיח</option>
              <option value="חתימה דיגיטלית">חתימה דיגיטלית</option>
              <option value="חתימה פיזית">חתימה פיזית (סרוק)</option>
            </select>
          </div>

          {/* File URL (optional) */}
          {(formData.method === 'PDF במייל' || formData.method === 'חתימה דיגיטלית' || formData.method === 'חתימה פיזית') && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                קישור לקובץ PDF
              </label>
              <input
                type="url"
                value={formData.file_url}
                onChange={(e) => setFormData({ ...formData, file_url: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="https://..."
                disabled={loading}
              />
              <p className="text-xs text-gray-500 mt-1">
                העלה את הקובץ ל-Google Drive או שירות אחסון אחר והדבק את הקישור כאן
              </p>
            </div>
          )}

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              הערות
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
              placeholder="הערות נוספות על אישור התקנון..."
              disabled={loading}
            />
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>שים לב:</strong> אישור התקנון הוא שלב חובה לפני המרת הליד לתלמיד. 
              ודא שהלקוח אישר את התנאים בצורה ברורה.
            </p>
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
                'שמור קניון'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default KinyanDialog;
