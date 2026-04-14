import { useState, useEffect, useCallback } from 'react'
import {
  Mail, ArrowDownLeft, ArrowUpRight, Paperclip, Search,
  ChevronRight, ChevronLeft, User, X, Download,
  RefreshCw,
} from 'lucide-react'
import { api } from '@/lib/api'
import s from '@/styles/shared.module.css'

/* ══════════════════════════════════════════════════════════════
   Types
   ══════════════════════════════════════════════════════════════ */
interface EmailItem {
  id: number
  gmail_id: string
  thread_id: string | null
  direction: string
  from_email: string
  from_name: string | null
  to_emails: Array<{ name?: string; email: string }> | null
  subject: string | null
  snippet: string | null
  has_attachment: boolean
  attachments_count: number
  folder: string | null
  lead_id: number | null
  lead_name: string | null
  matched_auto: boolean
  is_read: boolean
  email_date: string | null
  created_at: string
}

interface EmailDetail extends EmailItem {
  body_text: string | null
  body_html: string | null
  bcc_emails: Array<{ email: string }> | null
  label_ids: string[] | null
  message_id_header: string | null
  in_reply_to: string | null
  size_estimate: number | null
  history_id: string | null
  attachments: Array<{ id: number; filename: string; size_bytes: number; content_type: string }>
  thread_emails: Array<{
    id: number
    direction: string
    from_name: string | null
    from_email: string
    subject: string | null
    snippet: string | null
    email_date: string | null
    has_attachment: boolean
    is_current: boolean
  }>
}

interface LeadSearchResult {
  id: number
  full_name: string
  family_name?: string
  phone: string
  email?: string
}

/* ══════════════════════════════════════════════════════════════
   Helpers
   ══════════════════════════════════════════════════════════════ */
function formatDate(dateStr: string | null): string {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    const now = new Date()
    const isToday = d.toDateString() === now.toDateString()
    if (isToday) return d.toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' })
    const isThisYear = d.getFullYear() === now.getFullYear()
    if (isThisYear) return d.toLocaleDateString('he-IL', { day: 'numeric', month: 'short' })
    return d.toLocaleDateString('he-IL', { day: 'numeric', month: 'short', year: '2-digit' })
  } catch { return '' }
}

