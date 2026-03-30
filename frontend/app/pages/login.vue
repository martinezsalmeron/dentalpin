<script setup lang="ts">
definePageMeta({
  layout: 'guest'
})

const { t } = useI18n()
const auth = useAuth()
const router = useRouter()
const toast = useToast()

// Form state
const isLoading = ref(false)
const formState = reactive({
  email: '',
  password: ''
})
const errorMessage = ref('')

async function onSubmit() {
  errorMessage.value = ''
  isLoading.value = true

  try {
    await auth.login({
      email: formState.email,
      password: formState.password
    })

    toast.add({
      title: t('common.success'),
      description: `${t('auth.login')} ${t('common.success').toLowerCase()}`,
      color: 'success'
    })

    await router.push('/')
  } catch (error: unknown) {
    const fetchError = error as { statusCode?: number }

    if (fetchError.statusCode === 401) {
      errorMessage.value = t('auth.invalidCredentials')
    } else {
      errorMessage.value = t('auth.networkError')
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="w-full max-w-sm p-8">
    <!-- Logo -->
    <div class="text-center mb-8">
      <div class="flex items-center justify-center gap-2 mb-2">
        <UIcon
          name="i-lucide-smile"
          class="w-10 h-10 text-primary-500"
        />
      </div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        DentalPin
      </h1>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
        {{ t('app.tagline') }}
      </p>
    </div>

    <!-- Login form -->
    <UCard>
      <form
        class="space-y-4"
        @submit.prevent="onSubmit"
      >
        <!-- Error message -->
        <UAlert
          v-if="errorMessage"
          color="error"
          variant="subtle"
          :title="errorMessage"
          icon="i-lucide-alert-circle"
        />

        <!-- Email -->
        <UFormField
          :label="t('auth.email')"
          name="email"
          required
        >
          <UInput
            v-model="formState.email"
            type="email"
            class="w-full"
            :placeholder="t('auth.email')"
            icon="i-lucide-mail"
            autocomplete="email"
            :disabled="isLoading"
          />
        </UFormField>

        <!-- Password -->
        <UFormField
          :label="t('auth.password')"
          name="password"
          required
        >
          <UInput
            v-model="formState.password"
            type="password"
            class="w-full"
            :placeholder="t('auth.password')"
            icon="i-lucide-lock"
            autocomplete="current-password"
            :disabled="isLoading"
          />
        </UFormField>

        <!-- Submit -->
        <UButton
          type="submit"
          block
          :loading="isLoading"
          :disabled="isLoading"
        >
          {{ t('auth.loginButton') }}
        </UButton>
      </form>
    </UCard>

    <!-- Footer -->
    <p class="text-center text-xs text-gray-500 dark:text-gray-400 mt-6">
      &copy; {{ new Date().getFullYear() }} DentalPin
    </p>
  </div>
</template>
