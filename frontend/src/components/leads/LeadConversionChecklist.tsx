import React, { useState, useEffect } from 'react';
import { CheckCircle2, Loader2, AlertCircle, UserCheck, Sparkles } from 'lucide-react';
import styles from './LeadConversionChecklist.module.css';
import { api } from '@/lib/api';

interface Lead {
  id: number;
  full_name: string;
  phone: string;
  status: string;
  approved_terms?: boolean;
  shipping_details_complete?: boolean;
  student_chat_added?: boolean;
  personal_course_update?: boolean;
  personal_course_update_date?: string;
  personal_course_update_notes?: string;
  conversion_checklist_complete?: boolean;
  conversion_completed_at?: string;
  student_id?: number;
}

interface Props {
  lead: Lead;
  onUpdate: () => void;
}

const LeadConversionChecklist: React.FC<Props> = ({ lead, onUpdate }) => {
  const [loading, setLoading] = useState(false);
  const [converting, setConverting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check if all steps are completed
  const allStepsCompleted = 
    lead.approved_terms && 
    lead.shipping_details_complete && 
    lead.student_chat_added && 
    lead.personal_course_update;

  const completedCount = [
    lead.approved_terms,
    lead.shipping_details_complete,
    lead.student_chat_added,
    lead.personal_course_update
  ].filter(Boolean).length;

  const percentage = Math.round((completedCount / 4) * 100);

  // Auto-convert when all steps are completed
  useEffect(() => {
    if (allStepsCompleted && !lead.student_id && !converting) {
      handleAutoConvert();
    }
  }, [allStepsCompleted, lead.student_id]);

  const handleAutoConvert = async () => {
    try {
      setConverting(true);
      const response = await api.post(`/leads/${lead.id}/convert`);
      if (response) {
        onUpdate();
      }
    } catch (err) {
      console.error('Auto-conversion failed:', err);
    } finally {
      setConverting(false);
    }
  };

  const handleCheckboxChange = async (field: string, value: boolean) => {
    try {
      setLoading(true);
      setError(null);
      await api.patch(`/leads/${lead.id}`, { [field]: value });
      onUpdate();
    } catch (err) {
      setError('שגיאה בעדכון');
    } finally {
      setLoading(false);
    }
  };

  if (converting) {
    return (
      <div className={styles.loading}>
        <Loader2 size={24} className="animate-spin" style={{ color: '#3b82f6' }} />
        <p>ממיר לתלמיד...</p>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.headerLeft}>
            <div className={styles.headerIcon}>
              <Sparkles size={20} strokeWidth={2} />
            </div>
            <div className={styles.headerText}>
              <h3>רשימת משימות להמרה לתלמיד</h3>
              <p>
                {allStepsCompleted 
                  ? 'כל המשימות הושלמו! הליד יומר לתלמיד אוטומטית'
                  : 'השלם את כל המשימות והליד יומר לתלמיד באופן אוטומטי'}
              </p>
            </div>
          </div>
          {lead.student_id && (
            <div className={styles.completeBadge}>
              <UserCheck size={16} strokeWidth={2} />
              <span>הומר לתלמיד!</span>
            </div>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className={styles.progressSection}>
        <div className={styles.progressHeader}>
          <div className={styles.progressLeft}>
            <span>התקדמות:</span>
            <span className={styles.progressCount}>
              {completedCount}/4
            </span>
          </div>
          <div>
            <span className={styles.progressPercentage}>{percentage}%</span>
          </div>
        </div>
        <div className={styles.progressBarContainer}>
          <div 
            className={styles.progressBar}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>

      {error && (
        <div className={styles.error}>
          <AlertCircle size={20} style={{ color: '#dc2626' }} />
          <span>{error}</span>
        </div>
      )}

      {/* Checklist Items */}
      <div className={styles.stepsContainer}>
        {/* Step 1: Approved Terms */}
        <div className={`${styles.checklistItem} ${lead.approved_terms ? styles.completed : ''}`}>
          <label className={styles.checklistLabel}>
            <input
              type="checkbox"
              checked={lead.approved_terms || false}
              onChange={(e) => handleCheckboxChange('approved_terms', e.target.checked)}
              disabled={loading || lead.student_id !== null}
              className={styles.checkbox}
            />
            <div className={styles.checklistContent}>
              <div className={styles.checklistTitle}>
                <span>אישר תקנון</span>
              </div>
              <p className={styles.checklistDescription}>
                הלקוח אישר את תקנון הקורס
              </p>
            </div>
          </label>
        </div>

        {/* Step 2: Received Shipment */}
        <div className={`${styles.checklistItem} ${lead.shipping_details_complete ? styles.completed : ''}`}>
          <label className={styles.checklistLabel}>
            <input
              type="checkbox"
              checked={lead.shipping_details_complete || false}
              onChange={(e) => handleCheckboxChange('shipping_details_complete', e.target.checked)}
              disabled={loading || lead.student_id !== null}
              className={styles.checkbox}
            />
            <div className={styles.checklistContent}>
              <div className={styles.checklistTitle}>
                <span>קיבל את המשלוח</span>
              </div>
              <p className={styles.checklistDescription}>
                החומרים נשלחו והתקבלו אצל הלקוח
              </p>
            </div>
          </label>
        </div>

        {/* Step 3: Added to Chat */}
        <div className={`${styles.checklistItem} ${lead.student_chat_added ? styles.completed : ''}`}>
          <label className={styles.checklistLabel}>
            <input
              type="checkbox"
              checked={lead.student_chat_added || false}
              onChange={(e) => handleCheckboxChange('student_chat_added', e.target.checked)}
              disabled={loading || lead.student_id !== null}
              className={styles.checkbox}
            />
            <div className={styles.checklistContent}>
              <div className={styles.checklistTitle}>
                <span>הוכנס לרשימת צינתוקים</span>
              </div>
              <p className={styles.checklistDescription}>
                הלקוח נוסף לקבוצת הוואטסאפ/טלגרם של התלמידים
              </p>
            </div>
          </label>
        </div>

        {/* Step 4: Personal Course Update */}
        <div className={`${styles.checklistItem} ${lead.personal_course_update ? styles.completed : ''}`}>
          <label className={styles.checklistLabel}>
            <input
              type="checkbox"
              checked={lead.personal_course_update || false}
              onChange={(e) => handleCheckboxChange('personal_course_update', e.target.checked)}
              disabled={loading || lead.student_id !== null}
              className={styles.checkbox}
            />
            <div className={styles.checklistContent}>
              <div className={styles.checklistTitle}>
                <span>עודכן אישית על מיקום ושעת הקורס הקרוב</span>
              </div>
              <p className={styles.checklistDescription}>
                הלקוח קיבל עדכון אישי על המיקום והשעה של השיעור הקרוב
              </p>
              {lead.personal_course_update_date && (
                <p className={styles.checklistMeta}>
                  עודכן בתאריך: {new Date(lead.personal_course_update_date).toLocaleDateString('he-IL')}
                </p>
              )}
            </div>
          </label>
        </div>
      </div>

      {/* Conversion Status */}
      {allStepsCompleted && !lead.student_id && (
        <div className={styles.conversionNotice}>
          <Sparkles size={20} />
          <span>כל המשימות הושלמו! הליד יומר לתלמיד אוטומטית...</span>
        </div>
      )}

      {lead.student_id && (
        <div className={styles.conversionSuccess}>
          <CheckCircle2 size={20} />
          <span>הליד הומר בהצלחה לתלמיד #{lead.student_id}</span>
        </div>
      )}
    </div>
  );
};

export default LeadConversionChecklist;
