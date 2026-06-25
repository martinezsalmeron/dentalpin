<script setup lang="ts">
definePageMeta({
  layout: 'guest'
})

const { t } = useI18n()
const api = useApi()
const auth = useAuth()
const toast = useToast()

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const step = ref<1 | 2>(1)
const isLoading = ref(false)
const errorMessage = ref('')

const form = reactive({
  firstName: '',
  lastName: '',
  email: '',
  password: '',
  passwordConfirm: '',
  clinicName: '',
  taxId: ''
})

const errors = reactive<Record<string, string>>({})

function validateAccount(): boolean {
  errors.firstName = form.firstName.trim() ? '' : t('setup.firstNameRequired')
  errors.lastName = form.lastName.trim() ? '' : t('setup.lastNameRequired')

  const email = form.email.trim()
  if (!email) errors.email = t('setup.emailRequired')
  else if (!EMAIL_RE.test(email)) errors.email = t('setup.emailInvalid')
  else errors.email = ''

  // Mirror the backend strength check: 8+ chars with a letter and a digit.
  if (!form.password) errors.password = t('setup.passwordRequired')
  else if (form.password.length < 8) errors.password = t('setup.passwordTooShort')
  else if (!/[a-zA-Z]/.test(form.password) || !/\d/.test(form.password)) {
    errors.password = t('setup.passwordWeak')
  } else errors.password = ''

  errors.passwordConfirm = form.password === form.passwordConfirm ? '' : t('setup.passwordMismatch')

  return !errors.firstName && !errors.lastName && !errors.email
    && !errors.password && !errors.passwordConfirm
}

function validateClinic(): boolean {
  errors.clinicName = form.clinicName.trim() ? '' : t('setup.clinicNameRequired')
  errors.taxId = form.taxId.trim() ? '' : t('setup.taxIdRequired')
  return !errors.clinicName && !errors.taxId
}

function goNext() {
  errorMessage.value = ''
  if (validateAccount()) step.value = 2
}

function goBack() {
  errorMessage.value = ''
  step.value = 1
}

async function onSubmit() {
  errorMessage.value = ''
  if (!validateClinic()) return

  isLoading.value = true
  try {
    await api.post('/api/v1/auth/setup', {
      admin_first_name: form.firstName.trim(),
      admin_last_name: form.lastName.trim(),
      admin_email: form.email.trim(),
      admin_password: form.password,
      clinic_name: form.clinicName.trim(),
      clinic_tax_id: form.taxId.trim()
    }, { skipAuth: true })

    // ponytail: re-login con las credenciales recién creadas en vez de
    // inyectar los tokens a mano — una request barata y reusa fetchUser.
    await auth.login({ email: form.email.trim(), password: form.password })

    toast.add({ title: t('setup.success'), color: 'success' })
    await navigateTo('/')
  } catch (error: unknown) {
    const status = (error as { statusCode?: number }).statusCode
    if (status === 409) {
      errorMessage.value = t('setup.alreadyInitialized')
    } else if (status === 422) {
      errorMessage.value = t('setup.passwordWeak')
      step.value = 1
    } else {
      errorMessage.value = t('setup.error')
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="w-full max-w-[440px] p-6">
    <div class="text-center mb-6">
      <img
        src="/logo-icon.svg"
        alt="DentalPin"
        width="56"
        height="56"
        class="mx-auto mb-3"
      >
      <h1 class="text-h1 text-default">
        {{ t('setup.title') }}
      </h1>
      <p class="text-caption text-muted mt-1">
        {{ t('setup.subtitle') }}
      </p>
    </div>

    <UCard>
      <!-- Step indicator -->
      <div class="flex items-center gap-2 mb-4 text-caption">
        <span :class="step === 1 ? 'text-default font-medium' : 'text-subtle'">
          1. {{ t('setup.stepAccount') }}
        </span>
        <span class="text-subtle">&middot;</span>
        <span :class="step === 2 ? 'text-default font-medium' : 'text-subtle'">
          2. {{ t('setup.stepClinic') }}
        </span>
      </div>

      <div
        v-if="errorMessage"
        class="alert-surface-danger rounded-token-md px-3 py-2 flex items-start gap-2 mb-4"
        role="alert"
      >
        <UIcon
          name="i-lucide-alert-circle"
          class="w-4 h-4 mt-0.5 shrink-0"
          :style="{ color: 'var(--color-danger-accent)' }"
        />
        <span class="text-body">{{ errorMessage }}</span>
      </div>

      <!-- Step 1: admin account -->
      <form
        v-if="step === 1"
        class="space-y-4"
        @submit.prevent="goNext"
      >
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <UFormField
            :label="t('setup.firstName')"
            name="firstName"
            :error="errors.firstName || undefined"
          >
            <UInput
              v-model="form.firstName"
              class="w-full"
              autocomplete="given-name"
              :disabled="isLoading"
            />
          </UFormField>
          <UFormField
            :label="t('setup.lastName')"
            name="lastName"
            :error="errors.lastName || undefined"
          >
            <UInput
              v-model="form.lastName"
              class="w-full"
              autocomplete="family-name"
              :disabled="isLoading"
            />
          </UFormField>
        </div>

        <UFormField
          :label="t('setup.email')"
          name="email"
          :error="errors.email || undefined"
        >
          <UInput
            v-model="form.email"
            type="email"
            class="w-full"
            icon="i-lucide-mail"
            autocomplete="email"
            :disabled="isLoading"
          />
        </UFormField>

        <UFormField
          :label="t('setup.password')"
          name="password"
          :error="errors.password || undefined"
          :help="t('setup.passwordHint')"
        >
          <UInput
            v-model="form.password"
            type="password"
            class="w-full"
            icon="i-lucide-lock"
            autocomplete="new-password"
            :disabled="isLoading"
          />
        </UFormField>

        <UFormField
          :label="t('setup.passwordConfirm')"
          name="passwordConfirm"
          :error="errors.passwordConfirm || undefined"
        >
          <UInput
            v-model="form.passwordConfirm"
            type="password"
            class="w-full"
            icon="i-lucide-lock"
            autocomplete="new-password"
            :disabled="isLoading"
          />
        </UFormField>

        <UButton
          type="submit"
          color="primary"
          variant="soft"
          block
        >
          {{ t('setup.next') }}
        </UButton>
      </form>

      <!-- Step 2: clinic details -->
      <form
        v-else
        class="space-y-4"
        @submit.prevent="onSubmit"
      >
        <UFormField
          :label="t('setup.clinicName')"
          name="clinicName"
          :error="errors.clinicName || undefined"
        >
          <UInput
            v-model="form.clinicName"
            class="w-full"
            icon="i-lucide-building-2"
            :disabled="isLoading"
          />
        </UFormField>

        <UFormField
          :label="t('setup.taxId')"
          name="taxId"
          :error="errors.taxId || undefined"
        >
          <UInput
            v-model="form.taxId"
            class="w-full"
            icon="i-lucide-hash"
            :disabled="isLoading"
          />
        </UFormField>

        <div class="flex gap-3">
          <UButton
            color="neutral"
            variant="ghost"
            :disabled="isLoading"
            @click="goBack"
          >
            {{ t('setup.back') }}
          </UButton>
          <UButton
            type="submit"
            color="primary"
            variant="soft"
            block
            :loading="isLoading"
            :disabled="isLoading"
          >
            {{ t('setup.submit') }}
          </UButton>
        </div>
      </form>
    </UCard>

    <p class="text-center text-caption text-subtle mt-6">
      &copy; {{ new Date().getFullYear() }} DentalPin
    </p>
  </div>
</template>
