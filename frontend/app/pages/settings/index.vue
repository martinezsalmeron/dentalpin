<script setup lang="ts">
import type { Cabinet, CabinetCreate, ClinicAddress, ClinicUpdate, UserCreate, UserRole, UserUpdate } from '~/types'
import type { ClinicUser } from '~/composables/useUsers'

const { t } = useI18n()
const auth = useAuth()
const clinic = useClinic()
const { isAdmin } = usePermissions()
const { users, isLoading: usersLoading, availableRoles, fetchUsers, createUser, updateUser, deleteUser } = useUsers()
const { currentLocale, availableLocales, changeLocale } = useLocale()

// Translated role options for USelect
const translatedRoles = computed(() =>
  availableRoles.map(role => ({
    value: role.value,
    label: t(`settings.roles.${role.value}`)
  }))
)

// User creation modal state
const showCreateUserModal = ref(false)
const isCreatingUser = ref(false)
const newUser = ref({
  email: '',
  password: '',
  first_name: '',
  last_name: ''
})
const selectedRole = ref<UserRole>('receptionist')

// User edit modal state
const showEditUserModal = ref(false)
const isEditingUser = ref(false)
const editingUser = ref<ClinicUser | null>(null)
const editUserData = ref({
  email: '',
  first_name: '',
  last_name: '',
  is_active: true
})
const editSelectedRole = ref<UserRole>('receptionist')

// Delete confirmation modal state
const showDeleteModal = ref(false)
const isDeletingUser = ref(false)
const userToDelete = ref<ClinicUser | null>(null)

// Cabinet modal state
const showCreateCabinetModal = ref(false)
const isCreatingCabinet = ref(false)
const newCabinet = ref({
  name: '',
  color: '#3B82F6'
})

const showEditCabinetModal = ref(false)
const isEditingCabinet = ref(false)
const editingCabinet = ref<Cabinet | null>(null)
const editCabinetData = ref({
  name: '',
  color: ''
})

const showDeleteCabinetModal = ref(false)
const isDeletingCabinet = ref(false)
const cabinetToDelete = ref<Cabinet | null>(null)

// Predefined colors for cabinets
const cabinetColors = [
  '#3B82F6', // blue
  '#10B981', // green
  '#F59E0B', // amber
  '#EF4444', // red
  '#8B5CF6', // violet
  '#EC4899', // pink
  '#06B6D4', // cyan
  '#F97316' // orange
]

// Clinic info modal state
const showClinicInfoModal = ref(false)
const isSavingClinicInfo = ref(false)
const clinicInfoForm = ref({
  name: '',
  tax_id: '',
  legal_name: '',
  street: '',
  city: '',
  postal_code: '',
  country: '',
  phone: '',
  email: '',
  timezone: 'Europe/Madrid'
})

// ISO 3166-1 alpha-2 codes used by the country selector. Localized
// labels come from `Intl.DisplayNames` so we get every UI language
// for free. Storing the code (not the name) avoids brittle string
// matches when the user switches locale later.
const COUNTRY_CODES = [
  'AD', 'AE', 'AF', 'AG', 'AL', 'AM', 'AO', 'AR', 'AT', 'AU', 'AZ',
  'BA', 'BB', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BN', 'BO', 'BR', 'BS', 'BT', 'BW', 'BY', 'BZ',
  'CA', 'CD', 'CF', 'CG', 'CH', 'CI', 'CL', 'CM', 'CN', 'CO', 'CR', 'CU', 'CV', 'CY', 'CZ',
  'DE', 'DJ', 'DK', 'DM', 'DO', 'DZ',
  'EC', 'EE', 'EG', 'ER', 'ES', 'ET',
  'FI', 'FJ', 'FM', 'FR',
  'GA', 'GB', 'GD', 'GE', 'GH', 'GM', 'GN', 'GQ', 'GR', 'GT', 'GW', 'GY',
  'HN', 'HR', 'HT', 'HU',
  'ID', 'IE', 'IL', 'IN', 'IQ', 'IR', 'IS', 'IT',
  'JM', 'JO', 'JP',
  'KE', 'KG', 'KH', 'KI', 'KM', 'KN', 'KP', 'KR', 'KW', 'KZ',
  'LA', 'LB', 'LC', 'LI', 'LK', 'LR', 'LS', 'LT', 'LU', 'LV', 'LY',
  'MA', 'MC', 'MD', 'ME', 'MG', 'MH', 'MK', 'ML', 'MM', 'MN', 'MR', 'MT', 'MU', 'MV', 'MW', 'MX', 'MY', 'MZ',
  'NA', 'NE', 'NG', 'NI', 'NL', 'NO', 'NP', 'NR', 'NZ',
  'OM',
  'PA', 'PE', 'PG', 'PH', 'PK', 'PL', 'PT', 'PW', 'PY',
  'QA',
  'RO', 'RS', 'RU', 'RW',
  'SA', 'SB', 'SC', 'SD', 'SE', 'SG', 'SI', 'SK', 'SL', 'SM', 'SN', 'SO', 'SR', 'SS', 'ST', 'SV', 'SY', 'SZ',
  'TD', 'TG', 'TH', 'TJ', 'TL', 'TM', 'TN', 'TO', 'TR', 'TT', 'TV', 'TW', 'TZ',
  'UA', 'UG', 'US', 'UY', 'UZ',
  'VA', 'VC', 'VE', 'VN', 'VU',
  'WS',
  'XK',
  'YE',
  'ZA', 'ZM', 'ZW',
] as const

