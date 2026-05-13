import type { MaybeRef } from 'vue'
import type { SemanticRole, UiColor } from '~/config/severity'
import { roleToUiColor } from '~/config/severity'

export interface EntityStatusBinding {
  role: ComputedRef<SemanticRole>
  label: ComputedRef<string>
  uiColor: ComputedRef<UiColor>
}

export function useEntityStatus<T extends string>(
  status: MaybeRef<T | undefined | null>,
  roleMap: Record<T, SemanticRole>,
  labelKeyPrefix: string
): EntityStatusBinding {
  const { t } = useI18n()

  const role = computed<SemanticRole>(() => {
    const value = unref(status)
    if (!value) return 'neutral'
    return roleMap[value] ?? 'neutral'
  })

  const label = computed(() => {
    const value = unref(status)
    return value ? t(`${labelKeyPrefix}.${value}`) : ''
  })

  const uiColor = computed<UiColor>(() => roleToUiColor(role.value))

  return { role, label, uiColor }
}
