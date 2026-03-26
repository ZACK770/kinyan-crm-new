import { useState, useRef, useCallback, useEffect } from 'react'
import { Upload, FileSpreadsheet, X, CheckCircle2, AlertCircle, Info, Settings2 } from 'lucide-react'
import { api } from '@/lib/api'
import styles from './ImportLeads.module.css'
import s from '@/styles/shared.module.css'

interface ImportStats {
  created: number
  updated: number
  skipped_dup: number
  errors: number
}

interface ImportResult {
  message: string
  entity: string
  total_rows: number
  stats: ImportStats
  errors: Array<{ row: number; error: string }>
}

interface Entity {
  entity: string
  label: string
}

interface EntityField {
  name: string
  type: string
  nullable: boolean
  primary_key: boolean
  unique: boolean
  foreign_key: boolean
  writable: boolean
}

interface EntityDescription {
  entity: string
  fields: EntityField[]
  required_fields_suggested: string[]
  duplicate_keys_suggested: string[]
}

interface PreviewResponse {
  entity: string
  headers: string[]
  sample_rows: string[][]
  fields: EntityField[]
  required_fields_suggested: string[]
  duplicate_keys_suggested: string[]
}

type DuplicateMode = 'skip' | 'merge' | 'overwrite'
type WizardStep = 'entity' | 'upload' | 'mapping' | 'importing' | 'done'

const DUPLICATE_OPTIONS: { value: DuplicateMode; label: string; desc: string }[] = [
  { value: 'skip', label: 'דילוג', desc: 'דילוג על רשומות כפולות' },
  { value: 'merge', label: 'מיזוג', desc: 'עדכון שדות ריקים בלבד - לא דורס נתונים קיימים' },
  { value: 'overwrite', label: 'דריסה', desc: 'דריסה מלאה של כל השדות ברשומה הקיימת' },
]


function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

