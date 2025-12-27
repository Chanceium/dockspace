<script setup lang="ts">
interface Props {
  modelValue: boolean
  title?: string
  message?: string
  confirmText?: string
  cancelText?: string
  confirmColor?: string
  confirmVariant?: 'flat' | 'text' | 'outlined' | 'tonal' | 'plain'
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Are you sure?',
  message: 'This action cannot be undone.',
  confirmText: 'Confirm',
  cancelText: 'Cancel',
  confirmColor: 'error',
  confirmVariant: 'flat',
})

const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
  (event: 'confirm'): void
  (event: 'cancel'): void
}>()

const close = () => {
  emit('update:modelValue', false)
}

const confirm = () => {
  emit('confirm')
  close()
}

const cancel = () => {
  emit('cancel')
  close()
}
</script>

<template>
  <VDialog
    :model-value="props.modelValue"
    max-width="480"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <VCard>
      <VCardTitle>{{ props.title }}</VCardTitle>
      <VCardText>{{ props.message }}</VCardText>
      <VCardActions class="justify-end">
        <VBtn
          variant="text"
          @click="cancel"
        >
          {{ props.cancelText }}
        </VBtn>
        <VBtn
          :color="props.confirmColor"
          :variant="props.confirmVariant"
          @click="confirm"
        >
          {{ props.confirmText }}
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>
</template>
