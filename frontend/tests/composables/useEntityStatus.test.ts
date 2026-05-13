import { mountSuspended } from '@nuxt/test-utils/runtime'
import { describe, expect, it } from 'vitest'
import { defineComponent, h, ref } from 'vue'
import type { SemanticRole } from '~/config/severity'

async function runInSetup<T>(fn: () => T): Promise<T> {
  let captured!: T
  await mountSuspended(defineComponent({
    setup() {
      captured = fn()
      return () => h('div')
    }
  }))
  return captured
}

describe('useEntityStatus composable', () => {
  it('should export useEntityStatus function', async () => {
    const module = await import('~/composables/useEntityStatus')
    expect(module.useEntityStatus).toBeDefined()
    expect(typeof module.useEntityStatus).toBe('function')
  })

  it('should map status to semantic role via the provided map', async () => {
    const { useEntityStatus } = await import('~/composables/useEntityStatus')

    const roleMap: Record<'draft' | 'issued', SemanticRole> = {
      draft: 'neutral',
      issued: 'info'
    }
    const status = ref<'draft' | 'issued'>('issued')

    const { role } = await runInSetup(() =>
      useEntityStatus(status, roleMap, 'invoice.status')
    )

    expect(role.value).toBe('info')
    status.value = 'draft'
    expect(role.value).toBe('neutral')
  })

  it('should translate "danger" role to "error" UI colour', async () => {
    const { useEntityStatus } = await import('~/composables/useEntityStatus')

    const { uiColor } = await runInSetup(() =>
      useEntityStatus(
        ref('rejected'),
        { rejected: 'danger' as SemanticRole },
        'invoice.status'
      )
    )

    expect(uiColor.value).toBe('error')
  })

  it('should fall back to neutral when status is missing from map', async () => {
    const { useEntityStatus } = await import('~/composables/useEntityStatus')

    const { role } = await runInSetup(() =>
      useEntityStatus(
        ref('unknown'),
        { known: 'success' as SemanticRole },
        'invoice.status'
      )
    )

    expect(role.value).toBe('neutral')
  })

  it('should fall back to neutral and empty label when status is null', async () => {
    const { useEntityStatus } = await import('~/composables/useEntityStatus')

    const { role, label } = await runInSetup(() =>
      useEntityStatus(
        ref(null),
        {} as Record<string, SemanticRole>,
        'invoice.status'
      )
    )

    expect(role.value).toBe('neutral')
    expect(label.value).toBe('')
  })
})