const countryOptions = computed(() => {
  let displayNames: Intl.DisplayNames | null = null
  try {
    displayNames = new Intl.DisplayNames([currentLocale.value], { type: 'region' })
  } catch {
    displayNames = null
  }
  const collator = new Intl.Collator(currentLocale.value, { sensitivity: 'base' })
  return COUNTRY_CODES.map(code => ({
    value: code,
    label: displayNames?.of(code) ?? code,
  })).sort((a, b) => collator.compare(a.label, b.label))
})

function translateCountry(value: string | undefined | null): string {
  if (!value) return ''
  if (value.length === 2 && /^[A-Za-z]{2}$/.test(value)) {
    try {
      return new Intl.DisplayNames([currentLocale.value], { type: 'region' })
        .of(value.toUpperCase()) ?? value
    } catch {
      return value
    }
  }
  return value
}

// Curated IANA timezone list for the clinic metadata form. Covers the
// Spanish/European market + the Americas; users with exotic needs can
// call the API with any IANA id.
const timezoneOptions = [
  { label: 'Europe/Madrid', value: 'Europe/Madrid' },
  { label: 'Europe/London', value: 'Europe/London' },
  { label: 'Europe/Paris', value: 'Europe/Paris' },
  { label: 'Europe/Berlin', value: 'Europe/Berlin' },
  { label: 'Europe/Lisbon', value: 'Europe/Lisbon' },
  { label: 'Europe/Rome', value: 'Europe/Rome' },
  { label: 'Atlantic/Canary', value: 'Atlantic/Canary' },
  { label: 'America/New_York', value: 'America/New_York' },
  { label: 'America/Chicago', value: 'America/Chicago' },
  { label: 'America/Denver', value: 'America/Denver' },
  { label: 'America/Los_Angeles', value: 'America/Los_Angeles' },
  { label: 'America/Mexico_City', value: 'America/Mexico_City' },
  { label: 'America/Buenos_Aires', value: 'America/Buenos_Aires' },
  { label: 'America/Sao_Paulo', value: 'America/Sao_Paulo' },
  { label: 'UTC', value: 'UTC' }
]

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
    last_name: ''
  }
  selectedRole.value = 'receptionist'
  showCreateUserModal.value = true
}

async function handleCreateUser() {
  isCreatingUser.value = true
  const userData: UserCreate = {
    ...newUser.value,
    role: selectedRole.value
  }
  const result = await createUser(userData)
  isCreatingUser.value = false
  if (result) {
    showCreateUserModal.value = false
  }
}

function openEditUserModal(user: ClinicUser) {
  editingUser.value = user
  editUserData.value = {
    email: user.email,
    first_name: user.first_name,
    last_name: user.last_name,
    is_active: user.is_active
  }
  editSelectedRole.value = user.role
  showEditUserModal.value = true
}

