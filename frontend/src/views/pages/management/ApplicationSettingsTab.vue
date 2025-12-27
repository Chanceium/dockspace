<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { settingsService } from '@/services/settings'
import { oidcService } from '@/services/oidc'
import { mailService } from '@/services/mail'
import type { OIDCClient } from '@/services/oidc'
import type { MailGroup } from '@/services/mail'
import ApplicationSettingsCard from '@/components/management/ApplicationSettingsCard.vue'
import SmtpSettingsCard from '@/components/management/SmtpSettingsCard.vue'
import OidcClientsCard from '@/components/management/OidcClientsCard.vue'
import OidcClientDialog from '@/components/management/OidcClientDialog.vue'
import DeleteConfirmDialog from '@/components/management/DeleteConfirmDialog.vue'

// State
const isLoadingSettings = ref(false)
const isSavingAppSettings = ref(false)
const isSavingSmtpSettings = ref(false)
const settingsError = ref('')
const settingsSuccess = ref('')
const oidcClients = ref<OIDCClient[]>([])
const groups = ref<MailGroup[]>([])
const isLoadingOidc = ref(false)
const isSavingOidc = ref(false)
const oidcError = ref('')
const oidcSuccess = ref('')
const isDeleteOidcOpen = ref(false)
const oidcToDelete = ref<OIDCClient | null>(null)
const isOidcDialogOpen = ref(false)
const oidcDialogMode = ref<'add' | 'edit'>('add')

// Component refs
const oidcClientDialogRef = ref<InstanceType<typeof OidcClientDialog> | null>(null)
const applicationSettingsCardRef = ref<InstanceType<typeof ApplicationSettingsCard> | null>(null)
const smtpSettingsCardRef = ref<InstanceType<typeof SmtpSettingsCard> | null>(null)

// Default settings
const defaultSettings = {
  sessionTimeout: 60,
  domainUrl: 'https://dockspace.io',
  allowRegistration: false,
  smtpHost: 'smtp.dockspace.io',
  smtpPort: 587,
  smtpUsername: '',
  smtpPassword: '',
  smtpSecurity: 'starttls',
  smtpFromEmail: 'noreply@dockspace.io',
}

const loadOidcClients = async () => {
  oidcError.value = ''
  isLoadingOidc.value = true
  const response = await oidcService.listClients()
  if (response.success && response.clients) {
    oidcClients.value = response.clients
  } else if (!response.success) {
    oidcError.value = response.error || 'Failed to load OIDC clients'
  }
  isLoadingOidc.value = false
}

const loadGroups = async () => {
  const response = await mailService.listGroups()
  if (response.success && response.groups) {
    groups.value = response.groups
  }
}

// OIDC handlers
const handleAddOidcClient = () => {
  oidcDialogMode.value = 'add'
  oidcError.value = ''
  oidcSuccess.value = ''
  isOidcDialogOpen.value = true
}

const handleEditOidcClient = async (client: OIDCClient) => {
  oidcDialogMode.value = 'edit'
  oidcError.value = ''
  oidcSuccess.value = ''
  isOidcDialogOpen.value = true
  const response = await oidcService.getClient(client.id)
  if (response.success && response.client) {
    const c = response.client
    oidcClientDialogRef.value?.updateFormData({
      id: c.id,
      name: c.name,
      client_id: c.client_id,
      client_secret: c.client_secret || '',
      client_type: 'confidential',
      response_types: c.response_types || ['code'],
      redirect_uris: (c.redirect_uris || []).join('\n'),
      scope: c.scope || '',
      require_2fa: c.require_2fa || false,
      group_ids: c.groups ? c.groups.map(g => g.id) : [],
    })
  } else if (!response.success) {
    oidcError.value = response.error || 'Failed to load client'
  }
}

