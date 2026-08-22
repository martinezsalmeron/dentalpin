import { describe, expect, it } from 'vitest'
import { INDIA_STATES, useIndiaGstStates } from '#module-layers/india_gst/frontend/composables/useIndiaGstStates'

describe('INDIA_STATES', () => {
  it('contains all 38 states and union territories', () => {
    expect(Object.keys(INDIA_STATES)).toHaveLength(38)
  })

  it('maps Tamil Nadu to code 33', () => {
    expect(INDIA_STATES['33']).toBe('Tamil Nadu')
  })

  it('maps Maharashtra to code 27', () => {
    expect(INDIA_STATES['27']).toBe('Maharashtra')
  })

  it('maps Delhi to code 07', () => {
    expect(INDIA_STATES['07']).toBe('Delhi')
  })

  it('maps Karnataka to code 29', () => {
    expect(INDIA_STATES['29']).toBe('Karnataka')
  })

  it('maps Gujarat to code 24', () => {
    expect(INDIA_STATES['24']).toBe('Gujarat')
  })

  it('includes Other Territory with code 97', () => {
    expect(INDIA_STATES['97']).toBe('Other Territory')
  })

  it('includes Ladakh with code 38', () => {
    expect(INDIA_STATES['38']).toBe('Ladakh')
  })

  it('all values are non-empty strings', () => {
    for (const [code, name] of Object.entries(INDIA_STATES)) {
      expect(code).toMatch(/^\d{2}$/)
      expect(name).toBeTruthy()
      expect(typeof name).toBe('string')
    }
  })

  it('does not include code 25 (Daman and Diu merged into Dadra)', () => {
    expect(INDIA_STATES['25']).toBeUndefined()
  })
})

describe('useIndiaGstStates', () => {
  it('returns INDIA_STATES and options', () => {
    const { INDIA_STATES: states, options } = useIndiaGstStates()
    expect(states).toBe(INDIA_STATES)
    expect(options).toBeDefined()
    expect(Array.isArray(options)).toBe(true)
  })

  it('options have label and value for each state', () => {
    const { options } = useIndiaGstStates()
    expect(options).toHaveLength(38)
    for (const opt of options) {
      expect(opt).toHaveProperty('label')
      expect(opt).toHaveProperty('value')
      expect(opt.label).toContain('(')
      expect(opt.label).toContain(')')
    }
  })

  it('option labels follow "Name (code)" format', () => {
    const { options } = useIndiaGstStates()
    const tn = options.find(o => o.value === '33')
    expect(tn).toBeDefined()
    expect(tn!.label).toBe('Tamil Nadu (33)')
  })

  it('option values are the numeric string codes', () => {
    const { options } = useIndiaGstStates()
    for (const opt of options) {
      expect(opt.value).toMatch(/^\d{2}$/)
    }
  })
})
