/**
 * Pure helpers for the inline "create patient" flow in
 * `PatientVisualSelector.vue`. Extracted so they can be unit-tested
 * without standing up a full component mount.
 */

/**
 * Best-effort split of a free-text query into first / last name.
 * First whitespace-delimited token is the given name, the rest becomes
 * the surname. Users always see this pre-filled and can edit before
 * submitting — the heuristic just saves typing for the common case.
 *
 * "María"             → { first: "María",  last: "" }
 * "María García"      → { first: "María",  last: "García" }
 * "María García López"→ { first: "María",  last: "García López" }
 * "  "                → { first: "",       last: "" }
 */
export function splitName(query: string): { first: string, last: string } {
  const trimmed = query.trim().replace(/\s+/g, ' ')
  if (!trimmed) return { first: '', last: '' }
  const parts = trimmed.split(' ')
  if (parts.length === 1) return { first: parts[0] ?? '', last: '' }
  return { first: parts[0] ?? '', last: parts.slice(1).join(' ') }
}

/**
 * Strip the visual separators that humans sprinkle into phone numbers
 * (spaces, dashes, parentheses) so we can compare two strings for
 * "same phone" without false negatives. Country-code differences are
 * intentionally NOT normalized — "+34 600..." and "600..." are
 * different inputs and we should not silently treat them as the same.
 */
export function normalizePhone(p: string): string {
  return p.replace(/[\s\-()]/g, '')
}
