import { useState, useEffect, useCallback, type FC } from 'react'
import { X, Bell, Clock } from 'lucide-react'
import { api } from '@/lib/api'
import styles from './TaskReminderPopup.module.css'

interface TaskData {
  id: number
  title: string
  description?: string | null
  due_date: string
}

interface TaskReminderPopupProps {
  task: TaskData
  onDismiss: () => void
}

const TaskReminderPopup: FC<TaskReminderPopupProps> = ({ task, onDismiss }) => {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    // Small delay for animation
    const timer = setTimeout(() => setVisible(true), 100)
    return () => clearTimeout(timer)
  }, [])

  const handleDismiss = useCallback(() => {
    setVisible(false)
    setTimeout(onDismiss, 300)
  }, [onDismiss])

  const formatTime = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' })
    } catch {
      return ''
    }
  }

  return (
    <div className={`${styles.overlay} ${visible ? styles.visible : ''}`}>
      <div className={`${styles.popup} ${visible ? styles.visible : ''}`}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.icon}>
            <Bell size={20} />
          </div>
          <div className={styles.headerText}>
            <div className={styles.title}>תזכורת משימה</div>
            <div className={styles.time}>
              <Clock size={12} />
              {formatTime(task.due_date)}
            </div>
          </div>
          <button className={styles.closeBtn} onClick={handleDismiss} aria-label="סגירה">
            <X size={16} strokeWidth={2} />
          </button>
        </div>

        {/* Content */}
        <div className={styles.content}>
          <h3 className={styles.taskTitle}>{task.title}</h3>
          {task.description && (
            <p className={styles.taskDescription}>{task.description}</p>
          )}
        </div>

        {/* Footer */}
        <div className={styles.footer}>
          <button className={styles.dismissBtn} onClick={handleDismiss}>
            הבנתי
          </button>
        </div>
      </div>
    </div>
  )
}

export default TaskReminderPopup