async function handleUpdateUser() {
  if (!editingUser.value) return

  isEditingUser.value = true
  const updateData: UserUpdate = {
    first_name: editUserData.value.first_name,
    last_name: editUserData.value.last_name,
    email: editUserData.value.email,
    role: editSelectedRole.value,
    is_active: editUserData.value.is_active
  }
  const result = await updateUser(editingUser.value.id, updateData)
  isEditingUser.value = false
  if (result) {
    showEditUserModal.value = false
    editingUser.value = null
  }
}

function openDeleteModal(user: ClinicUser) {
  userToDelete.value = user
  showDeleteModal.value = true
}

async function handleDeleteUser() {
  if (!userToDelete.value) return

  isDeletingUser.value = true
  const result = await deleteUser(userToDelete.value.id)
  isDeletingUser.value = false
  if (result) {
    showDeleteModal.value = false
    userToDelete.value = null
  }
}

function isCurrentUser(userId: string): boolean {
  return auth.user.value?.id === userId
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
  return t(`settings.roles.${role}`)
}

// Cabinet functions
function openCreateCabinetModal() {
  newCabinet.value = {
    name: '',
    color: '#3B82F6'
  }
  showCreateCabinetModal.value = true
}

async function handleCreateCabinet() {
  isCreatingCabinet.value = true
  const cabinetData: CabinetCreate = {
    name: newCabinet.value.name,
    color: newCabinet.value.color
  }
  const result = await clinic.createCabinet(cabinetData)
  isCreatingCabinet.value = false
  if (result) {
    showCreateCabinetModal.value = false
  }
}

function openEditCabinetModal(cabinet: Cabinet) {
  editingCabinet.value = cabinet
  editCabinetData.value = {
    name: cabinet.name,
    color: cabinet.color
  }
  showEditCabinetModal.value = true
}

async function handleUpdateCabinet() {
  if (!editingCabinet.value) return

  isEditingCabinet.value = true
  const result = await clinic.updateCabinet(editingCabinet.value.id, {
    name: editCabinetData.value.name,
    color: editCabinetData.value.color
  })
  isEditingCabinet.value = false
  if (result) {
    showEditCabinetModal.value = false
    editingCabinet.value = null
  }
}

function openDeleteCabinetModal(cabinet: Cabinet) {
  cabinetToDelete.value = cabinet
  showDeleteCabinetModal.value = true
}

async function handleDeleteCabinet() {
  if (!cabinetToDelete.value) return

  isDeletingCabinet.value = true
  const result = await clinic.deleteCabinet(cabinetToDelete.value.id)
  isDeletingCabinet.value = false
  if (result) {
    showDeleteCabinetModal.value = false
    cabinetToDelete.value = null
  }
}

// Clinic info functions
function formatAddress(address?: Record<string, string>): string {
  if (!address) return '-'
  const parts = []
  if (address.street) parts.push(address.street)
  const cityLine = [address.postal_code, address.city].filter(Boolean).join(' ')
  if (cityLine) parts.push(cityLine)
  if (address.country) parts.push(translateCountry(address.country))
  return parts.length > 0 ? parts.join(', ') : '-'
}

function openClinicInfoModal() {
  const c = clinic.currentClinic.value
  clinicInfoForm.value = {
    name: c?.name || '',
    tax_id: c?.tax_id || '',
    legal_name: c?.legal_name || '',
    street: c?.address?.street || '',
    city: c?.address?.city || '',
    postal_code: c?.address?.postal_code || '',
    country: c?.address?.country || '',
    phone: c?.phone || '',
    email: c?.email || '',
    timezone: c?.timezone || 'Europe/Madrid'
  }
  showClinicInfoModal.value = true
}

