import React, { useState, useEffect } from 'react';
import { CheckCircle2, Circle, Loader2, AlertCircle } from 'lucide-react';
import PaymentDialog from './PaymentDialog';
import KinyanDialog from './KinyanDialog';
// import ShippingDialog from './ShippingDialog';
// import StudentChatDialog from './StudentChatDialog';
// import HandoffDialog from './HandoffDialog';

interface Lead {
  id: number;
  full_name: string;
  phone: string;
  status: string;
  payment_completed?: boolean;
  payment_completed_amount?: number;
  payment_completed_date?: string;
  payment_completed_method?: string;
  payment_verified?: boolean;
  kinyan_signed?: boolean;
  kinyan_signed_date?: string;
  kinyan_method?: string;
  shipping_details_complete?: boolean;
  shipping_full_address?: string;
  shipping_city?: string;
  student_chat_added?: boolean;
  student_chat_platform?: string;
  handoff_to_manager?: boolean;
  handoff_completed?: boolean;
  conversion_checklist_complete?: boolean;
  conversion_completed_at?: string;
}

interface ConversionProgress {
  steps: {
    payment: boolean;
    kinyan: boolean;
    shipping: boolean;
    chat: boolean;
    handoff: boolean;
  };
  completed: number;
  total: number;
  percentage: number;
  conversion_complete: boolean;
}

interface Props {
  lead: Lead;
  onUpdate: () => void;
}

