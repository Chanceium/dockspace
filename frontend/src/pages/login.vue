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
  email: '',
  password: '',
  remember: false,
})

const errorMessage = ref('')
const isLoading = ref(false)
const requiresTOTPRedirect = ref(false)

const vuetifyTheme = useTheme()
const { authProviders } = useAuthProviders()

const authThemeMask = computed(() => {
  return vuetifyTheme.global.name.value === 'light'
    ? authV1MaskLight
    : authV1MaskDark
})

const isPasswordVisible = ref(false)

const handleLogin = async () => {
  if (!form.value.email || !form.value.password) {
    errorMessage.value = 'Please enter your email and password'
    return
  }

  errorMessage.value = ''
  isLoading.value = true

  try {
    const result = await authStore.login(form.value.email, form.value.password)

    if (result.success) {
      // Use replace instead of push to prevent back button to login page
      await router.replace('/management')
    } else {
      if (result.requiresTOTP) {
        // Don't show error for 2FA - just redirect to TOTP page
        requiresTOTPRedirect.value = true
        await router.replace('/two-factor-required')
      } else {
        // Only show error if it's an actual login failure
        errorMessage.value = result.error || 'Login failed'
      }
    }
  } catch (error) {
    errorMessage.value = 'An error occurred during login'
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

      <VCardText>
        <VForm @submit.prevent="handleLogin">
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

            <!-- email -->
            <VCol cols="12">
              <VTextField
                v-model="form.email"
                label="Email"
                type="email"
                :disabled="isLoading"
              />
            </VCol>

            <!-- password -->
            <VCol cols="12">
              <VTextField
                v-model="form.password"
                label="Password"
                placeholder="············"
                :type="isPasswordVisible ? 'text' : 'password'"
                autocomplete="password"
                :disabled="isLoading"
                :append-inner-icon="isPasswordVisible ? 'ri-eye-off-line' : 'ri-eye-line'"
                @click:append-inner="isPasswordVisible = !isPasswordVisible"
              />

              <!-- remember me checkbox -->
              <div class="d-flex align-center justify-space-between flex-wrap my-6">
                <VCheckbox
                  v-model="form.remember"
                  label="Remember me"
                />

                <RouterLink
                  class="text-primary"
                  to="/reset-password"
                >
                  Forgot Password?
                </RouterLink>
              </div>

              <!-- login button -->
              <VBtn
                block
                type="submit"
                :loading="isLoading"
                :disabled="isLoading"
              >
                Login
              </VBtn>
            </VCol>

            <!-- create account -->
            <VCol
              cols="12"
              class="text-center text-base"
            >
              <span>New on our platform?</span>
              <RouterLink
                class="text-primary ms-2"
                to="/register"
              >
                Create an account
              </RouterLink>
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