const handleSaveOidcClient = async (formData: any) => {
  if (!formData.name.trim()) {
    oidcError.value = 'Client name is required'
    return
  }
  oidcError.value = ''
  oidcSuccess.value = ''
  isSavingOidc.value = true
  const payload = {
    name: formData.name.trim(),
    client_type: 'confidential' as const,
    response_types: formData.response_types,
    redirect_uris: formData.redirect_uris,
    scope: formData.scope,
    group_ids: formData.group_ids,
    require_2fa: formData.require_2fa,
  }

  if (oidcDialogMode.value === 'add') {
    const response = await oidcService.createClient(payload)
    if (response.success) {
      oidcSuccess.value = 'OIDC client created'
      isOidcDialogOpen.value = false
      await loadOidcClients()
    } else {
      oidcError.value = response.error || 'Failed to create client'
    }
  } else if (oidcDialogMode.value === 'edit' && formData.id) {
    const response = await oidcService.updateClient(formData.id, payload)
    if (response.success) {
      oidcSuccess.value = 'OIDC client updated'
      isOidcDialogOpen.value = false
      await loadOidcClients()
    } else {
      oidcError.value = response.error || 'Failed to update client'
    }
  }
  isSavingOidc.value = false
}

const handleDeleteOidcClient = (client: OIDCClient) => {
  oidcToDelete.value = client
  isDeleteOidcOpen.value = true
}

const confirmDeleteOidcClient = async () => {
  if (!oidcToDelete.value) return
  const response = await oidcService.deleteClient(oidcToDelete.value.id)
  if (response.success) {
    await loadOidcClients()
  } else {
    oidcError.value = response.error || 'Failed to delete client'
  }
  isDeleteOidcOpen.value = false
  oidcToDelete.value = null
}

// Settings handlers
const saveApplicationSettings = (settings: any) => {
  settingsError.value = ''
  settingsSuccess.value = ''
  isSavingAppSettings.value = true
  settingsService.updateSettings({
    session_timeout: settings.sessionTimeout * 60,
    domain_url: settings.domainUrl,
    allow_registration: settings.allowRegistration,
  }).then(response => {
    if (response.success) {
      settingsSuccess.value = 'Application settings saved'
    } else {
      settingsError.value = response.error || 'Failed to save application settings'
    }
  }).catch(() => {
    settingsError.value = 'Failed to save application settings'
  }).finally(() => {
    isSavingAppSettings.value = false
  })
}

const saveSmtpSettings = (settings: any) => {
  settingsError.value = ''
  settingsSuccess.value = ''
  isSavingSmtpSettings.value = true
  settingsService.updateSettings({
    smtp_host: settings.smtpHost,
    smtp_port: settings.smtpPort,
    smtp_username: settings.smtpUsername,
    smtp_password: settings.smtpPassword,
    smtp_from_email: settings.smtpFromEmail,
    smtp_security: settings.smtpSecurity.toLowerCase(),
  }).then(response => {
    if (response.success) {
      settingsSuccess.value = 'SMTP settings saved'
      smtpSettingsCardRef.value?.clearPassword()
    } else {
      settingsError.value = response.error || 'Failed to save SMTP settings'
    }
  }).catch(() => {
    settingsError.value = 'Failed to save SMTP settings'
  }).finally(() => {
    isSavingSmtpSettings.value = false
  })
}

const resetApplicationSettings = () => {
  settingsError.value = ''
  settingsSuccess.value = ''
  applicationSettingsCardRef.value?.updateSettings({
    sessionTimeout: defaultSettings.sessionTimeout,
    domainUrl: defaultSettings.domainUrl,
    allowRegistration: defaultSettings.allowRegistration,
  })
}

const resetSmtpSettings = () => {
  settingsError.value = ''
  settingsSuccess.value = ''
  smtpSettingsCardRef.value?.updateSettings({
    smtpHost: defaultSettings.smtpHost,
    smtpPort: defaultSettings.smtpPort,
    smtpUsername: defaultSettings.smtpUsername,
    smtpPassword: defaultSettings.smtpPassword,
    smtpSecurity: defaultSettings.smtpSecurity,
    smtpFromEmail: defaultSettings.smtpFromEmail,
  })
}

