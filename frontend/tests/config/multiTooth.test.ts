import { describe, expect, it } from 'vitest'
import {
  calculateToothRange,
  getArchOrder,
  getMultiToothConfig,
  isMultiToothTreatment,
  isSameArch,
  LOWER_ARCH_ORDER,
  MULTI_TOOTH_TREATMENTS,
  UPPER_ARCH_ORDER
} from '~/config/odontogramConstants'

describe('calculateToothRange', () => {
  it('expands a simple upper-right range', () => {
    expect(calculateToothRange(14, 16)).toEqual([16, 15, 14])
  })

  it('returns sorted-by-arch-order result (arch is ordered 18..28)', () => {
    // Arch order upper: 18,17,16,15,14,13,12,11,21,22,23,24,25,26,27,28
    expect(calculateToothRange(16, 14)).toEqual([16, 15, 14])
    expect(calculateToothRange(14, 16)).toEqual([16, 15, 14])
  })

  it('crosses the midline in the upper arch', () => {
    expect(calculateToothRange(13, 23)).toEqual([13, 12, 11, 21, 22, 23])
  })

  it('crosses the midline in the lower arch', () => {
    // Lower order: 48..41, 31..38
    expect(calculateToothRange(43, 33)).toEqual([43, 42, 41, 31, 32, 33])
  })

  it('returns a single tooth when start equals end', () => {
    expect(calculateToothRange(14, 14)).toEqual([14])
  })

  it('throws when teeth span different arches', () => {
    expect(() => calculateToothRange(14, 34)).toThrow('same_arch_required')
  })

  it('throws when either tooth is invalid', () => {
    expect(() => calculateToothRange(14, 99)).toThrow('same_arch_required')
    expect(() => calculateToothRange(99, 14)).toThrow('same_arch_required')
  })
})

describe('getArchOrder', () => {
  it('returns upper arch for upper teeth', () => {
    expect(getArchOrder(18)).toBe(UPPER_ARCH_ORDER)
    expect(getArchOrder(11)).toBe(UPPER_ARCH_ORDER)
    expect(getArchOrder(28)).toBe(UPPER_ARCH_ORDER)
  })

  it('returns lower arch for lower teeth', () => {
    expect(getArchOrder(48)).toBe(LOWER_ARCH_ORDER)
    expect(getArchOrder(31)).toBe(LOWER_ARCH_ORDER)
    expect(getArchOrder(38)).toBe(LOWER_ARCH_ORDER)
  })

  it('returns null for invalid tooth numbers', () => {
    expect(getArchOrder(99)).toBeNull()
    expect(getArchOrder(51)).toBeNull() // deciduous not supported for multi-tooth
  })
})

describe('isSameArch', () => {
  it('is true for a single tooth', () => {
    expect(isSameArch([14])).toBe(true)
  })

  it('is true for an empty array', () => {
    expect(isSameArch([])).toBe(true)
  })

  it('is true for teeth in the same upper arch', () => {
    expect(isSameArch([11, 21, 24])).toBe(true)
  })

  it('is true for teeth in the same lower arch', () => {
    expect(isSameArch([31, 41, 47])).toBe(true)
  })

  it('is false when teeth mix upper and lower arches', () => {
    expect(isSameArch([11, 31])).toBe(false)
  })

  it('is false when any tooth is invalid', () => {
    expect(isSameArch([11, 99])).toBe(false)
  })
})

describe('getMultiToothConfig', () => {
  it('returns bridge config for the bridge key', () => {
    const cfg = getMultiToothConfig('bridge')
    expect(cfg).not.toBeNull()
    expect(cfg?.mode).toBe('bridge')
    expect(cfg?.minTeeth).toBe(2)
    expect(cfg?.selectionMode).toBe('range')
  })

  it('returns uniform config for splint', () => {
    const cfg = getMultiToothConfig('splint')
    expect(cfg?.mode).toBe('uniform')
    expect(cfg?.minTeeth).toBe(2)
    expect(cfg?.selectionMode).toBe('free')
  })

  it('returns null for unknown keys', () => {
    expect(getMultiToothConfig('filling_composite')).toBeNull()
    expect(getMultiToothConfig('unknown')).toBeNull()
  })
})

describe('isMultiToothTreatment', () => {
  it('recognises registered keys', () => {
    for (const key of Object.keys(MULTI_TOOTH_TREATMENTS)) {
      expect(isMultiToothTreatment(key)).toBe(true)
    }
  })

  it('rejects single-tooth treatment types', () => {
    expect(isMultiToothTreatment('crown')).toBe(false)
    expect(isMultiToothTreatment('filling_composite')).toBe(false)
  })
})
