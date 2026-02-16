import React, { useState, useEffect } from 'react';
import { CheckCircle2, Loader2, AlertCircle, CreditCard, FileText, Package, MessageCircle, UserCheck, Sparkles, TrendingUp, Award } from 'lucide-react';
import PaymentDialog from './PaymentDialog';
import KinyanDialog from './KinyanDialog';
import ShippingDialog from './ShippingDialog';
import StudentChatDialog from './StudentChatDialog';
import HandoffDialog from './HandoffDialog';

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
    <div className="bg-gradient-to-br from-white via-blue-50/30 to-purple-50/30 border-2 border-blue-200/50 rounded-2xl shadow-2xl overflow-hidden">
      {/* Header */}
      <div className="relative border-b-2 border-blue-200/50 bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-600 px-8 py-6 overflow-hidden">
        {/* Animated background pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-64 h-64 bg-white rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-white rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        </div>
        
        <div className="relative z-10 flex items-center justify-between">
          <div className="flex items-start gap-4">
            <div className="bg-white/20 backdrop-blur-sm p-3 rounded-2xl border border-white/30 shadow-lg">
              <Sparkles className="w-8 h-8 text-white" strokeWidth={2} />
            </div>
            <div>
              <h3 className="text-2xl font-bold text-white flex items-center gap-3 mb-2">
                מסע ההמרה לתלמיד
                <TrendingUp className="w-6 h-6 animate-bounce" />
              </h3>
              <p className="text-blue-100 text-sm font-medium">
                השלם את כל השלבים והליד יומר לתלמיד באופן אוטומטי ✨
              </p>
            </div>
          </div>
          {lead.conversion_checklist_complete && (
            <div className="flex items-center gap-3 bg-gradient-to-r from-green-400 to-emerald-500 text-white px-6 py-3 rounded-2xl shadow-2xl border-2 border-white/30 animate-pulse">
              <Award className="w-6 h-6" strokeWidth={2.5} />
              <span className="font-bold text-lg">הומר לתלמיד!</span>
            </div>
          )}
        </div>
        
        {/* Enhanced Progress Bar */}
        <div className="relative z-10 mt-6">
          <div className="flex items-center justify-between text-sm mb-3">
            <div className="flex items-center gap-2">
              <span className="font-bold text-white text-lg">התקדמות:</span>
              <span className="bg-white/20 backdrop-blur-sm px-3 py-1 rounded-full font-bold text-white border border-white/30">
                {completed}/{total}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-3xl font-black text-white drop-shadow-lg">{percentage}%</span>
            </div>
          </div>
          <div className="relative w-full bg-white/20 backdrop-blur-sm rounded-full h-5 overflow-hidden border-2 border-white/30 shadow-inner">
            <div 
              className="bg-gradient-to-r from-yellow-300 via-orange-400 to-pink-500 h-full transition-all duration-700 ease-out relative overflow-hidden"
              style={{ width: `${percentage}%` }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent animate-shimmer" />
            </div>
            {percentage === 100 && (
              <div className="absolute inset-0 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white animate-spin" />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Checklist Steps */}
      <div className="p-8 space-y-5">
        {/* Step 1: Payment */}
        <div className={`group relative flex items-start gap-5 p-6 rounded-2xl border-2 transition-all duration-300 transform hover:scale-[1.02] ${
          steps.payment 
            ? 'bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 border-green-300 shadow-lg shadow-green-200/50' 
            : 'bg-white border-blue-200 hover:border-blue-400 hover:shadow-xl hover:shadow-blue-100/50'
        }`}>
          <div className="flex-shrink-0 mt-1">
            <div className={`relative p-3 rounded-2xl transition-all duration-300 ${
              steps.payment 
                ? 'bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg shadow-green-300/50' 
                : 'bg-gradient-to-br from-blue-100 to-indigo-100 group-hover:from-blue-200 group-hover:to-indigo-200'
            }`}>
              {steps.payment ? (
                <CheckCircle2 className="w-7 h-7 text-white" strokeWidth={2.5} />
              ) : (
                <CreditCard className="w-7 h-7 text-blue-600" strokeWidth={2} />
              )}
              {steps.payment && (
                <div className="absolute -top-1 -right-1 bg-yellow-400 rounded-full p-1 animate-bounce">
                  <Sparkles className="w-3 h-3 text-white" />
                </div>
              )}
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl font-black text-gray-300">1</span>
                <h4 className="text-xl font-bold text-gray-900">סליקה בוצעה ואושרה</h4>
              </div>
              {!steps.payment && (
                <button
                  onClick={() => setShowPaymentDialog(true)}
                  className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-300 text-sm font-bold shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  רשום סליקה
                </button>
              )}
            </div>
            {steps.payment && lead.payment_completed_amount && (
              <div className="mt-3 p-4 bg-white/60 backdrop-blur-sm rounded-xl border border-green-200">
                <p className="text-base font-bold text-green-700 flex items-center gap-2">
                  <CreditCard className="w-5 h-5" />
                  ₪{lead.payment_completed_amount.toLocaleString()} | {lead.payment_completed_method}
                </p>
                {lead.payment_completed_date && (
                  <p className="text-sm text-green-600 mt-2 font-medium">
                    📅 {new Date(lead.payment_completed_date).toLocaleDateString('he-IL')}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Step 2: Kinyan */}
        <div className={`group relative flex items-start gap-5 p-6 rounded-2xl border-2 transition-all duration-300 transform hover:scale-[1.02] ${
          steps.kinyan 
            ? 'bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 border-green-300 shadow-lg shadow-green-200/50' 
            : 'bg-white border-purple-200 hover:border-purple-400 hover:shadow-xl hover:shadow-purple-100/50'
        }`}>
          <div className="flex-shrink-0 mt-1">
            <div className={`relative p-3 rounded-2xl transition-all duration-300 ${
              steps.kinyan 
                ? 'bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg shadow-green-300/50' 
                : 'bg-gradient-to-br from-purple-100 to-pink-100 group-hover:from-purple-200 group-hover:to-pink-200'
            }`}>
              {steps.kinyan ? (
                <CheckCircle2 className="w-7 h-7 text-white" strokeWidth={2.5} />
              ) : (
                <FileText className="w-7 h-7 text-purple-600" strokeWidth={2} />
              )}
              {steps.kinyan && (
                <div className="absolute -top-1 -right-1 bg-yellow-400 rounded-full p-1 animate-bounce">
                  <Sparkles className="w-3 h-3 text-white" />
                </div>
              )}
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl font-black text-gray-300">2</span>
                <h4 className="text-xl font-bold text-gray-900">קניון/תקנון נחתם</h4>
              </div>
              {!steps.kinyan && (
                <button
                  onClick={() => setShowKinyanDialog(true)}
                  className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all duration-300 text-sm font-bold shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  רשום קניון
                </button>
              )}
            </div>
            {steps.kinyan && lead.kinyan_method && (
              <div className="mt-3 p-4 bg-white/60 backdrop-blur-sm rounded-xl border border-green-200">
                <p className="text-base font-bold text-green-700 flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  {lead.kinyan_method}
                </p>
                {lead.kinyan_signed_date && (
                  <p className="text-sm text-green-600 mt-2 font-medium">
                    📅 {new Date(lead.kinyan_signed_date).toLocaleDateString('he-IL')}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Step 3: Shipping */}
        <div className={`group relative flex items-start gap-5 p-6 rounded-2xl border-2 transition-all duration-300 transform hover:scale-[1.02] ${
          steps.shipping 
            ? 'bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 border-green-300 shadow-lg shadow-green-200/50' 
            : 'bg-white border-orange-200 hover:border-orange-400 hover:shadow-xl hover:shadow-orange-100/50'
        }`}>
          <div className="flex-shrink-0 mt-1">
            <div className={`relative p-3 rounded-2xl transition-all duration-300 ${
              steps.shipping 
                ? 'bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg shadow-green-300/50' 
                : 'bg-gradient-to-br from-orange-100 to-amber-100 group-hover:from-orange-200 group-hover:to-amber-200'
            }`}>
              {steps.shipping ? (
                <CheckCircle2 className="w-7 h-7 text-white" strokeWidth={2.5} />
              ) : (
                <Package className="w-7 h-7 text-orange-600" strokeWidth={2} />
              )}
              {steps.shipping && (
                <div className="absolute -top-1 -right-1 bg-yellow-400 rounded-full p-1 animate-bounce">
                  <Sparkles className="w-3 h-3 text-white" />
                </div>
              )}
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl font-black text-gray-300">3</span>
                <h4 className="text-xl font-bold text-gray-900">פרטי משלוח מלאים</h4>
              </div>
              {!steps.shipping && (
                <button
                  onClick={() => setShowShippingDialog(true)}
                  className="px-6 py-3 bg-gradient-to-r from-orange-600 to-amber-600 text-white rounded-xl hover:from-orange-700 hover:to-amber-700 transition-all duration-300 text-sm font-bold shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  מלא פרטים
                </button>
              )}
            </div>
            {steps.shipping && lead.shipping_city && (
              <div className="mt-3 p-4 bg-white/60 backdrop-blur-sm rounded-xl border border-green-200">
                <p className="text-base font-bold text-green-700 flex items-center gap-2">
                  <Package className="w-5 h-5" />
                  {lead.shipping_city}
                </p>
                {lead.shipping_full_address && (
                  <p className="text-sm text-green-600 mt-2 font-medium truncate">
                    📍 {lead.shipping_full_address}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Step 4: Student Chat */}
        <div className={`group relative flex items-start gap-5 p-6 rounded-2xl border-2 transition-all duration-300 transform hover:scale-[1.02] ${
          steps.chat 
            ? 'bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 border-green-300 shadow-lg shadow-green-200/50' 
            : 'bg-white border-cyan-200 hover:border-cyan-400 hover:shadow-xl hover:shadow-cyan-100/50'
        }`}>
          <div className="flex-shrink-0 mt-1">
            <div className={`relative p-3 rounded-2xl transition-all duration-300 ${
              steps.chat 
                ? 'bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg shadow-green-300/50' 
                : 'bg-gradient-to-br from-cyan-100 to-blue-100 group-hover:from-cyan-200 group-hover:to-blue-200'
            }`}>
              {steps.chat ? (
                <CheckCircle2 className="w-7 h-7 text-white" strokeWidth={2.5} />
              ) : (
                <MessageCircle className="w-7 h-7 text-cyan-600" strokeWidth={2} />
              )}
              {steps.chat && (
                <div className="absolute -top-1 -right-1 bg-yellow-400 rounded-full p-1 animate-bounce">
                  <Sparkles className="w-3 h-3 text-white" />
                </div>
              )}
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl font-black text-gray-300">4</span>
                <h4 className="text-xl font-bold text-gray-900">הוכנס לצ'אט תלמידים</h4>
              </div>
              {!steps.chat && (
                <button
                  onClick={() => setShowChatDialog(true)}
                  className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-xl hover:from-cyan-700 hover:to-blue-700 transition-all duration-300 text-sm font-bold shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  הוסף לצ'אט
                </button>
              )}
            </div>
            {steps.chat && lead.student_chat_platform && (
              <div className="mt-3 p-4 bg-white/60 backdrop-blur-sm rounded-xl border border-green-200">
                <p className="text-base font-bold text-green-700 flex items-center gap-2">
                  <MessageCircle className="w-5 h-5" />
                  {lead.student_chat_platform}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Step 5: Handoff */}
        <div className={`group relative flex items-start gap-5 p-6 rounded-2xl border-2 transition-all duration-300 transform hover:scale-[1.02] ${
          steps.handoff 
            ? 'bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 border-green-300 shadow-lg shadow-green-200/50' 
            : 'bg-white border-indigo-200 hover:border-indigo-400 hover:shadow-xl hover:shadow-indigo-100/50'
        }`}>
          <div className="flex-shrink-0 mt-1">
            <div className={`relative p-3 rounded-2xl transition-all duration-300 ${
              steps.handoff 
                ? 'bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg shadow-green-300/50' 
                : 'bg-gradient-to-br from-indigo-100 to-purple-100 group-hover:from-indigo-200 group-hover:to-purple-200'
            }`}>
              {steps.handoff ? (
                <CheckCircle2 className="w-7 h-7 text-white" strokeWidth={2.5} />
              ) : (
                <UserCheck className="w-7 h-7 text-indigo-600" strokeWidth={2} />
              )}
              {steps.handoff && (
                <div className="absolute -top-1 -right-1 bg-yellow-400 rounded-full p-1 animate-bounce">
                  <Sparkles className="w-3 h-3 text-white" />
                </div>
              )}
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl font-black text-gray-300">5</span>
                <h4 className="text-xl font-bold text-gray-900">הועבר למנהל כיתות</h4>
              </div>
              {!steps.handoff && (
                <button
                  onClick={() => setShowHandoffDialog(true)}
                  className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all duration-300 text-sm font-bold shadow-lg hover:shadow-xl transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                  disabled={!steps.payment || !steps.kinyan || !steps.shipping || !steps.chat}
                >
                  העבר למנהל
                </button>
              )}
            </div>
            {lead.handoff_to_manager && (
              <div className="mt-3 p-4 bg-white/60 backdrop-blur-sm rounded-xl border border-green-200">
                <p className="text-base font-bold">
                  {lead.handoff_completed ? (
                    <span className="text-green-700 flex items-center gap-2">
                      <CheckCircle2 className="w-5 h-5" />
                      המנהל אישר השלמה
                    </span>
                  ) : (
                    <span className="text-orange-600 flex items-center gap-2">
                      <Loader2 className="w-5 h-5 animate-spin" />
                      ממתין לאישור מנהל
                    </span>
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
