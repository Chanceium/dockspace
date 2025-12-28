<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { MailAccount } from '@/services/mail'

interface Props {
  isOpen: boolean
  accounts?: MailAccount[]
}

interface Emits {
  (e: 'update:isOpen', value: boolean): void
  (e: 'save', data: AliasFormData): void
}

interface AliasFormData {
  alias_email: string
  destination_email: string
}

const props = withDefaults(defineProps<Props>(), {
  accounts: () => [],
})
const emit = defineEmits<Emits>()

const formData = ref<AliasFormData>({
  alias_email: '',
  destination_email: '',
})

const isSaving = ref(false)

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const normalize = (value?: string) => (value || '').trim().toLowerCase()

const accountEmails = computed(() => props.accounts.map(account => account.email))
const accountEmailsNormalized = computed(() => accountEmails.value.map(normalize))

const requiredRule = (value: string) => value?.trim().length ? true : 'This field is required'
const aliasEmailRules = [
  requiredRule,
  (value: string) => emailPattern.test(value.trim()) ? true : 'Enter a valid email',
  (value: string) => accountEmailsNormalized.value.includes(normalize(value)) ? 'Alias email cannot match an account email' : true,
]
const destinationRules = [
  requiredRule,
  (value: string) => accountEmailsNormalized.value.includes(normalize(value)) ? true : 'Choose an account from the list',
]

const runRules = (rules: Array<(value: any) => true | string>, value: any) => {
  return rules.every(rule => rule(value) === true)
}

// Watch for dialog open to reset form and set default destination
watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    // Reset saving state when dialog opens
    isSaving.value = false
    resetForm()
    if (accountEmails.value.length) {
      formData.value.destination_email = accountEmails.value[0]
    }
  }
})

const resetForm = () => {
  formData.value = {
    alias_email: '',
    destination_email: '',
  }
}

const handleClose = () => {
  emit('update:isOpen', false)
  resetForm()
}

const handleSave = () => {
  isSaving.value = true
  emit('save', formData.value)
  // Parent component should handle the API call and close the dialog
}

const isFormValid = computed(() => {
  return runRules(aliasEmailRules, formData.value.alias_email)
    && runRules(destinationRules, formData.value.destination_email)
})
</script>

<template>
  <VDialog
    :model-value="isOpen"
    max-width="600"
    @update:model-value="handleClose"
  >
    <VCard>
      <VCardTitle class="d-flex align-center justify-space-between pa-4">
        <span>Add Mail Alias</span>
        <VBtn
          icon="ri-close-line"
          variant="text"
          size="small"
          @click="handleClose"
        />
      </VCardTitle>

      <VDivider />

      <VCardText class="pa-6">
        <VRow>
          <VCol cols="12">
            <VTextField
              v-model="formData.alias_email"
              label="Alias Email *"
              type="email"
              placeholder="alias@example.com"
              :rules="aliasEmailRules"
              :disabled="isSaving"
              hint="The email address that will forward to the destination"
              persistent-hint
            />
          </VCol>
          <VCol cols="12">
            <VSelect
              v-model="formData.destination_email"
              label="Destination Email *"
              :items="accountEmails"
              :rules="destinationRules"
              :disabled="isSaving || !accountEmails.length"
              hint="Select an existing account as the destination"
              persistent-hint
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
          :disabled="!isFormValid || isSaving"
          :loading="isSaving"
        >
          Create Alias
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>
</template>
