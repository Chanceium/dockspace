<script setup lang="ts">
import { useTheme } from 'vuetify'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AuthProvider from '@/views/pages/authentication/AuthProvider.vue'
import { useAuthProviders } from '@/composables/useAuthProviders'

import authV1MaskDark from '@images/pages/auth-v1-mask-dark.png'
import authV1MaskLight from '@images/pages/auth-v1-mask-light.png'
import fluke from '@images/svg/fluke.svg?url'
import waves from '@images/svg/waves.svg?url'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  firstName: '',
  lastName: '',
  email: '',
  password: '',
  confirmPassword: '',
  sessionTimeout: 1440,  // 24 hours in minutes
  domainUrl: typeof window !== 'undefined' ? window.location.origin : 'https://example.com',
})

const errorMessage = ref('')
const isLoading = ref(false)

const vuetifyTheme = useTheme()
const { authProviders } = useAuthProviders()

const authThemeMask = computed(() => {
  return vuetifyTheme.global.name.value === 'light'
    ? authV1MaskLight
    : authV1MaskDark
})

const isPasswordVisible = ref(false)
const isConfirmPasswordVisible = ref(false)

const handleSetup = async () => {
  // Validation
  if (!form.value.firstName || !form.value.email || !form.value.password || !form.value.domainUrl) {
    errorMessage.value = 'Please fill in all required fields'
    return
  }

  if (form.value.password !== form.value.confirmPassword) {
    errorMessage.value = 'Passwords do not match'
    return
  }

  if (form.value.password.length < 12) {
    errorMessage.value = 'Password must be at least 12 characters long'
    return
  }

  if (form.value.sessionTimeout < 5) {
    errorMessage.value = 'Session timeout must be at least 5 minutes'
    return
  }

  errorMessage.value = ''
  isLoading.value = true

  try {
    const result = await authStore.completeSetup({
      email: form.value.email,
      password: form.value.password,
      first_name: form.value.firstName,
      last_name: form.value.lastName,
      session_timeout: form.value.sessionTimeout * 60,  // Convert minutes to seconds
      domain_url: form.value.domainUrl,
    })

    console.log('Setup result:', result)
    console.log('Auth store user:', authStore.user)
    console.log('Is authenticated:', authStore.isAuthenticated)

    if (result.success) {
      // Backend automatically logs in the user, so we're already authenticated
      // Use replace instead of push to prevent back button to setup page
      console.log('Attempting to navigate to /management')
      await router.replace('/management')
      console.log('Navigation complete')
    } else {
      errorMessage.value = result.error || 'Setup failed'
    }
  } catch (error) {
    console.error('Setup error:', error)
    errorMessage.value = 'An error occurred during setup'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <!-- eslint-disable vue/no-v-html -->

  <div class="auth-wrapper d-flex align-center justify-center pa-4">
    <VCard
      class="auth-card pa-4 pt-7"
      max-width="448"
    >
      <VCardText class="d-flex justify-center">
        <RouterLink
          to="/"
          class="d-flex align-center gap-3"
        >
          <AppLogo :size="40" />
          <h2 class="font-weight-medium text-2xl text-uppercase">
            Dockspace
          </h2>
        </RouterLink>
      </VCardText>

      <VCardText class="pt-2">
        <h4 class="text-h4 mb-1">
          Setup
        </h4>
        <p class="text-body-2 mb-0">
          Configure your admin account and application settings.
        </p>
      </VCardText>

      <VCardText>
        <VForm @submit.prevent="handleSetup">
          <VRow>
            <!-- Error message -->
            <VCol
              v-if="errorMessage"
              cols="12"
            >
              <VAlert
                type="error"
                variant="tonal"
              >
                {{ errorMessage }}
              </VAlert>
            </VCol>

            <!-- First name -->
            <VCol
              cols="12"
              md="6"
            >
              <VTextField
                v-model="form.firstName"
                label="First name *"
                placeholder="John"
                required
                :disabled="isLoading"
              />
            </VCol>
            <!-- Last name -->
            <VCol
              cols="12"
              md="6"
            >
              <VTextField
                v-model="form.lastName"
                label="Last name"
                placeholder="Doe"
                :disabled="isLoading"
              />
            </VCol>
            <!-- email -->
            <VCol cols="12">
              <VTextField
                v-model="form.email"
                label="Email *"
                placeholder="admin@example.com"
                type="email"
                :disabled="isLoading"
              />
            </VCol>

            <!-- session timeout -->
            <VCol
              cols="12"
              md="6"
            >
              <VTextField
                v-model.number="form.sessionTimeout"
                label="Session timeout (minutes) *"
                hint="Idle session length before logout (min: 5)"
                persistent-hint
                type="number"
                min="5"
                :disabled="isLoading"
              />
            </VCol>

            <!-- domain url -->
            <VCol
              cols="12"
              md="6"
            >
              <VTextField
                v-model="form.domainUrl"
                label="Domain URL *"
                hint="Public URL for this application"
                persistent-hint
                :disabled="isLoading"
              />
            </VCol>

            <!-- password -->
            <VCol cols="12">
              <VTextField
                v-model="form.password"
                label="Password *"
                placeholder="············"
                :type="isPasswordVisible ? 'text' : 'password'"
                autocomplete="password"
                :disabled="isLoading"
                :append-inner-icon="isPasswordVisible ? 'ri-eye-off-line' : 'ri-eye-line'"
                @click:append-inner="isPasswordVisible = !isPasswordVisible"
              />
              <VTextField
                v-model="form.confirmPassword"
                label="Confirm Password *"
                placeholder="············"
                :type="isConfirmPasswordVisible ? 'text' : 'password'"
                autocomplete="new-password"
                :disabled="isLoading"
                :append-inner-icon="isConfirmPasswordVisible ? 'ri-eye-off-line' : 'ri-eye-line'"
                class="mt-4 mb-4"
                @click:append-inner="isConfirmPasswordVisible = !isConfirmPasswordVisible"
              />
              <VBtn
                block
                type="submit"
                :loading="isLoading"
                :disabled="isLoading"
              >
                Create Admin Account
              </VBtn>
            </VCol>

            <!-- auth providers -->
            <template v-if="authProviders.length > 0">
              <VCol
                cols="12"
                class="d-flex align-center"
              >
                <VDivider />
                <span class="mx-4">or</span>
                <VDivider />
              </VCol>

              <VCol
                cols="12"
                class="text-center"
              >
                <AuthProvider />
              </VCol>
            </template>
          </VRow>
        </VForm>
      </VCardText>
    </VCard>

    <VImg
      class="auth-footer-start d-none d-md-block"
      :src="waves"
      :width="250"
    />

    <VImg
      :src="fluke"
      class="auth-footer-end d-none d-md-block"
      :width="350"
    />

    <!-- bg img -->
    <VImg
      class="auth-footer-mask d-none d-md-block"
      :src="authThemeMask"
    />
  </div>
</template>

<style lang="scss">
@use "@core/scss/template/pages/page-auth";
</style>
