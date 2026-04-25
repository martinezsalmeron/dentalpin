<script setup lang="ts">
import type { UserCreate, UserRole, UserUpdate } from '~/types'
import type { ClinicUser } from '~/composables/useUsers'

const { t } = useI18n()
const auth = useAuth()
const { isAdmin } = usePermissions()
const { users, isLoading, availableRoles, fetchUsers, createUser, updateUser, deleteUser } = useUsers()

const translatedRoles = computed(() =>
  availableRoles.map(role => ({
    value: role.value,
    label: t(`settings.roles.${role.value}`)
  }))
)

const showCreate = ref(false)
const isCreating = ref(false)
const newUser = ref({ email: '', password: '', first_name: '', last_name: '' })
const selectedRole = ref<UserRole>('receptionist')

const showEdit = ref(false)
const isUpdating = ref(false)
const editing = ref<ClinicUser | null>(null)
const editData = ref({ email: '', first_name: '', last_name: '', is_active: true })
const editSelectedRole = ref<UserRole>('receptionist')

const showDelete = ref(false)
const isDeleting = ref(false)
const toDelete = ref<ClinicUser | null>(null)

onMounted(() => {
  if (isAdmin.value) fetchUsers()
})

watch(isAdmin, (value) => {
  if (value) fetchUsers()
})

function isCurrentUser(userId: string): boolean {
  return auth.user.value?.id === userId
}

type BadgeColor = 'error' | 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'neutral'

function getRoleBadgeColor(role: UserRole): BadgeColor {
  const colors: Record<UserRole, BadgeColor> = {
    admin: 'error',
    dentist: 'info',
    hygienist: 'success',
    assistant: 'warning',
    receptionist: 'neutral'
  }
  return colors[role] || 'neutral'
}

function getRoleLabel(role: UserRole): string {
  return t(`settings.roles.${role}`)
}

function openCreate() {
  newUser.value = { email: '', password: '', first_name: '', last_name: '' }
  selectedRole.value = 'receptionist'
  showCreate.value = true
}

async function handleCreate() {
  isCreating.value = true
  const data: UserCreate = { ...newUser.value, role: selectedRole.value }
  const result = await createUser(data)
  isCreating.value = false
  if (result) showCreate.value = false
}

function openEdit(user: ClinicUser) {
  editing.value = user
  editData.value = {
    email: user.email,
    first_name: user.first_name,
    last_name: user.last_name,
    is_active: user.is_active
  }
  editSelectedRole.value = user.role
  showEdit.value = true
}

async function handleUpdate() {
  if (!editing.value) return
  isUpdating.value = true
  const data: UserUpdate = {
    first_name: editData.value.first_name,
    last_name: editData.value.last_name,
    email: editData.value.email,
    role: editSelectedRole.value,
    is_active: editData.value.is_active
  }
  const result = await updateUser(editing.value.id, data)
  isUpdating.value = false
  if (result) {
    showEdit.value = false
    editing.value = null
  }
}

function openDelete(user: ClinicUser) {
  toDelete.value = user
  showDelete.value = true
}

async function handleDelete() {
  if (!toDelete.value) return
  isDeleting.value = true
  const result = await deleteUser(toDelete.value.id)
  isDeleting.value = false
  if (result) {
    showDelete.value = false
    toDelete.value = null
  }
}
</script>

