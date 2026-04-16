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

export interface ClinicAddress {
  street?: string
  city?: string
  postal_code?: string
  country?: string
}

export interface ClinicUpdate {
  name?: string
  tax_id?: string
  address?: ClinicAddress
  phone?: string
  email?: string
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
export interface PatientBillingAddress {
  street?: string
  city?: string
  postal_code?: string
  province?: string
  country?: string
}

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
  // Billing fields
  billing_name?: string
  billing_tax_id?: string
  billing_address?: PatientBillingAddress
  billing_email?: string
  has_complete_billing_info: boolean
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
  // Billing fields
  billing_name?: string
  billing_tax_id?: string
  billing_address?: PatientBillingAddress
  billing_email?: string
}

export interface PatientUpdate extends Partial<PatientCreate> {
  status?: 'active' | 'archived'
}

// Appointment treatment brief (from planned treatment item)
export interface AppointmentTreatmentBrief {
  id: string
  planned_item_id: string
  planned_item_status: 'pending' | 'completed' | 'cancelled'
  catalog_item_id?: string
  internal_code: string
  names: Record<string, string>
  default_price?: number
  default_duration_minutes?: number
  // Dental context
  tooth_number?: number
  surfaces?: string[]
  is_global: boolean
  // Plan info
  plan_id?: string
  plan_number?: string
  // Completion tracking
  completed_in_appointment: boolean
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
  treatment_type?: string // Legacy field
  treatments?: AppointmentTreatmentBrief[] // New: treatments from catalog
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
  treatment_type?: string // Legacy field
  planned_item_ids?: string[] // List of PlannedTreatmentItem IDs
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
  treatments?: Treatment[]
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

// ============================================================================
// Budget Types (Simplified)
// ============================================================================

export type BudgetStatus
  = | 'draft' // Initial state, editable
    | 'sent' // Sent to patient, awaiting response
    | 'accepted' // Patient accepted, ready for treatment/invoicing
    | 'completed' // All work done
    | 'rejected' // Patient rejected (terminal)
    | 'expired' // Validity period passed (terminal)
    | 'cancelled' // Cancelled before acceptance (terminal)

export type DiscountType = 'percentage' | 'absolute'

export type SignatureType = 'full_acceptance' | 'rejection'

export type SignatureMethod = 'click_accept' | 'drawn' | 'external_provider'

export type RelationshipToPatient = 'patient' | 'guardian' | 'representative'

// Brief types for nested responses
export interface PatientBrief {
  id: string
  first_name: string
  last_name: string
  phone?: string
  email?: string
}

export interface UserBrief {
  id: string
  first_name: string
  last_name: string
}

export interface CatalogItemBrief {
  id: string
  internal_code: string
  names: Record<string, string>
  default_price?: number
}

// Budget Item
export interface BudgetItem {
  id: string
  budget_id: string
  catalog_item_id: string
  // Pricing
  unit_price: number
  quantity: number
  // Line discount
  discount_type?: DiscountType
  discount_value?: number
  // VAT
  vat_type_id?: string
  vat_rate: number
  // Calculated totals
  line_subtotal: number
  line_discount: number
  line_tax: number
  line_total: number
  // Dental specifics
  tooth_number?: number
  surfaces?: string[]
  // Odontogram integration
  tooth_treatment_id?: string
  // Invoice tracking
  invoiced_quantity: number
  // Display
  display_order: number
  notes?: string
  // Timestamps
  created_at: string
  updated_at: string
  // Related
  catalog_item?: CatalogItemBrief
  vat_type?: VatTypeBrief
}

export interface BudgetItemCreate {
  catalog_item_id: string
  quantity?: number
  unit_price?: number
  discount_type?: DiscountType
  discount_value?: number
  tooth_number?: number
  surfaces?: string[]
  tooth_treatment_id?: string
  display_order?: number
  notes?: string
}

export interface BudgetItemUpdate {
  quantity?: number
  unit_price?: number
  discount_type?: DiscountType
  discount_value?: number
  tooth_number?: number
  surfaces?: string[]
  display_order?: number
  notes?: string
}

// Budget Signature
export interface BudgetSignature {
  id: string
  budget_id: string
  signature_type: SignatureType
  signed_items?: string[]
  signed_by_name: string
  signed_by_email?: string
  relationship_to_patient: RelationshipToPatient
  signature_method: SignatureMethod
  signature_data?: Record<string, unknown>
  ip_address?: string
  signed_at: string
  external_signature_id?: string
  external_provider?: string
  document_hash?: string
  created_at: string
}

export interface SignatureCreate {
  signed_by_name: string
  signed_by_email?: string
  relationship_to_patient?: RelationshipToPatient
  signature_data?: Record<string, unknown>
}

// Budget History
export interface BudgetHistoryEntry {
  id: string
  budget_id: string
  action: string
  changed_by: string
  changed_at: string
  previous_state?: Record<string, unknown>
  new_state?: Record<string, unknown>
  notes?: string
  user?: UserBrief
}

// Budget
export interface Budget {
  id: string
  clinic_id: string
  patient_id: string
  // Identification
  budget_number: string
  version: number
  parent_budget_id?: string
  // Status
  status: BudgetStatus
  // Validity
  valid_from: string
  valid_until?: string
  // Assignments
  created_by: string
  assigned_professional_id?: string
  // Global discount
  global_discount_type?: DiscountType
  global_discount_value?: number
  // Totals
  subtotal: number
  total_discount: number
  total_tax: number
  total: number
  currency: string
  // Notes
  internal_notes?: string
  patient_notes?: string
  // Insurance
  insurance_estimate?: number
  // Timestamps
  created_at: string
  updated_at: string
  deleted_at?: string
  // Related
  patient?: PatientBrief
  creator?: UserBrief
  assigned_professional?: UserBrief
}

export interface BudgetDetail extends Budget {
  items: BudgetItem[]
  signatures: BudgetSignature[]
}

export interface BudgetListItem {
  id: string
  budget_number: string
  version: number
  status: BudgetStatus
  valid_from: string
  valid_until?: string
  total: number
  currency: string
  created_at: string
  patient?: PatientBrief
  creator?: UserBrief
}

export interface BudgetCreate {
  patient_id: string
  valid_from?: string
  valid_until?: string
  assigned_professional_id?: string
  global_discount_type?: DiscountType
  global_discount_value?: number
  internal_notes?: string
  patient_notes?: string
  items?: BudgetItemCreate[]
}

export interface BudgetUpdate {
  valid_from?: string
  valid_until?: string
  assigned_professional_id?: string
  global_discount_type?: DiscountType
  global_discount_value?: number
  internal_notes?: string
  patient_notes?: string
}

// Workflow
export interface BudgetSendRequest {
  send_email?: boolean
  custom_message?: string
}

export interface BudgetAcceptRequest {
  signature: SignatureCreate
}

export interface BudgetRejectRequest {
  reason?: string
  signature?: SignatureCreate
}

export interface BudgetSendRequest {
  send_email?: boolean
  custom_message?: string
}

export interface BudgetCancelRequest {
  reason?: string
}

// Versions
export interface BudgetVersion {
  id: string
  version: number
  status: BudgetStatus
  total: number
  created_at: string
  is_current: boolean
}

export interface BudgetVersionList {
  budget_number: string
  versions: BudgetVersion[]
  current_version: number
}

// ============================================================================
// Notification Types
// ============================================================================

export interface EmailTemplate {
  id: string
  clinic_id?: string
  template_key: string
  locale: string
  subject: string
  body_html: string
  body_text?: string
  variables?: Record<string, unknown>
  description?: string
  is_system: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface EmailTemplateCreate {
  template_key: string
  locale?: string
  subject: string
  body_html: string
  body_text?: string
  variables?: Record<string, unknown>
  description?: string
  is_active?: boolean
}

export interface EmailTemplateUpdate {
  subject?: string
  body_html?: string
  body_text?: string
  variables?: Record<string, unknown>
  description?: string
  is_active?: boolean
}

export interface NotificationPreference {
  id: string
  clinic_id: string
  patient_id?: string
  user_id?: string
  email_enabled: boolean
  preferences: Record<string, boolean>
  preferred_locale: string
  created_at: string
  updated_at: string
}

export interface NotificationPreferenceUpdate {
  email_enabled?: boolean
  preferences?: Record<string, boolean>
  preferred_locale?: string
}

export interface NotificationTypeSettings {
  auto_send: boolean
  enabled: boolean
  hours_before?: number
}

export interface ClinicNotificationSettings {
  id: string
  clinic_id: string
  settings: Record<string, NotificationTypeSettings>
  created_at: string
  updated_at: string
}

export interface ClinicNotificationSettingsUpdate {
  settings: Record<string, Partial<NotificationTypeSettings>>
}

export interface EmailLog {
  id: string
  clinic_id: string
  recipient_email: string
  patient_id?: string
  template_key: string
  subject: string
  status: 'pending' | 'sent' | 'failed' | 'skipped'
  provider: string
  provider_message_id?: string
  error_message?: string
  created_at: string
  sent_at?: string
  triggered_by_event?: string
}

export interface ManualSendRequest {
  notification_type: string
  patient_id?: string
  appointment_id?: string
  budget_id?: string
  custom_context?: Record<string, unknown>
}

export interface ManualSendResponse {
  success: boolean
  message: string
  log_id?: string
}

export interface TestEmailRequest {
  to_email: string
}

export interface TestEmailResponse {
  success: boolean
  message: string
  provider: string
}

// SMTP Settings types
export type SmtpProvider = 'smtp' | 'console' | 'disabled'

export interface SmtpSettings {
  provider: SmtpProvider
  host: string | null
  port: number | null
  username: string | null
  has_password: boolean
  use_tls: boolean
  use_ssl: boolean
  from_email: string | null
  from_name: string | null
  is_active: boolean
  is_verified: boolean
  last_verified_at: string | null
}

export interface SmtpSettingsUpdate {
  provider?: SmtpProvider
  host?: string
  port?: number
  username?: string
  password?: string
  use_tls?: boolean
  use_ssl?: boolean
  from_email?: string
  from_name?: string
}

export interface SmtpTestRequest {
  host: string
  port: number
  username?: string
  password?: string
  use_tls: boolean
  use_ssl: boolean
  from_email: string
  to_email: string
}

// ============================================================================
// Billing Types
// ============================================================================

export type InvoiceStatus = 'draft' | 'issued' | 'partial' | 'paid' | 'cancelled' | 'voided'

export type PaymentMethod = 'cash' | 'card' | 'bank_transfer' | 'direct_debit' | 'other'

export type SeriesType = 'invoice' | 'credit_note'

// Invoice Series
export interface InvoiceSeries {
  id: string
  clinic_id: string
  prefix: string
  series_type: SeriesType
  description?: string
  current_number: number
  reset_yearly: boolean
  last_reset_year?: number
  is_default: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface InvoiceSeriesCreate {
  prefix: string
  series_type: SeriesType
  description?: string
  reset_yearly?: boolean
  is_default?: boolean
}

export interface InvoiceSeriesUpdate {
  prefix?: string
  description?: string
  reset_yearly?: boolean
  is_default?: boolean
  is_active?: boolean
}

export interface SeriesResetRequest {
  new_number: number
}

// Invoice Item
export interface InvoiceItem {
  id: string
  invoice_id: string
  budget_item_id?: string
  catalog_item_id?: string
  // Description
  description: string
  internal_code?: string
  // Pricing
  unit_price: number
  quantity: number
  // Discounts
  discount_type?: DiscountType
  discount_value?: number
  // VAT
  vat_type_id?: string
  vat_rate: number
  vat_exempt_reason?: string
  // Calculated totals
  line_subtotal: number
  line_discount: number
  line_tax: number
  line_total: number
  // Dental context
  tooth_number?: number
  surfaces?: string[]
  // Display
  display_order: number
  // Timestamps
  created_at: string
  updated_at: string
  // Related
  catalog_item?: CatalogItemBrief
  vat_type?: VatTypeBrief
}

export interface InvoiceItemCreate {
  description: string
  internal_code?: string
  catalog_item_id?: string
  unit_price: number
  quantity?: number
  discount_type?: DiscountType
  discount_value?: number
  vat_type_id?: string
  vat_exempt_reason?: string
  tooth_number?: number
  surfaces?: string[]
  display_order?: number
}

export interface InvoiceItemFromBudget {
  budget_item_id: string
  quantity?: number
}

export interface InvoiceItemUpdate {
  description?: string
  unit_price?: number
  quantity?: number
  discount_type?: DiscountType
  discount_value?: number
  vat_type_id?: string
  vat_exempt_reason?: string
  display_order?: number
}

// Payment
export interface Payment {
  id: string
  invoice_id: string
  amount: number
  payment_method: PaymentMethod
  payment_date: string
  reference?: string
  notes?: string
  recorded_by: string
  created_at: string
  // Voiding
  is_voided: boolean
  voided_at?: string
  voided_by?: string
  void_reason?: string
  // Related
  recorder?: UserBrief
  voider?: UserBrief
}

export interface PaymentCreate {
  amount: number
  payment_method: PaymentMethod
  payment_date?: string
  reference?: string
  notes?: string
}

export interface PaymentVoidRequest {
  reason: string
}

// Invoice History
export interface InvoiceHistoryEntry {
  id: string
  invoice_id: string
  action: string
  changed_by: string
  changed_at: string
  previous_state?: Record<string, unknown>
  new_state?: Record<string, unknown>
  notes?: string
  user?: UserBrief
}

// Invoice Brief (for references)
export interface InvoiceBrief {
  id: string
  invoice_number: string
  status: InvoiceStatus
  total: number
  issue_date?: string
}

// Billing Address
export interface BillingAddress {
  street?: string
  city?: string
  postal_code?: string
  province?: string
  country?: string
}

// Invoice
export interface Invoice {
  id: string
  clinic_id: string
  patient_id: string
  // Identification (null for drafts, assigned when issued)
  invoice_number: string | null
  sequential_number: number | null
  series_id: string | null
  // Links
  budget_id?: string
  credit_note_for_id?: string
  // Status
  status: InvoiceStatus
  // Dates
  issue_date?: string
  due_date?: string
  payment_term_days: number
  // Billing data
  billing_name: string
  billing_tax_id?: string
  billing_address?: BillingAddress
  billing_email?: string
  // Totals
  subtotal: number
  total_discount: number
  total_tax: number
  total: number
  total_paid: number
  balance_due: number
  currency: string
  // Notes
  internal_notes?: string
  public_notes?: string
  // Extensibility
  compliance_data?: Record<string, unknown>
  document_hash?: string
  // Audit
  created_by: string
  issued_by?: string
  // Timestamps
  created_at: string
  updated_at: string
  deleted_at?: string
  // Related
  patient?: PatientBrief
  creator?: UserBrief
  issuer?: UserBrief
  budget?: BudgetBrief
  credit_note_for?: InvoiceBrief
}

export interface InvoiceDetail extends Invoice {
  items: InvoiceItem[]
  payments: Payment[]
}

export interface InvoiceListItem {
  id: string
  invoice_number: string | null // Null for drafts (assigned when issued)
  status: InvoiceStatus
  issue_date?: string
  due_date?: string
  total: number
  total_paid: number
  balance_due: number
  currency: string
  created_at: string
  patient?: PatientBrief
  creator?: UserBrief
}

export interface BudgetBrief {
  id: string
  budget_number: string
  status: BudgetStatus
  total: number
}

export interface InvoiceCreate {
  patient_id: string
  series_id?: string
  // Billing data removed - drafts get it from patient dynamically
  payment_term_days?: number
  due_date?: string
  internal_notes?: string
  public_notes?: string
  items?: InvoiceItemCreate[]
}

export interface InvoiceFromBudgetCreate {
  items: InvoiceItemFromBudget[]
  // Billing data removed - drafts get it from patient dynamically
  payment_term_days?: number
  due_date?: string
  internal_notes?: string
  public_notes?: string
}

export interface InvoiceUpdate {
  patient_id?: string // Can change patient for draft invoices (without budget)
  // Billing data removed - drafts get it from patient dynamically
  payment_term_days?: number
  due_date?: string
  internal_notes?: string
  public_notes?: string
}

// Workflow
export interface InvoiceIssueRequest {
  issue_date?: string
}

export interface InvoiceSendRequest {
  send_email: boolean
  custom_message?: string
}

export interface CreditNoteItemSelect {
  invoice_item_id: string
  quantity?: number
}

export interface CreditNoteCreate {
  reason: string
  items?: CreditNoteItemSelect[]
  internal_notes?: string
  public_notes?: string
}

// Settings
export interface BillingSettings {
  default_payment_term_days: number
  invoice_footer_text?: string
  bank_account_info?: string
}

export interface BillingSettingsUpdate {
  default_payment_term_days?: number
  invoice_footer_text?: string
  bank_account_info?: string
}

// Report Types
export interface VatSummaryItem {
  vat_type_id?: string
  vat_rate: number
  vat_name: string
  base_amount: number
  tax_amount: number
  total_amount: number
}

export interface BillingSummary {
  period_start: string
  period_end: string
  total_invoiced: number
  total_paid: number
  total_pending: number
  invoice_count: number
  paid_count: number
  overdue_count: number
  vat_breakdown: VatSummaryItem[]
}

export interface OverdueInvoice {
  id: string
  invoice_number: string
  patient_name: string
  issue_date: string
  due_date: string
  days_overdue: number
  balance_due: number
}

export interface PaymentMethodSummary {
  payment_method: string
  total_amount: number
  payment_count: number
}

export interface ProfessionalBillingSummary {
  professional_id: string
  professional_name: string
  total_invoiced: number
  invoice_count: number
}

export interface NumberingGap {
  series_prefix: string
  year: number
  missing_numbers: number[]
}

export interface PatientBillingSummary {
  patient_id: string
  currency: string
  // Budget metrics
  total_budgeted: number
  work_in_progress: number
  work_completed: number
  // Invoice metrics
  total_invoiced: number
  total_paid: number
  balance_pending: number
}

// ============================================================================
// Patient Extended Types (Medical History, Emergency Contact, Timeline)
// ============================================================================

// Patient Address
export interface PatientAddress {
  street?: string
  city?: string
  postal_code?: string
  province?: string
  country?: string
}

// Emergency Contact
export interface EmergencyContact {
  name: string
  relationship?: string
  phone: string
  email?: string
  is_legal_guardian: boolean
}

// Legal Guardian (for minors)
export interface LegalGuardian {
  name: string
  relationship: string // parent, grandparent, legal_tutor, other
  dni?: string
  phone: string
  email?: string
  address?: string
  notes?: string
}

// Medical History Entry Types
export interface AllergyEntry {
  name: string
  type?: string // drug, food, material, environmental
  severity: 'low' | 'medium' | 'high' | 'critical'
  reaction?: string
  notes?: string
}

export interface MedicationEntry {
  name: string
  dosage?: string
  frequency?: string
  start_date?: string
  notes?: string
}

export interface SystemicDiseaseEntry {
  name: string
  type?: string // cardiovascular, respiratory, endocrine, etc.
  diagnosis_date?: string
  is_controlled: boolean
  is_critical: boolean
  medications?: string
  notes?: string
}

export interface SurgicalHistoryEntry {
  procedure: string
  surgery_date?: string
  complications?: string
  notes?: string
}

// Full Medical History
export interface MedicalHistory {
  // Lists
  allergies: AllergyEntry[]
  medications: MedicationEntry[]
  systemic_diseases: SystemicDiseaseEntry[]
  surgical_history: SurgicalHistoryEntry[]

