// User types
export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  professional_id?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ClinicMembership {
  id: string
  user_id: string
  clinic_id: string
  role: 'admin' | 'dentist' | 'hygienist' | 'assistant' | 'receptionist'
}

export interface Clinic {
  id: string
  name: string
  tax_id: string
  address?: Record<string, string>
  phone?: string
  email?: string
  settings: {
    slot_duration_min?: number
    currency?: string
    timezone?: string
  }
  cabinets: Array<{
    name: string
    color: string
  }>
  created_at: string
  updated_at: string
}

// Auth types
export interface LoginCredentials {
  email: string
  password: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface AuthResponse extends AuthTokens {
  user: User
  clinics: Array<{ id: string, name: string, role: string }>
}

// Patient types
export interface Patient {
  id: string
  clinic_id: string
  first_name: string
  last_name: string
  national_id?: string
  date_of_birth?: string
  gender?: 'male' | 'female' | 'other'
  phone?: string
  email?: string
  address?: Record<string, string>
  medical_history?: Record<string, unknown>
  insurance?: Record<string, string>
  notes?: string
  consent_signed: boolean
  consent_date?: string
  status: 'active' | 'inactive' | 'archived'
  created_at: string
  updated_at: string
}

export interface PatientCreate {
  first_name: string
  last_name: string
  phone?: string
  email?: string
  date_of_birth?: string
  notes?: string
}

export interface PatientUpdate extends Partial<PatientCreate> {
  status?: 'active' | 'inactive' | 'archived'
}

// Appointment types
export interface Appointment {
  id: string
  clinic_id: string
  patient_id?: string
  professional_id: string
  cabinet: string
  start_time: string
  end_time: string
  treatment_type?: string
  status: 'scheduled' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled' | 'no_show'
  notes?: string
  color?: string
  created_at: string
  updated_at: string
  patient?: Patient
  professional?: User
}

export interface AppointmentCreate {
  patient_id: string
  professional_id: string
  cabinet: string
  start_time: string
  end_time: string
  treatment_type?: string
  notes?: string
  color?: string
}

export interface AppointmentUpdate extends Partial<AppointmentCreate> {
  status?: Appointment['status']
}

// API Response types
export interface ApiResponse<T> {
  data: T
  message: string
  errors: string[]
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  page_size: number
}

// Module registry types
export interface NavigationItem {
  label: string
  icon: string
  to: string
}

export interface ModuleDefinition {
  name: string
  label: string
  icon: string
  navigation: NavigationItem[]
}
