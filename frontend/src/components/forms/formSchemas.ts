/**
 * Entity Form configuration and schema definitions
 * Single source of truth for all entity forms across the app
 */

// Field types
export type FieldType = 'text' | 'email' | 'tel' | 'number' | 'select' | 'textarea' | 'date' | 'boolean' | 'entity-select' | 'currency'

// Entity reference types for linked dropdowns
export type EntityRef = 'courses' | 'campaigns' | 'salespeople'

// Route paths for creating new entities (opened in new tab via '+' button)
export const entityRefRoutes: Record<EntityRef, string> = {
  courses: '/courses',
  campaigns: '/campaigns',
  salespeople: '/leads',  // Salespeople managed via Leads page
}

export interface FieldOption {
  value: string
  label: string
}

export interface FormField {
  key: string
  label: string
  type: FieldType
  required?: boolean
  placeholder?: string
  options?: FieldOption[]               // For static select
  entityRef?: EntityRef                 // For entity-linked select
  dir?: 'ltr' | 'rtl'
  halfWidth?: boolean                   // Two fields per row
  showPriceFrom?: string                // Key of entity-select to show price from
  dependsOn?: string                    // Show only if this field has a value
}

export interface FormSection {
  title?: string
  fields: FormField[]
}

export interface EntityFormSchema {
  createTitle: string
  editTitle: string
  sections: FormSection[]
  submitLabel?: string
  editSubmitLabel?: string
}

// ============================================================
// Status Options (reused across entities)
// ============================================================
const leadStatusOptions: FieldOption[] = [
  { value: 'new', label: 'חדש' },
  { value: 'contacted', label: 'נוצר קשר' },
  { value: 'interested', label: 'מעוניין' },
  { value: 'converted', label: 'הומר' },
  { value: 'irrelevant', label: 'לא רלוונטי' },
]

const sourceTypeOptions: FieldOption[] = [
  { value: 'yemot', label: 'ימות המשיח' },
  { value: 'elementor', label: 'אלמנטור' },
  { value: 'manual', label: 'ידני' },
  { value: 'referral', label: 'הפניה' },
  { value: 'other', label: 'אחר' },
]

const studentStatusOptions: FieldOption[] = [
  { value: 'active', label: 'פעיל' },
  { value: 'paused', label: 'מושהה' },
  { value: 'completed', label: 'סיים' },
  { value: 'left', label: 'עזב' },
]

const paymentStatusOptions: FieldOption[] = [
  { value: 'paid', label: 'שולם' },
  { value: 'partial', label: 'חלקי' },
  { value: 'pending', label: 'ממתין' },
  { value: 'overdue', label: 'באיחור' },
]

// ============================================================
// Entity Form Schemas
// ============================================================

export const leadFormSchema: EntityFormSchema = {
  createTitle: 'ליד חדש',
  editTitle: 'עריכת ליד',
  sections: [
    {
      title: 'פרטים אישיים',
      fields: [
        { key: 'full_name', label: 'שם פרטי', type: 'text', required: true, halfWidth: true },
        { key: 'family_name', label: 'שם משפחה', type: 'text', halfWidth: true },
        { key: 'phone', label: 'טלפון', type: 'tel', required: true, dir: 'ltr', halfWidth: true },
        { key: 'phone2', label: 'טלפון נוסף', type: 'tel', dir: 'ltr', halfWidth: true },
        { key: 'email', label: 'אימייל', type: 'email', dir: 'ltr', halfWidth: true },
        { key: 'city', label: 'עיר', type: 'text', halfWidth: true },
      ],
    },
    {
      title: 'מקור וקישורים',
      fields: [
        { key: 'source_type', label: 'מקור הגעה', type: 'select', options: sourceTypeOptions, halfWidth: true },
        { key: 'campaign_id', label: 'קמפיין', type: 'entity-select', entityRef: 'campaigns', halfWidth: true },
        { key: 'course_id', label: 'קורס מבוקש', type: 'entity-select', entityRef: 'courses', halfWidth: true },
        { key: 'salesperson_id', label: 'איש מכירות', type: 'entity-select', entityRef: 'salespeople', halfWidth: true },
      ],
    },
    {
      title: 'סטטוס',
      fields: [
        { key: 'status', label: 'סטטוס', type: 'select', options: leadStatusOptions, halfWidth: true },
        { key: 'notes', label: 'הערות', type: 'textarea' },
      ],
    },
  ],
  submitLabel: 'צור ליד',
  editSubmitLabel: 'עדכן',
}

