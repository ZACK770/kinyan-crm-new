import { useState, useEffect, useCallback, useRef, type FC } from 'react'
import {
  Plus,
  Pencil,
  Trash2,
  Copy,
  Eye,
  Zap,
  Clock,
  Users,
  // Image as ImageIcon,
  X,
  Upload,
  Megaphone,
  Flame,
  PartyPopper,
  AlertTriangle,
  Trophy,
  ArrowUp,
  Sparkles,
  ZoomIn,
  LayoutTemplate,
} from 'lucide-react'
import { api } from '@/lib/api'
import { useModal } from '@/components/ui/Modal'
import { useToast } from '@/components/ui/Toast'
import { PageHeader } from '@/components/ui/PageHeader'
import styles from './PopupManage.module.css'
import s from '@/styles/shared.module.css'
import clsx from 'clsx'

/* ============================================================
   Types
   ============================================================ */

interface Popup {
  id: number
  title: string
  body?: string | null
  image_url?: string | null
  cta_text?: string | null
  cta_link?: string | null
  theme: string
  animation: string
  target_audience: string
  min_permission_level: number
  is_active: boolean
  start_at?: string | null
  end_at?: string | null
  show_count: number
  is_template: boolean
  priority: number
  created_by_user_id?: number | null
  created_at?: string | null
  updated_at?: string | null
  dismiss_count?: number
}

type FormData = {
  title: string
  body: string
  image_url: string
  cta_text: string
  cta_link: string
  theme: string
  animation: string
  target_audience: string
  min_permission_level: number
  is_active: boolean
  start_at: string
  end_at: string
  show_count: number
  is_template: boolean
  priority: number
}

const EMPTY_FORM: FormData = {
  title: '',
  body: '',
  image_url: '',
  cta_text: '',
  cta_link: '',
  theme: 'default',
  animation: 'slideUp',
  target_audience: 'all',
  min_permission_level: 0,
  is_active: true,
  start_at: '',
  end_at: '',
  show_count: 1,
  is_template: false,
  priority: 0,
}

const THEMES = [
  { value: 'default', label: 'כללי', emoji: '📢', icon: Megaphone },
  { value: 'success', label: 'הצלחה', emoji: '🏆', icon: Trophy },
  { value: 'warning', label: 'אזהרה', emoji: '⚠️', icon: AlertTriangle },
  { value: 'fire', label: 'דחוף', emoji: '🔥', icon: Flame },
  { value: 'celebration', label: 'חגיגה', emoji: '🎉', icon: PartyPopper },
]

const ANIMATIONS = [
  { value: 'slideUp', label: 'החלקה למעלה', icon: ArrowUp },
  { value: 'fadeIn', label: 'דהייה', icon: Sparkles },
  { value: 'bounceIn', label: 'קפיצה', icon: Zap },
  { value: 'zoomIn', label: 'זום', icon: ZoomIn },
]

const AUDIENCES = [
  { value: 'all', label: 'כל המשתמשים' },
  { value: 'salesperson', label: 'אנשי מכירות' },
  { value: 'manager', label: 'מנהלים' },
  { value: 'admin', label: 'מנהלי מערכת' },
]

/* ============================================================
   Form Component (inside modal)
   ============================================================ */

