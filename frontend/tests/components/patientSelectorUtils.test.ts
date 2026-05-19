import { describe, expect, it } from 'vitest'
import { splitName, normalizePhone } from '../../app/components/shared/patientSelectorUtils'

describe('splitName', () => {
  it('returns empty parts for empty / whitespace input', () => {
    expect(splitName('')).toEqual({ first: '', last: '' })
    expect(splitName('   ')).toEqual({ first: '', last: '' })
  })

  it('puts a single token into first name and leaves last empty', () => {
    expect(splitName('María')).toEqual({ first: 'María', last: '' })
  })

  it('splits a two-token name into first / last', () => {
    expect(splitName('María García')).toEqual({ first: 'María', last: 'García' })
  })

  it('keeps Spanish compound surnames in the last-name field', () => {
    expect(splitName('María García López')).toEqual({
      first: 'María',
      last: 'García López'
    })
  })

  it('collapses internal whitespace before splitting', () => {
    expect(splitName('  María   García   López ')).toEqual({
      first: 'María',
      last: 'García López'
    })
  })
})

describe('normalizePhone', () => {
  it('strips spaces, dashes and parentheses', () => {
    expect(normalizePhone('+34 600-123 456')).toBe('+34600123456')
    expect(normalizePhone('(600) 123 456')).toBe('600123456')
  })

  it('leaves digits and plus-sign untouched', () => {
    expect(normalizePhone('+34600123456')).toBe('+34600123456')
  })

  it('treats two visually different inputs as the same phone', () => {
    expect(normalizePhone('+34 600 123 456')).toBe(normalizePhone('+34-600-123-456'))
  })

  it('does NOT strip the country-code prefix — different prefixes must remain different', () => {
    expect(normalizePhone('+34 600123456')).not.toBe(normalizePhone('600123456'))
  })
})
