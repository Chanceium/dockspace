<script lang="ts" setup>
import { useRoute, useRouter } from 'vue-router'
import AccountSettingsAccount from '@/views/pages/account-settings/AccountSettingsAccount.vue'
import AccountSettingsNotification from '@/views/pages/account-settings/AccountSettingsNotification.vue'
import AccountSettingsSecurity from '@/views/pages/account-settings/AccountSettingsSecurity.vue'
import AccountSettingsAppearance from '@/views/pages/account-settings/AccountSettingsAppearance.vue'

const route = useRoute()
const router = useRouter()
const tabOptions = new Set(['account', 'security', 'appearance', 'notification'])
const activeTab = ref(tabOptions.has(route.query.tab as string) ? String(route.query.tab) : 'account')

// tabs
const tabs = [
  { title: 'Account', icon: 'ri-group-line', tab: 'account' },
  { title: 'Security', icon: 'ri-lock-line', tab: 'security' },
  { title: 'Appearance', icon: 'ri-palette-line', tab: 'appearance' },
  { title: 'Notifications', icon: 'ri-notification-3-line', tab: 'notification' },
]

watch(activeTab, value => {
  if (route.query.tab !== value) {
    router.replace({ query: { ...route.query, tab: value } })
  }
})

watch(() => route.query.tab, value => {
  if (typeof value === 'string' && tabOptions.has(value) && activeTab.value !== value)
    activeTab.value = value
})
</script>

<template>
  <div>
    <VTabs
      v-model="activeTab"
      show-arrows
      class="v-tabs-pill"
    >
      <VTab
        v-for="item in tabs"
        :key="item.icon"
        :value="item.tab"
      >
        <VIcon
          size="20"
          start
          :icon="item.icon"
        />
        {{ item.title }}
      </VTab>
    </VTabs>

    <VWindow
      v-model="activeTab"
      class="mt-5 disable-tab-transition"
      :touch="false"
    >
      <!-- Account -->
      <VWindowItem value="account">
        <AccountSettingsAccount />
      </VWindowItem>

      <!-- Security -->
      <VWindowItem value="security">
        <AccountSettingsSecurity />
      </VWindowItem>

      <!-- Appearance -->
      <VWindowItem value="appearance">
        <AccountSettingsAppearance />
      </VWindowItem>

      <!-- Notification -->
      <VWindowItem value="notification">
        <AccountSettingsNotification />
      </VWindowItem>
    </VWindow>
  </div>
</template>
