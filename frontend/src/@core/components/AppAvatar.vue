<script lang="ts" setup>
import { createAvatar } from '@dicebear/core'
import { initials, avataaars, lorelei, micah, bottts } from '@dicebear/collection'

interface Props {
  name?: string
  src?: string
  size?: string | number
  variant?: 'initials' | 'avataaars' | 'lorelei' | 'micah' | 'bottts'
  color?: string
  seed?: string
}

const props = withDefaults(defineProps<Props>(), {
  name: '',
  src: '',
  size: 40,
  variant: 'initials',
  color: undefined,
  seed: undefined,
})

const avatarSrc = computed(() => {
  // If a custom image source is provided, use it
  if (props.src)
    return props.src

  // Generate avatar based on variant
  const seed = props.seed || props.name || 'default'

  const styleMap = {
    initials,
    avataaars,
    lorelei,
    micah,
    bottts,
  }

  const avatar = createAvatar(styleMap[props.variant], {
    seed,
    size: Number(props.size),
    ...(props.color && { backgroundColor: [props.color] }),
  })

  return avatar.toDataUri()
})
</script>

<template>
  <VAvatar
    :size="size"
    :image="avatarSrc"
  />
</template>
