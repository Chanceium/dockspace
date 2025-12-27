<script lang="ts" setup>
import NavItems from '@/layouts/components/NavItems.vue'
import NotificationBell from '@/components/NotificationBell.vue'
import logo from '@images/logo.svg?raw'
import VerticalNavLayout from '@layouts/components/VerticalNavLayout.vue'

// Components
import Footer from '@/layouts/components/Footer.vue'
import NavbarThemeSwitcher from '@/layouts/components/NavbarThemeSwitcher.vue'
import UserProfile from '@/layouts/components/UserProfile.vue'

const searchQuery = ref('')

const escapeRegExp = (value: string) => {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

const clearHighlights = (container: Element) => {
  const marks = container.querySelectorAll('mark[data-search-highlight="true"]')
  marks.forEach(mark => {
    const text = document.createTextNode(mark.textContent || '')
    const parent = mark.parentNode
    parent?.replaceChild(text, mark)
    parent?.normalize()
  })
}

const highlightMatches = (query: string) => {
  const container = document.querySelector('.layout-page-content')
  if (!container)
    return

  clearHighlights(container)

  const trimmedQuery = query.trim()
  if (!trimmedQuery)
    return

  const regex = new RegExp(escapeRegExp(trimmedQuery), 'gi')
  const walker = document.createTreeWalker(
    container,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode(node) {
        if (!node.nodeValue || !node.nodeValue.trim())
          return NodeFilter.FILTER_REJECT

        const parent = (node as Text).parentElement
        if (!parent)
          return NodeFilter.FILTER_REJECT

        if (parent.closest('mark[data-search-highlight="true"]'))
          return NodeFilter.FILTER_REJECT

        const tag = parent.tagName
        if (['SCRIPT', 'STYLE', 'INPUT', 'TEXTAREA', 'NOSCRIPT', 'CODE', 'PRE'].includes(tag))
          return NodeFilter.FILTER_REJECT

        if (parent.isContentEditable)
          return NodeFilter.FILTER_REJECT

        return NodeFilter.FILTER_ACCEPT
      },
    },
  )

  const textNodes: Text[] = []

  while (walker.nextNode())
    textNodes.push(walker.currentNode as Text)

  textNodes.forEach(textNode => {
    const text = textNode.nodeValue || ''
    if (!regex.test(text)) {
      regex.lastIndex = 0
      return
    }

    regex.lastIndex = 0
    const fragment = document.createDocumentFragment()
    let lastIndex = 0
    let match: RegExpExecArray | null

    while ((match = regex.exec(text)) !== null) {
      const start = match.index
      const end = start + match[0].length

      if (start > lastIndex)
        fragment.appendChild(document.createTextNode(text.slice(lastIndex, start)))

      const mark = document.createElement('mark')
      mark.setAttribute('data-search-highlight', 'true')
      mark.textContent = text.slice(start, end)
      fragment.appendChild(mark)

      lastIndex = end
    }

    if (lastIndex < text.length)
      fragment.appendChild(document.createTextNode(text.slice(lastIndex)))

    textNode.parentNode?.replaceChild(fragment, textNode)
  })
}

watch(searchQuery, value => {
  nextTick(() => highlightMatches(value))
})

const route = useRoute()

watch(
  () => route.fullPath,
  () => {
    nextTick(() => highlightMatches(searchQuery.value))
  },
)
</script>

<template>
  <VerticalNavLayout>
    <!-- 👉 navbar -->
    <template #navbar="{ toggleVerticalOverlayNavActive }">
      <div class="d-flex h-100 align-center">
        <!-- 👉 Vertical nav toggle in overlay mode -->
        <IconBtn
          class="ms-n3 d-lg-none"
          @click="toggleVerticalOverlayNavActive(true)"
        >
          <VIcon icon="ri-menu-line" />
        </IconBtn>

        <!-- 👉 Search -->
        <VTextField
          v-model="searchQuery"
          placeholder="Search"
          density="compact"
          variant="solo"
          hide-details
          clearable
          class="navbar-search"
          prepend-inner-icon="ri-search-line"
        />

        <VSpacer />

        <IconBtn
          href="https://github.com/Chanceium/dockspace"
          target="_blank"
          class="me-2"
        >
          <VIcon icon="ri-github-fill" />
        </IconBtn>

        <NotificationBell class="me-2" />

        <NavbarThemeSwitcher class="me-2" />

        <UserProfile />
      </div>
    </template>

    <template #vertical-nav-header="{ toggleIsOverlayNavActive }">
      <RouterLink
        to="/"
        class="app-logo app-title-wrapper"
      >
        <!-- eslint-disable vue/no-v-html -->
        <div
          class="d-flex app-logo-image"
          v-html="logo"
        />
        <!-- eslint-enable -->

        <h1 class="font-weight-medium leading-normal text-xl text-uppercase">
          Dockspace
        </h1>
      </RouterLink>

      <IconBtn
        class="d-block d-lg-none"
        @click="toggleIsOverlayNavActive(false)"
      >
        <VIcon icon="ri-close-line" />
      </IconBtn>
    </template>

    <template #vertical-nav-content>
      <NavItems />
    </template>

    <!-- 👉 Pages -->
    <slot />

    <!-- 👉 Footer -->
    <template #footer>
      <Footer />
    </template>
  </VerticalNavLayout>
</template>

<style lang="scss" scoped>
.meta-key {
  border: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 6px;
  block-size: 1.5625rem;
  line-height: 1.3125rem;
  padding-block: 0.125rem;
  padding-inline: 0.25rem;
}

.navbar-search {
  max-inline-size: 260px;
}

:deep(mark[data-search-highlight="true"]) {
  background-color: #f9ea5e;
  color: inherit;
  padding-inline: 0.12em;
  border-radius: 4px;
}

.app-logo {
  display: flex;
  align-items: center;
  column-gap: 0.75rem;

  .app-logo-image {
    max-width: 40px;
    max-height: 40px;

    :deep(svg) {
      width: 100%;
      height: 100%;
      max-width: 40px;
      max-height: 40px;
    }
  }

  .app-logo-title {
    font-size: 1.25rem;
    font-weight: 500;
    line-height: 1.75rem;
    text-transform: uppercase;
  }
}
</style>
