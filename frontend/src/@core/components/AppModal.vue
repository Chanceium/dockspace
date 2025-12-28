<script lang="ts" setup>
interface Props {
  modelValue: boolean
  title?: string
  subtitle?: string
  width?: string | number
  persistent?: boolean
  scrollable?: boolean
  fullscreen?: boolean
  showActions?: boolean
  confirmText?: string
  cancelText?: string
  confirmColor?: string
  loading?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  subtitle: '',
  width: 600,
  persistent: false,
  scrollable: true,
  fullscreen: false,
  showActions: true,
  confirmText: 'Save',
  cancelText: 'Cancel',
  confirmColor: 'primary',
  loading: false,
  disabled: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'confirm': []
  'cancel': []
}>()

const dialogValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const handleConfirm = () => {
  emit('confirm')
}

const handleCancel = () => {
  emit('cancel')
  dialogValue.value = false
}
</script>

<template>
  <VDialog
    v-model="dialogValue"
    :width="width"
    :persistent="persistent"
    :scrollable="scrollable"
    :fullscreen="fullscreen"
  >
    <VCard>
      <!-- Header -->
      <VCardTitle class="d-flex align-center justify-space-between">
        <div>
          <div class="text-h5">
            {{ title }}
          </div>
          <div
            v-if="subtitle"
            class="text-body-2 text-disabled mt-1"
          >
            {{ subtitle }}
          </div>
        </div>
        <VBtn
          icon
          variant="text"
          size="small"
          @click="dialogValue = false"
        >
          <VIcon icon="ri-close-line" />
        </VBtn>
      </VCardTitle>

      <VDivider />

      <!-- Content -->
      <VCardText class="pa-6">
        <slot />
      </VCardText>

      <!-- Actions -->
      <template v-if="showActions">
        <VDivider />
        <VCardActions class="pa-4">
          <VSpacer />
          <VBtn
            variant="outlined"
            color="secondary"
            @click="handleCancel"
          >
            {{ cancelText }}
          </VBtn>
          <VBtn
            :color="confirmColor"
            :loading="loading"
            :disabled="disabled"
            @click="handleConfirm"
          >
            {{ confirmText }}
          </VBtn>
        </VCardActions>
      </template>

      <!-- Custom actions slot -->
      <template v-else>
        <slot name="actions" />
      </template>
    </VCard>
  </VDialog>
</template>
