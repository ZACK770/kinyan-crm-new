import { useState, useEffect } from 'react'
import { UserPlus, UserCheck, Edit, Trash2, Shield, Eye } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useModal } from '@/components/ui/Modal'
import { useToast } from '@/components/ui/Toast'
import { DataTable } from '@/components/ui/DataTable'
import { AdminRoute } from '@/components/ProtectedRoute'
import { api } from '@/lib/api'
import type { User } from '@/types/auth'
import styles from './UsersManage.module.css'
import s from '@/styles/shared.module.css'

interface UserFormData {
  email: string
  full_name: string
  password?: string
  role_name: string
  is_active: boolean
}

function UserForm({ 
  user, 
  onSubmit, 
  loading 
}: { 
  user?: User
  onSubmit: (data: UserFormData) => void
  loading: boolean
}) {
  const [formData, setFormData] = useState<UserFormData>({
    email: user?.email || '',
    full_name: user?.full_name || '',
    role_name: user?.role_name || 'pending',
    is_active: user?.is_active !== false
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <form onSubmit={handleSubmit} className={s['form-container']}>
      <div className={s['form-group']}>
        <label className={s['form-label']}>כתובת מייל *</label>
        <input
          type="email"
          className={s.input}
          value={formData.email}
          onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
          required
          disabled={loading || !!user}
          dir="ltr"
        />
        {user && <small className={s['form-hint']}>לא ניתן לשנות כתובת מייל</small>}
      </div>

      <div className={s['form-group']}>
        <label className={s['form-label']}>שם מלא *</label>
        <input
          type="text"
          className={s.input}
          value={formData.full_name}
          onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))}
          required
          disabled={loading}
        />
      </div>

      {!user && (
        <div className={s['form-group']}>
          <label className={s['form-label']}>סיסמה *</label>
          <input
            type="password"
            className={s.input}
            value={formData.password || ''}
            onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
            required
            disabled={loading}
            minLength={6}
            dir="ltr"
          />
          <small className={s['form-hint']}>לפחות 6 תווים</small>
        </div>
      )}

      <div className={s['form-group']}>
        <label className={s['form-label']}>תפקיד *</label>
        <select
          className={s.select}
          value={formData.role_name}
          onChange={(e) => setFormData(prev => ({ ...prev, role_name: e.target.value }))}
          required
          disabled={loading}
        >
          <option value="pending">ממתין לאישור (0)</option>
          <option value="viewer">צופה (10)</option>
          <option value="editor">עורך (20)</option>
          <option value="salesperson">איש מכירות (25)</option>
          <option value="manager">מנהל (30)</option>
          <option value="admin">מנהל מערכת (40)</option>
        </select>
        <small className={s['form-hint']}>
          המספר בסוגריים מציין את רמת ההרשאה
        </small>
      </div>

      <div className={s['form-group']}>
        <label className={s['checkbox-label']}>
          <input
            type="checkbox"
            checked={formData.is_active}
            onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
            disabled={loading}
          />
          משתמש פעיל
        </label>
        <small className={s['form-hint']}>
          משתמשים לא פעילים לא יוכלו להתחבר למערכת
        </small>
      </div>

      <div className={s['form-actions']}>
        <button 
          type="submit" 
          className={`${s.btn} ${s['btn-primary']}`}
          disabled={loading}
        >
          {loading ? 'שומר...' : user ? 'עדכן משתמש' : 'צור משתמש'}
        </button>
      </div>
    </form>
  )
}

