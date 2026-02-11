import { useState, useEffect, useCallback } from 'react'
import { UserCheck, Plus, Edit2, Trash2 } from 'lucide-react'
import { useModal } from '@/components/ui/Modal'
import { api } from '@/lib/api'
import s from '@/styles/shared.module.css'

/* ══════════════════════════════════════════════════════════════
   Lecturers Page — ניהול מרצים
   ══════════════════════════════════════════════════════════════ */

interface Lecturer {
  id: number
  name: string
  specialty?: string
  phone?: string
  email?: string
  notes?: string
  created_at?: string
}

function LecturerForm({
  initial,
  onSubmit,
  onCancel,
}: {
  initial?: Partial<Lecturer>
  onSubmit: (data: Record<string, unknown>) => void
  onCancel?: () => void
}) {
  const [form, setForm] = useState({
    name: initial?.name ?? '',
    specialty: initial?.specialty ?? '',
    phone: initial?.phone ?? '',
    email: initial?.email ?? '',
    notes: initial?.notes ?? '',
  })

  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [key]: e.target.value }))

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(form)
  }

  return (
    <form onSubmit={handleSubmit} className={s.form}>
      <div className={s['form-group']}>
        <label className={s['form-label']}>שם מרצה *</label>
        <input
          type="text"
          className={s.input}
          value={form.name}
          onChange={set('name')}
          required
          placeholder="שם מלא"
        />
      </div>

      <div className={s['form-group']}>
        <label className={s['form-label']}>התמחות</label>
        <input
          type="text"
          className={s.input}
          value={form.specialty}
          onChange={set('specialty')}
          placeholder="תחום התמחות"
        />
      </div>

      <div className={s['form-row']}>
        <div className={s['form-group']}>
          <label className={s['form-label']}>טלפון</label>
          <input
            type="tel"
            className={s.input}
            value={form.phone}
            onChange={set('phone')}
            placeholder="050-1234567"
          />
        </div>
        <div className={s['form-group']}>
          <label className={s['form-label']}>אימייל</label>
          <input
            type="email"
            className={s.input}
            value={form.email}
            onChange={set('email')}
            placeholder="email@example.com"
          />
        </div>
      </div>

      <div className={s['form-group']}>
        <label className={s['form-label']}>הערות</label>
        <textarea
          className={s.textarea}
          value={form.notes}
          onChange={set('notes')}
          rows={3}
          placeholder="הערות נוספות"
        />
      </div>

      <div className={s['form-actions']}>
        {onCancel && (
          <button type="button" className={s['btn-secondary']} onClick={onCancel}>
            ביטול
          </button>
        )}
        <button type="submit" className={s['btn-primary']}>
          {initial ? 'עדכן' : 'צור מרצה'}
        </button>
      </div>
    </form>
  )
}

export function LecturersPage() {
  const [lecturers, setLecturers] = useState<Lecturer[]>([])
  const [loading, setLoading] = useState(true)
  const { openModal, closeModal } = useModal()

  const fetchLecturers = useCallback(async () => {
    try {
      setLoading(true)
      const data = await api.get<Lecturer[]>('/lecturers')
      setLecturers(data)
    } catch (err) {
      console.error('Failed to fetch lecturers:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchLecturers()
  }, [fetchLecturers])

  const handleCreate = () => {
    openModal({
      title: 'מרצה חדש',
      content: (
        <LecturerForm
          onSubmit={async (data) => {
            try {
              await api.post('/lecturers', data)
              closeModal()
              fetchLecturers()
            } catch (err) {
              console.error(err)
              alert('שגיאה ביצירת מרצה')
            }
          }}
          onCancel={closeModal}
        />
      ),
    })
  }

  const handleEdit = (lecturer: Lecturer) => {
    openModal({
      title: 'עריכת מרצה',
      content: (
        <LecturerForm
          initial={lecturer}
          onSubmit={async (data) => {
            try {
              await api.patch(`/lecturers/${lecturer.id}`, data)
              closeModal()
              fetchLecturers()
            } catch (err) {
              console.error(err)
              alert('שגיאה בעדכון מרצה')
            }
          }}
          onCancel={closeModal}
        />
      ),
    })
  }

  const handleDelete = async (lecturer: Lecturer) => {
    if (!confirm(`האם למחוק את המרצה "${lecturer.name}"?`)) return
    try {
      await api.delete(`/lecturers/${lecturer.id}`)
      fetchLecturers()
    } catch (err: any) {
      console.error(err)
      alert(err.response?.data?.detail || 'שגיאה במחיקת מרצה')
    }
  }

  return (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>מרצים</h1>
        <button className={s['btn-primary']} onClick={handleCreate}>
          <Plus size={18} strokeWidth={2} />
          מרצה חדש
        </button>
      </div>

      <div className={s.card}>
        {loading ? (
          <div className={s.empty} style={{ padding: 60 }}>
            <span className={s['empty-text']}>טוען...</span>
          </div>
        ) : lecturers.length === 0 ? (
          <div className={s.empty} style={{ padding: 60 }}>
            <span className={s['empty-icon']}>
              <UserCheck size={48} strokeWidth={1.5} />
            </span>
            <span className={s['empty-text']} style={{ fontSize: 15, fontWeight: 500 }}>
              אין מרצים
            </span>
            <span className={s['empty-text']}>התחל בהוספת מרצה ראשון</span>
          </div>
        ) : (
          <div className={s['table-container']}>
            <table className={s.table}>
              <thead>
                <tr>
                  <th>שם</th>
                  <th>התמחות</th>
                  <th>טלפון</th>
                  <th>אימייל</th>
                  <th style={{ width: 100 }}>פעולות</th>
                </tr>
              </thead>
              <tbody>
                {lecturers.map((lecturer) => (
                  <tr key={lecturer.id}>
                    <td>{lecturer.name}</td>
                    <td>{lecturer.specialty || '—'}</td>
                    <td>{lecturer.phone || '—'}</td>
                    <td>{lecturer.email || '—'}</td>
                    <td>
                      <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
                        <button
                          className={s['icon-btn']}
                          onClick={() => handleEdit(lecturer)}
                          title="עריכה"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          className={s['icon-btn-danger']}
                          onClick={() => handleDelete(lecturer)}
                          title="מחיקה"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
