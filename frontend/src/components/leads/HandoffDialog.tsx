import React, { useState, useEffect } from 'react';
import { X, UserCheck, Loader2, AlertCircle } from 'lucide-react';

interface User {
  id: number;
  full_name: string;
  email: string;
  role_name: string;
}

interface Props {
  leadId: number;
  leadName: string;
  onClose: () => void;
  onSuccess: () => void;
}

const HandoffDialog: React.FC<Props> = ({ leadId, leadName, onClose, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [loadingManagers, setLoadingManagers] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [managers, setManagers] = useState<User[]>([]);
  
  const [selectedManagerId, setSelectedManagerId] = useState<number | null>(null);

  useEffect(() => {
    fetchManagers();
  }, []);

  const fetchManagers = async () => {
    try {
      setLoadingManagers(true);
      const response = await fetch('/api/users?role=class_manager', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) throw new Error('Failed to fetch managers');
      
      const data = await response.json();
      setManagers(data.users || []);
      
      if (data.users && data.users.length > 0) {
        setSelectedManagerId(data.users[0].id);
      }
    } catch (err) {
      console.error('Error fetching managers:', err);
      setError('שגיאה בטעינת רשימת מנהלי כיתות');
    } finally {
      setLoadingManagers(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedManagerId) {
      setError('נא לבחור מנהל כיתות');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/leads/${leadId}/conversion/handoff`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          manager_id: selectedManagerId
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'שגיאה בהעברה למנהל');
      }

      await response.json();
      
      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'שגיאה בהעברה למנהל');
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
            <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
              <UserCheck className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">העברה למנהל כיתות</h2>
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
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Manager Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              בחר מנהל כיתות <span className="text-red-500">*</span>
            </label>
            
            {loadingManagers ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
              </div>
            ) : managers.length === 0 ? (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-sm text-yellow-800">
                  לא נמצאו מנהלי כיתות במערכת. נא ליצור קשר עם מנהל המערכת.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {managers.map((manager) => (
                  <label
                    key={manager.id}
                    className={`flex items-center gap-3 p-4 border-2 rounded-lg cursor-pointer transition-all ${
                      selectedManagerId === manager.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="manager"
                      value={manager.id}
                      checked={selectedManagerId === manager.id}
                      onChange={() => setSelectedManagerId(manager.id)}
                      className="w-4 h-4 text-blue-600"
                      disabled={loading}
                    />
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{manager.full_name}</p>
                      <p className="text-sm text-gray-600">{manager.email}</p>
                    </div>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-2">
            <p className="text-sm font-medium text-blue-900">
              מה יקרה לאחר ההעברה?
            </p>
            <ul className="text-sm text-blue-800 space-y-1 mr-4">
              <li className="list-disc">המנהל יקבל 2 משימות חדשות:</li>
              <li className="list-none mr-4">1. אישור קבלת חומרי לימוד/משלוח</li>
              <li className="list-none mr-4">2. וידוא הצטרפות לצ'אט תלמידים</li>
              <li className="list-disc mt-2">לאחר שהמנהל ישלים את המשימות, הליד יומר אוטומטית לתלמיד</li>
            </ul>
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
              disabled={loading || loadingManagers || managers.length === 0}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  מעביר...
                </>
              ) : (
                'העבר למנהל'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default HandoffDialog;
