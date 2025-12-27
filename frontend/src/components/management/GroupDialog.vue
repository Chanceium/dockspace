<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { MailGroup } from '@/services/mail'

interface Props {
  isOpen: boolean
  group?: MailGroup | null
  mode: 'add' | 'edit'
  errorMessage?: string
}

interface Emits {
  (e: 'update:isOpen', value: boolean): void
  (e: 'save', data: GroupFormData): void
}

interface GroupFormData {
  name: string
  description: string
}

const props = withDefaults(defineProps<Props>(), {
  errorMessage: '',
})
const emit = defineEmits<Emits>()

const formData = ref<GroupFormData>({
  name: '',
  description: '',
})

const isSaving = ref(false)

const dialogTitle = computed(() => {
  return props.mode === 'add' ? 'Add Mail Group' : 'Edit Mail Group'
})

// Watch for dialog open and populate form data
watch(() => props.isOpen, (isOpen) => {
  if (isOpen && props.group && props.mode === 'edit') {
    formData.value = {
      name: props.group.name,
      description: props.group.description || '',
    }
  } else if (isOpen && props.mode === 'add') {
    resetForm()
  }
  if (isOpen)
    isSaving.value = false
})

watch(() => props.errorMessage, (message) => {
  if (message)
    isSaving.value = false
})

const resetForm = () => {
  formData.value = {
    name: '',
    description: '',
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
  return formData.value.name.trim() !== ''
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
        <span>{{ dialogTitle }}</span>
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
          <VCol cols="12">
            <VTextField
              v-model="formData.name"
              label="Group Name"
              placeholder="e.g., Sales Team, Support"
              :disabled="isSaving"
            />
          </VCol>
          <VCol cols="12">
            <VTextarea
              v-model="formData.description"
              label="Description (optional)"
              placeholder="Enter a description for this group"
              :disabled="isSaving"
              rows="3"
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
          {{ mode === 'add' ? 'Create Group' : 'Save Changes' }}
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>
</template>
