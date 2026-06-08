// Lightweight client-side pub/sub for cross-module data-change signals.
//
// Mirrors the backend event bus: a publisher (e.g. the copilot, after a
// confirmed write tool) announces that a module's data changed; subscribers
// (e.g. the agenda page) react by refetching. This keeps modules decoupled —
// no cross-layer imports, just a shared channel keyed by module namespace.
//
// Namespaces match the tool/permission namespace (the module name), e.g.
// ``agenda``. The publisher never hardcodes a consumer; it forwards whatever
// namespace the mutated tool reported.

type Handler = () => void

export function useDataBus() {
  // A monotonic tick per namespace. Bumping it is the "event"; subscribers
  // watch their namespace's tick. useState keeps it SSR-safe and shared
  // across every component that calls this composable.
  const channels = useState<Record<string, number>>('databus:ticks', () => ({}))

  function publish(namespace: string): void {
    channels.value = {
      ...channels.value,
      [namespace]: (channels.value[namespace] ?? 0) + 1
    }
  }

  function on(namespace: string, handler: Handler): void {
    if (!import.meta.client) return
    const stop = watch(
      () => channels.value[namespace] ?? 0,
      (next, prev) => {
        if (next !== prev) handler()
      }
    )
    // Auto-clean when the subscribing component's scope is torn down.
    onScopeDispose(stop)
  }

  return { publish, on }
}
