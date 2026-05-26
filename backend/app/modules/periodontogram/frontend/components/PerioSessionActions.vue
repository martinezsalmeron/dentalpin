<script setup lang="ts">
/**
 * Sticky bottom action bar for an active draft.
 *
 * Discard requires explicit confirmation. Close prompts for an
 * optional note before flipping the snapshot to immutable.
 */
import { ref } from 'vue'

defineProps<{
  saving: boolean
  dirty: boolean
}>()

const emit = defineEmits<{
  close: [notes: string | null]
  discard: []
}>()

const showClose = ref(false)
const showDiscard = ref(false)
const notes = ref('')

function confirmClose() {
  emit('close', notes.value.trim() || null)
  showClose.value = false
  notes.value = ''
}

function confirmDiscard() {
  emit('discard')
  showDiscard.value = false
}
</script>

<template>
  <div
    class="perio-session-actions sticky bottom-0 z-10 flex items-center justify-between border-t border-gray-200 bg-white/95 px-4 py-3 backdrop-blur"
    role="toolbar"
    aria-label="Acciones de la sesión periodontal"
  >
    <div
      class="flex items-center gap-2 text-xs"
      aria-live="polite"
      role="status"
    >
      <UIcon
        v-if="saving"
        name="i-lucide-loader-2"
        class="animate-spin text-gray-500"
        aria-hidden="true"
      />
      <span v-if="saving" class="text-gray-500">Guardando…</span>
      <span v-else-if="dirty" class="text-amber-600">Cambios pendientes</span>
      <span v-else class="text-emerald-600">Guardado</span>
    </div>

    <div class="flex items-center gap-2">
      <UButton variant="ghost" color="error" @click="showDiscard = true">
        Descartar borrador
      </UButton>
      <UButton icon="i-lucide-check" @click="showClose = true">
        Cerrar sesión
      </UButton>
    </div>

    <UModal
      :open="showClose"
      title="Cerrar sesión periodontal"
      @update:open="(v) => { showClose = v }"
    >
      <template #body>
        <div class="space-y-3 p-4">
          <p class="text-sm text-gray-600">
            Una vez cerrada, la sesión queda inmutable y aparece en el historial.
            Para correcciones tendrás que abrir una nueva sesión.
          </p>
          <UFormField label="Nota (opcional)">
            <UTextarea
              v-model="notes"
              :rows="3"
              placeholder="Observaciones de la exploración…"
            />
          </UFormField>
        </div>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2 p-2">
          <UButton variant="outline" color="neutral" @click="showClose = false">
            Cancelar
          </UButton>
          <UButton color="primary" @click="confirmClose">
            Cerrar sesión
          </UButton>
        </div>
      </template>
    </UModal>

    <UModal
      :open="showDiscard"
      title="Descartar borrador"
      @update:open="(v) => { showDiscard = v }"
    >
      <template #body>
        <div class="p-4">
          <p class="text-sm text-gray-600">
            Se eliminarán todos los datos introducidos en esta sesión.
            Esta acción no se puede deshacer.
          </p>
        </div>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2 p-2">
          <UButton variant="outline" color="neutral" @click="showDiscard = false">
            Cancelar
          </UButton>
          <UButton color="error" @click="confirmDiscard">
            Descartar
          </UButton>
        </div>
      </template>
    </UModal>
  </div>
</template>
