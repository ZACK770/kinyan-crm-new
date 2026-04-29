import React, { useEffect, useState, type FC } from 'react'
import { X, MessageCircle } from 'lucide-react'
import styles from './ChatNotificationToast.module.css'

interface ChatNotification {
  id: number
  thread_id: number
  thread_title: string
  sender_name: string
  sender_avatar?: string | null
  content: string
  created_at: string
}

interface ChatNotificationToastProps {
  notification: ChatNotification
  onClose: () => void
  onOpenChat: (threadId: number) => void
}

export const ChatNotificationToast: FC<ChatNotificationToastProps> = ({
  notification,
  onClose,
  onOpenChat,
}) => {
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    // Auto-hide after 5 seconds
    const timer = setTimeout(() => {
      setVisible(false)
      setTimeout(onClose, 300) // Wait for fade-out animation
    }, 5000)

    return () => clearTimeout(timer)
  }, [onClose])

  const handleClick = () => {
    onOpenChat(notification.thread_id)
    onClose()
  }

  const formatTime = (dateStr: string) => {
    try {
      const d = new Date(dateStr)
      return d.toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' })
    } catch {
      return ''
    }
  }

  if (!visible) return null

  return (
    <div className={styles.toast}>
      <div className={styles.toastContent} onClick={handleClick}>
        <div className={styles.toastAvatar}>
          {notification.sender_avatar ? (
            <img src={notification.sender_avatar} alt="" />
          ) : (
            <MessageCircle size={20} />
          )}
        </div>
        <div className={styles.toastBody}>
          <div className={styles.toastHeader}>
            <span className={styles.toastSender}>{notification.sender_name}</span>
            <span className={styles.toastTime}>{formatTime(notification.created_at)}</span>
          </div>
          <div className={styles.toastThread}>{notification.thread_title}</div>
          <div className={styles.toastMessage}>{notification.content}</div>
        </div>
        <button className={styles.toastClose} onClick={(e) => { e.stopPropagation(); onClose() }}>
          <X size={16} />
        </button>
      </div>
    </div>
  )
}

interface ChatNotificationContainerProps {
  notifications: ChatNotification[]
  onClose: (id: number) => void
  onOpenChat: (threadId: number) => void
}

export const ChatNotificationContainer: FC<ChatNotificationContainerProps> = ({
  notifications,
  onClose,
  onOpenChat,
}) => {
  return (
    <div className={styles.container}>
      {notifications.map(n => (
        <ChatNotificationToast
          key={n.id}
          notification={n}
          onClose={() => onClose(n.id)}
          onOpenChat={onOpenChat}
        />
      ))}
    </div>
  )
}
