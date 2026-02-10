/* ============================================================
   Status label mapping & badge colors
   ============================================================ */

type BadgeColor = 'blue' | 'green' | 'yellow' | 'red' | 'gray' | 'orange'

interface StatusDef { label: string; color: BadgeColor }

const leadStatus: Record<string, StatusDef> = {
  new:        { label: 'חדש', color: 'blue' },
  contacted:  { label: 'נוצר קשר', color: 'yellow' },
  interested: { label: 'מעוניין', color: 'orange' },
  converted:  { label: 'הומר', color: 'green' },
  irrelevant: { label: 'לא רלוונטי', color: 'gray' },
}

const studentStatus: Record<string, StatusDef> = {
  active:    { label: 'פעיל', color: 'green' },
  inactive:  { label: 'לא פעיל', color: 'gray' },
  graduated: { label: 'סיים', color: 'blue' },
}

const paymentStatus: Record<string, StatusDef> = {
  paid:    { label: 'שולם', color: 'green' },
  partial: { label: 'חלקי', color: 'yellow' },
  unpaid:  { label: 'טרם שולם', color: 'red' },
  pending: { label: 'ממתין', color: 'yellow' },
}

const taskStatus: Record<string, StatusDef> = {
  new:         { label: 'חדש', color: 'blue' },
  in_progress: { label: 'בביצוע', color: 'yellow' },
  completed:   { label: 'הושלם', color: 'green' },
  cancelled:   { label: 'בוטל', color: 'gray' },
}

const inquiryStatus: Record<string, StatusDef> = {
  new:         { label: 'חדש', color: 'blue' },
  in_progress: { label: 'בטיפול', color: 'yellow' },
  closed:      { label: 'סגור', color: 'green' },
}

const collectionStatus: Record<string, StatusDef> = {
  pending:   { label: 'ממתין', color: 'yellow' },
  collected: { label: 'נגבה', color: 'green' },
  overdue:   { label: 'באיחור', color: 'red' },
  failed:    { label: 'נכשל', color: 'gray' },
}

const commitmentStatus: Record<string, StatusDef> = {
  active:    { label: 'פעיל', color: 'green' },
  completed: { label: 'הושלם', color: 'blue' },
  cancelled: { label: 'בוטל', color: 'gray' },
}

const enrollmentStatus: Record<string, StatusDef> = {
  active:    { label: 'פעיל', color: 'green' },
  completed: { label: 'הושלם', color: 'blue' },
  dropped:   { label: 'הפסיק', color: 'red' },
  paused:    { label: 'מושהה', color: 'yellow' },
}

const maps: Record<string, Record<string, StatusDef>> = {
  lead: leadStatus,
  student: studentStatus,
  payment: paymentStatus,
  task: taskStatus,
  inquiry: inquiryStatus,
  collection: collectionStatus,
  commitment: commitmentStatus,
  enrollment: enrollmentStatus,
}

export function getStatus(entity: string, value?: string): StatusDef {
  if (!value) return { label: '—', color: 'gray' }
  return maps[entity]?.[value] ?? { label: value, color: 'gray' }
}

const sourceTypes: Record<string, string> = {
  yemot:     'ימות המשיח',
  elementor: 'אלמנטור',
  manual:    'ידני',
  import:    'ייבוא',
  referral:  'הפניה',
  other:     'אחר',
}

export function getSourceLabel(value?: string): string {
  if (!value) return '—'
  return sourceTypes[value] ?? value
}

const priorityLabels: Record<number, StatusDef> = {
  1: { label: 'נמוך', color: 'gray' },
  2: { label: 'רגיל', color: 'blue' },
  3: { label: 'גבוה', color: 'orange' },
  4: { label: 'דחוף', color: 'red' },
}

export function getPriority(value?: number): StatusDef {
  if (!value) return { label: 'רגיל', color: 'blue' }
  return priorityLabels[value] ?? { label: String(value), color: 'gray' }
}

export function formatDate(iso?: string): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleDateString('he-IL', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
    })
  } catch {
    return iso
  }
}

export function formatDateTime(iso?: string): string {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    return `${d.toLocaleDateString('he-IL')} ${d.toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' })}`
  } catch {
    return iso
  }
}

export function formatCurrency(amount?: number): string {
  if (amount == null) return '—'
  return `₪${amount.toLocaleString('he-IL')}`
}
