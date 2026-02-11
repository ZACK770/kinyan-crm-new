import { useState, useEffect } from 'react'
import { Plus, Edit2, Trash2, Save, X, Upload, FileText } from 'lucide-react'
import { api } from '../lib/api'
import s from '../components/layout/AppLayout.module.css'

interface EmailTemplate {
  id: number
  name: string
  subject: string
  body_html: string
  category: string | null
  track_type: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  attachments: Array<{
    id: number
    filename: string
    size_bytes: number
    content_type: string
  }>
}

interface FileAttachment {
  id: number
  filename: string
  size_bytes: number
  content_type: string
}

export default function EmailTemplates() {
  const [templates, setTemplates] = useState<EmailTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [uploading, setUploading] = useState(false)

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    subject: '',
    body_html: '',
    category: '',
    track_type: '',
    is_active: true,
  })

  const [uploadedFiles, setUploadedFiles] = useState<FileAttachment[]>([])

  useEffect(() => {
    fetchTemplates()
  }, [])

  const fetchTemplates = async () => {
    try {
      const data = await api.get<EmailTemplate[]>('/templates/')
      setTemplates(data)
    } catch (err) {
      console.error('Failed to fetch templates:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingId(null)
    setFormData({
      name: '',
      subject: '',
      body_html: '',
      category: '',
      track_type: '',
      is_active: true,
    })
    setUploadedFiles([])
    setShowForm(true)
  }

  const handleEdit = (template: EmailTemplate) => {
    setEditingId(template.id)
    setFormData({
      name: template.name,
      subject: template.subject,
      body_html: template.body_html,
      category: template.category || '',
      track_type: template.track_type || '',
      is_active: template.is_active,
    })
    setUploadedFiles(template.attachments)
    setShowForm(true)
  }

  const handleSave = async () => {
    try {
      if (editingId) {
        await api.patch(`/templates/${editingId}`, formData)
      } else {
        await api.post<EmailTemplate>('/templates/', formData)
      }
      await fetchTemplates()
      setShowForm(false)
    } catch (err: any) {
      alert(err?.message || 'שמירה נכשלה')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('האם למחוק תבנית זו?')) return
    try {
      await api.delete(`/templates/${id}`)
      await fetchTemplates()
    } catch (err: any) {
      alert(err?.message || 'מחיקה נכשלה')
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setUploading(true)
    try {
      for (const file of Array.from(files)) {
        const formData = new FormData()
        formData.append('file', file)

        const result = await api.upload<FileAttachment>(
          `/files/upload?entity_type=${editingId ? 'templates' : 'temp'}&entity_id=${editingId || 0}`,
          formData
        )

        setUploadedFiles(prev => [...prev, result])
      }
    } catch (err: any) {
      alert(err?.message || 'העלאת קובץ נכשלה')
    } finally {
      setUploading(false)
    }
  }

  const handleRemoveFile = async (fileId: number) => {
    try {
      if (editingId) {
        await api.delete(`/templates/${editingId}/attachments/${fileId}`)
      } else {
        await api.delete(`/files/${fileId}`)
      }
      setUploadedFiles(prev => prev.filter(f => f.id !== fileId))
    } catch (err: any) {
      alert(err?.message || 'מחיקת קובץ נכשלה')
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <div>טוען תבניות...</div>
      </div>
    )
  }

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, fontWeight: 600, margin: 0 }}>תבניות מייל</h1>
        <button className={`${s.btn} ${s['btn-primary']}`} onClick={handleCreate}>
          <Plus size={18} /> תבנית חדשה
        </button>
      </div>

      {showForm && (
        <div style={{
          background: 'var(--color-bg-secondary, #f8fafc)',
          border: '1px solid var(--color-border)',
          borderRadius: 8,
          padding: 24,
          marginBottom: 24,
        }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>
            {editingId ? 'עריכת תבנית' : 'תבנית חדשה'}
          </h2>

          <div style={{ display: 'grid', gap: 16 }}>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 4 }}>שם התבנית</label>
              <input
                type="text"
                value={formData.name}
                onChange={e => setFormData({ ...formData, name: e.target.value })}
                placeholder="למשל: ערכת התרשמות - מסלול א"
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: 6,
                  border: '1px solid var(--color-border)',
                  fontSize: 14,
                }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 4 }}>קטגוריה</label>
                <select
                  value={formData.category}
                  onChange={e => setFormData({ ...formData, category: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: 6,
                    border: '1px solid var(--color-border)',
                    fontSize: 14,
                  }}
                >
                  <option value="">בחר קטגוריה</option>
                  <option value="התרשמות">התרשמות</option>
                  <option value="מעקב">מעקב</option>
                  <option value="כללי">כללי</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 4 }}>מסלול התעניינות</label>
                <input
                  type="text"
                  value={formData.track_type}
                  onChange={e => setFormData({ ...formData, track_type: e.target.value })}
                  placeholder="למשל: מסלול א, מסלול ב"
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: 6,
                    border: '1px solid var(--color-border)',
                    fontSize: 14,
                  }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 4 }}>נושא המייל</label>
              <input
                type="text"
                value={formData.subject}
                onChange={e => setFormData({ ...formData, subject: e.target.value })}
                placeholder="נושא המייל..."
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: 6,
                  border: '1px solid var(--color-border)',
                  fontSize: 14,
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 4 }}>תוכן המייל (HTML)</label>
              <textarea
                value={formData.body_html}
                onChange={e => setFormData({ ...formData, body_html: e.target.value })}
                placeholder="תוכן המייל... (ניתן להשתמש ב-HTML)"
                rows={10}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: 6,
                  border: '1px solid var(--color-border)',
                  fontSize: 14,
                  fontFamily: 'monospace',
                  resize: 'vertical',
                }}
              />
              <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 4 }}>
                טיפ: השתמש ב-{'{{lead_name}}'} לשם הליד, {'{{track_name}}'} למסלול
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, marginBottom: 8 }}>קבצים מצורפים</label>
              <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                <label className={`${s.btn} ${s['btn-secondary']}`} style={{ cursor: 'pointer' }}>
                  <Upload size={16} />
                  {uploading ? 'מעלה...' : 'העלה קובץ'}
                  <input
                    type="file"
                    multiple
                    onChange={handleFileUpload}
                    disabled={uploading}
                    style={{ display: 'none' }}
                  />
                </label>
              </div>

              {uploadedFiles.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {uploadedFiles.map(file => (
                    <div
                      key={file.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        padding: '8px 12px',
                        background: 'white',
                        border: '1px solid var(--color-border)',
                        borderRadius: 6,
                      }}
                    >
                      <FileText size={16} style={{ color: 'var(--color-primary)' }} />
                      <span style={{ flex: 1, fontSize: 13 }}>{file.filename}</span>
                      <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                        {formatFileSize(file.size_bytes)}
                      </span>
                      <button
                        className={`${s.btn} ${s['btn-ghost']} ${s['btn-sm']}`}
                        onClick={() => handleRemoveFile(file.id)}
                        style={{ padding: 4 }}
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={e => setFormData({ ...formData, is_active: e.target.checked })}
              />
              <label htmlFor="is_active" style={{ fontSize: 13, cursor: 'pointer' }}>תבנית פעילה</label>
            </div>

            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button className={`${s.btn} ${s['btn-ghost']}`} onClick={() => setShowForm(false)}>
                <X size={16} /> ביטול
              </button>
              <button className={`${s.btn} ${s['btn-primary']}`} onClick={handleSave}>
                <Save size={16} /> שמור
              </button>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gap: 16 }}>
        {templates.length === 0 ? (
          <div className={s['empty-state']}>
            <FileText size={48} style={{ opacity: 0.3, marginBottom: 16 }} />
            <div style={{ fontSize: 16, fontWeight: 500, marginBottom: 8 }}>אין תבניות מייל</div>
            <div style={{ fontSize: 14, color: 'var(--color-text-muted)', marginBottom: 16 }}>
              צור תבנית ראשונה כדי להתחיל לשלוח מיילים מותאמים אישית
            </div>
            <button className={`${s.btn} ${s['btn-primary']}`} onClick={handleCreate}>
              <Plus size={16} /> צור תבנית
            </button>
          </div>
        ) : (
          templates.map(template => (
            <div
              key={template.id}
              style={{
                background: 'white',
                border: '1px solid var(--color-border)',
                borderRadius: 8,
                padding: 16,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 12 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <h3 style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>{template.name}</h3>
                    {!template.is_active && (
                      <span style={{
                        fontSize: 11,
                        padding: '2px 6px',
                        borderRadius: 4,
                        background: 'var(--color-border)',
                        color: 'var(--color-text-muted)',
                      }}>
                        לא פעיל
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>
                    {template.category && <span>📁 {template.category}</span>}
                    {template.track_type && <span style={{ marginRight: 12 }}>🎯 {template.track_type}</span>}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 4 }}>
                  <button
                    className={`${s.btn} ${s['btn-ghost']} ${s['btn-sm']}`}
                    onClick={() => handleEdit(template)}
                  >
                    <Edit2 size={14} />
                  </button>
                  <button
                    className={`${s.btn} ${s['btn-ghost']} ${s['btn-sm']}`}
                    onClick={() => handleDelete(template.id)}
                    style={{ color: 'var(--color-danger)' }}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>נושא: {template.subject}</div>
              <div style={{
                fontSize: 13,
                color: 'var(--color-text-secondary)',
                maxHeight: 60,
                overflow: 'hidden',
                marginBottom: 8,
              }}>
                {template.body_html.replace(/<[^>]*>/g, '').substring(0, 150)}...
              </div>

              {template.attachments.length > 0 && (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {template.attachments.map(att => (
                    <div
                      key={att.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                        padding: '4px 8px',
                        background: 'var(--color-bg-secondary)',
                        borderRadius: 4,
                        fontSize: 12,
                      }}
                    >
                      <FileText size={12} />
                      <span>{att.filename}</span>
                      <span style={{ color: 'var(--color-text-muted)' }}>
                        ({formatFileSize(att.size_bytes)})
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
