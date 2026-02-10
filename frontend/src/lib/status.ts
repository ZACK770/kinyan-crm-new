/* ============================================================
   Status label mapping & badge colors
   ============================================================ */

type BadgeColor = 'blue' | 'green' | 'yellow' | 'red' | 'gray' | 'orange'

interface StatusDef { label: string; color: BadgeColor }

// Lead statuses per ENTITIES_SPEC.md
const leadStatus: Record<string, StatusDef> = {
  new:           { label: 'ליד חדש', color: 'blue' },
  first_call:    { label: 'חיוג ראשון', color: 'yellow' },
  follow_up:     { label: 'במעקב', color: 'yellow' },
  interested:    { label: 'מתעניין', color: 'orange' },
  payment_done:  { label: 'נסלק', color: 'green' },
  converted:     { label: 'ליד סגור-לקוח', color: 'green' },
  not_relevant:  { label: 'ליד סגור-לא רלוונטי', color: 'gray' },
  // Legacy mappings
  contacted:     { label: 'נוצר קשר', color: 'yellow' },
  irrelevant:    { label: 'לא רלוונטי', color: 'gray' },
}

// Interaction types
const interactionType: Record<string, StatusDef> = {
  call:          { label: 'שיחה', color: 'blue' },
  ivr_call:      { label: 'IVR', color: 'yellow' },
  outbound_call: { label: 'שיחה יוצאת', color: 'blue' },
  sms:           { label: 'SMS', color: 'gray' },
  whatsapp:      { label: 'וואטסאפ', color: 'green' },
  email:         { label: 'אימייל', color: 'orange' },
  website_form:  { label: 'טופס אתר', color: 'yellow' },
  meeting:       { label: 'פגישה', color: 'green' },
  note:          { label: 'הערה', color: 'gray' },
  generic:       { label: 'כללי', color: 'gray' },
}

// Call statuses
const callStatus: Record<string, StatusDef> = {
  answered:  { label: 'ענה', color: 'green' },
  no_answer: { label: 'לא ענה', color: 'red' },
  busy:      { label: 'תפוס', color: 'yellow' },
  voicemail: { label: 'תא קולי', color: 'gray' },
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
  leads: leadStatus,
  student: studentStatus,
  payment: paymentStatus,
  task: taskStatus,
  inquiry: inquiryStatus,
  collection: collectionStatus,
  commitment: commitmentStatus,
  enrollment: enrollmentStatus,
  interaction_type: interactionType,
  call_status: callStatus,
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
