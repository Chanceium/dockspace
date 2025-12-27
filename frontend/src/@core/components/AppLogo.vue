<script setup lang="ts">
import logo from '@images/logo.svg?raw'

interface Props {
  size?: number
}

const props = withDefaults(defineProps<Props>(), {
  size: 80,
})
</script>

<template>
  <div
    class="app-logo"
    :style="{ width: `${size}px`, height: `${size}px` }"
    v-html="logo"
  />
</template>

<style lang="scss" scoped>
.app-logo {
  display: inline-block;

  :deep(svg) {
    width: 100%;
    height: 100%;
    display: block;
  }
}
</style>
