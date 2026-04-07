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

export interface Cabinet {
  name: string
  color: string
}

export interface CabinetCreate {
  name: string
  color: string
}

export interface CabinetUpdate {
  name?: string
  color?: string
}

export interface ClinicUpdate {
  name?: string
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
  cabinets: Cabinet[]
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

export interface MeResponse {
  user: User
  clinics: Array<{ id: string, name: string, role: string }>
  permissions: string[]
}

export type UserRole = 'admin' | 'dentist' | 'hygienist' | 'assistant' | 'receptionist'

// Professional type (dentists and hygienists)
export interface Professional {
  id: string
  email: string
  first_name: string
  last_name: string
  role: 'dentist' | 'hygienist'
}

export interface UserCreate {
  email: string
  password: string
  first_name: string
  last_name: string
  role: UserRole
  clinic_id?: string
}

export interface UserUpdate {
  first_name?: string
  last_name?: string
  email?: string
  role?: UserRole
  is_active?: boolean
}

// Patient types
export interface Patient {
  id: string
  clinic_id: string
  first_name: string
  last_name: string
  phone?: string
  email?: string
  date_of_birth?: string
  notes?: string
  status: 'active' | 'archived'
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
  status?: 'active' | 'archived'
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
  message: string | null
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  page_size: number
  message?: string | null
}

export interface ErrorResponse {
  data: null
  message: string
  errors: string[]
}

// Module registry types
export interface NavigationItem {
  label: string
  icon: string
  to: string
  permission?: string // Required permission to see this item
}

export interface ModuleDefinition {
  name: string
  label: string
  icon: string
  navigation: NavigationItem[]
}

// Permission config for centralized management
export interface PermissionConfig {
  routes: Record<string, string> // path -> permission
  actions: Record<string, Record<string, string>> // resource -> action -> permission
}

// User list response (for admin)
export interface UserWithRole extends User {
  role?: UserRole
}

// Odontogram types
export type ToothCondition
  = | 'healthy'
    | 'caries'
    | 'filling'
    | 'crown'
    | 'missing'
    | 'root_canal'
    | 'implant'
    | 'bridge_pontic'
    | 'bridge_abutment'
    | 'extraction_indicated'
    | 'sealant'
    | 'fracture'

export type Surface = 'M' | 'D' | 'O' | 'V' | 'L'
export type ToothType = 'permanent' | 'deciduous'

export interface SurfaceConditions {
  M: ToothCondition
  D: ToothCondition
  O: ToothCondition
  V: ToothCondition
  L: ToothCondition
}

export interface ToothRecord {
  id: string
  patient_id: string
  tooth_number: number
  tooth_type: ToothType
  general_condition: ToothCondition
  surfaces: SurfaceConditions
  notes?: string
  // Positional markers
  is_displaced?: boolean
  is_rotated?: boolean
  displacement_notes?: string
  created_at: string
  updated_at: string
}

export interface OdontogramData {
  patient_id: string
  teeth: ToothRecord[]
  condition_colors: Record<ToothCondition, string>
  available_conditions: ToothCondition[]
  surfaces: Surface[]
}

export interface SurfaceUpdate {
  surface: Surface
  condition: ToothCondition
}

export interface ToothRecordUpdate {
  general_condition?: ToothCondition
  surface_updates?: SurfaceUpdate[]
  notes?: string
  is_displaced?: boolean
  is_rotated?: boolean
}

export interface BulkToothUpdate {
  tooth_number: number
  general_condition?: ToothCondition
  surface_updates?: SurfaceUpdate[]
  notes?: string
}

export interface OdontogramHistoryEntry {
  id: string
  tooth_number: number
  change_type: string
  surface?: Surface
  old_condition?: ToothCondition
  new_condition?: ToothCondition
  notes?: string
  changed_by: string
  changed_by_name?: string
  changed_at: string
}

// Treatment types (Gesdén style)
export type TreatmentStatus = 'existing' | 'planned'
export type TreatmentCategory = 'surface' | 'whole_tooth'
export type TreatmentType
  = | 'caries'
    | 'filling'
    | 'sealant'
    | 'crown'
    | 'root_canal'
    | 'implant'
    | 'bridge_pontic'
    | 'bridge_abutment'
    | 'extraction'
    | 'missing'
    | 'fracture'
    | 'post'
    | 'veneer'
    | 'apicoectomy'
    // Orthodontic treatments
    | 'bracket'
    | 'band'
    | 'attachment'
    | 'retainer'

export interface Treatment {
  id: string
  tooth_record_id: string
  tooth_number: number
  treatment_type: TreatmentType
  treatment_category: TreatmentCategory
  surfaces?: Surface[]
  status: TreatmentStatus
  recorded_at: string
  performed_at?: string
  performed_by?: string
  performed_by_name?: string
  budget_item_id?: string
  source_module: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface TreatmentCreate {
  treatment_type: TreatmentType
  status?: TreatmentStatus
  surfaces?: Surface[]
  notes?: string
  budget_item_id?: string
  source_module?: string
}

export interface TreatmentUpdate {
  status?: TreatmentStatus
  surfaces?: Surface[]
  notes?: string
}

export interface ToothRecordWithTreatments extends ToothRecord {
  treatments: Treatment[]
  is_displaced: boolean
  is_rotated: boolean
  displacement_notes?: string
}
