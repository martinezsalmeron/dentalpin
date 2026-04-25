<script setup lang="ts">
import type { Cabinet, CabinetCreate } from '~/types'

const { t } = useI18n()
const clinic = useClinic()
const { isAdmin } = usePermissions()

const cabinetColors = [
  '#3B82F6', '#10B981', '#F59E0B', '#EF4444',
  '#8B5CF6', '#EC4899', '#06B6D4', '#F97316'
]

const showCreate = ref(false)
const isCreating = ref(false)
const newCabinet = ref({ name: '', color: '#3B82F6' })

const showEdit = ref(false)
const isEditing = ref(false)
const editing = ref<Cabinet | null>(null)
const editData = ref({ name: '', color: '' })

const showDelete = ref(false)
const isDeleting = ref(false)
const toDelete = ref<Cabinet | null>(null)

function openCreate() {
  newCabinet.value = { name: '', color: '#3B82F6' }
  showCreate.value = true
}

async function handleCreate() {
  isCreating.value = true
  const data: CabinetCreate = { name: newCabinet.value.name, color: newCabinet.value.color }
  const result = await clinic.createCabinet(data)
  isCreating.value = false
  if (result) showCreate.value = false
}

function openEdit(cabinet: Cabinet) {
  editing.value = cabinet
  editData.value = { name: cabinet.name, color: cabinet.color }
  showEdit.value = true
}

async function handleUpdate() {
  if (!editing.value) return
  isEditing.value = true
  const result = await clinic.updateCabinet(editing.value.id, {
    name: editData.value.name,
    color: editData.value.color
  })
  isEditing.value = false
  if (result) {
    showEdit.value = false
    editing.value = null
  }
}

function openDelete(cabinet: Cabinet) {
  toDelete.value = cabinet
  showDelete.value = true
}

async function handleDelete() {
  if (!toDelete.value) return
  isDeleting.value = true
  const result = await clinic.deleteCabinet(toDelete.value.id)
  isDeleting.value = false
  if (result) {
    showDelete.value = false
    toDelete.value = null
  }
}
</script>