<template>
  <SectionCard
    icon="i-lucide-users"
    :title="t('settings.users')"
  >
    <template #actions>
      <UButton
        icon="i-lucide-plus"
        size="sm"
        @click="openCreate"
      >
        {{ t('settings.newUser') }}
      </UButton>
    </template>

    <div
      v-if="isLoading"
      class="space-y-3"
    >
      <USkeleton class="h-12 w-full" />
      <USkeleton class="h-12 w-full" />
      <USkeleton class="h-12 w-full" />
    </div>

    <div
      v-else-if="users.length === 0"
      class="text-center py-8 text-muted"
    >
      {{ t('settings.noUsers') }}
    </div>

    <div
      v-else
      class="divide-y divide-[var(--color-border-subtle)]"
    >
      <div
        v-for="user in users"
        :key="user.id"
        class="flex items-center justify-between gap-3 py-3 flex-wrap sm:flex-nowrap"
      >
        <div class="flex items-center gap-3 min-w-0 flex-1">
          <UAvatar
            :alt="user.first_name"
            size="sm"
            class="shrink-0"
          />
          <div class="min-w-0">
            <p class="font-medium text-default truncate">
              {{ user.first_name }} {{ user.last_name }}
              <span
                v-if="isCurrentUser(user.id)"
                class="text-caption text-subtle"
              >{{ t('settings.youTag') }}</span>
            </p>
            <p class="text-caption text-subtle truncate">
              {{ user.email }}
            </p>
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <UBadge
            :color="getRoleBadgeColor(user.role)"
            variant="subtle"
          >
            {{ getRoleLabel(user.role) }}
          </UBadge>
          <UBadge
            v-if="!user.is_active"
            color="error"
            variant="subtle"
          >
            {{ t('common.inactive') }}
          </UBadge>
          <UButton
            icon="i-lucide-pencil"
            size="xs"
            variant="ghost"
            color="neutral"
            :aria-label="t('settings.editUser')"
            @click="openEdit(user)"
          />
          <UButton
            v-if="!isCurrentUser(user.id)"
            icon="i-lucide-trash-2"
            size="xs"
            variant="ghost"
            color="error"
            :aria-label="t('settings.deleteUser')"
            @click="openDelete(user)"
          />
        </div>
      </div>
    </div>

    <!-- Create modal -->
    <UModal v-model:open="showCreate">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon
                name="i-lucide-user-plus"
                class="w-5 h-5 text-primary-accent"
              />
              <h3 class="font-semibold text-default">
                {{ t('settings.createUser') }}
              </h3>
            </div>
          </template>

          <form
            class="space-y-4"
            @submit.prevent="handleCreate"
          >
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <UFormField :label="t('common.firstName')">
                <UInput
                  v-model="newUser.first_name"
                  required
                />
              </UFormField>
              <UFormField :label="t('common.lastName')">
                <UInput
                  v-model="newUser.last_name"
                  required
                />
              </UFormField>
            </div>

            <UFormField :label="t('common.email')">
              <UInput
                v-model="newUser.email"
                type="email"
                required
              />
            </UFormField>

            <UFormField :label="t('common.password')">
              <UInput
                v-model="newUser.password"
                type="password"
                :placeholder="t('common.passwordPlaceholder')"
                required
              />
            </UFormField>

            <UFormField :label="t('common.role')">
              <USelect
                v-model="selectedRole"
                :items="translatedRoles"
                value-key="value"
                label-key="label"
                :placeholder="t('placeholders.selectRole')"
              />
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
                {{ t('settings.createUser') }}
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
                name="i-lucide-user-pen"
                class="w-5 h-5 text-primary-accent"
              />
              <h3 class="font-semibold text-default">
                {{ t('settings.editUser') }}
              </h3>
            </div>
          </template>

          <form
            class="space-y-4"
            @submit.prevent="handleUpdate"
          >
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <UFormField :label="t('common.firstName')">
                <UInput
                  v-model="editData.first_name"
                  required
                />
              </UFormField>
              <UFormField :label="t('common.lastName')">
                <UInput
                  v-model="editData.last_name"
                  required
                />
              </UFormField>
            </div>

            <UFormField :label="t('common.email')">
              <UInput
                v-model="editData.email"
                type="email"
                required
              />
            </UFormField>

            <UFormField :label="t('common.role')">
              <USelect
                v-model="editSelectedRole"
                :items="translatedRoles"
                value-key="value"
                label-key="label"
                :placeholder="t('placeholders.selectRole')"
              />
            </UFormField>

            <div
              v-if="editing && !isCurrentUser(editing.id)"
              class="flex items-center gap-3"
            >
              <USwitch v-model="editData.is_active" />
              <span class="text-sm text-muted">{{ t('settings.userActive') }}</span>
              <span
                v-if="!editData.is_active"
                class="text-xs text-danger-accent"
              >
                {{ t('settings.userInactiveNote') }}
              </span>
            </div>

            <div class="flex justify-end gap-2 pt-4">
              <UButton
                variant="ghost"
                @click="showEdit = false"
              >
                {{ t('common.cancel') }}
              </UButton>
              <UButton
                type="submit"
                :loading="isUpdating"
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
                {{ t('settings.deleteUser') }}
              </h3>
            </div>
          </template>

          <p class="text-muted dark:text-subtle">
            {{ t('settings.deleteUserConfirm') }}
            <strong class="text-default">
              {{ toDelete?.first_name }} {{ toDelete?.last_name }}
            </strong>?
          </p>
          <p class="mt-2 text-caption text-subtle">
            {{ t('settings.deleteUserNote') }}
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
