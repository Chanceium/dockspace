<script setup lang="ts">
import { useTheme } from 'vuetify'

import authV1MaskDark from '@images/pages/auth-v1-mask-dark.png'
import authV1MaskLight from '@images/pages/auth-v1-mask-light.png'
import fluke from '@images/svg/fluke.svg?url'
import waves from '@images/svg/waves.svg?url'

const vuetifyTheme = useTheme()

const authThemeMask = computed(() => {
  return vuetifyTheme.global.name.value === 'light'
    ? authV1MaskLight
    : authV1MaskDark
})
</script>

<template>
  <div class="auth-wrapper d-flex align-center justify-center pa-4">
    <VCard
      class="auth-card pa-4 pt-7"
      max-width="640"
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
        <div class="text-body-1 mb-6 text-center">
          You do not have two-factor authentication set up for this application.
        </div>

        <VCard
          variant="outlined"
          class="mb-6"
        >
          <VCardText>
            <div class="text-subtitle-1 font-weight-medium mb-2">
              Why am I seeing this?
            </div>
            <div class="text-body-2 mb-4">
              This application requires a two-factor method to be configured before you can sign in.
            </div>
            <div class="text-subtitle-1 font-weight-medium mb-2">
              What should I do?
            </div>
            <div class="text-body-2">
              Set up two-factor authentication in your account settings, or contact your system administrator for help.
            </div>
          </VCardText>
        </VCard>

        <VBtn
          block
          to="/settings?tab=security"
        >
          Go to Security Settings
        </VBtn>
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
