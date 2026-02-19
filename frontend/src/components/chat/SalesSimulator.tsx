import { useState, useRef, useEffect, useCallback, type FC } from 'react'
import { Bot, X, Send, RotateCcw } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { api } from '@/lib/api'
import styles from './SalesSimulator.module.css'
import clsx from 'clsx'

interface SimMessage {
  role: 'salesperson' | 'customer'
  content: string
}

export const SalesSimulator: FC = () => {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<SimMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, loading])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  const sendMessage = useCallback(async () => {
    if (!input.trim() || loading) return
    setError(null)

    const userMsg: SimMessage = { role: 'salesperson', content: input.trim() }
    const updatedMessages = [...messages, userMsg]
    setMessages(updatedMessages)
    setInput('')
    setLoading(true)

    try {
      const res = await api.post<{ response: string }>('/sales-simulator/chat', {
        messages: updatedMessages,
      })
      setMessages(prev => [...prev, { role: 'customer', content: res.response }])
    } catch (err: any) {
      setError(err?.message || 'שגיאה בתקשורת עם השרת')
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }, [input, messages, loading])

  const resetChat = useCallback(() => {
    setMessages([])
    setError(null)
    setInput('')
  }, [])

  if (!user || user.permission_level < 10) return null

  return (
    <>
      {/* FAB Button — left side */}
      <button
        className={clsx(styles.fab, open && styles.fabHidden)}
        onClick={() => setOpen(true)}
        aria-label="סימולטור מכירות"
        title="סימולטור מכירות"
      >
        <Bot size={22} />
      </button>

      {/* Drawer */}
      <div className={clsx(styles.drawer, open && styles.drawerOpen)}>
        {/* Header */}
        <div className={styles.drawerHeader}>
          <div className={styles.headerTitle}>
            <Bot size={16} />
            <span>שיחה עם לקוח (סימולטור)</span>
          </div>
          <div className={styles.headerActions}>
            <button className={styles.resetBtn} onClick={resetChat} title="התחל מחדש">
              <RotateCcw size={14} />
            </button>
          </div>
          <button className={styles.closeBtn} onClick={() => setOpen(false)}>
            <X size={16} />
          </button>
        </div>

        {/* Messages */}
        <div className={styles.messageList}>
          {messages.length === 0 && (
            <div className={styles.welcomeMessage}>
              <h3>סימולטור לקוח — "דוד כהן"</h3>
              <p>
                אתה איש מכירות של קניין הוראה.<br />
                דוד כהן עשה חידון באינטרנט וקיבל ציון בינוני.<br />
                אתה מתקשר לבשר לו שזכה בהטבה.<br /><br />
                <strong>התחל את השיחה — כתוב את המשפט הפותח שלך.</strong>
              </p>
            </div>
          )}

          {messages.map((m, i) => (
            <div
              key={i}
              className={clsx(
                styles.message,
                m.role === 'salesperson' ? styles.messageSalesperson : styles.messageCustomer,
              )}
            >
              <div className={styles.msgBubble}>
                <div className={styles.msgSender}>
                  {m.role === 'salesperson' ? 'אתה (איש מכירות)' : 'דוד כהן (לקוח)'}
                </div>
                <div className={styles.msgContent}>{m.content}</div>
              </div>
            </div>
          ))}

          {loading && (
            <div className={styles.typingIndicator}>
              <div className={styles.typingDot} />
              <div className={styles.typingDot} />
              <div className={styles.typingDot} />
            </div>
          )}

          {error && <div className={styles.errorMsg}>{error}</div>}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className={styles.inputBar}>
          <input
            ref={inputRef}
            className={styles.chatInput}
            placeholder="הקלד את המשפט שלך..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                sendMessage()
              }
            }}
            disabled={loading}
          />
          <button
            className={styles.sendBtn}
            onClick={sendMessage}
            disabled={!input.trim() || loading}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </>
  )
}