const LeadConversionChecklist: React.FC<Props> = ({ lead, onUpdate }) => {
  const [progress, setProgress] = useState<ConversionProgress | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [showKinyanDialog, setShowKinyanDialog] = useState(false);
  const [showShippingDialog, setShowShippingDialog] = useState(false);
  const [showChatDialog, setShowChatDialog] = useState(false);
  const [showHandoffDialog, setShowHandoffDialog] = useState(false);

  useEffect(() => {
    fetchConversionStatus();
  }, [lead.id]);

  const fetchConversionStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/leads/${lead.id}/conversion/status`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) throw new Error('Failed to fetch conversion status');
      
      const data = await response.json();
      setProgress(data.conversion_progress);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'שגיאה בטעינת סטטוס המרה');
    } finally {
      setLoading(false);
    }
  };

  const handleStepComplete = async () => {
    await fetchConversionStatus();
    onUpdate();
  };

  if (loading && !progress) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-red-800">שגיאה בטעינת נתונים</p>
          <p className="text-sm text-red-600 mt-1">{error}</p>
        </div>
      </div>
    );
  }

  const steps = progress?.steps || {
    payment: lead.payment_completed || false,
    kinyan: lead.kinyan_signed || false,
    shipping: lead.shipping_details_complete || false,
    chat: lead.student_chat_added || false,
    handoff: (lead.handoff_to_manager && lead.handoff_completed) || false
  };

  const completed = Object.values(steps).filter(Boolean).length;
  const total = 5;
  const percentage = Math.round((completed / total) * 100);

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
      {/* Header */}
      <div className="border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              📋 רשימת משימות להמרת ליד לתלמיד
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              השלם את כל השלבים כדי להמיר את הליד לתלמיד באופן אוטומטי
            </p>
          </div>
          {lead.conversion_checklist_complete && (
            <div className="flex items-center gap-2 bg-green-100 text-green-800 px-4 py-2 rounded-full">
              <CheckCircle2 className="w-5 h-5" />
              <span className="font-medium">הומר לתלמיד!</span>
            </div>
          )}
        </div>
        
        {/* Progress Bar */}
        <div className="mt-4">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="font-medium text-gray-700">התקדמות: {completed}/{total}</span>
            <span className="font-bold text-blue-600">{percentage}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div 
              className="bg-gradient-to-r from-blue-500 to-indigo-600 h-full transition-all duration-500 ease-out"
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Checklist Steps */}
      <div className="p-6 space-y-4">
        {/* Step 1: Payment */}
        <div className={`flex items-start gap-4 p-4 rounded-lg border-2 transition-all ${
          steps.payment 
            ? 'bg-green-50 border-green-200' 
            : 'bg-white border-gray-200 hover:border-blue-300'
        }`}>
          <div className="flex-shrink-0 mt-1">
            {steps.payment ? (
              <CheckCircle2 className="w-6 h-6 text-green-600" />
            ) : (
              <Circle className="w-6 h-6 text-gray-400" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-gray-900">1. סליקה בוצעה ואושרה</h4>
              {!steps.payment && (
                <button
                  onClick={() => setShowPaymentDialog(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                >
                  רשום סליקה
                </button>
              )}
            </div>
            {steps.payment && lead.payment_completed_amount && (
              <div className="mt-2 text-sm text-gray-600">
                <p>💰 ₪{lead.payment_completed_amount.toLocaleString()} | {lead.payment_completed_method}</p>
                {lead.payment_completed_date && (
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(lead.payment_completed_date).toLocaleDateString('he-IL')}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Step 2: Kinyan */}
        <div className={`flex items-start gap-4 p-4 rounded-lg border-2 transition-all ${
          steps.kinyan 
            ? 'bg-green-50 border-green-200' 
            : 'bg-white border-gray-200 hover:border-blue-300'
        }`}>
          <div className="flex-shrink-0 mt-1">
            {steps.kinyan ? (
              <CheckCircle2 className="w-6 h-6 text-green-600" />
            ) : (
              <Circle className="w-6 h-6 text-gray-400" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-gray-900">2. קניון/תקנון נחתם</h4>
              {!steps.kinyan && (
                <button
                  onClick={() => setShowKinyanDialog(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                >
                  רשום קניון
                </button>
              )}
            </div>
            {steps.kinyan && lead.kinyan_method && (
              <div className="mt-2 text-sm text-gray-600">
                <p>📄 {lead.kinyan_method}</p>
                {lead.kinyan_signed_date && (
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(lead.kinyan_signed_date).toLocaleDateString('he-IL')}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Step 3: Shipping */}
        <div className={`flex items-start gap-4 p-4 rounded-lg border-2 transition-all ${
          steps.shipping 
            ? 'bg-green-50 border-green-200' 
            : 'bg-white border-gray-200 hover:border-blue-300'
        }`}>
          <div className="flex-shrink-0 mt-1">
            {steps.shipping ? (
              <CheckCircle2 className="w-6 h-6 text-green-600" />
            ) : (
              <Circle className="w-6 h-6 text-gray-400" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-gray-900">3. פרטי משלוח מלאים</h4>
              {!steps.shipping && (
                <button
                  onClick={() => setShowShippingDialog(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                >
                  מלא פרטים
                </button>
              )}
            </div>
            {steps.shipping && lead.shipping_city && (
              <div className="mt-2 text-sm text-gray-600">
                <p>📦 {lead.shipping_city}</p>
                {lead.shipping_full_address && (
                  <p className="text-xs text-gray-500 mt-1 truncate">
                    {lead.shipping_full_address}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Step 4: Student Chat */}
        <div className={`flex items-start gap-4 p-4 rounded-lg border-2 transition-all ${
          steps.chat 
            ? 'bg-green-50 border-green-200' 
            : 'bg-white border-gray-200 hover:border-blue-300'
        }`}>
          <div className="flex-shrink-0 mt-1">
            {steps.chat ? (
              <CheckCircle2 className="w-6 h-6 text-green-600" />
            ) : (
              <Circle className="w-6 h-6 text-gray-400" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-gray-900">4. הוכנס לצ'אט תלמידים</h4>
              {!steps.chat && (
                <button
                  onClick={() => setShowChatDialog(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                >
                  הוסף לצ'אט
                </button>
              )}
            </div>
            {steps.chat && lead.student_chat_platform && (
              <div className="mt-2 text-sm text-gray-600">
                <p>💬 {lead.student_chat_platform}</p>
              </div>
            )}
          </div>
        </div>

        {/* Step 5: Handoff */}
        <div className={`flex items-start gap-4 p-4 rounded-lg border-2 transition-all ${
          steps.handoff 
            ? 'bg-green-50 border-green-200' 
            : 'bg-white border-gray-200 hover:border-blue-300'
        }`}>
          <div className="flex-shrink-0 mt-1">
            {steps.handoff ? (
              <CheckCircle2 className="w-6 h-6 text-green-600" />
            ) : (
              <Circle className="w-6 h-6 text-gray-400" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-gray-900">5. הועבר למנהל כיתות</h4>
              {!steps.handoff && (
                <button
                  onClick={() => setShowHandoffDialog(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                  disabled={!steps.payment || !steps.kinyan || !steps.shipping || !steps.chat}
                >
                  העבר למנהל
                </button>
              )}
            </div>
            {lead.handoff_to_manager && (
              <div className="mt-2 text-sm text-gray-600">
                <p>
                  {lead.handoff_completed ? (
                    <span className="text-green-600 font-medium">✓ המנהל אישר השלמה</span>
                  ) : (
                    <span className="text-orange-600 font-medium">⏳ ממתין לאישור מנהל</span>
                  )}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Dialogs */}
      {showPaymentDialog && (
        <PaymentDialog
          leadId={lead.id}
          onClose={() => setShowPaymentDialog(false)}
          onSuccess={handleStepComplete}
        />
      )}
      
      {showKinyanDialog && (
        <KinyanDialog
          leadId={lead.id}
          onClose={() => setShowKinyanDialog(false)}
          onSuccess={handleStepComplete}
        />
      )}
      
      {showShippingDialog && (
        <ShippingDialog
          leadId={lead.id}
          leadName={lead.full_name}
          existingAddress={lead.shipping_full_address}
          existingCity={lead.shipping_city}
          onClose={() => setShowShippingDialog(false)}
          onSuccess={handleStepComplete}
        />
      )}
      
      {showChatDialog && (
        <StudentChatDialog
          leadId={lead.id}
          leadName={lead.full_name}
          onClose={() => setShowChatDialog(false)}
          onSuccess={handleStepComplete}
        />
      )}
      
      {showHandoffDialog && (
        <HandoffDialog
          leadId={lead.id}
          leadName={lead.full_name}
          onClose={() => setShowHandoffDialog(false)}
          onSuccess={handleStepComplete}
        />
      )}
    </div>
  );
};

export default LeadConversionChecklist;