export const studentFormSchema: EntityFormSchema = {
  createTitle: 'תלמיד חדש',
  editTitle: 'עריכת תלמיד',
  sections: [
    {
      title: 'פרטים אישיים',
      fields: [
        { key: 'full_name', label: 'שם מלא', type: 'text', required: true, halfWidth: true },
        { key: 'id_number', label: 'ת.ז.', type: 'text', dir: 'ltr', halfWidth: true },
        { key: 'phone', label: 'טלפון', type: 'tel', required: true, dir: 'ltr', halfWidth: true },
        { key: 'phone2', label: 'טלפון נוסף', type: 'tel', dir: 'ltr', halfWidth: true },
        { key: 'email', label: 'אימייל', type: 'email', dir: 'ltr', halfWidth: true },
        { key: 'city', label: 'עיר', type: 'text', halfWidth: true },
        { key: 'address', label: 'כתובת', type: 'text' },
      ],
    },
    {
      title: 'סטטוס ותשלום',
      fields: [
        { key: 'status', label: 'סטטוס', type: 'select', options: studentStatusOptions, halfWidth: true },
        { key: 'payment_status', label: 'סטטוס תשלום', type: 'select', options: paymentStatusOptions, halfWidth: true },
        { key: 'total_price', label: 'סה"כ מחיר', type: 'currency', halfWidth: true },
        { key: 'notes', label: 'הערות', type: 'textarea' },
      ],
    },
  ],
  submitLabel: 'צור תלמיד',
  editSubmitLabel: 'עדכן',
}

export const courseFormSchema: EntityFormSchema = {
  createTitle: 'קורס חדש',
  editTitle: 'עריכת קורס',
  sections: [
    {
      fields: [
        { key: 'name', label: 'שם הקורס', type: 'text', required: true },
        { key: 'description', label: 'תיאור', type: 'textarea' },
        { key: 'semester', label: 'סמסטר', type: 'text', halfWidth: true },
        { key: 'total_sessions', label: 'סה"כ שיעורים', type: 'number', halfWidth: true },
        { key: 'start_date', label: 'תאריך התחלה', type: 'date', halfWidth: true },
        { key: 'end_date', label: 'תאריך סיום', type: 'date', halfWidth: true },
        { key: 'is_active', label: 'פעיל', type: 'boolean' },
      ],
    },
  ],
  submitLabel: 'צור קורס',
  editSubmitLabel: 'עדכן',
}

export const campaignFormSchema: EntityFormSchema = {
  createTitle: 'קמפיין חדש',
  editTitle: 'עריכת קמפיין',
  sections: [
    {
      fields: [
        { key: 'name', label: 'שם הקמפיין', type: 'text', required: true },
        { key: 'course_id', label: 'קורס', type: 'entity-select', entityRef: 'courses', halfWidth: true },
        { key: 'platforms', label: 'פלטפורמות', type: 'text', placeholder: 'פייסבוק, גוגל...', halfWidth: true },
        { key: 'landing_page_url', label: 'דף נחיתה', type: 'text', dir: 'ltr' },
        { key: 'start_date', label: 'תאריך התחלה', type: 'date', halfWidth: true },
        { key: 'end_date', label: 'תאריך סיום', type: 'date', halfWidth: true },
        { key: 'description', label: 'תיאור', type: 'textarea' },
        { key: 'is_active', label: 'פעיל', type: 'boolean' },
      ],
    },
  ],
  submitLabel: 'צור קמפיין',
  editSubmitLabel: 'עדכן',
}

