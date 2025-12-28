<script setup lang="ts">
import { computed, ref, watchEffect } from 'vue'
import { useTheme } from 'vuetify'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

import authV1MaskDark from '@images/pages/auth-v1-mask-dark.png'
import authV1MaskLight from '@images/pages/auth-v1-mask-light.png'
import fluke from '@images/svg/fluke.svg?url'
import waves from '@images/svg/waves.svg?url'

const form = ref({
  code: '',
})
const errorMessage = ref('')
const isLoading = ref(false)

const vuetifyTheme = useTheme()
const authStore = useAuthStore()
const router = useRouter()

const authThemeMask = computed(() => {
  return vuetifyTheme.global.name.value === 'light'
    ? authV1MaskLight
    : authV1MaskDark
})

const pendingLogin = computed(() => authStore.pendingLogin)

watchEffect(() => {
  if (!pendingLogin.value) {
    router.replace('/login')
  }
})

const handleVerify = async () => {
  if (!pendingLogin.value) {
    await router.replace('/login')
    return
  }
  if (!form.value.code.trim()) {
    errorMessage.value = 'Enter your authentication code'
    return
  }
  errorMessage.value = ''
  isLoading.value = true
  const result = await authStore.login(
    pendingLogin.value.email,
    pendingLogin.value.password,
    form.value.code.trim()
  )
  isLoading.value = false

  if (result.success) {
    await router.replace('/management')
    return
  }

  errorMessage.value = result.error || 'Invalid code, please try again'
}
</script>

<template>
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
        <div class="text-h4 font-weight-medium mb-3 text-center">
          Two-factor required
        </div>
        <div class="text-body-2 mb-6 text-center">
          Enter the 6-digit code from your authenticator app to continue.
        </div>

        <VAlert
          v-if="errorMessage"
          type="error"
          variant="tonal"
          class="mb-4"
        >
          {{ errorMessage }}
        </VAlert>

        <VForm @submit.prevent="handleVerify">
          <VRow>
            <VCol cols="12">
              <VTextField
                v-model="form.code"
                label="Authentication code"
                placeholder="123456"
                inputmode="numeric"
                autocomplete="one-time-code"
                :disabled="isLoading"
              />
            </VCol>

            <VCol cols="12">
              <VBtn
                block
                type="submit"
                :loading="isLoading"
                :disabled="isLoading"
              >
                Verify
              </VBtn>
            </VCol>

            <VCol
              cols="12"
              class="text-center text-base"
            >
              <RouterLink
                class="text-primary"
                to="/login"
              >
                Back to login
              </RouterLink>
            </VCol>
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