const PopupForm: FC<{
  initial?: FormData
  onSubmit: (data: FormData) => Promise<void>
  onCancel: () => void
}> = ({ initial, onSubmit, onCancel }) => {
  const [form, setForm] = useState<FormData>(initial || EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const set = <K extends keyof FormData>(key: K, val: FormData[K]) =>
    setForm(prev => ({ ...prev, [key]: val }))

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 2 * 1024 * 1024) {
      alert('הקובץ גדול מדי. מקסימום 2MB')
      return
    }
    const reader = new FileReader()
    reader.onload = () => {
      set('image_url', reader.result as string)
    }
    reader.readAsDataURL(file)
  }

  const handleSubmit = async () => {
    if (!form.title.trim()) return
    setSaving(true)
    try {
      await onSubmit(form)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={styles.form}>
      {/* Title */}
      <div className={styles.formGroup}>
        <label className={styles.formLabel}>כותרת *</label>
        <input
          className={styles.formInput}
          value={form.title}
          onChange={e => set('title', e.target.value)}
          placeholder="למשל: מבצע יומי - 20% הנחה!"
        />
      </div>

      {/* Body */}
      <div className={styles.formGroup}>
        <label className={styles.formLabel}>תוכן ההודעה</label>
        <textarea
          className={styles.formTextarea}
          value={form.body}
          onChange={e => set('body', e.target.value)}
          placeholder="תיאור מפורט של ההודעה..."
          rows={3}
        />
      </div>

      {/* Image */}
      <div className={styles.formGroup}>
        <label className={styles.formLabel}>תמונה</label>
        <div className={styles.imageUpload}>
          {form.image_url ? (
            <div className={styles.imagePreview}>
              <img src={form.image_url} alt="preview" />
              <button
                className={styles.imageRemove}
                onClick={() => set('image_url', '')}
                type="button"
              >
                <X size={14} />
              </button>
            </div>
          ) : (
            <div
              className={styles.imageDropzone}
              onClick={() => fileRef.current?.click()}
            >
              <Upload size={20} />
              <span>לחץ להעלאת תמונה (עד 2MB)</span>
              <span style={{ fontSize: 11 }}>או הדבק קישור URL למטה</span>
            </div>
          )}
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={handleImageUpload}
          />
          {!form.image_url && (
            <input
              className={styles.formInput}
              value={form.image_url}
              onChange={e => set('image_url', e.target.value)}
              placeholder="או הדבק קישור לתמונה..."
            />
          )}
        </div>
      </div>

      {/* Theme */}
      <div className={styles.formGroup}>
        <label className={styles.formLabel}>ערכת עיצוב</label>
        <div className={styles.themeSelector}>
          {THEMES.map(t => (
            <button
              key={t.value}
              type="button"
              className={clsx(styles.themeOption, form.theme === t.value && styles.selected)}
              onClick={() => set('theme', t.value)}
            >
              <span>{t.emoji}</span>
              <span>{t.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Animation */}
      <div className={styles.formGroup}>
        <label className={styles.formLabel}>אנימציה</label>
        <div className={styles.animSelector}>
          {ANIMATIONS.map(a => {
            const Icon = a.icon
            return (
              <button
                key={a.value}
                type="button"
                className={clsx(styles.animOption, form.animation === a.value && styles.selected)}
                onClick={() => set('animation', a.value)}
              >
                <Icon size={14} />
                <span>{a.label}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* CTA */}
      <div className={styles.formRow}>
        <div className={styles.formGroup}>
          <label className={styles.formLabel}>טקסט כפתור (CTA)</label>
          <input
            className={styles.formInput}
            value={form.cta_text}
            onChange={e => set('cta_text', e.target.value)}
            placeholder="למשל: לפרטים נוספים"
          />
        </div>
        <div className={styles.formGroup}>
          <label className={styles.formLabel}>קישור כפתור</label>
          <input
            className={styles.formInput}
            value={form.cta_link}
            onChange={e => set('cta_link', e.target.value)}
            placeholder="https://..."
          />
        </div>
      </div>

      {/* Targeting */}
      <div className={styles.formRow}>
        <div className={styles.formGroup}>
          <label className={styles.formLabel}>קהל יעד</label>
          <select
            className={styles.formSelect}
            value={form.target_audience}
            onChange={e => set('target_audience', e.target.value)}
          >
            {AUDIENCES.map(a => (
              <option key={a.value} value={a.value}>{a.label}</option>
            ))}
          </select>
        </div>
        <div className={styles.formGroup}>
          <label className={styles.formLabel}>מספר הצגות למשתמש</label>
          <input
            className={styles.formInput}
            type="number"
            min={0}
            value={form.show_count}
            onChange={e => set('show_count', parseInt(e.target.value) || 0)}
          />
          <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>0 = ללא הגבלה</span>
        </div>
      </div>

      {/* Schedule */}
      <div className={styles.formRow}>
        <div className={styles.formGroup}>
          <label className={styles.formLabel}>תחילת הצגה</label>
          <input
            className={styles.formInput}
            type="datetime-local"
            value={form.start_at}
            onChange={e => set('start_at', e.target.value)}
          />
        </div>
        <div className={styles.formGroup}>
          <label className={styles.formLabel}>סיום הצגה</label>
          <input
            className={styles.formInput}
            type="datetime-local"
            value={form.end_at}
            onChange={e => set('end_at', e.target.value)}
          />
        </div>
      </div>

      {/* Priority */}
      <div className={styles.formRow}>
        <div className={styles.formGroup}>
          <label className={styles.formLabel}>עדיפות (גבוה = מוצג קודם)</label>
          <input
            className={styles.formInput}
            type="number"
            value={form.priority}
            onChange={e => set('priority', parseInt(e.target.value) || 0)}
          />
        </div>
        <div className={styles.formGroup} style={{ justifyContent: 'flex-end' }}>
          <label className={styles.formCheckbox}>
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={e => set('is_active', e.target.checked)}
            />
            <span>פעיל</span>
          </label>
          <label className={styles.formCheckbox}>
            <input
              type="checkbox"
              checked={form.is_template}
              onChange={e => set('is_template', e.target.checked)}
            />
            <span>שמור כתבנית</span>
          </label>
        </div>
      </div>

      {/* Footer */}
      <div className={styles.formFooter}>
        <button
          className={`${s.btn} ${s['btn-primary']}`}
          onClick={handleSubmit}
          disabled={saving || !form.title.trim()}
        >
          {saving ? 'שומר...' : initial ? 'עדכן' : 'צור הודעה'}
        </button>
        <button className={`${s.btn} ${s['btn-secondary']}`} onClick={onCancel}>
          ביטול
        </button>
      </div>
    </div>
  )
}

/* ============================================================
   Main Page
   ============================================================ */

export function PopupManagePage() {
  const { openModal, closeModal, confirm } = useModal()
  const toast = useToast()

  const [popups, setPopups] = useState<Popup[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'active' | 'all' | 'templates'>('all')

  const fetchPopups = useCallback(async () => {
    setLoading(true)
    try {
      if (tab === 'templates') {
        const data = await api.get<Popup[]>('/popups/templates')
        setPopups(data)
      } else {
        const data = await api.get<Popup[]>('/popups/?include_templates=false')
        if (tab === 'active') {
          setPopups(data.filter(p => p.is_active))
        } else {
          setPopups(data)
        }
      }
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה בטעינת הודעות')
    } finally {
      setLoading(false)
    }
  }, [tab, toast])

  useEffect(() => { fetchPopups() }, [fetchPopups])

  const getStatus = (p: Popup) => {
    if (!p.is_active) return { label: 'לא פעיל', cls: styles.statusInactive }
    const now = new Date()
    if (p.start_at && new Date(p.start_at) > now) return { label: 'מתוזמן', cls: styles.statusScheduled }
    if (p.end_at && new Date(p.end_at) < now) return { label: 'פג תוקף', cls: styles.statusExpired }
    return { label: 'פעיל', cls: styles.statusActive }
  }

  const openCreate = (template?: Popup) => {
    const initial: FormData = template
      ? {
          title: template.title,
          body: template.body || '',
          image_url: template.image_url || '',
          cta_text: template.cta_text || '',
          cta_link: template.cta_link || '',
          theme: template.theme,
          animation: template.animation,
          target_audience: template.target_audience,
          min_permission_level: template.min_permission_level,
          is_active: true,
          start_at: '',
          end_at: '',
          show_count: template.show_count,
          is_template: false,
          priority: template.priority,
        }
      : EMPTY_FORM

    openModal({
      title: 'הודעת פופ-אפ חדשה',
      size: 'lg',
      content: (
        <PopupForm
          initial={initial}
          onSubmit={async (data) => {
            await api.post('/popups/', data)
            toast.success('ההודעה נוצרה בהצלחה')
            closeModal()
            fetchPopups()
          }}
          onCancel={closeModal}
        />
      ),
    })
  }

  const openEdit = (popup: Popup) => {
    const initial: FormData = {
      title: popup.title,
      body: popup.body || '',
      image_url: popup.image_url || '',
      cta_text: popup.cta_text || '',
      cta_link: popup.cta_link || '',
      theme: popup.theme,
      animation: popup.animation,
      target_audience: popup.target_audience,
      min_permission_level: popup.min_permission_level,
      is_active: popup.is_active,
      start_at: popup.start_at ? popup.start_at.slice(0, 16) : '',
      end_at: popup.end_at ? popup.end_at.slice(0, 16) : '',
      show_count: popup.show_count,
      is_template: popup.is_template,
      priority: popup.priority,
    }

    openModal({
      title: `עריכת הודעה — ${popup.title}`,
      size: 'lg',
      content: (
        <PopupForm
          initial={initial}
          onSubmit={async (data) => {
            await api.patch(`/popups/${popup.id}`, data)
            toast.success('ההודעה עודכנה')
            closeModal()
            fetchPopups()
          }}
          onCancel={closeModal}
        />
      ),
    })
  }

  const handleDelete = async (popup: Popup) => {
    const ok = await confirm({
      title: 'מחיקת הודעה',
      message: `למחוק את ההודעה "${popup.title}"?`,
      danger: true,
      confirmLabel: 'מחק',
    })
    if (!ok) return
    try {
      await api.delete(`/popups/${popup.id}`)
      toast.success('ההודעה נמחקה')
      fetchPopups()
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה')
    }
  }

  const handleDuplicate = async (popup: Popup) => {
    try {
      await api.post(`/popups/${popup.id}/duplicate`)
      toast.success('ההודעה שוכפלה')
      fetchPopups()
    } catch (err: unknown) {
      toast.error((err as { message?: string }).message ?? 'שגיאה')
    }
  }

  const handlePreview = (popup: Popup) => {
    openModal({
      title: 'תצוגה מקדימה',
      size: 'sm',
      content: (
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <p style={{ fontSize: 13, color: 'var(--color-text-muted)', marginBottom: 16 }}>
            הפופ-אפ ייפתח כשתסגור את החלון הזה
          </p>
          <button
            className={`${s.btn} ${s['btn-primary']}`}
            onClick={async () => {
              closeModal()
              // Small delay to let modal close, then show the popup preview
              setTimeout(() => {
                // Trigger a temporary preview by dispatching a custom event
                window.dispatchEvent(new CustomEvent('popup-preview', { detail: popup }))
              }, 300)
            }}
          >
            הצג תצוגה מקדימה
          </button>
        </div>
      ),
    })
  }

  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return '—'
    try {
      return new Date(dateStr).toLocaleDateString('he-IL', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return dateStr
    }
  }

  const audienceLabel = (val: string) =>
    AUDIENCES.find(a => a.value === val)?.label || val

  return (
    <div className={styles.page}>
      <PageHeader title="הודעות פופ-אפ">
        <div className={styles.headerRight}>
          <button className={`${s.btn} ${s['btn-primary']}`} onClick={() => openCreate()}>
            <Plus size={16} />
            הודעה חדשה
          </button>
        </div>
      </PageHeader>

      {/* Tabs */}
      <div className={styles.tabs}>
        <button
          className={clsx(styles.tab, tab === 'all' && styles.active)}
          onClick={() => setTab('all')}
        >
          <Zap size={15} />
          הכל
        </button>
        <button
          className={clsx(styles.tab, tab === 'active' && styles.active)}
          onClick={() => setTab('active')}
        >
          <Eye size={15} />
          פעילות
        </button>
        <button
          className={clsx(styles.tab, tab === 'templates' && styles.active)}
          onClick={() => setTab('templates')}
        >
          <LayoutTemplate size={15} />
          תבניות
        </button>
      </div>

      {/* Content */}
      {loading ? (
        <div className={styles.loading}>טוען...</div>
      ) : popups.length === 0 ? (
        <div className={styles.empty}>
          <div className={styles.emptyIcon}>
            <Zap size={24} />
          </div>
          <div className={styles.emptyTitle}>
            {tab === 'templates' ? 'אין תבניות שמורות' : 'אין הודעות'}
          </div>
          <div className={styles.emptyText}>
            {tab === 'templates'
              ? 'צור הודעה וסמן "שמור כתבנית" כדי לשמור אותה לשימוש חוזר'
              : 'צור הודעת פופ-אפ חדשה כדי להודיע לצוות על מבצעים, אתגרים ועדכונים'}
          </div>
          <button className={`${s.btn} ${s['btn-primary']}`} onClick={() => openCreate()}>
            <Plus size={16} />
            צור הודעה ראשונה
          </button>
        </div>
      ) : (
        <div className={styles.grid}>
          {popups.map(popup => {
            const status = getStatus(popup)
            const themeData = THEMES.find(t => t.value === popup.theme)

            return (
              <div key={popup.id} className={styles.card}>
                <div className={clsx(styles.cardAccent, styles[popup.theme])} />
                <div className={styles.cardBody}>
                  <div className={styles.cardHeader}>
                    <div className={styles.cardTitle}>
                      {themeData?.emoji} {popup.title}
                    </div>
                    <span className={clsx(styles.cardStatus, status.cls)}>
                      {status.label}
                    </span>
                  </div>

                  {popup.image_url && (
                    <img src={popup.image_url} alt="" className={styles.cardImage} />
                  )}

                  {popup.body && (
                    <div className={styles.cardPreview}>{popup.body}</div>
                  )}

                  <div className={styles.cardMeta}>
                    <span className={styles.metaTag}>
                      <Users size={11} />
                      {audienceLabel(popup.target_audience)}
                    </span>
                    <span className={styles.metaTag}>
                      <Eye size={11} />
                      {popup.show_count === 0 ? 'ללא הגבלה' : `${popup.show_count}x`}
                    </span>
                    {popup.start_at && (
                      <span className={styles.metaTag}>
                        <Clock size={11} />
                        {formatDate(popup.start_at)}
                      </span>
                    )}
                    {popup.cta_text && (
                      <span className={styles.metaTag}>
                        כפתור: {popup.cta_text}
                      </span>
                    )}
                  </div>

                  <div className={styles.cardActions}>
                    <button className={styles.cardBtn} onClick={() => openEdit(popup)} title="עריכה">
                      <Pencil size={13} />
                      עריכה
                    </button>
                    <button className={styles.cardBtn} onClick={() => handleDuplicate(popup)} title="שכפול">
                      <Copy size={13} />
                    </button>
                    <button
                      className={styles.cardBtnPreview}
                      onClick={() => handlePreview(popup)}
                      title="תצוגה מקדימה"
                    >
                      <Eye size={13} />
                    </button>
                    <button
                      className={clsx(styles.cardBtn, styles.cardBtnDanger)}
                      onClick={() => handleDelete(popup)}
                      title="מחיקה"
                    >
                      <Trash2 size={13} />
                    </button>
                    {typeof popup.dismiss_count === 'number' && popup.dismiss_count > 0 && (
                      <span className={styles.dismissCount}>
                        {popup.dismiss_count} צפיות
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
