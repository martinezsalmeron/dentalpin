<script setup lang="ts">
definePageMeta({
  layout: 'guest'
})

const { t } = useI18n()
const auth = useAuth()
const toast = useToast()

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

    await navigateTo('/')
  } catch (error: unknown) {
    console.error('Login error:', error)
    const fetchError = error as { statusCode?: number, message?: string, data?: { message?: string } }

    if (fetchError.statusCode === 401) {
      errorMessage.value = t('auth.invalidCredentials')
    } else {
      errorMessage.value = fetchError.data?.message || fetchError.message || t('auth.networkError')
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="w-full max-w-[400px] p-6">
    <!-- Brand -->
    <div class="text-center mb-6">
      <UIcon
        name="i-lucide-smile"
        class="w-10 h-10 mx-auto mb-2"
        :style="{ color: 'var(--color-primary)' }"
      />
      <h1 class="text-h1 text-default">
        DentalPin
      </h1>
      <p class="text-caption text-muted mt-1">
        {{ t('app.tagline') }}
      </p>
    </div>

    <UCard>
      <form
        class="space-y-4"
        @submit.prevent="onSubmit"
      >
        <!-- Error message — pastel danger (DESIGN §2.4) -->
        <div
          v-if="errorMessage"
          class="alert-surface-danger rounded-token-md px-3 py-2 flex items-start gap-2"
          role="alert"
        >
          <UIcon
            name="i-lucide-alert-circle"
            class="w-4 h-4 mt-0.5 shrink-0"
            :style="{ color: 'var(--color-danger-accent)' }"
          />
          <span class="text-body">
            {{ errorMessage }}
          </span>
        </div>

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

        <UButton
          type="submit"
          color="primary"
          variant="soft"
          block
          :loading="isLoading"
          :disabled="isLoading"
        >
          {{ t('auth.loginButton') }}
        </UButton>
      </form>
    </UCard>

    <p class="text-center text-caption text-subtle mt-6">
      &copy; {{ new Date().getFullYear() }} DentalPin
    </p>
  </div>
</template>
