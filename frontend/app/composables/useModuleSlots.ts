/**
 * Slot registry — UI extension points.
 *
 * A "slot" is a named location in the UI (e.g. ``patient.detail.tabs``)
 * where any module can inject a component. Module layers register
 * entries at setup time via :func:`registerSlot`; the host page
 * renders them via :component:`<ModuleSlot>`.
 *
 * Canonical slot names (v1):
 *   - ``patient.detail.tabs``
 *   - ``patient.detail.sidebar``
 *   - ``appointment.detail.actions``
 *   - ``dashboard.widgets``
 *   - ``settings.sections``
 *
 * Registrations are stored in :func:`useState` so SSR + HMR preserve
 * them across reloads and every consumer (across layers) sees the
 * same map.
 */

import type { Component } from 'vue'

export interface SlotEntry<Ctx = unknown> {
  /**
   * Stable identifier for the entry. Required so HMR, re-registration
   * and test cleanup can operate deterministically. Convention:
   * ``<module>.<slot>.<qualifier>`` — e.g. ``billing.patient.detail.sidebar``.
   */
  id: string
  component: Component
  /**
   * Lower numbers render first. Ties resolve in registration order.
   */
  order?: number
  /**
   * Optional permission string (namespaced). When set, the entry
   * renders only when ``usePermissions().can(permission)`` is truthy.
   */
  permission?: string
  /**
   * Optional predicate evaluated at render time with the slot's
   * ``ctx`` prop. Return false to hide the entry for this context.
   */
  condition?: (ctx: Ctx) => boolean
}

type SlotMap = Record<string, SlotEntry[]>

function useSlotState() {
  return useState<SlotMap>('modules:slots', () => ({}))
}

export function registerSlot(name: string, entry: SlotEntry): void {
  const state = useSlotState()
  const current = state.value[name] || []
  // Replace any existing entry with the same id — keeps HMR idempotent.
  const deduped = current.filter(e => e.id !== entry.id)
  state.value = {
    ...state.value,
    [name]: [...deduped, entry]
  }
}

export function unregisterSlot(name: string, id: string): void {
  const state = useSlotState()
  const current = state.value[name]
  if (!current) return
  state.value = {
    ...state.value,
    [name]: current.filter(e => e.id !== id)
  }
}

export function clearSlots(name?: string): void {
  const state = useSlotState()
  state.value = name ? { ...state.value, [name]: [] } : {}
}

export function resolveSlot<Ctx = unknown>(
  name: string,
  ctx: Ctx,
  opts: { can: (p: string) => boolean }
): SlotEntry<Ctx>[] {
  const state = useSlotState()
  const entries = (state.value[name] || []) as SlotEntry<Ctx>[]
  return [...entries]
    .filter((entry) => {
      if (entry.permission && !opts.can(entry.permission)) return false
      if (entry.condition && !entry.condition(ctx)) return false
      return true
    })
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
}

/**
 * Composable wrapper. Named ``useModuleSlots`` to avoid colliding with
 * Vue 3's built-in ``useSlots`` which is also auto-imported by Nuxt.
 */
export function useModuleSlots() {
  const { can } = usePermissions()

  function resolve<Ctx = unknown>(name: string, ctx: Ctx): SlotEntry<Ctx>[] {
    return resolveSlot<Ctx>(name, ctx, { can })
  }

  return {
    register: registerSlot,
    unregister: unregisterSlot,
    clear: clearSlots,
    resolve
  }
}
