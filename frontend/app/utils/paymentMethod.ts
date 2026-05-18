/**
 * Localized label for a payment method. The translation lives under
 * ``invoice.payments.methods.{method}`` in the host i18n bundle so both
 * billing and reports modules read from the same source of truth.
 *
 * Pass the active ``t`` from ``useI18n()`` — the helper stays a pure
 * function so it can be called inside computeds without re-running
 * setup-only composables.
 */
export type TFn = (key: string) => string

export function paymentMethodLabel(t: TFn, method: string): string {
  const label = t(`invoice.payments.methods.${method}`)
  // i18n returns the key when no translation exists — fall back to the raw value
  // so unknown methods (e.g. ``insurance``) still render something readable.
  return label.startsWith('invoice.payments.methods.') ? method : label
}