export const inquiryFormSchema: EntityFormSchema = {
  createTitle: 'פניה חדשה',
  editTitle: 'עריכת פניה',
  sections: [
    {
      fields: [
        { key: 'subject', label: 'נושא', type: 'text', required: true },
        { key: 'inquiry_type', label: 'סוג פניה', type: 'select', options: [
          { value: 'email', label: 'מייל' },
          { value: 'phone', label: 'טלפון' },
          { value: 'voicemail', label: 'דואר קולי' },
          { value: 'other', label: 'אחר' },
        ], halfWidth: true },
        { key: 'phone', label: 'טלפון פונה', type: 'tel', dir: 'ltr', halfWidth: true },
        { key: 'status', label: 'סטטוס', type: 'select', options: [
          { value: 'new', label: 'חדש' },
          { value: 'in_progress', label: 'בטיפול' },
          { value: 'resolved', label: 'טופל' },
          { value: 'closed', label: 'סגור' },
        ], halfWidth: true },
        { key: 'notes', label: 'הערות', type: 'textarea' },
      ],
    },
  ],
  submitLabel: 'צור פניה',
  editSubmitLabel: 'עדכן',
}

export const paymentFormSchema: EntityFormSchema = {
  createTitle: 'תשלום חדש',
  editTitle: 'עריכת תשלום',
  sections: [
    {
      fields: [
        { key: 'amount', label: 'סכום', type: 'currency', required: true, halfWidth: true },
        { key: 'payment_date', label: 'תאריך תשלום', type: 'date', halfWidth: true },
        { key: 'payment_method', label: 'צורת תשלום', type: 'select', options: [
          { value: 'credit', label: 'אשראי' },
          { value: 'bank', label: 'העברה בנקאית' },
          { value: 'cash', label: 'מזומן' },
          { value: 'check', label: 'צ\'ק' },
        ], halfWidth: true },
        { key: 'status', label: 'סטטוס', type: 'select', options: paymentStatusOptions, halfWidth: true },
        { key: 'reference', label: 'אסמכתא', type: 'text', dir: 'ltr' },
      ],
    },
  ],
  submitLabel: 'הוסף תשלום',
  editSubmitLabel: 'עדכן',
}

export const expenseFormSchema: EntityFormSchema = {
  createTitle: 'הוצאה חדשה',
  editTitle: 'עריכת הוצאה',
  sections: [
    {
      fields: [
        { key: 'vendor', label: 'ספק', type: 'text', required: true, halfWidth: true },
        { key: 'amount', label: 'סכום', type: 'currency', required: true, halfWidth: true },
        { key: 'expense_date', label: 'תאריך', type: 'date', halfWidth: true },
        { key: 'payment_method', label: 'צורת תשלום', type: 'select', options: [
          { value: 'credit', label: 'אשראי' },
          { value: 'bank', label: 'העברה' },
          { value: 'cash', label: 'מזומן' },
        ], halfWidth: true },
        { key: 'course_id', label: 'קורס קשור', type: 'entity-select', entityRef: 'courses', halfWidth: true },
        { key: 'campaign_id', label: 'קמפיין קשור', type: 'entity-select', entityRef: 'campaigns', halfWidth: true },
        { key: 'description', label: 'פירוט', type: 'textarea' },
      ],
    },
  ],
  submitLabel: 'הוסף הוצאה',
  editSubmitLabel: 'עדכן',
}

// Map entity names to schemas
export const formSchemas: Record<string, EntityFormSchema> = {
  leads: leadFormSchema,
  students: studentFormSchema,
  courses: courseFormSchema,
  campaigns: campaignFormSchema,
  inquiries: inquiryFormSchema,
  payments: paymentFormSchema,
  expenses: expenseFormSchema,
}

// Default values by type
export function getDefaultValue(type: FieldType): unknown {
  switch (type) {
    case 'boolean': return false
    case 'number': 
    case 'currency': return ''
    default: return ''
  }
}

// Build initial form state from schema
export function buildInitialState(schema: EntityFormSchema, initial?: Record<string, unknown>): Record<string, unknown> {
  const state: Record<string, unknown> = {}
  for (const section of schema.sections) {
    for (const field of section.fields) {
      state[field.key] = initial?.[field.key] ?? getDefaultValue(field.type)
    }
  }
  return state
}
