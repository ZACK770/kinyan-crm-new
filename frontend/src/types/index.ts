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
  active_task_id?: number
  created_at: string
  updated_at: string
  created_by?: string
  interactions?: LeadInteraction[]
}

export interface LeadInteraction {
  id: number
  lead_id: number
  interaction_type: string
  interaction_date: string
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
  nedarim_id?: string
  lead_id?: number
  total_price?: number
  total_paid?: number
  payment_status: string
  shipping_status?: string
  created_at: string
  updated_at: string
  enrollments?: Enrollment[]
}

export interface Course {
  id: number
  name: string
  description?: string
  start_date?: string
  end_date?: string
  semester?: string
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
  payment_date?: string
  amount: number
  currency?: string
  transaction_type?: string
  payment_method?: string
  status: string
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

export interface CollectionItem {
  id: number
  student_id: number
  student_name?: string
  amount: number
  due_date: string
  status: string
  payment_method?: string
  collected_date?: string
  notes?: string
  created_at: string
}

export interface Commitment {
  id: number
  student_id: number
  student_name?: string
  course_id?: number
  total_amount: number
  paid_amount: number
  remaining: number
  installments?: number
  status: string
  start_date?: string
  created_at: string
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
