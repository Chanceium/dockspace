<script setup lang="ts">
interface Props {
  title: string
  value: number
  icon: string
  color: string
  loading?: boolean
}

defineProps<Props>()
</script>

<template>
  <VCard>
    <VCardText class="d-flex align-center justify-space-between">
      <div>
        <div class="text-caption text-disabled mb-1">
          {{ title }}
        </div>
        <div class="text-h4 font-weight-bold">
          <VSkeletonLoader
            v-if="loading"
            type="text"
            width="60"
          />
          <span v-else>{{ value }}</span>
        </div>
      </div>
      <VAvatar
        :color="color"
        variant="tonal"
        size="48"
      >
        <VIcon
          :icon="icon"
          size="24"
        />
      </VAvatar>
    </VCardText>
  </VCard>
</template>
