/**
 * Narrow `unknown` thrown by `useApi` / `$fetch` to a user-facing message.
 * Reads, in order: `.data.detail`, `.data.message`, `.message`. Falls back
 * to the provided default.
 */
export function errorMessage(e: unknown, fallback: string): string {
  if (typeof e === 'object' && e !== null) {
    const obj = e as { data?: { detail?: string, message?: string }, message?: string }
    return obj.data?.detail ?? obj.data?.message ?? obj.message ?? fallback
  }
  return fallback
}

export function errorStatus(e: unknown): number | undefined {
  if (typeof e === 'object' && e !== null) {
    return (e as { statusCode?: number }).statusCode
  }
  return undefined
}