  // Special conditions
  is_pregnant: boolean
  pregnancy_week?: number
  is_lactating: boolean

  // Anticoagulants
  is_on_anticoagulants: boolean
  anticoagulant_medication?: string
  inr_value?: number
  last_inr_date?: string

  // Lifestyle
  is_smoker: boolean
  smoking_frequency?: string
  alcohol_consumption?: string

  // Dental specific
  bruxism: boolean

  // Anesthesia
  adverse_reactions_to_anesthesia: boolean
  anesthesia_reaction_details?: string

  // Metadata
  last_updated_at?: string
  last_updated_by?: string
}

// Patient Alert
export interface PatientAlert {
  type: 'allergy' | 'pregnancy' | 'lactating' | 'anticoagulant' | 'anesthesia_reaction' | 'systemic_disease'
  severity: 'low' | 'medium' | 'high' | 'critical'
  title: string
  details?: string
}

// Extended Patient (with all new fields)
export interface PatientExtended extends Patient {
  // Extended demographics
  gender?: 'male' | 'female' | 'other' | 'prefer_not_say'
  national_id?: string
  national_id_type?: 'dni' | 'nie' | 'passport'
  profession?: string
  workplace?: string
  preferred_language: string
  address?: PatientAddress
  photo_url?: string

  // Emergency contact
  emergency_contact?: EmergencyContact

