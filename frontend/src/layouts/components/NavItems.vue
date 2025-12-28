<script lang="ts" setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import VerticalNavSectionTitle from '@/@layouts/components/VerticalNavSectionTitle.vue'
import VerticalNavLink from '@layouts/components/VerticalNavLink.vue'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.isAdmin)
</script>

<template>
  <VerticalNavLink
    :item="{
      title: 'Management',
      icon: 'ri-shield-user-line',
      to: '/management',
    }"
    v-if="isAdmin"
  />
  <VerticalNavLink
    :item="{
      title: 'Settings',
      icon: 'ri-settings-4-line',
      to: '/settings',
    }"
  />
</template>
