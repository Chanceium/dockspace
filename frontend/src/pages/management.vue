<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { mailService } from '@/services/mail'
import { oidcService } from '@/services/oidc'
import StatsCard from '@/components/management/StatsCard.vue'
import MailManagementTab from '@/views/pages/management/MailManagementTab.vue'
import ApplicationSettingsTab from '@/views/pages/management/ApplicationSettingsTab.vue'
import AuditHistoryCard from '@/components/management/AuditHistoryCard.vue'

// Tab management
const route = useRoute()
const router = useRouter()
const tabOptions = new Set(['mail-management', 'application-settings'])
const activeTab = ref(tabOptions.has(route.query.tab as string) ? String(route.query.tab) : 'mail-management')

const tabs = [
  { title: 'Mail Management', icon: 'ri-mail-settings-line', tab: 'mail-management' },
  { title: 'Application Settings', icon: 'ri-settings-4-line', tab: 'application-settings' },
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

// Statistics state
const accountsCount = ref(0)
const groupsCount = ref(0)
const aliasesCount = ref(0)
const oidcClientsCount = ref(0)
const isLoadingAccounts = ref(false)
const isLoadingGroups = ref(false)
const isLoadingAliases = ref(false)
const isLoadingOidc = ref(false)

// Statistics
const stats = computed(() => ([
  { title: 'Accounts', value: accountsCount.value, icon: 'ri-user-line', color: 'primary', loading: isLoadingAccounts.value },
  { title: 'Groups', value: groupsCount.value, icon: 'ri-group-line', color: 'info', loading: isLoadingGroups.value },
  { title: 'Aliases', value: aliasesCount.value, icon: 'ri-mail-line', color: 'success', loading: isLoadingAliases.value },
  { title: 'OIDC Clients', value: oidcClientsCount.value, icon: 'ri-shield-keyhole-line', color: 'warning', loading: isLoadingOidc.value },
]))

// Load stats
const loadStats = async () => {
  isLoadingAccounts.value = true
  isLoadingAliases.value = true
  isLoadingGroups.value = true
  isLoadingOidc.value = true

  const [accountsRes, aliasesRes, groupsRes, oidcRes] = await Promise.all([
    mailService.listAccounts(),
    mailService.listAliases(),
    mailService.listGroups(),
    oidcService.listClients(),
  ])

  if (accountsRes.success && accountsRes.accounts) {
    accountsCount.value = accountsRes.accounts.length
  }
  if (aliasesRes.success && aliasesRes.aliases) {
    aliasesCount.value = aliasesRes.aliases.length
  }
  if (groupsRes.success && groupsRes.groups) {
    groupsCount.value = groupsRes.groups.length
  }
  if (oidcRes.success && oidcRes.clients) {
    oidcClientsCount.value = oidcRes.clients.length
  }

  isLoadingAccounts.value = false
  isLoadingAliases.value = false
  isLoadingGroups.value = false
  isLoadingOidc.value = false
}

// Load data on mount
onMounted(() => {
  loadStats()
})
</script>

<template>
  <VRow>
    <!-- Statistics Cards -->
    <VCol
      v-for="stat in stats"
      :key="stat.title"
      cols="12"
      sm="6"
      lg="3"
    >
      <StatsCard
        :title="stat.title"
        :value="stat.value"
        :icon="stat.icon"
        :color="stat.color"
        :loading="stat.loading"
      />
    </VCol>

    <!-- Tabs -->
    <VCol cols="12">
      <VTabs
        v-model="activeTab"
        show-arrows
        class="v-tabs-pill"
      >
        <VTab
          v-for="item in tabs"
          :key="item.tab"
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
        <!-- Application Settings Tab -->
        <VWindowItem value="application-settings">
          <ApplicationSettingsTab />
        </VWindowItem>

        <!-- Mail Management Tab -->
        <VWindowItem value="mail-management">
          <MailManagementTab />
        </VWindowItem>
      </VWindow>
    </VCol>

    <!-- Audit History - Always visible at bottom -->
    <VCol cols="12">
      <AuditHistoryCard />
    </VCol>
  </VRow>
</template>

<style scoped lang="scss">
.stat-card {
  min-block-size: 96px;
}

.recent-list-scroll {
  max-block-size: 320px;
  overflow-y: auto;
  padding-inline-end: 0.25rem;
}
</style>
