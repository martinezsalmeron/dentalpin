<script setup lang="ts">
import type { UserCreate, UserRole } from '~/types'

const { t } = useI18n()
const auth = useAuth()
const clinic = useClinic()
const { isAdmin } = usePermissions()
const { users, isLoading: usersLoading, availableRoles, fetchUsers, createUser } = useUsers()

// User creation modal state
const showCreateUserModal = ref(false)
const isCreatingUser = ref(false)
const newUser = ref<UserCreate>({
  email: '',
  password: '',
  first_name: '',
  last_name: '',
  role: 'receptionist'
})

// Fetch users when admin visits the page
onMounted(() => {
  if (isAdmin.value) {
    fetchUsers()
  }
})

// Watch for permission changes
watch(isAdmin, (value) => {
  if (value) {
    fetchUsers()
  }
})

function openCreateUserModal() {
  newUser.value = {
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'receptionist'
  }
  showCreateUserModal.value = true
}

async function handleCreateUser() {
  isCreatingUser.value = true
  const result = await createUser(newUser.value)
  isCreatingUser.value = false
  if (result) {
    showCreateUserModal.value = false
  }
}

function getRoleBadgeColor(role: UserRole): string {
  const colors: Record<UserRole, string> = {
    admin: 'red',
    dentist: 'blue',
    hygienist: 'green',
    assistant: 'yellow',
    receptionist: 'gray'
  }
  return colors[role] || 'gray'
}

function getRoleLabel(role: UserRole): string {
  const labels: Record<UserRole, string> = {
    admin: 'Administrador',
    dentist: 'Dentista',
    hygienist: 'Higienista',
    assistant: 'Auxiliar',
    receptionist: 'Recepcionista'
  }
  return labels[role] || role
}
</script>

<template>
  <div class="space-y-6">
    <!-- Page header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ t('settings.title') }}
      </h1>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Clinic info -->
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-building-2"
              class="w-5 h-5 text-primary-500"
            />
            <h2 class="font-semibold text-gray-900 dark:text-white">
              {{ t('settings.clinic') }}
            </h2>
          </div>
        </template>

        <div
          v-if="clinic.isLoading.value"
          class="space-y-3"
        >
          <USkeleton class="h-4 w-24" />
          <USkeleton class="h-4 w-48" />
        </div>

        <div
          v-else-if="clinic.currentClinic.value"
          class="space-y-4"
        >
          <div>
            <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
              {{ t('settings.clinicName') }}
            </label>
            <p class="text-gray-900 dark:text-white">
              {{ clinic.currentClinic.value.name }}
            </p>
          </div>

          <div>
            <label class="text-sm font-medium text-gray-500 dark:text-gray-400">
              {{ t('settings.cabinets') }}
            </label>
            <div class="flex flex-wrap gap-2 mt-1">
              <UBadge
                v-for="cabinet in clinic.cabinets.value"
                :key="cabinet.name"
                variant="subtle"
                :style="{ backgroundColor: cabinet.color + '20', color: cabinet.color }"
              >
                {{ cabinet.name }}
              </UBadge>
              <span
                v-if="clinic.cabinets.value.length === 0"
                class="text-gray-500 dark:text-gray-400"
              >
                -
              </span>
            </div>
          </div>
        </div>

        <div
          v-else
          class="text-gray-500 dark:text-gray-400"
        >
          {{ t('common.noData') }}
        </div>
      </UCard>

      <!-- User profile -->
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-user"
              class="w-5 h-5 text-primary-500"
            />
            <h2 class="font-semibold text-gray-900 dark:text-white">
              {{ t('settings.profile') }}
            </h2>
          </div>
        </template>

        <div
          v-if="auth.user.value"
          class="space-y-4"
        >
          <div class="flex items-center gap-4">
            <UAvatar
              :alt="auth.user.value.first_name"
              size="lg"
            />
            <div>
              <p class="font-medium text-gray-900 dark:text-white">
                {{ auth.user.value.first_name }} {{ auth.user.value.last_name }}
              </p>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                {{ auth.user.value.email }}
              </p>
            </div>
          </div>
        </div>
      </UCard>
    </div>

    <!-- User Management (Admin only) -->
    <UCard v-if="isAdmin">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-users"
              class="w-5 h-5 text-primary-500"
            />
            <h2 class="font-semibold text-gray-900 dark:text-white">
              Usuarios de la Clínica
            </h2>
          </div>
          <UButton
            icon="i-lucide-plus"
            size="sm"
            @click="openCreateUserModal"
          >
            Nuevo Usuario
          </UButton>
        </div>
      </template>

      <div
        v-if="usersLoading"
        class="space-y-3"
      >
        <USkeleton class="h-12 w-full" />
        <USkeleton class="h-12 w-full" />
        <USkeleton class="h-12 w-full" />
      </div>

      <div
        v-else-if="users.length === 0"
        class="text-center py-8 text-gray-500 dark:text-gray-400"
      >
        No hay usuarios registrados
      </div>

      <div
        v-else
        class="divide-y divide-gray-200 dark:divide-gray-700"
      >
        <div
          v-for="user in users"
          :key="user.id"
          class="flex items-center justify-between py-3"
        >
          <div class="flex items-center gap-3">
            <UAvatar
              :alt="user.first_name"
              size="sm"
            />
            <div>
              <p class="font-medium text-gray-900 dark:text-white">
                {{ user.first_name }} {{ user.last_name }}
              </p>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                {{ user.email }}
              </p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <UBadge
              :color="getRoleBadgeColor(user.role as UserRole)"
              variant="subtle"
            >
              {{ getRoleLabel(user.role as UserRole) }}
            </UBadge>
            <UBadge
              v-if="!user.is_active"
              color="red"
              variant="subtle"
            >
              Inactivo
            </UBadge>
          </div>
        </div>
      </div>
    </UCard>

    <!-- Create User Modal -->
    <UModal v-model:open="showCreateUserModal">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon
                name="i-lucide-user-plus"
                class="w-5 h-5 text-primary-500"
              />
              <h3 class="font-semibold text-gray-900 dark:text-white">
                Crear Nuevo Usuario
              </h3>
            </div>
          </template>

          <form
            class="space-y-4"
            @submit.prevent="handleCreateUser"
          >
            <div class="grid grid-cols-2 gap-4">
              <UFormField label="Nombre">
                <UInput
                  v-model="newUser.first_name"
                  placeholder="Juan"
                  required
                />
              </UFormField>
              <UFormField label="Apellidos">
                <UInput
                  v-model="newUser.last_name"
                  placeholder="Garcia"
                  required
                />
              </UFormField>
            </div>

            <UFormField label="Email">
              <UInput
                v-model="newUser.email"
                type="email"
                placeholder="usuario@ejemplo.com"
                required
              />
            </UFormField>

            <UFormField label="Contrasena">
              <UInput
                v-model="newUser.password"
                type="password"
                placeholder="Minimo 8 caracteres"
                required
              />
            </UFormField>

            <UFormField label="Rol">
              <USelect
                v-model="newUser.role"
                :items="availableRoles"
                value-key="value"
                label-key="label"
              />
            </UFormField>

            <div class="flex justify-end gap-2 pt-4">
              <UButton
                variant="ghost"
                @click="showCreateUserModal = false"
              >
                Cancelar
              </UButton>
              <UButton
                type="submit"
                :loading="isCreatingUser"
              >
                Crear Usuario
              </UButton>
            </div>
          </form>
        </UCard>
      </template>
    </UModal>
  </div>
</template>