export function UsersManagePage() {
  const { user: currentUser } = useAuth()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterRole, setFilterRole] = useState('all')
  const { openModal, closeModal } = useModal()
  const { error: showError, success: showSuccess } = useToast()

  const loadUsers = async () => {
    try {
      setLoading(true)
      const res = await api.get<{ items: User[]; total: number }>('/users')
      setUsers(Array.isArray(res) ? res : res.items ?? [])
    } catch (err: unknown) {
      showError('שגיאה בטעינת רשימת המשתמשים')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadUsers()
  }, [])

  const filteredUsers = users.filter(user => {
    const matchesSearch = 
      user.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesRole = filterRole === 'all' || user.role_name === filterRole

    return matchesSearch && matchesRole
  })

  const handleCreateUser = () => {
    openModal({
      title: 'משתמש חדש',
      size: 'md',
      content: (
        <UserForm
          onSubmit={async (data) => {
            try {
              await api.post('/users', data)
              showSuccess('המשתמש נוצר בהצלחה')
              loadUsers()
              closeModal()
            } catch (err: unknown) {
              const message = err instanceof Error ? err.message : 'שגיאה ביצירת המשתמש'
              showError(message)
            }
          }}
          loading={false}
        />
      ),
    })
  }

  const handleEditUser = (user: User) => {
    openModal({
      title: `עריכת משתמש - ${user.full_name}`,
      size: 'md',
      content: (
        <UserForm
          user={user}
          onSubmit={async (data) => {
            try {
              await api.patch(`/users/${user.id}`, data)
              showSuccess('המשתמש עודכן בהצלחה')
              loadUsers()
              closeModal()
            } catch (err: unknown) {
              const message = err instanceof Error ? err.message : 'שגיאה בעדכון המשתמש'
              showError(message)
            }
          }}
          loading={false}
        />
      ),
    })
  }

  const handleDeleteUser = (user: User) => {
    if (user.id === currentUser?.id) {
      showError('לא ניתן למחוק את המשתמש הנוכחי')
      return
    }

    openModal({
      title: 'מחיקת משתמש',
      size: 'sm',
      content: (
        <div className={styles.deleteConfirm}>
          <p>האם אתה בטוח שברצונך למחוק את המשתמש <strong>{user.full_name}</strong>?</p>
          <p>פעולה זו בלתי הפיכה.</p>
          <div className={styles.deleteActions}>
            <button
              className={`${s.btn} ${s['btn-danger']}`}
              onClick={async () => {
                try {
                  await api.delete(`/users/${user.id}`)
                  showSuccess('המשתמש נמחק בהצלחה')
                  loadUsers()
                  closeModal()
                } catch (err: unknown) {
                  const message = err instanceof Error ? err.message : 'שגיאה במחיקת המשתמש'
                  showError(message)
                }
              }}
            >
              מחק משתמש
            </button>
            <button
              className={`${s.btn} ${s['btn-secondary']}`}
              onClick={closeModal}
            >
              ביטול
            </button>
          </div>
        </div>
      ),
    })
  }

  const getRoleDisplay = (role: string) => {
    switch (role) {
      case 'admin': return { label: 'מנהל מערכת', color: '#dc2626' }
      case 'manager': return { label: 'מנהל', color: '#ea580c' }
      case 'salesperson': return { label: 'איש מכירות', color: '#7c3aed' }
      case 'editor': return { label: 'עורך', color: '#2563eb' }
      case 'viewer': return { label: 'צופה', color: '#16a34a' }
      case 'pending': return { label: 'ממתין לאישור', color: '#ca8a04' }
      default: return { label: role, color: '#6b7280' }
    }
  }

  const columns = [
    {
      key: 'full_name',
      header: 'שם',
      render: (user: User) => (
        <div className={styles.userInfo}>
          <div className={styles.userName}>{user.full_name}</div>
          <div className={styles.userEmail}>{user.email}</div>
        </div>
      )
    },
    {
      key: 'role_name',
      header: 'תפקיד',
      render: (user: User) => {
        const role = getRoleDisplay(user.role_name)
        return (
          <span 
            className={styles.roleBadge}
            style={{ backgroundColor: role.label + '20', color: role.color }}
          >
            {role.label}
          </span>
        )
      }
    },
    {
      key: 'is_active',
      header: 'סטטוס',
      render: (user: User) => (
        <span className={`${styles.statusBadge} ${user.is_active ? styles.active : styles.inactive}`}>
          {user.is_active ? 'פעיל' : 'לא פעיל'}
        </span>
      )
    },
    {
      key: 'created_at',
      header: 'תאריך הצטרפות',
      render: (user: User) => new Date(user.created_at).toLocaleDateString('he-IL')
    },
    {
      key: 'actions',
      header: 'פעולות',
      render: (user: User) => (
        <div className={styles.actions}>
          <button
            className={styles.actionBtn}
            onClick={() => handleEditUser(user)}
            title="עריכה"
          >
            <Edit size={16} />
          </button>
          {user.id !== currentUser?.id && (
            <button
              className={`${styles.actionBtn} ${styles.danger}`}
              onClick={() => handleDeleteUser(user)}
              title="מחיקה"
            >
              <Trash2 size={16} />
            </button>
          )}
        </div>
      )
    }
  ]

  return (
    <AdminRoute>
      <div className={styles.container}>
        <div className={styles.header}>
          <div className={styles.headerInfo}>
            <h1 className={styles.title}>ניהול משתמשים</h1>
            <p className={styles.subtitle}>
              ניהול משתמשי המערכת והרשאות
            </p>
          </div>
          
          <button 
            className={`${s.btn} ${s['btn-primary']}`}
            onClick={handleCreateUser}
          >
            <UserPlus size={18} />
            משתמש חדש
          </button>
        </div>

        <div className={styles.filters}>
          <div className={styles.searchBox}>
            <input
              type="text"
              placeholder="חיפוש לפי שם או מייל..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={s.input}
            />
          </div>

          <div className={styles.filterBox}>
            <select
              value={filterRole}
              onChange={(e) => setFilterRole(e.target.value)}
              className={s.select}
            >
              <option value="all">כל התפקידים</option>
              <option value="pending">ממתין לאישור</option>
              <option value="viewer">צופה</option>
              <option value="editor">עורך</option>
              <option value="manager">מנהל</option>
              <option value="admin">מנהל מערכת</option>
            </select>
          </div>
        </div>

        <div className={styles.usersGrid}>
          <DataTable
            data={filteredUsers}
            columns={columns}
            loading={loading}
            emptyText="לא נמצאו משתמשים"
            keyExtractor={(user) => user.id}
          />
        </div>

        {!loading && filteredUsers.length > 0 && (
          <div className={styles.summary}>
            <div className={styles.summaryItem}>
              <Shield size={16} />
              {filteredUsers.length} משתמשים
            </div>
            <div className={styles.summaryItem}>
              <UserCheck size={16} />
              {filteredUsers.filter(u => u.is_active).length} פעילים
            </div>
            <div className={styles.summaryItem}>
              <Eye size={16} />
              {filteredUsers.filter(u => u.role_name === 'pending').length} ממתינים לאישור
            </div>
          </div>
        )}
      </div>
    </AdminRoute>
  )
}