const loadSettings = async () => {
  settingsError.value = ''
  settingsSuccess.value = ''
  isLoadingSettings.value = true
  const response = await settingsService.getSettings()
  if (response.success && response.settings) {
    const apiSettings = response.settings
    const sessionTimeout = Math.round(apiSettings.session_timeout / 60)
    const domainUrl = apiSettings.domain_url
    const allowRegistration = apiSettings.allow_registration ?? false
    const smtpHost = apiSettings.smtp_host || ''
    const smtpPort = apiSettings.smtp_port || defaultSettings.smtpPort
    const smtpUsername = apiSettings.smtp_username || ''
    const smtpFromEmail = apiSettings.smtp_from_email || defaultSettings.smtpFromEmail
    const smtpSecurity = apiSettings.smtp_security || defaultSettings.smtpSecurity

    applicationSettingsCardRef.value?.updateSettings({
      sessionTimeout,
      domainUrl,
      allowRegistration,
    })

    smtpSettingsCardRef.value?.updateSettings({
      smtpHost,
      smtpPort,
      smtpUsername,
      smtpPassword: '',
      smtpSecurity,
      smtpFromEmail,
    })

    defaultSettings.sessionTimeout = sessionTimeout
    defaultSettings.domainUrl = domainUrl
    defaultSettings.allowRegistration = allowRegistration
    defaultSettings.smtpHost = smtpHost
    defaultSettings.smtpPort = smtpPort
    defaultSettings.smtpUsername = smtpUsername
    defaultSettings.smtpPassword = ''
    defaultSettings.smtpSecurity = smtpSecurity
    defaultSettings.smtpFromEmail = smtpFromEmail
  } else if (!response.success) {
    settingsError.value = response.error || 'Failed to load settings'
  }
  isLoadingSettings.value = false
}

// Load data on mount
onMounted(() => {
  loadSettings()
  loadOidcClients()
  loadGroups()
})

// Expose load functions for parent to trigger refresh
defineExpose({
  loadSettings,
  loadOidcClients,
})
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VAlert
        v-if="settingsError"
        type="error"
        variant="tonal"
        class="mb-4"
      >
        {{ settingsError }}
      </VAlert>
      <VAlert
        v-else-if="settingsSuccess"
        type="success"
        variant="tonal"
        class="mb-4"
      >
        {{ settingsSuccess }}
      </VAlert>
    </VCol>
    <VCol cols="12" md="6">
      <ApplicationSettingsCard
        ref="applicationSettingsCardRef"
        :loading="isLoadingSettings"
        :saving="isSavingAppSettings"
        @save="saveApplicationSettings"
        @reset="resetApplicationSettings"
      />
    </VCol>

    <VCol cols="12" md="6">
      <SmtpSettingsCard
        ref="smtpSettingsCardRef"
        :loading="isLoadingSettings"
        :saving="isSavingSmtpSettings"
        @save="saveSmtpSettings"
        @reset="resetSmtpSettings"
      />
    </VCol>

    <VCol cols="12">
      <OidcClientsCard
        :clients="oidcClients"
        :loading="isLoadingOidc"
        :error-message="oidcError"
        :success-message="oidcSuccess"
        @add="handleAddOidcClient"
        @edit="handleEditOidcClient"
        @delete="handleDeleteOidcClient"
      />
    </VCol>
  </VRow>

  <OidcClientDialog
    ref="oidcClientDialogRef"
    v-model:is-open="isOidcDialogOpen"
    :mode="oidcDialogMode"
    :groups="groups"
    :error-message="oidcError"
    :is-saving="isSavingOidc"
    @save="handleSaveOidcClient"
  />

  <DeleteConfirmDialog
    v-model:is-open="isDeleteOidcOpen"
    title="Delete OIDC Client"
    :message="`Are you sure you want to delete ${oidcToDelete?.name}? This action cannot be undone.`"
    :is-deleting="false"
    @confirm="confirmDeleteOidcClient"
  />
</template>
