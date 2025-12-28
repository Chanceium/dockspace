<script setup lang="ts">
interface Props {
  isOpen: boolean
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  isDeleting?: boolean
}

interface Emits {
  (e: 'update:isOpen', value: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  confirmText: 'Delete',
  cancelText: 'Cancel',
  isDeleting: false,
})

const emit = defineEmits<Emits>()

const handleConfirm = () => {
  emit('confirm')
}

const handleCancel = () => {
  emit('cancel')
  emit('update:isOpen', false)
}

const handleClose = () => {
  if (!props.isDeleting) {
    emit('update:isOpen', false)
  }
}
</script>

<template>
  <VDialog
    :model-value="isOpen"
    max-width="500"
    persistent
    @update:model-value="handleClose"
  >
    <VCard>
      <VCardTitle class="d-flex align-center pa-4">
        <VIcon
          icon="ri-error-warning-line"
          color="error"
          size="24"
          class="me-2"
        />
        <span>{{ title }}</span>
      </VCardTitle>

      <VDivider />

      <VCardText class="pa-6">
        <p class="text-body-1">
          {{ message }}
        </p>
      </VCardText>

      <VDivider />

      <VCardActions class="pa-4">
        <VSpacer />
        <VBtn
          variant="text"
          :disabled="isDeleting"
          @click="handleCancel"
        >
          {{ cancelText }}
        </VBtn>
        <VBtn
          color="error"
          :loading="isDeleting"
          :disabled="isDeleting"
          @click="handleConfirm"
        >
          {{ confirmText }}
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>
</template>
