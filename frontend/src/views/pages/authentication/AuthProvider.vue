<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthProviders } from '@/composables/useAuthProviders'

const { authProviders, fetchProviders } = useAuthProviders()

onMounted(() => {
  fetchProviders()
})

const handleProviderClick = (provider: any) => {
  // Redirect to the provider's authentication URL
  window.location.href = provider.url
}
</script>

<template>
  <div
    v-if="authProviders.length > 0"
    class="d-flex justify-center gap-2"
  >
    <VBtn
      v-for="provider in authProviders"
      :key="provider.id"
      variant="text"
      :color="provider.color || 'primary'"
      @click="handleProviderClick(provider)"
    >
      <VIcon
        v-if="provider.icon"
        :icon="provider.icon"
      />
      <span v-else>{{ provider.name }}</span>
    </VBtn>
  </div>
</template>
