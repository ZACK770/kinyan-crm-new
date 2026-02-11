import React, { useState } from 'react';
import { X, MessageCircle, Loader2 } from 'lucide-react';

interface Props {
  leadId: number;
  leadName: string;
  onClose: () => void;
  onSuccess: () => void;
}

const StudentChatDialog: React.FC<Props> = ({ leadId, leadName, onClose, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    chat_link: '',
    platform: 'WhatsApp'
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.chat_link) {
      setError('נא להזין קישור לקבוצה');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/leads/${leadId}/conversion/student-chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          chat_link: formData.chat_link,
          platform: formData.platform
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'שגיאה בשמירת פרטי הצ\'אט');
      }

      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'שגיאה בשמירת פרטי הצ\'אט');
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
              <MessageCircle className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">הוספה לצ'אט תלמידים</h2>
              <p className="text-sm text-gray-600">{leadName}</p>
            </div>
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

          {/* Platform */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              פלטפורמה <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.platform}
              onChange={(e) => setFormData({ ...formData, platform: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
              disabled={loading}
            >
              <option value="WhatsApp">WhatsApp</option>
              <option value="Telegram">Telegram</option>
              <option value="Discord">Discord</option>
              <option value="Slack">Slack</option>
              <option value="אחר">אחר</option>
            </select>
          </div>

          {/* Chat Link */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              קישור לקבוצה <span className="text-red-500">*</span>
            </label>
            <input
              type="url"
              value={formData.chat_link}
              onChange={(e) => setFormData({ ...formData, chat_link: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="https://chat.whatsapp.com/..."
              required
              disabled={loading}
            />
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>טיפ:</strong> העתק את הקישור לקבוצת התלמידים הרלוונטית והדבק כאן. 
              ודא שהקישור תקף ופעיל לפני השמירה.
            </p>
          </div>

          {/* Platform-specific instructions */}
          {formData.platform === 'WhatsApp' && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <p className="text-xs text-green-800">
                <strong>WhatsApp:</strong> בקבוצה, לחץ על שם הקבוצה → הזמן באמצעות קישור → העתק קישור
              </p>
            </div>
          )}

          {formData.platform === 'Telegram' && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-xs text-blue-800">
                <strong>Telegram:</strong> בקבוצה, לחץ על שם הקבוצה → הוסף חברים → העתק קישור
              </p>
            </div>
          )}

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
                'שמור'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default StudentChatDialog;
