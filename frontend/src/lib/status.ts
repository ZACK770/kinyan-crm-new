/* ============================================================
   Status label mapping & badge colors
   ============================================================ */

type BadgeColor = 'blue' | 'green' | 'yellow' | 'red' | 'gray' | 'orange' | 'purple' | 'teal'

interface StatusDef { label: string; color: BadgeColor }

// Lead statuses — DB stores Hebrew values
const leadStatus: Record<string, StatusDef> = {
  // Primary keys (Hebrew — as stored in DB)
  'ליד חדש':                { label: 'ליד חדש', color: 'blue' },
  'ליד בתהליך':             { label: 'ליד בתהליך', color: 'purple' },
  'חיוג ראשון':             { label: 'חיוג ראשון', color: 'yellow' },
  'ליד ישן':                { label: 'ליד ישן', color: 'gray' },
  'נסלק':                   { label: 'נסלק', color: 'green' },
  'תלמיד פעיל':             { label: 'תלמיד פעיל', color: 'teal' },
  'ליד סגור - לקוח':       { label: 'נסלק', color: 'green' },
  'ליד סגור - לא רלוונטי': { label: 'לא רלוונטי', color: 'red' },
  'לא רלוונטי':             { label: 'לא רלוונטי', color: 'red' },
  'converted':              { label: 'הומר לתלמיד', color: 'green' },
  // Legacy English keys (for backward compatibility)
  'במעקב':       { label: 'במעקב', color: 'orange' },
  'מתעניין':     { label: 'מתעניין', color: 'teal' },
  new:           { label: 'ליד חדש', color: 'blue' },
  first_call:    { label: 'חיוג ראשון', color: 'yellow' },
  follow_up:     { label: 'במעקב', color: 'orange' },
  interested:    { label: 'מתעניין', color: 'teal' },
  payment_done:  { label: 'נסלק', color: 'green' },
  not_relevant:  { label: 'לא רלוונטי', color: 'gray' },
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
  paid:     { label: 'שולם', color: 'green' },
  'שולם':  { label: 'שולם', color: 'green' },
  partial:  { label: 'חלקי', color: 'yellow' },
  unpaid:   { label: 'טרם שולם', color: 'red' },
  pending:  { label: 'ממתין', color: 'yellow' },
  'ממתין': { label: 'ממתין', color: 'yellow' },
  failed:   { label: 'נכשל', color: 'red' },
  refunded: { label: 'הוחזר', color: 'gray' },
}

const taskStatus: Record<string, StatusDef> = {
  // Hebrew keys (as stored in DB)
  'חדש':     { label: 'חדש', color: 'blue' },
  'בטיפול':  { label: 'בטיפול', color: 'yellow' },
  'הושלם':   { label: 'הושלם', color: 'green' },
  'בוטל':    { label: 'בוטל', color: 'gray' },
  // Legacy English keys
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
  'ייבוא ממערכת ישנה': 'ייבוא ממערכת ישנה',
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
