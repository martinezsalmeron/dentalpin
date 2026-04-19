/**
 * useDensity — global UI density toggle (comfortable | compact).
 *
 * Persists in localStorage under 'ui:density'. Applies as class on <html>.
 * Forced to 'comfortable' on viewports < 1024 px to keep tap targets ≥ 44 px.
 *
 * DESIGN.md §5
 */
export type Density = 'comfortable' | 'compact'

const STORAGE_KEY = 'ui:density'

export function useDensity() {
  const density = useState<Density>('ui:density', () => 'comfortable')

  function applyToHtml(value: Density) {
    if (!import.meta.client) return
    const html = document.documentElement
    html.classList.remove('density-comfortable', 'density-compact')
    html.classList.add(`density-${value}`)
  }

  function setDensity(value: Density) {
    density.value = value
    if (import.meta.client) {
      localStorage.setItem(STORAGE_KEY, value)
      applyToHtml(value)
    }
  }

  function toggle() {
    setDensity(density.value === 'comfortable' ? 'compact' : 'comfortable')
  }

  function init() {
    if (!import.meta.client) return
    const saved = localStorage.getItem(STORAGE_KEY) as Density | null
    const narrow = window.matchMedia('(max-width: 1023px)').matches
    const initial: Density = narrow ? 'comfortable' : (saved === 'compact' ? 'compact' : 'comfortable')
    density.value = initial
    applyToHtml(initial)
  }

  return {
    density,
    setDensity,
    toggle,
    init
  }
}
