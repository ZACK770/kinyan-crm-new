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

type DuplicateMode = 'skip' | 'merge' | 'overwrite' | 'update_field'

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
]

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
  const [result, setResult] = useState<ImportResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

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

  const handleImport = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      let url = `/admin/import-leads?duplicate_mode=${duplicateMode}`
      if (duplicateMode === 'update_field') {
        url += `&update_field_name=${updateFieldName}`
      }

      const res = await api.upload<ImportResult>(url, formData)
      setResult(res)
    } catch (err: unknown) {
      const message = (err as any)?.message || 'שגיאה בייבוא הלידים'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setFile(null)
    setResult(null)
    setError(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const totalProcessed = result ? Object.values(result.stats).reduce((a, b) => a + b, 0) : 0

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>ייבוא לידים</h1>
        <p className={styles.subtitle}>
          העלאת לידים מקובץ אקסל למערכת
        </p>
      </div>

      {/* Upload area */}
      {!file && !result && (
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

      {/* Duplicate handling options */}
      {file && !result && !loading && (
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
          <div className={styles.progressText}>מייבא לידים...</div>
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
              disabled={loading}
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
