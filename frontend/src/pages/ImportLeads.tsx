import { useState, useRef, useCallback } from 'react'
import { Upload, FileSpreadsheet, X, CheckCircle2, AlertCircle, Info, Settings2 } from 'lucide-react'
import { api } from '@/lib/api'
import styles from './ImportLeads.module.css'
import s from '@/styles/shared.module.css'

interface ImportStats {
  created: number
  merged: number
  overwritten: number
  updated: number
  skipped_dup: number
  skipped_no_phone: number
  skipped_not_found: number
  errors: number
}

interface ImportResult {
  message: string
  total_rows: number
  stats: ImportStats
  errors: Array<{ row: number; error: string }>
}

interface PreviewResponse {
  headers: string[]
  sample_rows: Array<Record<string, string | null>>
  supported_fields: string[]
  required_fields: string[]
}

type DuplicateMode = 'skip' | 'merge' | 'overwrite' | 'update_field'

type WizardStep = 'upload' | 'mapping' | 'importing' | 'done'

const DUPLICATE_OPTIONS: { value: DuplicateMode; label: string; desc: string }[] = [
  { value: 'skip', label: 'דילוג', desc: 'דילוג על לידים עם טלפון שכבר קיים במערכת' },
  { value: 'merge', label: 'מיזוג', desc: 'עדכון שדות ריקים בלבד - לא דורס נתונים קיימים' },
  { value: 'overwrite', label: 'דריסה', desc: 'דריסה מלאה של כל השדות בליד הקיים' },
  { value: 'update_field', label: 'עדכון שדה ספציפי', desc: 'עדכון שדה אחד בלבד בלידים קיימים (לפי טלפון)' },
]

const FIELD_OPTIONS = [
  { value: 'status', label: 'סטטוס' },
  { value: 'lead_response', label: 'סטטוס מענה' },
  { value: 'salesperson_id', label: 'איש מכירות' },
  { value: 'course_id', label: 'קורס' },
  { value: 'full_name', label: 'שם מלא' },
  { value: 'email', label: 'אימייל' },
  { value: 'city', label: 'עיר' },
  { value: 'address', label: 'כתובת' },
  { value: 'notes', label: 'הערות' },
  { value: 'created_at', label: 'תאריך יצירה' },
  { value: 'arrival_date', label: 'תאריך הגעה' },
  { value: 'last_contact_date', label: 'תאריך שיחה אחרונה' },
]

const LEAD_FIELD_LABELS: Record<string, string> = {
  full_name: 'שם מלא',
  family_name: 'משפחה',
  phone: 'טלפון ראשי',
  phone2: 'טלפון נוסף',
  email: 'אימייל',
  city: 'עיר',
  address: 'כתובת',
  id_number: 'תעודת זהות',
  notes: 'הערות',
  source_type: 'מקור הגעה כללי',
  source_message: 'הודעה מהליד',
  campaign_name: 'שם מפרסם/קמפיין',
  requested_course: 'מוצר/קורס מתעניין',
  status: 'סטטוס ליד',
  lead_response: 'סטטוס מענה',
  salesperson_name: 'איש מכירות (שם)',
  course_name: 'קורס (שם)',
  created_at: 'תאריך יצירה',
  arrival_date: 'תאריך הגעה',
  last_contact_date: 'תאריך פניה אחרונה',
}

const SUPPORTED_COLUMNS = [
  { name: 'שם מלא', required: true },
  { name: 'טלפון ראשי', required: true },
  { name: 'מייל לקוח', required: false },
  { name: 'עיר מגורים', required: false },
  { name: 'כתובת', required: false },
  { name: 'הערות ליד', required: false },
  { name: 'איש מכירות', required: false },
  { name: 'מוצר שמתעניין', required: false },
  { name: 'סטאטוס ליד', required: false },
  { name: 'סטטוס מענה', required: false },
  { name: 'הודעה מהליד', required: false },
  { name: 'שם המפרסם', required: false },
  { name: 'תאריך יצירה', required: false },
  { name: 'תאריך פניה אחרונה', required: false },
]

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

