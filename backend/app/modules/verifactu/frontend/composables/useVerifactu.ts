// Composable wrapping the /api/v1/verifactu/* endpoints.
//
// Returns reactive references plus action methods. Uses the shared
// `useApi` composable for auth + token refresh.
import type { ApiResponse, PaginatedResponse } from '~~/app/types'

export interface VerifactuSettings {
  id: string
  clinic_id: string
  enabled: boolean
  environment: 'test' | 'prod'
  nif_emisor: string | null
  nombre_razon_emisor: string | null
  numero_instalacion: string
  last_huella: string | null
  next_send_after: string | null
  last_aeat_response_at: string | null
  has_active_certificate: boolean
  producer_nif: string | null
  producer_name: string | null
  producer_id_sistema: string
  producer_version: string | null
  declaracion_responsable_signed_at: string | null
  declaracion_responsable_signed_by: string | null
}

export interface ProducerDefaults {
  name: string
  nif: string
  id_sistema: string
  version: string
}

export interface ProducerInfoUpdate {
  producer_nif: string
  producer_name: string
  producer_id_sistema: string
  producer_version: string
  sign_declaracion: boolean
}

export interface VerifactuCertificate {
  id: string
  clinic_id: string
  subject_cn: string | null
  issuer_cn: string | null
  nif_titular: string | null
  valid_from: string | null
  valid_until: string | null
  is_active: boolean
  uploaded_by: string | null
  created_at: string
}

export interface VerifactuRecord {
  id: string
  clinic_id: string
  invoice_id: string
  record_type: string
  tipo_factura: string
  tipo_rectificativa: string | null
  serie_numero: string
  fecha_expedicion: string
  cuota_total: string
  importe_total: string
  huella: string
  huella_anterior: string | null
  is_first_record: boolean
  state: string
  aeat_csv: string | null
  aeat_estado_envio: string | null
  aeat_estado_registro: string | null
  aeat_codigo_error: number | null
  aeat_descripcion_error: string | null
  aeat_timestamp_presentacion: string | null
  subsanacion: boolean
  submission_attempt: number
  last_attempt_at: string | null
  created_at: string
}

export interface VerifactuRecordDetail extends VerifactuRecord {
  xml_payload: string | null
  aeat_response_xml: string | null
}

export interface VerifactuQueueItem {
  id: string
  invoice_id: string
  serie_numero: string
  importe_total: string
  state: string
  aeat_codigo_error: number | null
  aeat_descripcion_error: string | null
  submission_attempt: number
  last_attempt_at: string | null
}

export interface VerifactuHealth {
  enabled: boolean
  environment: string | null
  has_certificate: boolean
  certificate_valid_until: string | null
  last_aeat_response_at: string | null
  next_send_after: string | null
  pending_count: number
  rejected_count: number
}

export const useVerifactu = () => {
  const api = useApi()

  return {
    async getSettings() {
      const r = await api.get<ApiResponse<VerifactuSettings>>('/api/v1/verifactu/settings')
      return r.data
    },
    async updateSettings(body: Partial<Pick<VerifactuSettings, 'enabled' | 'environment'>>) {
      const r = await api.put<ApiResponse<VerifactuSettings>>('/api/v1/verifactu/settings', body)
      return r.data
    },
    async getProducerDefaults() {
      const r = await api.get<ApiResponse<ProducerDefaults>>('/api/v1/verifactu/producer/defaults')
      return r.data
    },
    async updateProducer(body: ProducerInfoUpdate) {
      const r = await api.put<ApiResponse<VerifactuSettings>>('/api/v1/verifactu/producer', body)
      return r.data
    },
    async revokeDeclaration() {
      const r = await api.del<ApiResponse<VerifactuSettings>>('/api/v1/verifactu/producer/declaracion')
      return r.data
    },
    async getActiveCertificate() {
      const r = await api.get<ApiResponse<VerifactuCertificate | null>>('/api/v1/verifactu/certificate')
      return r.data
    },
    async getCertificateHistory() {
      const r = await api.get<ApiResponse<VerifactuCertificate[]>>('/api/v1/verifactu/certificate/history')
      return r.data
    },
    async uploadCertificate(file: File, password: string) {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('password', password)
      const r = await api.post<ApiResponse<VerifactuCertificate>>('/api/v1/verifactu/certificate', fd)
      return r.data
    },
    async listRecords(params: { page?: number; page_size?: number; state?: string; tipo_factura?: string } = {}) {
      const r = await api.get<PaginatedResponse<VerifactuRecord>>('/api/v1/verifactu/records', { params })
      return r
    },
    async getRecord(id: string) {
      const r = await api.get<ApiResponse<VerifactuRecordDetail>>(`/api/v1/verifactu/records/${id}`)
      return r.data
    },
    async listQueue(state?: string) {
      const r = await api.get<ApiResponse<VerifactuQueueItem[]>>('/api/v1/verifactu/queue', { params: state ? { state } : undefined })
      return r.data
    },
    async retryRecord(id: string) {
      const r = await api.post<ApiResponse<VerifactuRecord>>(`/api/v1/verifactu/queue/${id}/retry`)
      return r.data
    },
    async processNow() {
      const r = await api.post<ApiResponse<{ processed: number }>>('/api/v1/verifactu/queue/process-now')
      return r.data
    },
    async health() {
      const r = await api.get<ApiResponse<VerifactuHealth>>('/api/v1/verifactu/health')
      return r.data
    },
    async listVatMapping() {
      const r = await api.get<ApiResponse<{ items: VatClassificationItem[] }>>(
        '/api/v1/verifactu/vat-mapping'
      )
      return r.data.items
    },
    async upsertVatMapping(
      vat_type_id: string,
      body: { classification: string | null; exemption_cause?: string | null; notes?: string | null }
    ) {
      const r = await api.put<ApiResponse<VatClassificationItem>>(
        `/api/v1/verifactu/vat-mapping/${vat_type_id}`,
        body
      )
      return r.data
    }
  }
}

export interface VatClassificationItem {
  vat_type_id: string
  label: string
  rate: string
  is_default: boolean
  inferred_classification: string
  inferred_exemption_cause: string | null
  override_classification: string | null
  override_exemption_cause: string | null
  override_notes: string | null
}