<template>
  <SectionCard
    icon="i-lucide-door-open"
    :title="t('settings.cabinets')"
  >
    <template
      v-if="isAdmin"
      #actions
    >
      <UButton
        icon="i-lucide-plus"
        size="xs"
        variant="ghost"
        @click="openCreate"
      >
        {{ t('settings.addCabinet') }}
      </UButton>
    </template>

    <p class="text-caption text-subtle mb-4">
      {{ t('settings.cabinetsDescription') }}
    </p>

    <div
      v-if="clinic.isLoading.value"
      class="space-y-3"
    >
      <USkeleton class="h-8 w-full" />
      <USkeleton class="h-8 w-full" />
    </div>

    <div v-else>
      <div
        v-if="clinic.cabinets.value.length === 0"
        class="text-muted py-2"
      >
        {{ t('settings.noCabinets') }}
      </div>

      <ul
        v-else
        class="divide-y divide-[var(--color-border-subtle)]"
      >
        <li
          v-for="cabinet in clinic.cabinets.value"
          :key="cabinet.id"
          class="flex items-center justify-between gap-3 py-3 min-h-[44px]"
        >
          <div class="flex items-center gap-3 min-w-0">
            <span
              class="w-3 h-3 rounded-full shrink-0"
              :style="{ backgroundColor: cabinet.color }"
            />
            <span class="text-default truncate">{{ cabinet.name }}</span>
          </div>
          <div
            v-if="isAdmin"
            class="flex items-center gap-1 shrink-0"
          >
            <UButton
              icon="i-lucide-pencil"
              size="xs"
              variant="ghost"
              color="neutral"
              :aria-label="t('settings.editCabinet')"
              @click="openEdit(cabinet)"
            />
            <UButton
              icon="i-lucide-trash-2"
              size="xs"
              variant="ghost"
              color="error"
              :aria-label="t('settings.deleteCabinet')"
              @click="openDelete(cabinet)"
            />
          </div>
        </li>
      </ul>
    </div>

    <!-- Create modal -->
    <UModal v-model:open="showCreate">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon
                name="i-lucide-square-plus"
                class="w-5 h-5 text-primary-accent"
              />
              <h3 class="font-semibold text-default">
                {{ t('settings.newCabinet') }}
              </h3>
            </div>
          </template>

          <form
            class="space-y-4"
            @submit.prevent="handleCreate"
          >
            <UFormField :label="t('common.name')">
              <UInput
                v-model="newCabinet.name"
                required
              />
            </UFormField>

            <UFormField :label="t('common.color')">
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="color in cabinetColors"
                  :key="color"
                  type="button"
                  class="w-8 h-8 rounded-full border-2 transition-all"
                  :class="newCabinet.color === color ? 'border-default ring-2 ring-[var(--color-primary)] scale-110' : 'border-transparent'"
                  :style="{ backgroundColor: color }"
                  @click="newCabinet.color = color"
                />
              </div>
            </UFormField>

            <div class="flex justify-end gap-2 pt-4">
              <UButton
                variant="ghost"
                @click="showCreate = false"
              >
                {{ t('common.cancel') }}
              </UButton>
              <UButton
                type="submit"
                :loading="isCreating"
              >
                {{ t('settings.createCabinet') }}
              </UButton>
            </div>
          </form>
        </UCard>
      </template>
    </UModal>

    <!-- Edit modal -->
    <UModal v-model:open="showEdit">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon
                name="i-lucide-pencil"
                class="w-5 h-5 text-primary-accent"
              />
              <h3 class="font-semibold text-default">
                {{ t('settings.editCabinet') }}
              </h3>
            </div>
          </template>

          <form
            class="space-y-4"
            @submit.prevent="handleUpdate"
          >
            <UFormField :label="t('common.name')">
              <UInput
                v-model="editData.name"
                required
              />
            </UFormField>

            <UFormField :label="t('common.color')">
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="color in cabinetColors"
                  :key="color"
                  type="button"
                  class="w-8 h-8 rounded-full border-2 transition-all"
                  :class="editData.color === color ? 'border-default ring-2 ring-[var(--color-primary)] scale-110' : 'border-transparent'"
                  :style="{ backgroundColor: color }"
                  @click="editData.color = color"
                />
              </div>
            </UFormField>

            <div class="flex justify-end gap-2 pt-4">
              <UButton
                variant="ghost"
                @click="showEdit = false"
              >
                {{ t('common.cancel') }}
              </UButton>
              <UButton
                type="submit"
                :loading="isEditing"
              >
                {{ t('settings.saveChanges') }}
              </UButton>
            </div>
          </form>
        </UCard>
      </template>
    </UModal>

    <!-- Delete modal -->
    <UModal v-model:open="showDelete">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon
                name="i-lucide-alert-triangle"
                class="w-5 h-5 text-danger-accent"
              />
              <h3 class="font-semibold text-default">
                {{ t('settings.deleteCabinet') }}
              </h3>
            </div>
          </template>

          <p class="text-muted dark:text-subtle">
            {{ t('settings.deleteCabinetConfirm') }}
            <strong class="text-default">
              {{ toDelete?.name }}
            </strong>?
          </p>
          <p class="mt-2 text-caption text-subtle">
            {{ t('settings.deleteCabinetNote') }}
          </p>

          <div class="flex justify-end gap-2 pt-6">
            <UButton
              variant="ghost"
              @click="showDelete = false"
            >
              {{ t('common.cancel') }}
            </UButton>
            <UButton
              color="error"
              :loading="isDeleting"
              @click="handleDelete"
            >
              {{ t('common.delete') }}
            </UButton>
          </div>
        </UCard>
      </template>
    </UModal>
  </SectionCard>
</template>