function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('he-IL', { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch { return '' }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function getRecipientDisplay(email: EmailItem): string {
  if (email.direction === 'outbound' && email.to_emails?.length) {
    const first = email.to_emails[0]
    return first.name || first.email
  }
  return email.from_name || email.from_email
}

/* ══════════════════════════════════════════════════════════════
   Main Component
   ══════════════════════════════════════════════════════════════ */
export function EmailInboxPage() {
  const [emails, setEmails] = useState<EmailItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [selectedEmail, setSelectedEmail] = useState<EmailDetail | null>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)

  // Filters
  const [direction, setDirection] = useState<string>('all')
  const [isRead, setIsRead] = useState<string>('all')
  const [unmatched, setUnmatched] = useState(false)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [page, setPage] = useState(0)
  const PAGE_SIZE = 50

  // Lead assignment
  const [showAssign, setShowAssign] = useState(false)
  const [leadSearch, setLeadSearch] = useState('')
  const [leadResults, setLeadResults] = useState<LeadSearchResult[]>([])
  const [assigningLead, setAssigningLead] = useState(false)

  const fetchEmails = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (direction && direction !== 'all') params.set('direction', direction)
      if (isRead === 'true') params.set('is_read', 'true')
      if (isRead === 'false') params.set('is_read', 'false')
      if (unmatched) params.set('unmatched', 'true')
      if (search) params.set('search', search)
      params.set('limit', String(PAGE_SIZE))
      params.set('offset', String(page * PAGE_SIZE))

      const data = await api.get<{ items: EmailItem[]; total: number }>(`/inbound-emails/?${params}`)
      setEmails(data.items)
      setTotal(data.total)
    } catch (err) {
      console.error('Failed to fetch emails:', err)
    } finally {
      setLoading(false)
    }
  }, [direction, isRead, unmatched, search, page])

  useEffect(() => { fetchEmails() }, [fetchEmails])

  const openEmail = async (emailId: number) => {
    setLoadingDetail(true)
    setShowAssign(false)
    try {
      const detail = await api.get<EmailDetail>(`/inbound-emails/${emailId}`)
      setSelectedEmail(detail)
      // Update list item to show as read
      setEmails(prev => prev.map(e => e.id === emailId ? { ...e, is_read: true } : e))
    } catch (err) {
      console.error('Failed to load email:', err)
    } finally {
      setLoadingDetail(false)
    }
  }

  const handleSearch = () => {
    setSearch(searchInput)
    setPage(0)
  }

  const handleAssignLead = async (leadId: number | null) => {
    if (!selectedEmail) return
    setAssigningLead(true)
    try {
      await api.patch(`/inbound-emails/${selectedEmail.id}/assign`, { lead_id: leadId })
      // Refresh detail
      const detail = await api.get<EmailDetail>(`/inbound-emails/${selectedEmail.id}`)
      setSelectedEmail(detail)
      // Update list
      setEmails(prev => prev.map(e => e.id === selectedEmail.id ? { ...e, lead_id: leadId, lead_name: detail.lead_name } : e))
      setShowAssign(false)
      setLeadSearch('')
      setLeadResults([])
    } catch (err) {
      console.error('Failed to assign lead:', err)
    } finally {
      setAssigningLead(false)
    }
  }

  const searchLeads = async (q: string) => {
    setLeadSearch(q)
    if (q.length < 2) { setLeadResults([]); return }
    try {
      const data = await api.get<{ items: LeadSearchResult[] }>(`/leads/?search=${encodeURIComponent(q)}&limit=10`)
      setLeadResults(data.items || [])
    } catch {
      setLeadResults([])
    }
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div>
      <div className={s['page-header']}>
        <h1 className={s['page-title']}>📧 תיבת מייל</h1>
        <button className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`} onClick={fetchEmails}>
          <RefreshCw size={14} /> רענן
        </button>
      </div>

      <div className={s.card} style={{ display: 'flex', height: 'calc(100vh - 140px)', overflow: 'hidden' }}>
        {/* ── Email List Panel ── */}
        <div style={{ width: selectedEmail ? '40%' : '100%', borderLeft: selectedEmail ? '1px solid var(--color-border-light)' : 'none', display: 'flex', flexDirection: 'column', transition: 'width 0.2s' }}>
          {/* Filters */}
          <div style={{ padding: '10px 12px', borderBottom: '1px solid var(--color-border-light)', display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
            <div style={{ display: 'flex', gap: 4 }}>
              <FilterBtn active={direction === 'all'} onClick={() => { setDirection('all'); setPage(0) }}>הכל</FilterBtn>
              <FilterBtn active={direction === 'inbound'} onClick={() => { setDirection('inbound'); setPage(0) }}>
                <ArrowDownLeft size={12} /> נכנסים
              </FilterBtn>
              <FilterBtn active={direction === 'outbound'} onClick={() => { setDirection('outbound'); setPage(0) }}>
                <ArrowUpRight size={12} /> יוצאים
              </FilterBtn>
            </div>
            <div style={{ width: 1, height: 20, background: 'var(--color-border-light)' }} />
            <div style={{ display: 'flex', gap: 4 }}>
              <FilterBtn active={isRead === 'false'} onClick={() => { setIsRead(isRead === 'false' ? 'all' : 'false'); setPage(0) }}>
                לא נקראו
              </FilterBtn>
              <FilterBtn active={unmatched} onClick={() => { setUnmatched(!unmatched); setPage(0) }}>
                לא משויכים
              </FilterBtn>
            </div>
            <div style={{ flex: 1 }} />
            <form onSubmit={e => { e.preventDefault(); handleSearch() }} style={{ display: 'flex', gap: 4 }}>
              <input
                type="text"
                value={searchInput}
                onChange={e => setSearchInput(e.target.value)}
                placeholder="חיפוש..."
                style={{ padding: '4px 8px', borderRadius: 4, border: '1px solid var(--color-border)', fontSize: 13, width: 160 }}
              />
              <button type="submit" className={`${s.btn} ${s['btn-ghost']} ${s['btn-sm']}`}>
                <Search size={14} />
              </button>
              {search && (
                <button type="button" className={`${s.btn} ${s['btn-ghost']} ${s['btn-sm']}`} onClick={() => { setSearch(''); setSearchInput(''); setPage(0) }}>
                  <X size={14} />
                </button>
              )}
            </form>
          </div>

          {/* Email List */}
          <div style={{ flex: 1, overflow: 'auto' }}>
            {loading ? (
              <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>טוען...</div>
            ) : emails.length === 0 ? (
              <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>
                <Mail size={40} style={{ opacity: 0.3, marginBottom: 8 }} />
                <div>אין מיילים להצגה</div>
              </div>
            ) : (
              emails.map(email => (
                <div
                  key={email.id}
                  onClick={() => openEmail(email.id)}
                  style={{
                    padding: '10px 14px',
                    borderBottom: '1px solid var(--color-border-light)',
                    cursor: 'pointer',
                    background: selectedEmail?.id === email.id ? 'var(--color-primary-light, #eff6ff)' : email.is_read ? 'transparent' : 'var(--color-bg-secondary, #f8fafc)',
                    display: 'flex',
                    gap: 10,
                    alignItems: 'flex-start',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => { if (selectedEmail?.id !== email.id) (e.currentTarget as HTMLElement).style.background = 'var(--color-bg-hover, #f1f5f9)' }}
                  onMouseLeave={e => { if (selectedEmail?.id !== email.id) (e.currentTarget as HTMLElement).style.background = email.is_read ? 'transparent' : 'var(--color-bg-secondary, #f8fafc)' }}
                >
                  {/* Direction icon */}
                  <div style={{ marginTop: 2, flexShrink: 0 }}>
                    {email.direction === 'inbound' ? (
                      <ArrowDownLeft size={16} style={{ color: 'var(--color-primary, #2563eb)' }} />
                    ) : (
                      <ArrowUpRight size={16} style={{ color: 'var(--color-success, #16a34a)' }} />
                    )}
                  </div>

                  {/* Content */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontWeight: email.is_read ? 400 : 600, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {getRecipientDisplay(email)}
                      </span>
                      <span style={{ fontSize: 11, color: 'var(--color-text-muted)', flexShrink: 0 }}>
                        {formatDate(email.email_date)}
                      </span>
                    </div>
                    <div style={{ fontSize: 13, fontWeight: email.is_read ? 400 : 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 2 }}>
                      {email.subject || '(ללא נושא)'}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--color-text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 2 }}>
                      {email.snippet || ''}
                    </div>
                    {/* Tags row */}
                    <div style={{ display: 'flex', gap: 4, marginTop: 4, flexWrap: 'wrap' }}>
                      {email.has_attachment && (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 2, fontSize: 10, padding: '1px 5px', background: 'var(--color-bg-secondary)', borderRadius: 3, color: 'var(--color-text-secondary)' }}>
                          <Paperclip size={10} /> {email.attachments_count || ''}
                        </span>
                      )}
                      {email.lead_name && (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 2, fontSize: 10, padding: '1px 5px', background: 'var(--color-primary-light, #eff6ff)', borderRadius: 3, color: 'var(--color-primary, #2563eb)' }}>
                          <User size={10} /> {email.lead_name}
                        </span>
                      )}
                      {!email.is_read && (
                        <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-primary, #2563eb)', flexShrink: 0, marginTop: 2 }} />
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ padding: '8px 12px', borderTop: '1px solid var(--color-border-light)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12, color: 'var(--color-text-muted)' }}>
              <span>{total} מיילים</span>
              <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                <button disabled={page === 0} onClick={() => setPage(p => p - 1)} className={`${s.btn} ${s['btn-ghost']} ${s['btn-sm']}`}>
                  <ChevronRight size={14} />
                </button>
                <span>{page + 1} / {totalPages}</span>
                <button disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)} className={`${s.btn} ${s['btn-ghost']} ${s['btn-sm']}`}>
                  <ChevronLeft size={14} />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* ── Email Detail Panel ── */}
        {selectedEmail && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            {loadingDetail ? (
              <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>טוען...</div>
            ) : (
              <>
                {/* Header */}
                <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--color-border-light)', flexShrink: 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>{selectedEmail.subject || '(ללא נושא)'}</h3>
                      <div style={{ marginTop: 6, fontSize: 13, color: 'var(--color-text-secondary)' }}>
                        <div>
                          <strong>מאת:</strong> {selectedEmail.from_name && `${selectedEmail.from_name} `}
                          <span dir="ltr" style={{ color: 'var(--color-text-muted)' }}>&lt;{selectedEmail.from_email}&gt;</span>
                        </div>
                        <div>
                          <strong>אל:</strong>{' '}
                          {selectedEmail.to_emails?.map((t, i) => (
                            <span key={i}>
                              {t.name && `${t.name} `}
                              <span dir="ltr" style={{ color: 'var(--color-text-muted)' }}>&lt;{t.email}&gt;</span>
                              {i < (selectedEmail.to_emails?.length || 0) - 1 && ', '}
                            </span>
                          ))}
                        </div>
                        <div>
                          <strong>תאריך:</strong> {formatDateTime(selectedEmail.email_date)}
                          <span style={{ marginRight: 8, padding: '1px 6px', borderRadius: 4, fontSize: 11, background: selectedEmail.direction === 'inbound' ? 'var(--color-primary-light, #eff6ff)' : 'var(--color-success-light, #f0fdf4)', color: selectedEmail.direction === 'inbound' ? 'var(--color-primary)' : 'var(--color-success)' }}>
                            {selectedEmail.direction === 'inbound' ? '📥 נכנס' : '📤 יוצא'}
                          </span>
                        </div>
                      </div>
                    </div>
                    <button className={`${s.btn} ${s['btn-ghost']} ${s['btn-sm']}`} onClick={() => setSelectedEmail(null)}>
                      <X size={16} />
                    </button>
                  </div>

                  {/* Lead assignment */}
                  <div style={{ marginTop: 8, padding: '8px 10px', background: 'var(--color-bg-secondary, #f8fafc)', borderRadius: 6, fontSize: 13 }}>
                    {selectedEmail.lead_id ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <User size={14} style={{ color: 'var(--color-primary)' }} />
                        <span>משויך ל: <strong>{selectedEmail.lead_name}</strong></span>
                        <button
                          className={`${s.btn} ${s['btn-ghost']} ${s['btn-sm']}`}
                          style={{ marginRight: 'auto', fontSize: 11 }}
                          onClick={() => handleAssignLead(null)}
                          disabled={assigningLead}
                        >
                          הסר שיוך
                        </button>
                      </div>
                    ) : (
                      <div>
                        {!showAssign ? (
                          <button className={`${s.btn} ${s['btn-secondary']} ${s['btn-sm']}`} onClick={() => setShowAssign(true)}>
                            <User size={12} /> שייך לליד
                          </button>
                        ) : (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                            <div style={{ display: 'flex', gap: 4 }}>
                              <input
                                type="text"
                                value={leadSearch}
                                onChange={e => searchLeads(e.target.value)}
                                placeholder="חפש ליד לפי שם, טלפון, מייל..."
                                autoFocus
                                style={{ flex: 1, padding: '4px 8px', borderRadius: 4, border: '1px solid var(--color-border)', fontSize: 13 }}
                              />
                              <button className={`${s.btn} ${s['btn-ghost']} ${s['btn-sm']}`} onClick={() => { setShowAssign(false); setLeadSearch(''); setLeadResults([]) }}>
                                <X size={14} />
                              </button>
                            </div>
                            {leadResults.length > 0 && (
                              <div style={{ maxHeight: 150, overflow: 'auto', border: '1px solid var(--color-border)', borderRadius: 4, background: 'white' }}>
                                {leadResults.map(lead => (
                                  <div
                                    key={lead.id}
                                    onClick={() => handleAssignLead(lead.id)}
                                    style={{ padding: '6px 10px', cursor: 'pointer', borderBottom: '1px solid var(--color-border-light)', fontSize: 12, display: 'flex', justifyContent: 'space-between' }}
                                    onMouseEnter={e => (e.currentTarget.style.background = 'var(--color-bg-hover, #f1f5f9)')}
                                    onMouseLeave={e => (e.currentTarget.style.background = 'white')}
                                  >
                                    <span>{lead.full_name} {lead.family_name || ''}</span>
                                    <span style={{ color: 'var(--color-text-muted)' }}>{lead.phone}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Thread indicator */}
                {selectedEmail.thread_emails.length > 1 && (
                  <div style={{ padding: '8px 16px', borderBottom: '1px solid var(--color-border-light)', background: 'var(--color-bg-secondary, #f8fafc)', fontSize: 12 }}>
                    <div style={{ fontWeight: 600, marginBottom: 4 }}>שרשור ({selectedEmail.thread_emails.length} הודעות)</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      {selectedEmail.thread_emails.map(te => (
                        <div
                          key={te.id}
                          onClick={() => { if (!te.is_current) openEmail(te.id) }}
                          style={{
                            display: 'flex', gap: 6, alignItems: 'center', padding: '3px 6px', borderRadius: 4,
                            cursor: te.is_current ? 'default' : 'pointer',
                            background: te.is_current ? 'var(--color-primary-light, #eff6ff)' : 'transparent',
                            fontWeight: te.is_current ? 600 : 400,
                          }}
                        >
                          {te.direction === 'inbound' ? <ArrowDownLeft size={10} /> : <ArrowUpRight size={10} />}
                          <span>{te.from_name || te.from_email}</span>
                          <span style={{ color: 'var(--color-text-muted)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            — {te.subject || te.snippet || ''}
                          </span>
                          <span style={{ color: 'var(--color-text-muted)', flexShrink: 0 }}>{formatDate(te.email_date)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Attachments */}
                {selectedEmail.attachments.length > 0 && (
                  <div style={{ padding: '8px 16px', borderBottom: '1px solid var(--color-border-light)', fontSize: 12 }}>
                    <div style={{ fontWeight: 600, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                      <Paperclip size={12} /> קבצים מצורפים ({selectedEmail.attachments.length})
                    </div>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {selectedEmail.attachments.map(att => (
                        <div key={att.id} style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '4px 8px', background: 'var(--color-bg-secondary)', borderRadius: 4, border: '1px solid var(--color-border-light)' }}>
                          <Paperclip size={10} />
                          <span>{att.filename}</span>
                          <span style={{ color: 'var(--color-text-muted)' }}>({formatFileSize(att.size_bytes)})</span>
                          <a href={`/api/files/${att.id}/download`} target="_blank" rel="noreferrer" style={{ color: 'var(--color-primary)', display: 'flex' }}>
                            <Download size={12} />
                          </a>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Email Body */}
                <div style={{ flex: 1, overflow: 'auto', padding: 0 }}>
                  {selectedEmail.body_html ? (
                    <iframe
                      srcDoc={`<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8"><style>body{font-family:Arial,sans-serif;font-size:14px;padding:16px;margin:0;direction:rtl;color:#333;}img{max-width:100%;height:auto;}a{color:#2563eb;}</style></head><body>${selectedEmail.body_html}</body></html>`}
                      style={{ width: '100%', height: '100%', border: 'none' }}
                      sandbox="allow-same-origin"
                      title="Email body"
                    />
                  ) : (
                    <pre style={{ padding: 16, margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'inherit', fontSize: 14, direction: 'rtl' }}>
                      {selectedEmail.body_text || '(ללא תוכן)'}
                    </pre>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

/* ── Filter Button ── */
function FilterBtn({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '4px 10px',
        borderRadius: 4,
        border: '1px solid',
        borderColor: active ? 'var(--color-primary, #2563eb)' : 'var(--color-border)',
        background: active ? 'var(--color-primary-light, #eff6ff)' : 'transparent',
        color: active ? 'var(--color-primary, #2563eb)' : 'var(--color-text-secondary)',
        fontSize: 12,
        fontWeight: active ? 600 : 400,
        cursor: 'pointer',
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
      }}
    >
      {children}
    </button>
  )
}
