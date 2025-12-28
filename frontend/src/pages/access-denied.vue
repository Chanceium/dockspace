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
          Access Denied
        </div>
        <div class="text-body-1 mb-6 text-center">
          You do not have permission to access this application.
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
              This application requires you to be a member of specific user groups. Your account is currently not assigned to any of the required groups.
            </div>
            <div class="text-subtitle-1 font-weight-medium mb-2">
              Required Groups:
            </div>
            <VChip
              color="primary"
              variant="tonal"
            >
              Portainer
            </VChip>
          </VCardText>
        </VCard>

        <div class="text-subtitle-1 font-weight-medium mb-2">
          What should I do?
        </div>
        <div class="text-body-2 mb-6">
          Contact your system administrator to request access to this application. They can add you to the appropriate user groups.
        </div>

        <VBtn
          block
          to="/login"
        >
          Back to Login
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
