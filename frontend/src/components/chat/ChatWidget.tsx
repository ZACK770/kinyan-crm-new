import React, { useState, useEffect, useRef, useCallback, type FC } from 'react'
import {
  MessageCircle, X, Send, ChevronLeft, Plus, Users, Pin,
  Search, Reply, Lock, UserPlus, Trash2, Paperclip, Download, Smile, FileText, Image as ImageIcon,
  Check, CheckCheck,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { api } from '@/lib/api'
import styles from './ChatWidget.module.css'
import clsx from 'clsx'
import { ChatNotificationContainer } from './ChatNotificationToast'

/* ── Types ── */
interface ChatUser {
  id: number
  full_name: string
  avatar_url?: string | null
  role_name?: string
}

interface ThreadMember {
  user_id: number
  full_name: string
  avatar_url?: string | null
}

interface LastMessage {
  id: number
  sender_name: string
  content: string
  created_at?: string | null
}

interface Thread {
  id: number
  thread_type: string
  title: string | null
  is_sales_team: boolean
  members: ThreadMember[]
  last_message: LastMessage | null
  created_at?: string | null
  updated_at?: string | null
  unread_count: number
}

interface Message {
  id: number
  thread_id: number
  sender_user_id: number
  sender_name: string
  sender_avatar?: string | null
  content: string
  reply_to_message_id?: number | null
  reply_to_preview?: string | null
  is_pinned: boolean
  pinned_by_user_id?: number | null
  created_at?: string | null
  is_read: boolean
  read_by_count?: number
  total_members?: number
}

interface FileAttachment {
  id: number
  filename: string
  size_bytes: number
  content_type?: string
}

interface ReadReceipt {
  user_id: number
  full_name: string
  avatar_url?: string | null
  read_at: string | null
  is_read: boolean
}

interface ChatNotification {
  id: number
  thread_id: number
  thread_title: string
  sender_name: string
  sender_avatar?: string | null
  content: string
  created_at: string
}

const EMOJI_LIST = [
  '😀','😂','😍','🤩','😎','🤔','😅','👍','👏','🙏',
  '❤️','🔥','✅','⭐','💪','🎉','😊','🤝','💯','👋',
  '😢','😡','🤷','🙄','😴','🤦','💡','📌','🚀','✨',
]

function parseFileFromContent(content: string): FileAttachment | null {
  const match = content.match(/^\[file:(\d+)\|(.+?)\|(\d+)(?:\|(.+?))?\]$/)
  if (!match) return null
  return { id: parseInt(match[1]), filename: match[2], size_bytes: parseInt(match[3]), content_type: match[4] }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

/* ── Notification sound ── */
const DING_URL = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdH2LkZeYl5KMhX13cW1ub3V8g4mOkZKSkI2JhYF9eXZ1dXd6fYGFiIqLi4qJh4WCf3x6eHd3eHp8f4KFh4mKioqJiIaCf3x6eHd3eHp9gIOGiImKiomIhoN/fHp4d3d4en2Ag4aIiYqKiYiGg398enl3d3h6fYCDhoiJioqJiIaDf3x6eXd3eHp9gIOGiImKiomIhoN/fHp5d3d4en2Ag4aIiYqKiYiGg398enl3d3h6fYCDhoiJioqJiIaDgHx6eXd3eHp9gIOGiImKiomIhoOAfHp5eHd4en2Ag4aIiYqKiYiGg4B8enl4d3h6fYCDhoiJioqJiIaDgHx6eXh4eHp9gIOGiImKiomIhoOAfHp5eHh5en2Ag4aIiYqKiYiGg4B8e3l4eHl6fYCDhoiJioqJiIaDgHx7eXh4eXp9gIOGiImKiomIhoOAfHt5eHh5en2Ag4aIiYqKiYiGg4B8e3l4eHl6fYCDhoeJioqJiIaDgHx7eXh4eXp9gIOGh4mKiomIhoOAfHt5eHl5en2Ag4aHiYqKiYiGg4B8e3l4eXl7fYCDhoeJioqJiIaDgH17eXh5eXt9gIOGh4mKiomIhoOAfXt5eHl5e32Ag4aHiYqKiYiGg4B9e3l5eXl7fYCDhoeJioqJiIaDgH17eXl5eXt9gIOGh4mKiomIhoSAfXt5eXl6e32Ag4aHiYqKiYiGhIB9e3l5eXp7fYCDhoeJioqJiIaEgH17enl5ent9gIOGh4mKiomIhoSAfXt6eXl6e32Ag4aHiYqKiYiGhIB9e3p5enp7fYCDhoeJioqJiIaEgH17enl6ent9gIOGh4mKiomJhoSAfXt6enp6e32Ag4aHiYqKiYmGhIB9e3p6enp7fYCDhoeJioqJiYaEgH17enp6ent+gIOGh4mKiomJhoSBfXt6enp6e36Ag4aHiYqKiYmGhIF9fHp6enp7foCDhoeJioqJiYaEgX18enp6e3t+gIOGh4mKiomJhoSBfXx6enp7e36Ag4aHiYqKiYmHhIF9fHp6e3t7foCDhoeJioqJiYeEgX18enp7e3t+gIOGh4mKiomJh4SBfXx6e3t7e36Ag4aHiYqKiYmHhIF9fHt7e3t7foCDhoeJioqJiYeEgX18e3t7e3x+gIOGh4mKiomJh4WBfXx7e3t7fH6Ag4aHiYqKiYmHhYF+fHt7e3x8foCDhoeJioqKiYeFgX58e3t7fHx+gIOGh4mKioqJh4WBfnx7e3x8fH6Bg4aHiYqKiomHhYF+fHt7fHx8foCDhoeJioqKiYeF'
const playDing = () => {
  try {
    const audio = new Audio(DING_URL)
    audio.volume = 0.4
    audio.play().catch(() => {})
  } catch {}
}

/* ── Main Widget ── */
export const ChatWidget: FC = () => {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [threads, setThreads] = useState<Thread[]>([])
  const [activeThread, setActiveThread] = useState<Thread | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [replyTo, setReplyTo] = useState<Message | null>(null)
  const [loading, setLoading] = useState(false)
  const [showNewChat, setShowNewChat] = useState(false)
  const [showMembers, setShowMembers] = useState(false)
  const [showPinned, setShowPinned] = useState(false)
  const [pinnedMessages, setPinnedMessages] = useState<Message[]>([])
  const [availableUsers, setAvailableUsers] = useState<ChatUser[]>([])
  const [newGroupTitle, setNewGroupTitle] = useState('')
  const [selectedUserIds, setSelectedUserIds] = useState<number[]>([])
  const [searchUsers, setSearchUsers] = useState('')
  const [unreadCount, setUnreadCount] = useState(0)
  const [contextMenu, setContextMenu] = useState<{ msg: Message; x: number; y: number } | null>(null)
  const [showEmoji, setShowEmoji] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [readReceiptsModal, setReadReceiptsModal] = useState<{ messageId: number; receipts: ReadReceipt[] } | null>(null)
  const [notifications, setNotifications] = useState<ChatNotification[]>([])
  const [lightboxImage, setLightboxImage] = useState<{ url: string; filename: string } | null>(null)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const notificationWsRef = useRef<WebSocket | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const seenMsgIds = useRef<Set<number>>(new Set())

  const isManager = (user?.permission_level ?? 0) >= 30

  // ── Mention autocomplete state ──
  const [threadMembers, setThreadMembers] = useState<{id: number, name: string, avatar?: string | null}[]>([])
  const [mentionQuery, setMentionQuery] = useState('')
  const [showMentionSuggestions, setShowMentionSuggestions] = useState(false)
  const [mentionCursorIndex, setMentionCursorIndex] = useState(0)

  // Filter members based on mention query
  const filteredMembers = threadMembers.filter(m =>
    m.name.toLowerCase().includes(mentionQuery.toLowerCase())
  )

  console.log('[Chat] Filtered members:', { threadMembers: threadMembers.length, mentionQuery, filteredMembers: filteredMembers.length, showMentionSuggestions })

  // ── Load threads ──
  const loadThreads = useCallback(async () => {
    try {
      const data = await api.get<Thread[]>('/chat/threads')
      setThreads(data)
      // Calculate total unread count
      const totalUnread = data.reduce((sum, t) => sum + (t.unread_count || 0), 0)
      setUnreadCount(totalUnread)
    } catch {}
  }, [])

  useEffect(() => {
    if (open && user) loadThreads()
  }, [open, user, loadThreads])

  // ── Global notification WebSocket connection ──
  useEffect(() => {
    if (!user) return

    const token = localStorage.getItem('kinyan_auth_token')
    if (!token) return

    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const wsUrl = `${proto}://${window.location.host}/api/chat/ws/notifications`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      ws.send(token)
    }

    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data)
        if (data.type === 'chat_notification') {
          // Add notification to list
          setNotifications(prev => {
            // Avoid duplicates
            if (prev.some(n => n.id === data.id)) return prev
            return [data, ...prev].slice(0, 5) // Keep max 5 notifications
          })
          // Increment unread count
          setUnreadCount(prev => prev + 1)
          playDing()
        }
      } catch {}
    }

    ws.onclose = () => {}

    // Ping every 30s
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send('ping')
    }, 30000)

    notificationWsRef.current = ws

    return () => {
      clearInterval(pingInterval)
      ws.close()
      notificationWsRef.current = null
    }
  }, [user])

  // ── Load messages for active thread ──
  const loadMessages = useCallback(async (threadId: number) => {
    try {
      setLoading(true)
      const data = await api.get<Message[]>(`/chat/threads/${threadId}/messages`)
      setMessages(data)
      // Track all loaded message IDs for dedup
      seenMsgIds.current = new Set(data.map(m => m.id))
    } catch {} finally { setLoading(false) }
  }, [])

  // ── Load read receipts for a message ──
  const loadReadReceipts = useCallback(async (messageId: number) => {
    try {
      const data = await api.get<{ receipts: ReadReceipt[] }>(`/chat/messages/${messageId}/read-receipts`)
      setReadReceiptsModal({ messageId, receipts: data.receipts })
    } catch {}
  }, [])

  // ── Handle notification close ──
  const handleCloseNotification = useCallback((id: number) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }, [])

  // ── Load thread members for @mentions ──
  const loadThreadMembers = useCallback(async (threadId: number) => {
    try {
      const data = await api.get<{id: number, name: string, avatar?: string | null}[]>(`/chat/threads/${threadId}/members`)
      console.log('[Chat] Loaded thread members:', data)
      setThreadMembers(data)
    } catch (e) {
      console.error('[Chat] Failed to load thread members:', e)
    }
  }, [])

  // ── WebSocket connection ──
  useEffect(() => {
    if (!activeThread || !open) return

    const token = localStorage.getItem('kinyan_auth_token')
    if (!token) return

    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const wsUrl = `${proto}://${window.location.host}/api/chat/ws/${activeThread.id}`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      ws.send(token)
    }

    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data)
        if (data.type === 'new_message') {
          const msg: Message = data.message
          // Deduplicate: skip if we already have this message (optimistic add)
          if (seenMsgIds.current.has(msg.id)) return
          seenMsgIds.current.add(msg.id)
          if (msg.sender_user_id !== user?.id) {
            playDing()
          }
          setMessages(prev => {
            // Extra safety: check if already in array
            if (prev.some(m => m.id === msg.id)) return prev
            return [...prev, msg]
          })
          setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
        } else if (data.type === 'message_pinned') {
          setMessages(prev => prev.map(m =>
            m.id === data.message_id ? { ...m, is_pinned: true } : m
          ))
        } else if (data.type === 'message_unpinned') {
          setMessages(prev => prev.map(m =>
            m.id === data.message_id ? { ...m, is_pinned: false } : m
          ))
        } else if (data.type === 'message_read') {
          // Update message read status
          setMessages(prev => prev.map(m => {
            if (m.id === data.message_id) {
              // Increment read count if not already counted
              const currentReadCount = m.read_by_count || 0
              return {
                ...m,
                read_by_count: currentReadCount + 1,
                is_read: true
              }
            }
            return m
          }))
        }
      } catch {}
    }

    ws.onclose = () => {}

    // Ping every 30s
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send('ping')
    }, 30000)

    wsRef.current = ws

    return () => {
      clearInterval(pingInterval)
      ws.close()
      wsRef.current = null
    }
  }, [activeThread, open, user?.id])

  // ── Open thread ──
  const openThread = useCallback(async (thread: Thread) => {
    setActiveThread(thread)
    setReplyTo(null)
    setShowPinned(false)
    setShowMembers(false)
    setContextMenu(null)
    await loadMessages(thread.id)
    await loadThreadMembers(thread.id)
    // Mark all messages as read
    try {
      await api.post(`/chat/threads/${thread.id}/mark-read`)
      // Update local thread unread count
      setThreads(prev => prev.map(t =>
        t.id === thread.id ? { ...t, unread_count: 0 } : t
      ))
      // Update global unread count (subtract this thread's unread count)
      setUnreadCount(prev => Math.max(0, prev - (thread.unread_count || 0)))
    } catch {}
    setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'auto' }), 100)
  }, [loadMessages, loadThreadMembers])

  // ── Handle open chat from notification ──
  const handleNotificationOpenChat = useCallback(async (threadId: number) => {
    try {
      const thread = await api.get<Thread>(`/chat/threads/${threadId}`)
      setOpen(true)
      // Refresh threads list to get latest data
      const refreshedThreads = await api.get<Thread[]>('/chat/threads')
      setThreads(refreshedThreads)
      openThread(thread)
    } catch {}
  }, [openThread])

  // ── Start DM ──
  const startDM = useCallback(async (targetUserId: number) => {
    try {
      const thread = await api.post<Thread>('/chat/threads/dm', { user_id: targetUserId })
      setShowNewChat(false)
      setSelectedUserIds([])
      // Refresh threads list
      const refreshedThreads = await api.get<Thread[]>('/chat/threads')
      setThreads(refreshedThreads)
      openThread(thread)
    } catch {}
  }, [openThread])

  // ── Create group ──
  const createGroup = useCallback(async () => {
    if (!newGroupTitle.trim() || selectedUserIds.length === 0) return
    try {
      const thread = await api.post<Thread>('/chat/threads/group', {
        title: newGroupTitle.trim(),
        member_user_ids: selectedUserIds,
      })
      setShowNewChat(false)
      setNewGroupTitle('')
      setSelectedUserIds([])
      // Refresh threads list
      const refreshedThreads = await api.get<Thread[]>('/chat/threads')
      setThreads(refreshedThreads)
      openThread(thread)
    } catch {}
  }, [newGroupTitle, selectedUserIds, openThread])

  // ── Open sales team thread ──
  const openSalesTeam = useCallback(async () => {
    try {
      const thread = await api.get<Thread>('/chat/threads/sales-team')
      setShowNewChat(false)
      // Refresh threads list
      const refreshedThreads = await api.get<Thread[]>('/chat/threads')
      setThreads(refreshedThreads)
      openThread(thread)
    } catch {}
  }, [openThread])

  // ── Send message ──
  const sendMessage = useCallback(async () => {
    if (!input.trim() || !activeThread) return
    try {
      const res = await api.post<Message>(`/chat/threads/${activeThread.id}/messages`, {
        content: input.trim(),
        reply_to_message_id: replyTo?.id || null,
      })
      // Optimistic: add message immediately and track its ID for dedup
      if (res?.id) {
        seenMsgIds.current.add(res.id)
        setMessages(prev => prev.some(m => m.id === res.id) ? prev : [...prev, res])
        setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
      }
      setInput('')
      setReplyTo(null)
      setShowEmoji(false)
      inputRef.current?.focus()
    } catch {}
  }, [input, activeThread, replyTo])

  // ── Upload file ──
  const handleFileUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !activeThread) return
    if (file.size > 10 * 1024 * 1024) {
      alert('הקובץ גדול מדי. מקסימום 10MB')
      return
    }
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const uploadRes = await fetch(`/api/files/upload?entity_type=chat&entity_id=${activeThread.id}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('kinyan_auth_token')}` },
        body: formData,
      })
      if (!uploadRes.ok) throw new Error('Upload failed')
      const uploadData = await uploadRes.json()
      // Send file message
      const fileContent = `[file:${uploadData.id}|${file.name}|${file.size}|${file.type}]`
      const res = await api.post<Message>(`/chat/threads/${activeThread.id}/messages`, {
        content: fileContent,
        reply_to_message_id: null,
      })
      if (res?.id) {
        seenMsgIds.current.add(res.id)
        setMessages(prev => prev.some(m => m.id === res.id) ? prev : [...prev, res])
        setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
      }
    } catch { alert('שגיאה בהעלאת הקובץ') }
    finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }, [activeThread])

  // ── Handle input change for @mention autocomplete ──
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setInput(value)

    // Detect @ symbol and show autocomplete
    const cursorPos = e.target.selectionStart || value.length
    const textBeforeCursor = value.substring(0, cursorPos)

    // Find the last @ symbol
    const lastAtIndex = textBeforeCursor.lastIndexOf('@')

    console.log('[Chat] Input change:', { value, lastAtIndex, threadMembers: threadMembers.length })

    if (lastAtIndex !== -1) {
      // Check if there's a space after the @ (meaning it's not part of a mention)
      const textAfterAt = textBeforeCursor.substring(lastAtIndex + 1)
      const hasSpaceBeforeAt = lastAtIndex > 0 && textBeforeCursor[lastAtIndex - 1] === ' '
      const hasSpaceAfterAt = textAfterAt.includes(' ')

      console.log('[Chat] @ detected:', { textAfterAt, hasSpaceBeforeAt, hasSpaceAfterAt })

      if (!hasSpaceAfterAt && (lastAtIndex === 0 || hasSpaceBeforeAt)) {
        const query = textAfterAt.toLowerCase()
        setMentionQuery(query)
        setShowMentionSuggestions(true)
        setMentionCursorIndex(0)
        console.log('[Chat] Showing mention suggestions')
        return
      }
    }

    setShowMentionSuggestions(false)
    setMentionQuery('')
  }, [threadMembers.length])

  // ── Handle paste event for images ──
  const handlePaste = useCallback(async (e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items
    if (!items) return

    for (let i = 0; i < items.length; i++) {
      const item = items[i]
      if (item.type.startsWith('image/')) {
        e.preventDefault()
        const file = item.getAsFile()
        if (file && activeThread) {
          setUploading(true)
          try {
            const formData = new FormData()
            formData.append('file', file)
            const uploadRes = await fetch(`/api/files/upload?entity_type=chat&entity_id=${activeThread.id}`, {
              method: 'POST',
              headers: { 'Authorization': `Bearer ${localStorage.getItem('kinyan_auth_token')}` },
              body: formData,
            })
            if (!uploadRes.ok) throw new Error('Upload failed')
            const uploadData = await uploadRes.json()
            // Send file message
            const fileContent = `[file:${uploadData.id}|${file.name}|${file.size}|${file.type}]`
            const res = await api.post<Message>(`/chat/threads/${activeThread.id}/messages`, {
              content: fileContent,
              reply_to_message_id: null,
            })
            if (res?.id) {
              seenMsgIds.current.add(res.id)
              setMessages(prev => prev.some(m => m.id === res.id) ? prev : [...prev, res])
              setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
            }
          } catch { alert('שגיאה בהעלאת התמונה') }
          finally {
            setUploading(false)
          }
        }
        break
      }
    }
  }, [activeThread])

  // ── Handle mention selection ──
  const handleSelectMention = useCallback((member: {id: number, name: string}) => {
    const cursorPos = inputRef.current?.selectionStart || input.length
    const textBeforeCursor = input.substring(0, cursorPos)
    const textAfterCursor = input.substring(cursorPos)

    const lastAtIndex = textBeforeCursor.lastIndexOf('@')
    if (lastAtIndex !== -1) {
      const newText = textBeforeCursor.substring(0, lastAtIndex) + `@${member.name} ` + textAfterCursor
      setInput(newText)
      setShowMentionSuggestions(false)
      setMentionQuery('')
      // Focus back on input
      setTimeout(() => {
        inputRef.current?.focus()
        const newCursorPos = lastAtIndex + member.name.length + 2
        inputRef.current?.setSelectionRange(newCursorPos, newCursorPos)
      }, 0)
    }
  }, [input])

  // ── Handle delete message ──
  const handleDeleteMessage = useCallback(async (messageId: number) => {
    if (!confirm('למחוק את הודעה?')) return
    try {
      await api.delete(`/chat/messages/${messageId}`)
      setMessages(prev => prev.filter(m => m.id !== messageId))
    } catch { alert('שגיאה במחיקת הודעה') }
  }, [])

  // ── Load available users ──
  useEffect(() => {
    if (showNewChat || showMembers) {
      api.get<ChatUser[]>('/chat/users/available').then(setAvailableUsers).catch(() => {})
    }
  }, [showNewChat, showMembers])

  // ── Pin/Unpin ──
  const togglePin = useCallback(async (msg: Message) => {
    if (!activeThread) return
    try {
      if (msg.is_pinned) {
        await api.delete(`/chat/threads/${activeThread.id}/messages/${msg.id}/pin`)
      } else {
        await api.post(`/chat/threads/${activeThread.id}/messages/${msg.id}/pin`)
      }
      setContextMenu(null)
    } catch {}
  }, [activeThread])

  // ── Load pinned ──
  const loadPinned = useCallback(async () => {
    if (!activeThread) return
    try {
      const data = await api.get<Message[]>(`/chat/threads/${activeThread.id}/pinned`)
      setPinnedMessages(data)
      setShowPinned(true)
    } catch {}
  }, [activeThread])

  // ── Add member ──
  const addMember = useCallback(async (userId: number) => {
    if (!activeThread) return
    try {
      await api.post(`/chat/threads/${activeThread.id}/members`, { user_ids: [userId] })
      const refreshed = await api.get<Thread[]>('/chat/threads')
      setThreads(refreshed)
      const updated = refreshed.find(t => t.id === activeThread.id)
      if (updated) setActiveThread(updated)
    } catch {}
  }, [activeThread])

  // ── Remove member ──
  const removeMember = useCallback(async (userId: number) => {
    if (!activeThread) return
    try {
      await api.delete(`/chat/threads/${activeThread.id}/members/${userId}`)
      const refreshed = await api.get<Thread[]>('/chat/threads')
      setThreads(refreshed)
      const updated = refreshed.find(t => t.id === activeThread.id)
      if (updated) setActiveThread(updated)
    } catch {}
  }, [activeThread])

  // ── Double-click reply ──
  const handleDoubleClick = useCallback((msg: Message, e: React.MouseEvent) => {
    e.preventDefault()
    setReplyTo(msg)
    inputRef.current?.focus()
  }, [])

  // ── Right-click context menu ──
  const handleContextMenu = useCallback((msg: Message, e: React.MouseEvent) => {
    e.preventDefault()
    setContextMenu({ msg, x: e.clientX, y: e.clientY })
  }, [])

  // Close context menu on click outside
  useEffect(() => {
    if (!contextMenu) return
    const handler = () => setContextMenu(null)
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [contextMenu])

  // ── Private reply (start DM from context menu) ──
  const privateReply = useCallback(async (msg: Message) => {
    setContextMenu(null)
    if (msg.sender_user_id === user?.id) return
    await startDM(msg.sender_user_id)
  }, [user?.id, startDM])

  // ── Scroll to bottom on new messages ──
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  // ── Time format ──
  const formatTime = (dateStr?: string | null) => {
    if (!dateStr) return ''
    try {
      const d = new Date(dateStr)
      return d.toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' })
    } catch { return '' }
  }

  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    if (date.toDateString() === today.toDateString()) {
      return 'היום'
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'אתמול'
    } else {
      return date.toLocaleDateString('he-IL', { day: '2-digit', month: '2-digit', year: '2-digit' })
    }
  }

  // Render message content with @mentions highlighted in blue
  const renderMessageContent = (content: string) => {
    const parts = content.split(/(@\S+)/g)
    return parts.map((part, idx) => {
      if (part.startsWith('@')) {
        return <span key={idx} className={styles.mentionHighlight}>{part}</span>
      }
      return part
    })
  }

  const filteredUsers = availableUsers.filter(u =>
    u.full_name.includes(searchUsers) || u.role_name?.includes(searchUsers)
  )

  if (!user || user.permission_level < 10) return null

  return (
    <>
      {/* ── FAB Button ── */}
      <button
        className={clsx(styles.fab, open && styles.fabHidden)}
        onClick={() => setOpen(true)}
        aria-label="פתח צ'אט"
      >
        <MessageCircle size={22} />
        {unreadCount > 0 && <span className={styles.fabBadge}>{unreadCount}</span>}
      </button>

      {/* ── Chat Drawer ── */}
      <div className={clsx(styles.drawer, open && styles.drawerOpen)}>
        {/* Header */}
        <div className={styles.drawerHeader}>
          {activeThread ? (
            <>
              <button className={styles.backBtn} onClick={() => { setActiveThread(null); setShowPinned(false); setShowMembers(false) }}>
                <ChevronLeft size={18} />
              </button>
              <div className={styles.headerTitle}>
                {activeThread.thread_type === 'group' && <Users size={14} />}
                {activeThread.thread_type === 'dm' && <Lock size={14} />}
                <span>{activeThread.title || 'צ\'אט'}</span>
              </div>
              <div className={styles.headerActions}>
                <button onClick={loadPinned} title="הודעות מוצמדות"><Pin size={15} /></button>
                {activeThread.thread_type === 'group' && (
                  <button onClick={() => setShowMembers(!showMembers)} title="חברים"><Users size={15} /></button>
                )}
              </div>
            </>
          ) : (
            <>
              <div className={styles.headerTitle}>
                <MessageCircle size={16} />
                <span>צ'אט צוות</span>
              </div>
              <div className={styles.headerActions}>
                <button onClick={() => setShowNewChat(!showNewChat)} title="צ'אט חדש"><Plus size={16} /></button>
              </div>
            </>
          )}
          <button className={styles.closeBtn} onClick={() => setOpen(false)}>
            <X size={16} />
          </button>
        </div>

        {/* ── New Chat Panel ── */}
        {showNewChat && !activeThread && (
          <div className={styles.newChatPanel}>
            <button className={styles.salesTeamBtn} onClick={openSalesTeam}>
              <Users size={16} />
              <span>כל אנשי המכירות</span>
            </button>

            <div className={styles.newGroupSection}>
              <input
                className={styles.chatInput}
                placeholder="שם קבוצה חדשה..."
                value={newGroupTitle}
                onChange={e => setNewGroupTitle(e.target.value)}
              />
            </div>

            <div className={styles.userSearch}>
              <Search size={14} />
              <input
                placeholder="חפש משתמש..."
                value={searchUsers}
                onChange={e => setSearchUsers(e.target.value)}
              />
            </div>

            <div className={styles.userList}>
              {filteredUsers.map(u => (
                <div key={u.id} className={styles.userItem}>
                  <div className={styles.userAvatar}>
                    {u.avatar_url ? <img src={u.avatar_url} alt="" /> : u.full_name[0]}
                  </div>
                  <div className={styles.userName}>{u.full_name}</div>
                  {newGroupTitle.trim() ? (
                    <label className={styles.userCheck}>
                      <input
                        type="checkbox"
                        checked={selectedUserIds.includes(u.id)}
                        onChange={e => {
                          if (e.target.checked) setSelectedUserIds(p => [...p, u.id])
                          else setSelectedUserIds(p => p.filter(id => id !== u.id))
                        }}
                      />
                    </label>
                  ) : (
                    <button className={styles.dmBtn} onClick={() => startDM(u.id)}>
                      <MessageCircle size={14} />
                    </button>
                  )}
                </div>
              ))}
            </div>

            {newGroupTitle.trim() && selectedUserIds.length > 0 && (
              <button className={styles.createGroupBtn} onClick={createGroup}>
                צור קבוצה ({selectedUserIds.length} חברים)
              </button>
            )}
          </div>
        )}

        {/* ── Members Panel ── */}
        {showMembers && activeThread && (
          <div className={styles.membersPanel}>
            <div className={styles.membersPanelTitle}>חברי הקבוצה ({activeThread.members.length})</div>
            {activeThread.members.map(m => (
              <div key={m.user_id} className={styles.memberItem}>
                <div className={styles.userAvatar}>
                  {m.avatar_url ? <img src={m.avatar_url} alt="" /> : m.full_name[0]}
                </div>
                <span>{m.full_name}</span>
                {m.user_id !== user.id && (
                  <button className={styles.removeMemberBtn} onClick={() => removeMember(m.user_id)}>
                    <Trash2 size={12} />
                  </button>
                )}
              </div>
            ))}
            <>
              <div className={styles.addMemberTitle}>הוסף חבר</div>
              {availableUsers
                  .filter(u => !activeThread.members.some(m => m.user_id === u.id))
                  .map(u => (
                    <div key={u.id} className={styles.memberItem}>
                      <div className={styles.userAvatar}>
                        {u.avatar_url ? <img src={u.avatar_url} alt="" /> : u.full_name[0]}
                      </div>
                      <span>{u.full_name}</span>
                      <button className={styles.addMemberBtn} onClick={() => addMember(u.id)}>
                        <UserPlus size={13} />
                      </button>
                    </div>
                  ))}
            </>
          </div>
        )}

        {/* ── Pinned Messages Panel ── */}
        {showPinned && activeThread && (
          <div className={styles.pinnedPanel}>
            <div className={styles.pinnedTitle}>
              <Pin size={14} /> הודעות מוצמדות
              <button onClick={() => setShowPinned(false)}><X size={14} /></button>
            </div>
            {pinnedMessages.length === 0 ? (
              <div className={styles.emptyPinned}>אין הודעות מוצמדות</div>
            ) : pinnedMessages.map(m => (
              <div key={m.id} className={styles.pinnedMsg}>
                <strong>{m.sender_name}</strong>
                <p>{m.content}</p>
                <span className={styles.msgTime}>{formatTime(m.created_at)}</span>
              </div>
            ))}
          </div>
        )}

        {/* ── Thread List ── */}
        {!activeThread && !showNewChat && (
          <div className={styles.threadList}>
            {threads.length === 0 ? (
              <div className={styles.emptyState}>
                <MessageCircle size={32} strokeWidth={1} />
                <p>אין שיחות עדיין</p>
                <button onClick={() => setShowNewChat(true)}>התחל צ'אט</button>
              </div>
            ) : threads.map(t => (
              <div key={t.id} className={styles.threadItem} onClick={() => openThread(t)}>
                <div className={styles.threadIcon}>
                  {t.thread_type === 'group' ? <Users size={18} /> : <MessageCircle size={18} />}
                </div>
                <div className={styles.threadInfo}>
                  <div className={styles.threadName}>
                    {t.title || 'צ\'אט פרטי'}
                    {t.is_sales_team && <span className={styles.salesBadge}>צוות</span>}
                  </div>
                  {t.last_message && (
                    <div className={styles.threadPreview}>
                      <span className={styles.previewSender}>{t.last_message.sender_name}:</span>
                      {' '}{t.last_message.content}
                    </div>
                  )}
                </div>
                <div className={styles.threadMeta}>
                  {t.last_message?.created_at && (
                    <div className={styles.threadTime}>{formatTime(t.last_message.created_at)}</div>
                  )}
                  {t.unread_count > 0 && (
                    <span className={styles.threadUnreadBadge}>{t.unread_count > 99 ? '99+' : t.unread_count}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── Messages ── */}
        {activeThread && !showPinned && !showMembers && (
          <>
            <div className={styles.messageList}>
              {loading ? (
                <div className={styles.loadingMsg}>טוען הודעות...</div>
              ) : messages.length === 0 ? (
                <div className={styles.emptyMessages}>אין הודעות עדיין. שלח את ההודעה הראשונה!</div>
              ) : messages.map((m, idx) => {
                // Check if we need to show a date separator (day changed from previous message)
                const showDateSeparator = idx === 0 || (
                  m.created_at && messages[idx - 1]?.created_at &&
                  new Date(m.created_at).toDateString() !== new Date(messages[idx - 1].created_at).toDateString()
                )

                return (
                  <React.Fragment key={m.id}>
                    {showDateSeparator && m.created_at && (
                      <div className={styles.dateSeparator}>
                        {formatDate(m.created_at)}
                      </div>
                    )}
                    <div
                      className={clsx(
                        styles.message,
                        m.sender_user_id === user?.id && styles.messageMine,
                        m.is_pinned && styles.messagePinned,
                      )}
                      onDoubleClick={(e) => handleDoubleClick(m, e)}
                      onContextMenu={(e) => handleContextMenu(m, e)}
                    >
                      {m.is_pinned && <div className={styles.pinIndicator}><Pin size={10} /> מוצמד</div>}
                      {m.reply_to_preview && (
                        <div className={styles.replyPreview}>
                          <Reply size={10} />
                          <span>{m.reply_to_preview}</span>
                        </div>
                      )}
                      <div className={styles.msgBubble}>
                        {m.sender_user_id !== user?.id && (
                          <div className={styles.msgSender}>{m.sender_name}</div>
                        )}
                        {(() => {
                          const fileInfo = parseFileFromContent(m.content)
                          if (fileInfo) {
                            const isImage = fileInfo.content_type?.startsWith('image/')
                            const imageUrl = `/api/files/${fileInfo.id}/download`
                            if (isImage) {
                              return (
                                <div className={styles.imageAttachment}>
                                  <img
                                    src={imageUrl}
                                    alt={fileInfo.filename}
                                    className={styles.chatImage}
                                    onClick={() => setLightboxImage({ url: imageUrl, filename: fileInfo.filename })}
                                  />
                                  <div className={styles.imageInfo}>
                                    <span className={styles.fileName}>{fileInfo.filename}</span>
                                  </div>
                                </div>
                              )
                            }
                            return (
                              <div className={styles.fileAttachment}>
                                <div className={styles.fileIcon}>
                                  {isImage ? <ImageIcon size={18} /> : <FileText size={18} />}
                                </div>
                                <div className={styles.fileInfo}>
                                  <span className={styles.fileName}>{fileInfo.filename}</span>
                                  <span className={styles.fileSize}>{formatFileSize(fileInfo.size_bytes)}</span>
                                </div>
                                <a
                                  href={imageUrl}
                                  target="_blank"
                                  rel="noreferrer"
                                  className={styles.fileDownload}
                                  onClick={e => e.stopPropagation()}
                                >
                                  <Download size={14} />
                                </a>
                              </div>
                            )
                          }
                          return <div className={styles.msgContent}>{renderMessageContent(m.content)}</div>
                        })()}
                        <div className={styles.msgTime}>
                          {formatTime(m.created_at)}
                          {m.sender_user_id === user?.id && (
                            <span
                              className={styles.msgReadStatus}
                              onClick={() => loadReadReceipts(m.id)}
                              title="לחץ לראות מי קרא"
                            >
                              {m.read_by_count === m.total_members ? (
                                <CheckCheck size={14} />
                              ) : m.read_by_count > 0 ? (
                                <Check size={14} />
                              ) : (
                                <Check size={14} opacity={0.5} />
                              )}
                              {m.read_by_count > 0 && m.total_members > 0 && (
                                <span className={styles.readCount}>{m.read_by_count}/{m.total_members}</span>
                              )}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </React.Fragment>
                )
              })}
              <div ref={messagesEndRef} />
            </div>

            {/* Reply indicator */}
            {replyTo && (
              <div className={styles.replyBar}>
                <Reply size={12} />
                <span>מגיב ל: {replyTo.sender_name} — {replyTo.content.slice(0, 40)}</span>
                <button onClick={() => setReplyTo(null)}><X size={12} /></button>
              </div>
            )}

            {/* Emoji Picker */}
            {showEmoji && (
              <div className={styles.emojiPicker}>
                {EMOJI_LIST.map(em => (
                  <button key={em} className={styles.emojiBtn} onClick={() => { setInput(prev => prev + em); inputRef.current?.focus() }}>
                    {em}
                  </button>
                ))}
              </div>
            )}

            {/* Input */}
            <div className={styles.inputBar}>
              <input
                ref={inputRef}
                className={styles.chatInput}
                placeholder="הקלד הודעה... (@ לתיוג)"
                value={input}
                onChange={handleInputChange}
                onPaste={handlePaste}
                onKeyDown={e => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    if (showMentionSuggestions && mentionCursorIndex < filteredMembers.length) {
                      handleSelectMention(filteredMembers[mentionCursorIndex])
                    } else {
                      sendMessage()
                    }
                  } else if (e.key === 'ArrowDown' && showMentionSuggestions) {
                    e.preventDefault()
                    setMentionCursorIndex(prev => Math.min(prev + 1, filteredMembers.length - 1))
                  } else if (e.key === 'ArrowUp' && showMentionSuggestions) {
                    e.preventDefault()
                    setMentionCursorIndex(prev => Math.max(prev - 1, 0))
                  } else if (e.key === 'Escape') {
                    setShowMentionSuggestions(false)
                  }
                }}
              />
              <button className={styles.emojiToggle} onClick={() => setShowEmoji(v => !v)} title="אימוג'י">
                <Smile size={18} />
              </button>
              <input ref={fileInputRef} type="file" hidden onChange={handleFileUpload} />
              <button className={styles.attachBtn} onClick={() => fileInputRef.current?.click()} disabled={uploading} title="צרף קובץ">
                <Paperclip size={18} />
              </button>
              <button className={styles.sendBtn} onClick={sendMessage} disabled={!input.trim()}>
                <Send size={16} />
              </button>

              {/* @Mention Autocomplete Dropdown */}
              {showMentionSuggestions && (
                <div className={styles.mentionDropdown}>
                  {filteredMembers.length === 0 ? (
                    <div className={styles.mentionNoResults}>לא נמצאו תוצאות</div>
                  ) : (
                    filteredMembers.map((member, idx) => (
                      <div
                        key={member.id}
                        className={clsx(styles.mentionItem, idx === mentionCursorIndex && styles.mentionItemActive)}
                        onClick={() => handleSelectMention(member)}
                      >
                        {member.avatar ? (
                          <img src={member.avatar} alt={member.name} className={styles.mentionAvatar} />
                        ) : (
                          <div className={styles.mentionAvatarPlaceholder}>{member.name[0]}</div>
                        )}
                        <span className={styles.mentionName}>{member.name}</span>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* ── Context Menu ── */}
      {contextMenu && (
        <div
          className={styles.contextMenu}
          style={{ top: contextMenu.y, left: contextMenu.x }}
        >
          <button onClick={() => { setReplyTo(contextMenu.msg); setContextMenu(null); inputRef.current?.focus() }}>
            <Reply size={13} /> הגב
          </button>
          {contextMenu.msg.sender_user_id !== user?.id && (
            <button onClick={() => privateReply(contextMenu.msg)}>
              <Lock size={13} /> הגב בפרטי
            </button>
          )}
          {isManager && (
            <button onClick={() => togglePin(contextMenu.msg)}>
              <Pin size={13} /> {contextMenu.msg.is_pinned ? 'בטל הצמדה' : 'הצמד'}
            </button>
          )}
          {(contextMenu.msg.sender_user_id === user?.id || user?.is_superuser) && (
            <button onClick={() => { handleDeleteMessage(contextMenu.msg.id); setContextMenu(null) }}>
              <Trash2 size={13} /> מחק
            </button>
          )}
        </div>
      )}

      {/* ── Read Receipts Modal ── */}
      {readReceiptsModal && (
        <div className={styles.modalOverlay} onClick={() => setReadReceiptsModal(null)}>
          <div className={styles.modalContent} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h3>מי קרא את ההודעה</h3>
              <button onClick={() => setReadReceiptsModal(null)}><X size={20} /></button>
            </div>
            <div className={styles.modalBody}>
              {readReceiptsModal.receipts.length === 0 ? (
                <div className={styles.emptyReceipts}>אף אחד לא קרא עדיין</div>
              ) : (
                readReceiptsModal.receipts.map(r => (
                  <div key={r.user_id} className={styles.receiptItem}>
                    <div className={styles.receiptAvatar}>
                      {r.avatar_url ? <img src={r.avatar_url} alt="" /> : r.full_name[0]}
                    </div>
                    <div className={styles.receiptInfo}>
                      <div className={styles.receiptName}>{r.full_name}</div>
                      {r.is_read && r.read_at && (
                        <div className={styles.receiptTime}>
                          {new Date(r.read_at).toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      )}
                    </div>
                    {r.is_read ? (
                      <div className={clsx(styles.receiptStatus, 'read')}><CheckCheck size={16} /></div>
                    ) : (
                      <div className={clsx(styles.receiptStatus, 'unread')}><Check size={16} opacity={0.3} /></div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── Notification Container ── */}
      <ChatNotificationContainer
        notifications={notifications}
        onClose={handleCloseNotification}
        onOpenChat={handleNotificationOpenChat}
      />

      {/* ── Image Lightbox ── */}
      {lightboxImage && (
        <div className={styles.lightboxOverlay} onClick={() => setLightboxImage(null)}>
          <div className={styles.lightboxContent} onClick={e => e.stopPropagation()}>
            <button className={styles.lightboxClose} onClick={() => setLightboxImage(null)}>
              <X size={24} />
            </button>
            <img src={lightboxImage.url} alt={lightboxImage.filename} className={styles.lightboxImage} />
            <div className={styles.lightboxFilename}>{lightboxImage.filename}</div>
            <a
              href={lightboxImage.url}
              download={lightboxImage.filename}
              className={styles.lightboxDownload}
              target="_blank"
              rel="noreferrer"
            >
              <Download size={20} /> הורד
            </a>
          </div>
        </div>
      )}
    </>
  )
}
