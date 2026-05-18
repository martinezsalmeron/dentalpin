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