export function ImportLeadsPage() {
  const [file, setFile] = useState<File | null>(null)
  const [duplicateMode, setDuplicateMode] = useState<DuplicateMode>('skip')
  const [updateFieldName, setUpdateFieldName] = useState<string>('status')
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState<WizardStep>('upload')
  const [result, setResult] = useState<ImportResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [preview, setPreview] = useState<PreviewResponse | null>(null)
  const [mapping, setMapping] = useState<Record<string, string>>({})

  const handleFileSelect = useCallback((selectedFile: File) => {
    const validTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
    ]
    if (!validTypes.includes(selectedFile.type) && !selectedFile.name.endsWith('.xlsx') && !selectedFile.name.endsWith('.xls')) {
      setError('יש להעלות קובץ אקסל בלבד (.xlsx)')
      return
    }
    setFile(selectedFile)
    setResult(null)
    setError(null)
    setPreview(null)
    setMapping({})
    setStep('mapping')
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    if (e.dataTransfer.files?.[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }, [handleFileSelect])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(true)
  }, [])

  const handleDragLeave = useCallback(() => {
    setDragActive(false)
  }, [])

  const loadPreview = useCallback(async (selectedFile: File) => {
    setLoading(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      const res = await api.upload<PreviewResponse>('/admin/import-leads/preview-file', formData)
      setPreview(res)
      const initial: Record<string, string> = {}
      // naive auto-mapping by exact header matches
      res.required_fields.forEach((f) => {
        const label = LEAD_FIELD_LABELS[f] || f
        const exact = res.headers.find((h) => h === label) || res.headers.find((h) => h === (f === 'phone' ? 'טלפון ראשי' : ''))
        if (exact) initial[f] = exact
      })
      if (Object.keys(initial).length) setMapping((m) => ({ ...m, ...initial }))
    } catch (err: unknown) {
      const message = (err as any)?.message || 'שגיאה בקריאת הקובץ'
      setError(message)
      setStep('upload')
    } finally {
      setLoading(false)
    }
  }, [])

  const handleImport = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)
    setStep('importing')

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('mapping_json', JSON.stringify(mapping))

      let url = `/admin/import-leads?duplicate_mode=${duplicateMode}`
      if (duplicateMode === 'update_field') {
        url += `&update_field_name=${updateFieldName}`
      }

      const res = await api.upload<ImportResult>(url, formData)
      setResult(res)
      setStep('done')
    } catch (err: unknown) {
      const message = (err as any)?.message || 'שגיאה בייבוא הלידים'
      setError(message)
      setStep('mapping')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setFile(null)
    setResult(null)
    setError(null)
    setPreview(null)
    setMapping({})
    setStep('upload')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const totalProcessed = result ? Object.values(result.stats).reduce((a, b) => a + b, 0) : 0

  const canImport = (() => {
    if (!preview) return false
    for (const req of preview.required_fields) {
      if (!mapping[req]) return false
      if (!preview.headers.includes(mapping[req])) return false
    }
    return true
  })()

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>ייבוא לידים</h1>
        <p className={styles.subtitle}>
          העלאת לידים מקובץ אקסל למערכת
        </p>
      </div>

      {/* Upload area */}
      {step === 'upload' && !file && !result && (
        <div
          className={`${styles.uploadArea} ${dragActive ? styles.uploadAreaActive : ''}`}
          onClick={() => fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          <div className={styles.uploadIcon}>
            <Upload size={48} strokeWidth={1.2} />
          </div>
          <div className={styles.uploadText}>
            גרור קובץ אקסל לכאן או לחץ לבחירה
          </div>
          <div className={styles.uploadHint}>
            קבצי .xlsx בלבד
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls"
            style={{ display: 'none' }}
            onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
          />
        </div>
      )}

      {/* File info */}
      {file && !result && (
        <div className={styles.fileInfo}>
          <div className={styles.fileIcon}>
            <FileSpreadsheet size={24} />
          </div>
          <div className={styles.fileName}>{file.name}</div>
          <div className={styles.fileSize}>{formatFileSize(file.size)}</div>
          <button className={styles.removeFile} onClick={handleReset}>
            <X size={16} />
          </button>
        </div>
      )}

      {/* Preview + mapping */}
      {file && step === 'mapping' && !result && (
        <div className={styles.optionsSection}>
          <h3 className={styles.optionsTitle}>
            <Info size={18} />
            מיפוי עמודות מהקובץ לשדות בליד
          </h3>

          {!preview && !loading && (
            <button
              className={`${s.btn} ${s['btn-primary']}`}
              onClick={() => loadPreview(file)}
            >
              טען תצוגה מקדימה
            </button>
          )}

          {preview && (
            <>
              <div style={{ marginBottom: '1rem', fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                בחר לאיזו עמודה בקובץ מתאים כל שדה. חובה: {preview.required_fields.map((f) => LEAD_FIELD_LABELS[f] || f).join(', ')}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                {[
                  ...preview.required_fields,
                  'email',
                  'city',
                  'address',
                  'notes',
                  'status',
                  'lead_response',
                  'salesperson_name',
                  'requested_course',
                  'campaign_name',
                  'created_at',
                  'last_contact_date',
                ]
                  .filter((f, idx, arr) => preview.supported_fields.includes(f) && arr.indexOf(f) === idx)
                  .map((field) => (
                    <div key={field}>
                      <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: '0.85rem' }}>
                        {LEAD_FIELD_LABELS[field] || field}
                        {preview.required_fields.includes(field) ? ' (חובה)' : ''}
                      </label>
                      <select
                        value={mapping[field] || ''}
                        onChange={(e) => {
                          const v = e.target.value
                          setMapping((m) => {
                            const next = { ...m }
                            if (!v) {
                              delete next[field]
                            } else {
                              next[field] = v
                            }
                            return next
                          })
                        }}
                        className={s.input}
                      >
                        <option value="">(לא למפות)</option>
                        {preview.headers.map((h) => (
                          <option key={h} value={h}>
                            {h}
                          </option>
                        ))}
                      </select>
                    </div>
                  ))}
              </div>

              <div style={{ marginTop: '1rem' }}>
                <div style={{ fontWeight: 600, marginBottom: 6, fontSize: '0.85rem' }}>תצוגה מקדימה (עד 5 שורות)</div>
                <div style={{ overflowX: 'auto', border: '1px solid var(--color-border-light)', borderRadius: 8 }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                    <thead>
                      <tr>
                        {preview.headers.slice(0, 8).map((h) => (
                          <th
                            key={h}
                            style={{
                              textAlign: 'right',
                              padding: '8px 10px',
                              borderBottom: '1px solid var(--color-border-light)',
                              background: '#f8fafc',
                            }}
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {preview.sample_rows.map((r, i) => (
                        <tr key={i}>
                          {preview.headers.slice(0, 8).map((h) => (
                            <td key={h} style={{ padding: '8px 10px', borderBottom: '1px solid var(--color-border-light)' }}>
                              {r[h] || ''}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Duplicate handling options */}
      {file && !result && !loading && step === 'mapping' && (
        <div className={styles.optionsSection}>
          <h3 className={styles.optionsTitle}>
            <Settings2 size={18} />
            טיפול בכפילויות (טלפון קיים)
          </h3>
          <div className={styles.duplicateOptions}>
            {DUPLICATE_OPTIONS.map((opt) => (
              <label
                key={opt.value}
                className={`${styles.duplicateOption} ${duplicateMode === opt.value ? styles.duplicateOptionSelected : ''}`}
              >
                <input
                  type="radio"
                  name="duplicateMode"
                  value={opt.value}
                  checked={duplicateMode === opt.value}
                  onChange={() => setDuplicateMode(opt.value)}
                />
                <div>
                  <div className={styles.optionLabel}>{opt.label}</div>
                  <div className={styles.optionDesc}>{opt.desc}</div>
                </div>
              </label>
            ))}
          </div>
          
          {/* Field selection for update_field mode */}
          {duplicateMode === 'update_field' && (
            <div style={{ marginTop: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, fontSize: '0.9rem' }}>
                בחר שדה לעדכון:
              </label>
              <select
                value={updateFieldName}
                onChange={(e) => setUpdateFieldName(e.target.value)}
                className={s.input}
                style={{ width: '100%', maxWidth: '300px' }}
              >
                {FIELD_OPTIONS.map((field) => (
                  <option key={field.value} value={field.value}>
                    {field.label}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className={styles.progressSection}>
          <div className={styles.spinner} />
          <div className={styles.progressText}>{step === 'importing' ? 'מייבא לידים...' : 'טוען נתונים...'}</div>
          <div className={styles.progressHint}>
            התהליך עשוי לקחת מספר שניות, אנא המתן
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className={styles.resultsSection}>
          <div className={styles.resultsHeader}>
            <AlertCircle size={24} className={styles.resultsIconError} />
            <div className={styles.resultsTitle}>שגיאה בייבוא</div>
          </div>
          <div style={{ padding: '1.5rem', color: '#dc2626', fontSize: '0.9rem' }}>
            {error}
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className={styles.resultsSection}>
          <div className={styles.resultsHeader}>
            <CheckCircle2 size={24} className={styles.resultsIcon} />
            <div className={styles.resultsTitle}>
              {result.message} ({totalProcessed} שורות עובדו)
            </div>
          </div>
          <div className={styles.statsGrid}>
            <div className={styles.statItem}>
              <span className={`${styles.statNumber} ${styles.statNumberGreen}`}>
                {result.stats.created}
              </span>
              <span className={styles.statLabel}>נוצרו חדשים</span>
            </div>
            {result.stats.merged > 0 && (
              <div className={styles.statItem}>
                <span className={`${styles.statNumber} ${styles.statNumberBlue}`}>
                  {result.stats.merged}
                </span>
                <span className={styles.statLabel}>מוזגו</span>
              </div>
            )}
            {result.stats.overwritten > 0 && (
              <div className={styles.statItem}>
                <span className={`${styles.statNumber} ${styles.statNumberOrange}`}>
                  {result.stats.overwritten}
                </span>
                <span className={styles.statLabel}>נדרסו</span>
              </div>
            )}
            {result.stats.updated > 0 && (
              <div className={styles.statItem}>
                <span className={`${styles.statNumber} ${styles.statNumberBlue}`}>
                  {result.stats.updated}
                </span>
                <span className={styles.statLabel}>עודכנו</span>
              </div>
            )}
            <div className={styles.statItem}>
              <span className={`${styles.statNumber} ${styles.statNumberGray}`}>
                {result.stats.skipped_dup}
              </span>
              <span className={styles.statLabel}>דולגו (כפילות)</span>
            </div>
            <div className={styles.statItem}>
              <span className={`${styles.statNumber} ${styles.statNumberGray}`}>
                {result.stats.skipped_no_phone}
              </span>
              <span className={styles.statLabel}>דולגו (אין טלפון)</span>
            </div>
            {result.stats.skipped_not_found > 0 && (
              <div className={styles.statItem}>
                <span className={`${styles.statNumber} ${styles.statNumberGray}`}>
                  {result.stats.skipped_not_found}
                </span>
                <span className={styles.statLabel}>דולגו (לא נמצא)</span>
              </div>
            )}
            {result.stats.errors > 0 && (
              <div className={styles.statItem}>
                <span className={`${styles.statNumber} ${styles.statNumberRed}`}>
                  {result.stats.errors}
                </span>
                <span className={styles.statLabel}>שגיאות</span>
              </div>
            )}
          </div>
          {result.errors.length > 0 && (
            <div className={styles.errorsList}>
              <div className={styles.errorsTitle}>פירוט שגיאות:</div>
              {result.errors.map((err, i) => (
                <div key={i} className={styles.errorItem}>
                  שורה {err.row}: {err.error}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      {file && !loading && (
        <div className={styles.actions}>
          <button
            className={`${s.btn} ${s['btn-secondary']}`}
            onClick={handleReset}
          >
            {result ? 'ייבוא נוסף' : 'ביטול'}
          </button>
          {!result && (
            <button
              className={`${s.btn} ${s['btn-primary']}`}
              onClick={handleImport}
              disabled={loading || step !== 'mapping' || !preview || !canImport}
            >
              <Upload size={16} />
              התחל ייבוא
            </button>
          )}
        </div>
      )}

      {/* Supported columns info */}
      <div className={styles.columnsInfo}>
        <h3 className={styles.columnsTitle}>
          <Info size={18} />
          עמודות נתמכות בקובץ האקסל
        </h3>
        <div className={styles.columnsList}>
          {SUPPORTED_COLUMNS.map((col) => (
            <div key={col.name} className={styles.columnItem}>
              <span>{col.name}</span>
              {col.required ? (
                <span className={styles.columnRequired}>חובה</span>
              ) : (
                <span className={styles.columnOptional}>אופציונלי</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
