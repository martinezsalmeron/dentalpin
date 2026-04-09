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

// Treatment types with new clinical categories and visualization rules
export type TreatmentStatus = 'existing' | 'planned'
export type TreatmentCategory = 'surface' | 'whole_tooth'
export type TreatmentClinicalCategory = 'diagnostico' | 'restauradora' | 'cirugia' | 'endodoncia' | 'ortodoncia'
export type VisualizationRule = 'pulp_fill' | 'occlusal_surface' | 'lateral_icon' | 'pattern_fill'

export type TreatmentType
  // Diagnóstico
  = | 'pulpitis'
    | 'caries'
    | 'incipient_caries'
    | 'pigmentation'
    | 'fracture'
    | 'missing'
    | 'periapical_small'
    | 'periapical_medium'
    | 'periapical_large'
    | 'rotated'
    | 'displaced'
    | 'unerupted'
    // Restauradora
    | 'filling_composite'
    | 'filling_amalgam'
    | 'filling_temporary'
    | 'sealant'
    | 'veneer'
    | 'inlay'
    | 'overlay'
    | 'crown'
    | 'pontic'
    | 'bridge_abutment'
    // Cirugía
    | 'extraction'
    | 'implant'
    | 'apicoectomy'
    // Endodoncia
    | 'root_canal_full'
    | 'root_canal_two_thirds'
    | 'root_canal_half'
    | 'post'
    | 'root_canal_overfill'
    // Ortodoncia
    | 'bracket'
    | 'tube'
    | 'band'
    | 'attachment'
    | 'retainer'
    // Legacy types (for backwards compatibility)
    | 'filling'
    | 'root_canal'
    | 'bridge_pontic'

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

// ============================================================================
// VAT Type Types
// ============================================================================

export interface VatType {
  id: string
  clinic_id: string
  names: Record<string, string>
  rate: number
  is_default: boolean
  is_active: boolean
  is_system: boolean
  created_at: string
  updated_at: string
}

export interface VatTypeCreate {
  names: Record<string, string>
  rate: number
  is_default?: boolean
}

export interface VatTypeUpdate {
  names?: Record<string, string>
  rate?: number
  is_default?: boolean
  is_active?: boolean
}

export interface VatTypeBrief {
  id: string
  names: Record<string, string>
  rate: number
  is_default: boolean
  is_active: boolean
  is_system: boolean
}

// ============================================================================
// Catalog Types
// ============================================================================

export interface TreatmentCatalogCategory {
  id: string
  clinic_id: string
  parent_id?: string
  key: string
  names: Record<string, string>
  descriptions?: Record<string, string>
  display_order: number
  icon?: string
  is_active: boolean
  is_system: boolean
  created_at: string
  updated_at: string
}

export interface TreatmentCatalogCategoryCreate {
  key: string
  names: Record<string, string>
  descriptions?: Record<string, string>
  parent_id?: string
  display_order?: number
  icon?: string
}

export interface TreatmentCatalogCategoryUpdate {
  key?: string
  names?: Record<string, string>
  descriptions?: Record<string, string>
  parent_id?: string
  display_order?: number
  icon?: string
  is_active?: boolean
}

export interface OdontogramMapping {
  id: string
  odontogram_treatment_type: string
  visualization_rules: string[]
  visualization_config: Record<string, unknown>
  clinical_category: string
}

export interface OdontogramMappingCreate {
  odontogram_treatment_type: string
  visualization_rules: string[]
  visualization_config: Record<string, unknown>
  clinical_category: string
}

export interface TreatmentCatalogItem {
  id: string
  clinic_id: string
  category_id: string
  internal_code: string
  names: Record<string, string>
  descriptions?: Record<string, string>
  // Pricing
  default_price?: number
  cost_price?: number
  currency: string
  // Scheduling
  default_duration_minutes?: number
  requires_appointment: boolean
  // Tax - references VatType
  vat_type_id?: string
  vat_type?: VatTypeBrief
  // Treatment characteristics
  treatment_scope: 'surface' | 'whole_tooth'
  is_diagnostic: boolean
  requires_surfaces: boolean
  // Material
  material_notes?: string
  // Status
  is_active: boolean
  is_system: boolean
  deleted_at?: string
  // Timestamps
  created_at: string
  updated_at: string
  // Related
  category?: TreatmentCatalogCategory
  odontogram_mapping?: OdontogramMapping
}

export interface TreatmentCatalogItemCreate {
  internal_code: string
  category_id: string
  names: Record<string, string>
  descriptions?: Record<string, string>
  // Pricing
  default_price?: number
  cost_price?: number
  currency?: string
  // Scheduling
  default_duration_minutes?: number
  requires_appointment?: boolean
  // Tax - references VatType (uses clinic default if not provided)
  vat_type_id?: string
  // Treatment characteristics
  treatment_scope?: 'surface' | 'whole_tooth'
  is_diagnostic?: boolean
  requires_surfaces?: boolean
  // Material
  material_notes?: string
  // Odontogram mapping
  odontogram_mapping?: OdontogramMappingCreate
}

export interface TreatmentCatalogItemUpdate {
  internal_code?: string
  category_id?: string
  names?: Record<string, string>
  descriptions?: Record<string, string>
  default_price?: number
  cost_price?: number
  currency?: string
  default_duration_minutes?: number
  requires_appointment?: boolean
  vat_type_id?: string
  treatment_scope?: 'surface' | 'whole_tooth'
  is_diagnostic?: boolean
  requires_surfaces?: boolean
  material_notes?: string
  is_active?: boolean
  odontogram_mapping?: OdontogramMappingCreate
}

export interface OdontogramTreatment {
  id: string
  internal_code: string
  names: Record<string, string>
  default_price?: number
  treatment_scope: 'surface' | 'whole_tooth'
  requires_surfaces: boolean
  is_diagnostic: boolean
  // Odontogram specific
  odontogram_treatment_type: string
  visualization_rules: string[]
  visualization_config: Record<string, unknown>
  clinical_category: string
  // Category info
  category_key: string
  category_names: Record<string, string>
}