export function ImportLeadsPage() {
  const [file, setFile] = useState<File | null>(null)
  const [duplicateMode, setDuplicateMode] = useState<DuplicateMode>('skip')
  const [duplicateKeyField, setDuplicateKeyField] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState<WizardStep>('entity')
  const [result, setResult] = useState<ImportResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [entities, setEntities] = useState<Entity[]>([])
  const [selectedEntity, setSelectedEntity] = useState<string>('')
  const [entityDescription, setEntityDescription] = useState<EntityDescription | null>(null)
  const [preview, setPreview] = useState<PreviewResponse | null>(null)
  // UI mapping is: Excel header -> entity field name (or '')
  const [mapping, setMapping] = useState<Record<string, string>>({})

  // Load entities on mount
  useEffect(() => {
    const loadEntities = async () => {
      try {
        const res = await api.get<Entity[]>('/admin/import/entities')
        setEntities(res)
      } catch (err: unknown) {
        setError('שגיאה בטעינת ישויות')
      }
    }
    loadEntities()
  }, [])

  // Load entity description when entity is selected
  const loadEntityDescription = useCallback(async (entity: string) => {
    try {
      const res = await api.get<EntityDescription>(`/admin/import/entities/${entity}`)
      setEntityDescription(res)
      if (res.duplicate_keys_suggested.length > 0) {
        setDuplicateKeyField(res.duplicate_keys_suggested[0])
      }
    } catch (err: unknown) {
      setError('שגיאה בטעינת תיאור ישות')
    }
  }, [])

  const handleEntitySelect = useCallback((entity: string) => {
    setSelectedEntity(entity)
    setEntityDescription(null)
    setDuplicateKeyField('')
    loadEntityDescription(entity)
  }, [loadEntityDescription])
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
      formData.append('entity', selectedEntity)
      const res = await api.upload<PreviewResponse>('/admin/import/preview-file', formData)
      setPreview(res)
      const initial: Record<string, string> = {}
      // Auto-map columns whose header matches a target field name
      res.headers.forEach((h) => {
        const exact = res.fields.find((f) => f.writable && f.name === h) || res.fields.find((f) => f.writable && f.name.toLowerCase() === h.toLowerCase())
        if (exact) initial[h] = exact.name
      })
      if (Object.keys(initial).length) setMapping((m) => ({ ...m, ...initial }))
    } catch (err: unknown) {
      const message = (err as any)?.message || 'שגיאה בקריאת הקובץ'
      setError(message)
      setStep('upload')
    } finally {
      setLoading(false)
    }
  }, [selectedEntity])

  const handleImport = async () => {
    if (!file || !selectedEntity) return
    setLoading(true)
    setError(null)
    setResult(null)
    setStep('importing')

    try {
      if (!preview) {
        throw new Error('יש לטעון תצוגה מקדימה לפני ייבוא')
      }

      // Convert UI mapping (header -> field) into backend mapping (field -> header)
      const backendMapping: Record<string, string> = {}
      for (const [header, fieldName] of Object.entries(mapping)) {
        if (!fieldName) continue
        backendMapping[fieldName] = header
      }

      // Validate required fields are mapped
      const requiredMissing = (preview.required_fields_suggested || []).filter((f) => !backendMapping[f])
      if (requiredMissing.length) {
        throw new Error(`חובה למפות את השדות: ${requiredMissing.join(', ')}`)
      }

      const formData = new FormData()
      formData.append('file', file)
      formData.append('entity', selectedEntity)
      formData.append('mapping_json', JSON.stringify(backendMapping))

      let url = `/admin/import/import?duplicate_mode=${duplicateMode}`
      if (duplicateKeyField) {
        url += `&duplicate_key_field=${duplicateKeyField}`
      }

      const res = await api.upload<ImportResult>(url, formData)
      setResult(res)
      setStep('done')
    } catch (err: unknown) {
      const message = (err as any)?.message || 'שגיאה בייבוא הנתונים'
      setError(message)
      setStep('mapping')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setFile(null)
    setSelectedEntity('')
    setEntityDescription(null)
    setResult(null)
    setError(null)
    setPreview(null)
    setMapping({})
    setDuplicateKeyField('')
    setStep('entity')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const totalProcessed = result ? Object.values(result.stats).reduce((a, b) => a + b, 0) : 0

  const writableFields = preview ? preview.fields.filter((f) => f.writable) : []
  const mappedTargetFields = new Set(Object.values(mapping).filter(Boolean))
  const requiredMissingUi = preview
    ? (preview.required_fields_suggested || []).filter((f) => !mappedTargetFields.has(f))
    : []
  const hasDuplicateTargetField = (() => {
    const counts = new Map<string, number>()
    Object.values(mapping)
      .filter(Boolean)
      .forEach((v) => counts.set(v, (counts.get(v) || 0) + 1))
    for (const n of counts.values()) {
      if (n > 1) return true
    }
    return false
  })()
  const canImport = Boolean(preview) && requiredMissingUi.length === 0 && !hasDuplicateTargetField

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>ייבוא נתונים גנרי</h1>
        <p className={styles.subtitle}>
          העלאת נתונים מקובץ אקסל למערכת
        </p>
      </div>

      {/* Entity selection */}
      {step === 'entity' && !file && !result && (
        <div className={styles.optionsSection}>
          <h3 className={styles.optionsTitle}>
            <Settings2 size={18} />
            בחר ישות לייבוא
          </h3>
          
          {loading ? (
            <div>טוען ישויות...</div>
          ) : entities.length === 0 ? (
            <div>לא נמצאו ישויות זמינות לייבוא</div>
          ) : (
            <div style={{ display: 'grid', gap: '0.5rem' }}>
              {entities.map((entity) => (
                <button
                  key={entity.entity}
                  className={`${s.btn} ${selectedEntity === entity.entity ? s['btn-primary'] : s['btn-secondary']}`}
                  onClick={() => {
                    handleEntitySelect(entity.entity)
                    setStep('upload')
                  }}
                  style={{ justifyContent: 'flex-start', textAlign: 'right' }}
                >
                  {entity.label}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

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
            מיפוי עמודות מהקובץ לשדות ב{selectedEntity}
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
                בחר עבור כל עמודה בקובץ לאיזה שדה ב{selectedEntity} למפות. חובה: {preview.required_fields_suggested.join(', ')}
              </div>

              {(requiredMissingUi.length > 0 || hasDuplicateTargetField) && (
                <div style={{ marginBottom: '0.75rem', fontSize: '0.85rem', color: 'var(--color-danger)' }}>
                  {requiredMissingUi.length > 0 ? `חסרים שדות חובה במיפוי: ${requiredMissingUi.join(', ')}` : ''}
                  {requiredMissingUi.length > 0 && hasDuplicateTargetField ? ' | ' : ''}
                  {hasDuplicateTargetField ? 'לא ניתן למפות שני עמודות לאותו שדה יעד' : ''}
                </div>
              )}

              <div style={{ marginTop: '1rem' }}>
                <div style={{ fontWeight: 600, marginBottom: 6, fontSize: '0.85rem' }}>תצוגה מקדימה (עד 5 שורות)</div>
                <div style={{ overflowX: 'auto', border: '1px solid var(--color-border-light)', borderRadius: 8 }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                    <thead>
                      <tr>
                        {preview.headers.map((h) => (
                          <th
                            key={h}
                            style={{
                              textAlign: 'right',
                              padding: '8px 10px',
                              borderBottom: '1px solid var(--color-border-light)',
                              background: '#f8fafc',
                              verticalAlign: 'top',
                            }}
                          >
                            <div style={{ display: 'grid', gap: 6 }}>
                              <div style={{ fontWeight: 700 }}>{h}</div>
                              <select
                                value={mapping[h] || ''}
                                onChange={(e) => {
                                  const v = e.target.value
                                  setMapping((m) => {
                                    const next = { ...m }
                                    if (!v) {
                                      delete next[h]
                                    } else {
                                      next[h] = v
                                    }
                                    return next
                                  })
                                }}
                                className={s.input}
                              >
                                <option value="">(לא למפות)</option>
                                {writableFields.map((f) => (
                                  <option key={f.name} value={f.name}>
                                    {f.name}
                                  </option>
                                ))}
                              </select>
                            </div>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {preview.sample_rows.map((row, i) => (
                        <tr key={i}>
                          {preview.headers.map((_, j) => (
                            <td key={j} style={{ padding: '8px 10px', borderBottom: '1px solid var(--color-border-light)' }}>
                              {row?.[j] || ''}
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
            טיפול בכפילויות
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
          
          {/* Duplicate key field selection */}
          {entityDescription?.duplicate_keys_suggested && entityDescription.duplicate_keys_suggested.length > 0 && (
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500, fontSize: '0.9rem' }}>
                שדה לזיהוי כפילויות:
              </label>
              <select
                value={duplicateKeyField}
                onChange={(e) => setDuplicateKeyField(e.target.value)}
                className={s.input}
                style={{ width: '100%', maxWidth: '300px' }}
              >
                {entityDescription.duplicate_keys_suggested.map((field) => (
                  <option key={field} value={field}>
                    {field}
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
          <div className={styles.progressText}>{step === 'importing' ? 'מייבא נתונים...' : 'טוען נתונים...'}</div>
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
            <div className={styles.statItem}>
              <span className={`${styles.statNumber} ${styles.statNumberBlue}`}>
                {result.stats.updated}
              </span>
              <span className={styles.statLabel}>עודכנו</span>
            </div>
            <div className={styles.statItem}>
              <span className={`${styles.statNumber} ${styles.statNumberGray}`}>
                {result.stats.skipped_dup}
              </span>
              <span className={styles.statLabel}>דולגו (כפילות)</span>
            </div>
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

      {/* Entity info */}
      {selectedEntity && preview && (
        <div className={styles.columnsInfo}>
          <h3 className={styles.columnsTitle}>
            <Info size={18} />
            שדות נתמכים ב{selectedEntity}
          </h3>
          <div className={styles.columnsList}>
            {preview.fields
              .filter(field => field.writable)
              .map((field) => (
                <div key={field.name} className={styles.columnItem}>
                  <span>{field.name}</span>
                  {preview.required_fields_suggested.includes(field.name) ? (
                    <span className={styles.columnRequired}>חובה</span>
                  ) : (
                    <span className={styles.columnOptional}>אופציונלי</span>
                  )}
                  <span className={styles.columnType}>{field.type}</span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}
