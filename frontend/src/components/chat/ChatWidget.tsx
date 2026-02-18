import { useState, useEffect, useRef, useCallback, type FC } from 'react'
import {
  MessageCircle, X, Send, ChevronLeft, Plus, Users, Pin,
  Search, Reply, Lock, UserPlus, Trash2,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { api } from '@/lib/api'
import styles from './ChatWidget.module.css'
import clsx from 'clsx'

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
  const [unreadCount] = useState(0)
  const [contextMenu, setContextMenu] = useState<{ msg: Message; x: number; y: number } | null>(null)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const isManager = (user?.permission_level ?? 0) >= 30

  // ── Load threads ──
  const loadThreads = useCallback(async () => {
    try {
      const data = await api.get<Thread[]>('/chat/threads')
      setThreads(data)
    } catch {}
  }, [])

  useEffect(() => {
    if (open && user) loadThreads()
  }, [open, user, loadThreads])

  // ── Load messages for active thread ──
  const loadMessages = useCallback(async (threadId: number) => {
    try {
      setLoading(true)
      const data = await api.get<Message[]>(`/chat/threads/${threadId}/messages`)
      setMessages(data)
    } catch {} finally { setLoading(false) }
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
          if (msg.sender_user_id !== user?.id) {
            playDing()
          }
          setMessages(prev => [...prev, msg])
          // Scroll to bottom
          setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
        } else if (data.type === 'message_pinned') {
          setMessages(prev => prev.map(m =>
            m.id === data.message_id ? { ...m, is_pinned: true } : m
          ))
        } else if (data.type === 'message_unpinned') {
          setMessages(prev => prev.map(m =>
            m.id === data.message_id ? { ...m, is_pinned: false } : m
          ))
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
    setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'auto' }), 100)
  }, [loadMessages])

  // ── Send message ──
  const sendMessage = useCallback(async () => {
    if (!input.trim() || !activeThread) return
    try {
      await api.post(`/chat/threads/${activeThread.id}/messages`, {
        content: input.trim(),
        reply_to_message_id: replyTo?.id || null,
      })
      setInput('')
      setReplyTo(null)
      inputRef.current?.focus()
    } catch {}
  }, [input, activeThread, replyTo])

  // ── Start DM ──
  const startDM = useCallback(async (targetUserId: number) => {
    try {
      const thread = await api.post<Thread>('/chat/threads/dm', { user_id: targetUserId })
      setShowNewChat(false)
      setSelectedUserIds([])
      await loadThreads()
      openThread(thread)
    } catch {}
  }, [loadThreads, openThread])

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
      await loadThreads()
      openThread(thread)
    } catch {}
  }, [newGroupTitle, selectedUserIds, loadThreads, openThread])

  // ── Open sales team thread ──
  const openSalesTeam = useCallback(async () => {
    try {
      const thread = await api.get<Thread>('/chat/threads/sales-team')
      setShowNewChat(false)
      await loadThreads()
      openThread(thread)
    } catch {}
  }, [loadThreads, openThread])

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
      await loadThreads()
      const refreshed = await api.get<Thread[]>('/chat/threads')
      const updated = refreshed.find(t => t.id === activeThread.id)
      if (updated) setActiveThread(updated)
    } catch {}
  }, [activeThread, loadThreads])

  // ── Remove member ──
  const removeMember = useCallback(async (userId: number) => {
    if (!activeThread) return
    try {
      await api.delete(`/chat/threads/${activeThread.id}/members/${userId}`)
      await loadThreads()
      const refreshed = await api.get<Thread[]>('/chat/threads')
      const updated = refreshed.find(t => t.id === activeThread.id)
      if (updated) setActiveThread(updated)
    } catch {}
  }, [activeThread, loadThreads])

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

            {isManager && (
              <div className={styles.newGroupSection}>
                <input
                  className={styles.chatInput}
                  placeholder="שם קבוצה חדשה..."
                  value={newGroupTitle}
                  onChange={e => setNewGroupTitle(e.target.value)}
                />
              </div>
            )}

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
                  {isManager && newGroupTitle.trim() ? (
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

            {isManager && newGroupTitle.trim() && selectedUserIds.length > 0 && (
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
                {isManager && m.user_id !== user.id && (
                  <button className={styles.removeMemberBtn} onClick={() => removeMember(m.user_id)}>
                    <Trash2 size={12} />
                  </button>
                )}
              </div>
            ))}
            {isManager && (
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
            )}
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
                {t.last_message?.created_at && (
                  <div className={styles.threadTime}>{formatTime(t.last_message.created_at)}</div>
                )}
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
              ) : messages.map(m => (
                <div
                  key={m.id}
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
                    <div className={styles.msgContent}>{m.content}</div>
                    <div className={styles.msgTime}>{formatTime(m.created_at)}</div>
                  </div>
                </div>
              ))}
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

            {/* Input */}
            <div className={styles.inputBar}>
              <input
                ref={inputRef}
                className={styles.chatInput}
                placeholder="הקלד הודעה..."
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }}
              />
              <button className={styles.sendBtn} onClick={sendMessage} disabled={!input.trim()}>
                <Send size={16} />
              </button>
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
        </div>
      )}
    </>
  )
}
