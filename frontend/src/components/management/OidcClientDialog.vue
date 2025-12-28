<script setup lang="ts">
import { ref, watch } from 'vue'
import type { OIDCClient } from '@/services/oidc'
import type { MailGroup } from '@/services/mail'

interface Props {
  isOpen: boolean
  mode: 'add' | 'edit'
  groups: MailGroup[]
  errorMessage?: string
  isSaving?: boolean
}

interface OidcFormData {
  id: number
  name: string
  client_id: string
  client_secret: string
  client_type: string
  response_types: string[]
  redirect_uris: string
  scope: string
  require_2fa: boolean
  group_ids: number[]
}

const props = withDefaults(defineProps<Props>(), {
  errorMessage: '',
  isSaving: false,
})

const emit = defineEmits<{
  (e: 'update:isOpen', value: boolean): void
  (e: 'save', data: OidcFormData): void
}>()

const formData = ref<OidcFormData>({
  id: 0,
  name: '',
  client_id: '',
  client_secret: '',
  client_type: 'confidential',
  response_types: ['code'],
  redirect_uris: '',
  scope: 'openid email profile',
  require_2fa: false,
  group_ids: [],
})

const resetForm = () => {
  formData.value = {
    id: 0,
    name: '',
    client_id: '',
    client_secret: '',
    client_type: 'confidential',
    response_types: ['code'],
    redirect_uris: '',
    scope: 'openid email profile',
    require_2fa: false,
    group_ids: [],
  }
}

const updateFormData = (data: Partial<OidcFormData>) => {
  formData.value = { ...formData.value, ...data }
}

const handleClose = () => {
  emit('update:isOpen', false)
}

const handleSave = () => {
  emit('save', formData.value)
}

watch(() => props.isOpen, (newValue) => {
  if (!newValue) {
    resetForm()
  }
})

defineExpose({
  updateFormData,
})
</script>

<template>
  <VDialog
    :model-value="isOpen"
    max-width="720"
    @update:model-value="emit('update:isOpen', $event)"
  >
    <VCard>
      <VCardTitle class="d-flex align-center justify-space-between pa-4">
        <span>{{ mode === 'add' ? 'Add OIDC Client' : 'Edit OIDC Client' }}</span>
        <VBtn
          icon="ri-close-line"
          variant="text"
          size="small"
          @click="handleClose"
        />
      </VCardTitle>
      <VDivider />
      <VCardText class="pa-6">
        <VAlert
          v-if="errorMessage"
          type="error"
          variant="tonal"
          class="mb-4"
        >
          {{ errorMessage }}
        </VAlert>
        <VRow>
          <VCol cols="12" md="6">
            <VTextField
              v-model="formData.name"
              label="Name *"
              placeholder="Portainer"
              :disabled="isSaving"
            />
          </VCol>
          <VCol
            v-if="mode === 'edit'"
            cols="12"
            md="6"
          >
            <VTextField
              v-model="formData.client_id"
              label="Client ID"
              readonly
              hint="Auto-generated"
              persistent-hint
            />
          </VCol>
          <VCol
            v-if="mode === 'edit'"
            cols="12"
            md="6"
          >
            <VTextField
              v-model="formData.client_secret"
              label="Client Secret"
              readonly
              hint="Auto-generated; use client_credentials or auth flows"
              persistent-hint
            />
          </VCol>
          <VCol cols="12">
            <VSelect
              v-model="formData.response_types"
              label="Response Types"
              multiple
              chips
              closable-chips
              :items="[
                'code',
                'id_token',
                'id_token token',
                'code token',
                'code id_token',
                'code id_token token',
              ]"
              :disabled="isSaving"
              hint="Choose allowed OIDC response types"
              persistent-hint
            />
          </VCol>
          <VCol cols="12">
            <VTextarea
              v-model="formData.redirect_uris"
              label="Redirect URIs"
              placeholder="https://example.com/callback"
              rows="2"
              auto-grow
              hint="One URI per line."
              persistent-hint
              :disabled="isSaving"
            />
          </VCol>
          <VCol cols="12">
            <VTextField
              v-model="formData.scope"
              label="Scopes"
              placeholder="openid email profile"
              hint="Space-separated scopes. Leave blank for defaults."
              persistent-hint
              :disabled="isSaving"
            />
          </VCol>
          <VCol cols="12" md="6">
            <VSelect
              v-model="formData.group_ids"
              label="Allowed Groups"
              :items="groups"
              item-title="name"
              item-value="id"
              multiple
              chips
              closable-chips
              clearable
              :disabled="isSaving"
              hint="Restrict client to these groups (optional)"
              persistent-hint
            />
          </VCol>
          <VCol cols="12" md="6" class="d-flex align-center">
            <VCheckbox
              v-model="formData.require_2fa"
              label="Require two-factor authentication"
              :disabled="isSaving"
            />
          </VCol>
        </VRow>
      </VCardText>
      <VDivider />
      <VCardActions class="pa-4">
        <VSpacer />
        <VBtn
          variant="outlined"
          @click="handleClose"
          :disabled="isSaving"
        >
          Cancel
        </VBtn>
        <VBtn
          color="primary"
          @click="handleSave"
          :loading="isSaving"
          :disabled="isSaving"
        >
          Save Client
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>
</template>