async function handleSaveClinicInfo() {
  isSavingClinicInfo.value = true
  const address: ClinicAddress = {
    street: clinicInfoForm.value.street || undefined,
    city: clinicInfoForm.value.city || undefined,
    postal_code: clinicInfoForm.value.postal_code || undefined,
    country: clinicInfoForm.value.country || undefined
  }
  const updateData: ClinicUpdate = {
    name: clinicInfoForm.value.name || undefined,
    tax_id: clinicInfoForm.value.tax_id || undefined,
    legal_name: clinicInfoForm.value.legal_name || '',
    address,
    phone: clinicInfoForm.value.phone || undefined,
    email: clinicInfoForm.value.email || undefined,
    timezone: clinicInfoForm.value.timezone || undefined
  }
  const result = await clinic.updateClinic(updateData)
  isSavingClinicInfo.value = false
  if (result) {
    showClinicInfoModal.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Page header -->
    <div>
      <h1 class="text-display text-default">
        {{ t('settings.title') }}
      </h1>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Clinic Information (admin only) -->
      <UCard v-if="isAdmin">
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <UIcon
                name="i-lucide-building-2"
                class="w-5 h-5 text-primary-accent"
              />
              <h2 class="font-semibold text-default">
                {{ t('settings.clinicInfo') }}
              </h2>
            </div>
            <UButton
              icon="i-lucide-pencil"
              size="xs"
              variant="ghost"
              @click="openClinicInfoModal"
            >
              {{ t('settings.editClinicInfo') }}
            </UButton>
          </div>
        </template>

        <p class="text-caption text-subtle mb-4">
          {{ t('settings.clinicInfoDescription') }}
        </p>

        <div
          v-if="clinic.isLoading.value"
          class="space-y-3"
        >
          <USkeleton class="h-4 w-24" />
          <USkeleton class="h-4 w-48" />
        </div>

        <div
          v-else-if="clinic.currentClinic.value"
          class="space-y-3"
        >
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="text-sm font-medium text-muted">
                {{ t('settings.clinicName') }}
              </label>
              <p class="text-default">
                {{ clinic.currentClinic.value.name || '-' }}
              </p>
            </div>
            <div>
              <label class="text-sm font-medium text-muted">
                {{ t('settings.taxId') }}
              </label>
              <p class="text-default">
                {{ clinic.currentClinic.value.tax_id || '-' }}
              </p>
            </div>
          </div>

          <div>
            <label class="text-sm font-medium text-muted">
              {{ t('settings.legalName') }}
            </label>
            <p class="text-default">
              {{ clinic.currentClinic.value.legal_name || '-' }}
            </p>
          </div>

          <div>
            <label class="text-sm font-medium text-muted">
              {{ t('settings.street') }}
            </label>
            <p class="text-default">
              {{ formatAddress(clinic.currentClinic.value.address) }}
            </p>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="text-sm font-medium text-muted">
                {{ t('settings.phone') }}
              </label>
              <p class="text-default">
                {{ clinic.currentClinic.value.phone || '-' }}
              </p>
            </div>
            <div>
              <label class="text-sm font-medium text-muted">
                {{ t('common.email') }}
              </label>
              <p class="text-default">
                {{ clinic.currentClinic.value.email || '-' }}
              </p>
            </div>
          </div>
        </div>
      </UCard>

      <!-- Cabinets -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <UIcon
                name="i-lucide-door-open"
                class="w-5 h-5 text-primary-accent"
              />
              <h2 class="font-semibold text-default">
                {{ t('settings.cabinets') }}
              </h2>
            </div>
            <UButton
              v-if="isAdmin"
              icon="i-lucide-plus"
              size="xs"
              variant="ghost"
              @click="openCreateCabinetModal"
            >
              {{ t('settings.addCabinet') }}
            </UButton>
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
          v-else
          class="space-y-2"
        >
          <div
            v-for="cabinet in clinic.cabinets.value"
            :key="cabinet.name"
            class="flex items-center justify-between py-1"
          >
            <div class="flex items-center gap-2">
              <span
                class="w-3 h-3 rounded-full"
                :style="{ backgroundColor: cabinet.color }"
              />
              <span class="text-default">{{ cabinet.name }}</span>
            </div>
            <div
              v-if="isAdmin"
              class="flex items-center gap-1"
            >
              <UButton
                icon="i-lucide-pencil"
                size="xs"
                variant="ghost"
                color="neutral"
                @click="openEditCabinetModal(cabinet)"
              />
              <UButton
                icon="i-lucide-trash-2"
                size="xs"
                variant="ghost"
                color="error"
                @click="openDeleteCabinetModal(cabinet)"
              />
            </div>
          </div>
          <span
            v-if="clinic.cabinets.value.length === 0"
            class="text-muted"
          >
            {{ t('settings.noCabinets') }}
          </span>
        </div>
      </UCard>

      <!-- User profile -->
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-user"
              class="w-5 h-5 text-primary-accent"
            />
            <h2 class="font-semibold text-default">
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
              <p class="font-medium text-default">
                {{ auth.user.value.first_name }} {{ auth.user.value.last_name }}
              </p>
              <p class="text-caption text-subtle">
                {{ auth.user.value.email }}
              </p>
            </div>
          </div>
        </div>
      </UCard>

      <!-- Language settings -->
      <UCard>
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-languages"
              class="w-5 h-5 text-primary-accent"
            />
            <h2 class="font-semibold text-default">
              {{ t('settings.language') }}
            </h2>
          </div>
        </template>

        <p class="text-caption text-subtle mb-4">
          {{ t('settings.languageDescription') }}
        </p>

        <div class="flex gap-2">
          <UButton
            v-for="loc in availableLocales"
            :key="loc.code"
            :variant="currentLocale === loc.code ? 'solid' : 'outline'"
            @click="changeLocale(loc.code)"
          >
            {{ loc.name }}
          </UButton>
        </div>
      </UCard>

      <!-- Catalog link (admin only) -->
      <UCard v-if="isAdmin">
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-list"
              class="w-5 h-5 text-primary-accent"
            />
            <h2 class="font-semibold text-default">
              {{ t('catalog.title') }}
            </h2>
          </div>
        </template>

        <p class="text-caption text-subtle mb-4">
          {{ t('catalog.description') }}
        </p>

        <NuxtLink to="/settings/catalog">
          <UButton icon="i-lucide-arrow-right">
            {{ t('nav.catalog') }}
          </UButton>
        </NuxtLink>
      </UCard>

      <!-- VAT Types link (admin only) -->
      <UCard v-if="isAdmin">
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-percent"
              class="w-5 h-5 text-primary-accent"
            />
            <h2 class="font-semibold text-default">
              {{ t('vatTypes.title') }}
            </h2>
          </div>
        </template>

        <p class="text-caption text-subtle mb-4">
          {{ t('vatTypes.description') }}
        </p>

        <NuxtLink to="/settings/vat-types">
          <UButton icon="i-lucide-arrow-right">
            {{ t('vatTypes.title') }}
          </UButton>
        </NuxtLink>
      </UCard>

      <!-- Notifications link (admin only) -->
      <UCard v-if="isAdmin">
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-mail"
              class="w-5 h-5 text-primary-accent"
            />
            <h2 class="font-semibold text-default">
              {{ t('notifications.title') }}
            </h2>
          </div>
        </template>

        <p class="text-caption text-subtle mb-4">
          {{ t('notifications.description') }}
        </p>

        <NuxtLink to="/settings/notifications">
          <UButton icon="i-lucide-arrow-right">
            {{ t('notifications.title') }}
          </UButton>
        </NuxtLink>
      </UCard>

      <!-- Invoice Series link (admin only) -->
      <UCard v-if="isAdmin">
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-hash"
              class="w-5 h-5 text-primary-accent"
            />
            <h2 class="font-semibold text-default">
              {{ t('invoiceSeries.title') }}
            </h2>
          </div>
        </template>

        <p class="text-caption text-subtle mb-4">
          {{ t('invoiceSeries.description') }}
        </p>

        <NuxtLink to="/settings/invoice-series">
          <UButton icon="i-lucide-arrow-right">
            {{ t('invoiceSeries.title') }}
          </UButton>
        </NuxtLink>
      </UCard>

      <!-- Modules (admin only) -->
      <UCard v-if="isAdmin">
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-puzzle"
              class="w-5 h-5 text-primary-accent"
            />
            <h2 class="font-semibold text-default">
              {{ t('settings.modules.title') }}
            </h2>
          </div>
        </template>

        <p class="text-caption text-subtle mb-4">
          {{ t('settings.modules.description') }}
        </p>

        <NuxtLink to="/settings/modules">
          <UButton icon="i-lucide-arrow-right">
            {{ t('settings.modules.title') }}
          </UButton>
        </NuxtLink>
      </UCard>
    </div>

    <!-- User Management (Admin only) -->
    <UCard v-if="isAdmin">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-users"
              class="w-5 h-5 text-primary-accent"
            />
            <h2 class="font-semibold text-default">
              {{ t('settings.users') }}
            </h2>
          </div>
          <UButton
            icon="i-lucide-plus"
            size="sm"
            @click="openCreateUserModal"
          >
            {{ t('settings.newUser') }}
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
              :color="getRoleBadgeColor(user.role as UserRole)"
              variant="subtle"
            >
              {{ getRoleLabel(user.role as UserRole) }}
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
              @click="openEditUserModal(user)"
            />
            <UButton
              v-if="!isCurrentUser(user.id)"
              icon="i-lucide-trash-2"
              size="xs"
              variant="ghost"
              color="error"
              @click="openDeleteModal(user)"
            />
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
                class="w-5 h-5 text-primary-accent"
              />
              <h3 class="font-semibold text-default">
                {{ t('settings.createUser') }}
              </h3>
            </div>
          </template>

          <form
            class="space-y-4"
            @submit.prevent="handleCreateUser"
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
                @click="showCreateUserModal = false"
              >
                {{ t('common.cancel') }}
              </UButton>
              <UButton
                type="submit"
                :loading="isCreatingUser"
              >
                {{ t('settings.createUser') }}
              </UButton>
            </div>
          </form>
        </UCard>
      </template>
    </UModal>

    <!-- Edit User Modal -->
    <UModal v-model:open="showEditUserModal">
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
            @submit.prevent="handleUpdateUser"
          >
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <UFormField :label="t('common.firstName')">
                <UInput
                  v-model="editUserData.first_name"
                  required
                />
              </UFormField>
              <UFormField :label="t('common.lastName')">
                <UInput
                  v-model="editUserData.last_name"
                  required
                />
              </UFormField>
            </div>

            <UFormField :label="t('common.email')">
              <UInput
                v-model="editUserData.email"
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
              v-if="editingUser && !isCurrentUser(editingUser.id)"
              class="flex items-center gap-3"
            >
              <USwitch v-model="editUserData.is_active" />
              <span class="text-sm text-muted">
                {{ t('settings.userActive') }}
              </span>
              <span
                v-if="!editUserData.is_active"
                class="text-xs text-danger-accent"
              >
                {{ t('settings.userInactiveNote') }}
              </span>
            </div>

            <div class="flex justify-end gap-2 pt-4">
              <UButton
                variant="ghost"
                @click="showEditUserModal = false"
              >
                {{ t('common.cancel') }}
              </UButton>
              <UButton
                type="submit"
                :loading="isEditingUser"
              >
                {{ t('settings.saveChanges') }}
              </UButton>
            </div>
          </form>
        </UCard>
      </template>
    </UModal>

    <!-- Delete Confirmation Modal -->
    <UModal v-model:open="showDeleteModal">
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
              {{ userToDelete?.first_name }} {{ userToDelete?.last_name }}
            </strong>?
          </p>
          <p class="mt-2 text-caption text-subtle">
            {{ t('settings.deleteUserNote') }}
          </p>

          <div class="flex justify-end gap-2 pt-6">
            <UButton
              variant="ghost"
              @click="showDeleteModal = false"
            >
              {{ t('common.cancel') }}
            </UButton>
            <UButton
              color="error"
              :loading="isDeletingUser"
              @click="handleDeleteUser"
            >
              {{ t('common.delete') }}
            </UButton>
          </div>
        </UCard>
      </template>
    </UModal>

    <!-- Create Cabinet Modal -->
    <UModal v-model:open="showCreateCabinetModal">
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
            @submit.prevent="handleCreateCabinet"
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
                @click="showCreateCabinetModal = false"
              >
                {{ t('common.cancel') }}
              </UButton>
              <UButton
                type="submit"
                :loading="isCreatingCabinet"
              >
                {{ t('settings.createCabinet') }}
              </UButton>
            </div>
          </form>
        </UCard>
      </template>
    </UModal>

    <!-- Edit Cabinet Modal -->
    <UModal v-model:open="showEditCabinetModal">
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
            @submit.prevent="handleUpdateCabinet"
          >
            <UFormField :label="t('common.name')">
              <UInput
                v-model="editCabinetData.name"
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
                  :class="editCabinetData.color === color ? 'border-default ring-2 ring-[var(--color-primary)] scale-110' : 'border-transparent'"
                  :style="{ backgroundColor: color }"
                  @click="editCabinetData.color = color"
                />
              </div>
            </UFormField>

            <div class="flex justify-end gap-2 pt-4">
              <UButton
                variant="ghost"
                @click="showEditCabinetModal = false"
              >
                {{ t('common.cancel') }}
              </UButton>
              <UButton
                type="submit"
                :loading="isEditingCabinet"
              >
                {{ t('settings.saveChanges') }}
              </UButton>
            </div>
          </form>
        </UCard>
      </template>
    </UModal>

    <!-- Delete Cabinet Confirmation Modal -->
    <UModal v-model:open="showDeleteCabinetModal">
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
              {{ cabinetToDelete?.name }}
            </strong>?
          </p>
          <p class="mt-2 text-caption text-subtle">
            {{ t('settings.deleteCabinetNote') }}
          </p>

          <div class="flex justify-end gap-2 pt-6">
            <UButton
              variant="ghost"
              @click="showDeleteCabinetModal = false"
            >
              {{ t('common.cancel') }}
            </UButton>
            <UButton
              color="error"
              :loading="isDeletingCabinet"
              @click="handleDeleteCabinet"
            >
              {{ t('common.delete') }}
            </UButton>
          </div>
        </UCard>
      </template>
    </UModal>

    <!-- Edit Clinic Info Modal -->
    <UModal v-model:open="showClinicInfoModal">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon
                name="i-lucide-building-2"
                class="w-5 h-5 text-primary-accent"
              />
              <h3 class="font-semibold text-default">
                {{ t('settings.editClinicInfo') }}
              </h3>
            </div>
          </template>

          <form
            class="space-y-4"
            @submit.prevent="handleSaveClinicInfo"
          >
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <UFormField :label="t('settings.clinicName')">
                <UInput
                  v-model="clinicInfoForm.name"
                  required
                />
              </UFormField>
              <UFormField :label="t('settings.taxId')">
                <UInput v-model="clinicInfoForm.tax_id" />
              </UFormField>
            </div>

            <UFormField
              :label="t('settings.legalName')"
              :help="t('settings.legalNameHelp')"
            >
              <UInput v-model="clinicInfoForm.legal_name" />
            </UFormField>

            <UFormField :label="t('settings.street')">
              <UInput v-model="clinicInfoForm.street" />
            </UFormField>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <UFormField :label="t('settings.postalCode')">
                <UInput v-model="clinicInfoForm.postal_code" />
              </UFormField>
              <UFormField :label="t('settings.city')">
                <UInput v-model="clinicInfoForm.city" />
              </UFormField>
              <UFormField :label="t('settings.country')">
                <USelectMenu
                  v-model="clinicInfoForm.country"
                  :items="countryOptions"
                  value-key="value"
                  label-key="label"
                  searchable
                  :search-input="{ placeholder: t('settings.countrySearchPlaceholder') }"
                  :placeholder="t('settings.countryPlaceholder')"
                  class="w-full"
                />
              </UFormField>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <UFormField :label="t('settings.phone')">
                <UInput
                  v-model="clinicInfoForm.phone"
                  type="tel"
                />
              </UFormField>
              <UFormField :label="t('common.email')">
                <UInput
                  v-model="clinicInfoForm.email"
                  type="email"
                />
              </UFormField>
            </div>

            <UFormField
              :label="t('settings.timezone')"
              :help="t('settings.timezoneHelp')"
            >
              <USelect
                v-model="clinicInfoForm.timezone"
                :items="timezoneOptions"
                value-key="value"
                label-key="label"
              />
            </UFormField>

            <div class="flex justify-end gap-2 pt-4">
              <UButton
                variant="ghost"
                @click="showClinicInfoModal = false"
              >
                {{ t('common.cancel') }}
              </UButton>
              <UButton
                type="submit"
                :loading="isSavingClinicInfo"
              >
                {{ t('settings.saveChanges') }}
              </UButton>
            </div>
          </form>
        </UCard>
      </template>
    </UModal>

    <!-- Extension point for module-provided settings sections. -->
    <ModuleSlot
      name="settings.sections"
      :ctx="{}"
    />
  </div>
</template>