  // Legal guardian (for minors)
  legal_guardian?: LegalGuardian

  // Computed alerts
  active_alerts: PatientAlert[]
}

export interface PatientExtendedUpdate extends PatientUpdate {
  // Extended demographics
  gender?: string
  national_id?: string
  national_id_type?: string
  profession?: string
  workplace?: string
  preferred_language?: string
  address?: PatientAddress
  photo_url?: string

  // Emergency contact
  emergency_contact?: EmergencyContact

  // Legal guardian (for minors)
  legal_guardian?: LegalGuardian
}

// Timeline Types
export type TimelineCategory = 'visit' | 'treatment' | 'financial' | 'communication' | 'medical'

export interface TimelineEntry {
  id: string
  event_type: string
  event_category: TimelineCategory
  source_table: string
  source_id: string
  title: string
  description?: string
  event_data?: Record<string, unknown>
  occurred_at: string
  created_by?: string
}

export interface TimelineResponse {
  entries: TimelineEntry[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

// ============================================================================
// Document Types (Media Module)
// ============================================================================

export type DocumentType = 'consent' | 'id_scan' | 'insurance' | 'report' | 'referral' | 'other'

export interface UploaderBrief {
  id: string
  first_name: string
  last_name: string
}

export interface Document {
  id: string
  patient_id: string
  document_type: DocumentType
  title: string
  description?: string
  original_filename: string
  mime_type: string
  file_size: number
  status: 'active' | 'archived'
  uploaded_by: string
  uploader?: UploaderBrief
  created_at: string
  updated_at: string
}

export interface DocumentCreate {
  document_type: DocumentType
  title: string
  description?: string
}

export interface DocumentUpdate {
  document_type?: DocumentType
  title?: string
  description?: string
}

// ============================================================================
// Treatment Plan Types
// ============================================================================

export type TreatmentPlanStatus = 'draft' | 'active' | 'completed' | 'archived' | 'cancelled'

export type PlannedItemStatus = 'pending' | 'completed' | 'cancelled'

export type TreatmentMediaType = 'before' | 'after' | 'xray' | 'reference'

// Brief types for nested responses
export interface ToothTreatmentBrief {
  id: string
  tooth_number: number
  treatment_type: string
  status: TreatmentStatus
  surfaces?: string[]
}

export interface TreatmentCatalogItemBrief {
  id: string
  internal_code: string
  names: Record<string, string>
  default_price?: number
}

// Treatment Media (before/after images)
export interface TreatmentMedia {
  id: string
  document_id: string
  media_type: TreatmentMediaType
  display_order: number
  notes?: string
  created_at: string
}

export interface TreatmentMediaCreate {
  document_id: string
  media_type: TreatmentMediaType
  display_order?: number
  notes?: string
}

// Brief treatment plan info (for embedding in items)
export interface TreatmentPlanBrief {
  id: string
  plan_number: string
  title?: string
  status: TreatmentPlanStatus
}

// Planned Treatment Item
export interface PlannedTreatmentItem {
  id: string
  clinic_id: string
  treatment_plan_id: string
  tooth_treatment_id?: string
  catalog_item_id?: string
  is_global: boolean
  sequence_order: number
  status: PlannedItemStatus
  completed_without_appointment: boolean
  completed_at?: string
  completed_by?: string
  notes?: string
  created_at: string
  updated_at: string
  // Nested data
  tooth_treatment?: ToothTreatmentBrief
  catalog_item?: TreatmentCatalogItemBrief
  media: TreatmentMedia[]
  // Optional plan info (enriched client-side for appointment selector)
  treatment_plan?: TreatmentPlanBrief
}

export interface PlannedTreatmentItemCreate {
  tooth_treatment_id?: string
  catalog_item_id?: string
  is_global?: boolean
  sequence_order?: number
  notes?: string
}

export interface PlannedTreatmentItemUpdate {
  sequence_order?: number
  notes?: string
}

export interface CompleteItemRequest {
  completed_without_appointment?: boolean
  notes?: string
}

// Treatment Plan
export interface TreatmentPlan {
  id: string
  clinic_id: string
  patient_id: string
  plan_number: string
  title?: string
  status: TreatmentPlanStatus
  budget_id?: string
  assigned_professional_id?: string
  created_by: string
  created_at: string
  updated_at: string
  item_count: number
  completed_count: number
  total: number
  patient?: PatientBrief
  budget?: BudgetBrief
}

export interface TreatmentPlanDetail extends TreatmentPlan {
  diagnosis_notes?: string
  internal_notes?: string
  items: PlannedTreatmentItem[]
  patient?: PatientBrief
  budget?: BudgetBrief
}

export interface TreatmentPlanCreate {
  patient_id: string
  title?: string
  assigned_professional_id?: string
  diagnosis_notes?: string
  internal_notes?: string
}

export interface TreatmentPlanUpdate {
  title?: string
  assigned_professional_id?: string
  diagnosis_notes?: string
  internal_notes?: string
}

export interface TreatmentPlanStatusUpdate {
  status: TreatmentPlanStatus
}

// Budget integration
export interface LinkBudgetRequest {
  budget_id: string
}

export interface GenerateBudgetResponse {
  budget_id: string
  budget_number: string
}
