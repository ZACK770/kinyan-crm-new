/* ============================================================
   Shared TypeScript types — mirrors backend models
   ============================================================ */

export interface Lead {
  id: number
  full_name: string
  family_name?: string
  phone: string
  phone2?: string
  email?: string
  address?: string
  city?: string
  id_number?: string
  notes?: string
  source_type?: string
  source_name?: string
  campaign_name?: string
  source_message?: string
  source_details?: string
  arrival_date?: string
  salesperson_id?: number
  status: string
  first_payment: boolean
  first_lesson: boolean
  approved_terms: boolean
  conversion_date?: string
  student_id?: number
  campaign_id?: number
  course_id?: number  // Interested course
  requested_course?: string  // Free text - what the lead asked for
  interested_track_id?: number
  active_task_id?: number
  // Payment tracking (selected course for sale)
  selected_course_id?: number
  selected_price?: number
  selected_payments_count?: number
  selected_payment_day?: number
  first_payment_id?: number
  nedarim_payment_link?: string
  // Conversion checklist fields
  shipping_details_complete?: boolean
  student_chat_added?: boolean
  personal_course_update?: boolean
  personal_course_update_date?: string
  personal_course_update_notes?: string
  conversion_checklist_complete?: boolean
  conversion_completed_at?: string
  created_at: string
  updated_at?: string
  last_edited_at?: string
  created_by?: string
  interactions?: LeadInteraction[]
  payments?: Payment[]
}

export interface LeadInteraction {
  id: number
  lead_id?: number
  interaction_type: string
  interaction_date?: string
  call_status?: string
  wait_time?: string
  call_duration?: string
  total_duration?: string
  ivr_product?: string
  form_product?: string
  form_content?: string
  user_name?: string
  description?: string
  next_call_date?: string
  created_at: string
}

export interface Student {
  id: number
  full_name: string
  id_number?: string
  phone: string
  phone2?: string
  address?: string
  city?: string
  email?: string
  notes?: string
  status: string
  approved_terms: boolean
  nedarim_payer_id?: string
  lead_id?: number
  total_price?: number
  total_paid?: number
  payment_status: string
  shipping_status?: string
  created_at: string
  updated_at: string
  enrollments?: Enrollment[]
  payments?: Payment[]
  collections?: Collection[]
  commitments?: Commitment[]
}

export interface Course {
  id: number
  name: string
  description?: string
  start_date?: string
  end_date?: string
  semester?: string
  price?: number
  payments_count: number
  is_active: boolean
  total_sessions?: number
  created_at: string
}

export interface CourseModule {
  id: number
  course_id: number
  name: string
  module_order: number
  sessions_count?: number
  hours_estimate?: number
  start_date?: string
  start_time?: string
  end_time?: string
}

export interface Enrollment {
  id: number
  student_id: number
  course_id?: number
  status: string
  current_module: number
  total_modules?: number
  sessions_remaining?: number
  estimated_finish?: string
}

export interface Salesperson {
  id: number
  name: string
  email?: string
  phone?: string
  ref_code?: string
  is_active: boolean
}

export interface SalesTask {
  id: number
  salesperson_id: number
  lead_id?: number
  student_id?: number
  title: string
  description?: string
  due_date?: string
  status: string
  priority: number
  created_at: string
  completed_at?: string
}

export interface Payment {
  id: number
  reference?: string
  student_id?: number
  lead_id?: number
  course_id?: number
  commitment_id?: number
  payment_date?: string
  amount: number
  currency?: string
  transaction_type?: string
  installments?: number
  payment_method?: string
  status: string
  nedarim_donation_id?: string
  nedarim_transaction_id?: string
  created_at: string
}

export interface Campaign {
  id: number
  name: string
  course_id?: number
  platforms?: string
  start_date?: string
  end_date?: string
  is_active: boolean
  created_at: string
}

export interface Inquiry {
  id: number
  subject: string
  inquiry_type: string
  lead_id?: number
  student_id?: number
  phone?: string
  status: string
  notes?: string
  handled_by?: string
  created_at: string
}

export interface Expense {
  id: number
  description: string
  category?: string
  amount: number
  expense_date?: string
  vendor?: string
  receipt_url?: string
  notes?: string
  created_at: string
}

export interface Collection {
  id: number
  student_id: number
  commitment_id?: number
  payment_id?: number
  course_id?: number
  amount: number
  due_date: string
  charge_day?: number
  installment_number?: number
  total_installments?: number
  status: string
  attempts: number
  collected_at?: string
  reference?: string
  notes?: string
  nedarim_donation_id?: string
  nedarim_subscription_id?: string
  created_at: string
  // Joined data
  student?: {
    id: number
    full_name: string
    phone: string
  }
  commitment?: {
    id: number
    monthly_amount: number
    installments?: number
    status: string
  }
}

export interface Commitment {
  id: number
  reference?: string
  student_id: number
  course_id?: number
  end_date?: string
  monthly_amount: number
  total_amount?: number
  installments?: number
  charge_day?: number
  payment_method?: string
  status: string
  nedarim_subscription_id?: string
  created_at: string
  // Computed
  paid_amount?: number
  remaining?: number
}

export interface InquiryResponse {
  id: number
  inquiry_id: number
  response_text: string
  responded_by?: string
  created_at: string
}

export interface DashboardOverview {
  total_leads: number
  new_leads: number
  total_students: number
  active_enrollments: number
  total_revenue: number
}

export interface SalespersonStats {
  id: number
  name: string
  total_leads: number
  new_leads: number
  open_tasks: number
}

// ============================================================
// Lead Payment & Product Selection API Types
// ============================================================

export interface CreatePaymentLinkRequest {
  amount: number
  currency?: string
  installments?: number
  payment_method?: string
  product_id?: number
  redirect_url?: string
}

export interface CreatePaymentLinkResponse {
  payment_id: number
  lead_id: number
  nedarim_donation_id: string
  payment_link: string
  status: string
}

export interface SelectCourseRequest {
  course_id: number
  price?: number
  payments_count?: number
  payment_day?: number
}

export interface SelectCourseResponse {
  lead_id: number
  course_id: number
  course_name: string
  price: number
  payments_count: number
  payment_day: number
}

export interface LeadPaymentStatus {
  lead_id: number
  first_payment: boolean
  first_payment_id?: number
  nedarim_payment_link?: string
  selected_course_id?: number
  payments: Payment[]
}

export interface CollectionSummary {
  pending_amount: number
  collected_amount: number
  failed_amount: number
  overdue_count: number
}

export interface LeadProduct {
  id: number
  lead_id: number
  course_id?: number
  price?: number
  payments_count?: number
  monthly_payment?: number
  payment_day?: number
  payment_type: string
  language: string
  coupon_id?: number
  discount_type?: string
  discount_amount?: number
  final_price?: number
  entry_module_id?: number
  entry_date?: string
  sessions_remaining?: number
  estimated_finish?: string
  created_at: string
}
