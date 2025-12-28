<script lang="ts" setup>
import { useTheme } from 'vuetify'

const theme = useTheme()
const storageKey = 'dockspace-theme-settings'

// Predefined color options
const colorOptions = [
  { name: 'Dockspace Blue', value: '#1980d8', darken: '#1565C0' },
  { name: 'Purple', value: '#8C57FF', darken: '#7E4EE6' },
  { name: 'Pink', value: '#E91E63', darken: '#C2185B' },
  { name: 'Cyan', value: '#00BCD4', darken: '#0097A7' },
  { name: 'Green', value: '#4CAF50', darken: '#388E3C' },
  { name: 'Orange', value: '#FF9800', darken: '#F57C00' },
  { name: 'Teal', value: '#009688', darken: '#00796B' },
  { name: 'Red', value: '#F44336', darken: '#D32F2F' },
]

const darkBackgroundOptions = [
  { name: 'Default Dark', value: '#28243D' },
  { name: 'Deep Navy', value: '#1B2233' },
  { name: 'Charcoal', value: '#1C1D24' },
  { name: 'Graphite', value: '#20222B' },
  { name: 'Midnight', value: '#15171E' },
]

const darkSurfaceOptions = [
  { name: 'Default Surface', value: '#312d4b' },
  { name: 'Navy Surface', value: '#242C3E' },
  { name: 'Slate Surface', value: '#2A2D3A' },
  { name: 'Graphite Surface', value: '#2C303B' },
  { name: 'Midnight Surface', value: '#1D202A' },
]

// Get current primary colors
const selectedPrimaryColor = ref(theme.themes.value.light.colors.primary)
const selectedDarkBackground = ref(theme.themes.value.dark.colors.background)
const selectedDarkSurface = ref(theme.themes.value.dark.colors.surface)

const persistThemeSettings = () => {
  if (typeof localStorage === 'undefined')
    return

  localStorage.setItem(storageKey, JSON.stringify({
    primary: selectedPrimaryColor.value,
    primaryDarken: theme.themes.value.light.colors['primary-darken-1'],
    darkBackground: selectedDarkBackground.value,
    darkSurface: selectedDarkSurface.value,
  }))
}

const updatePrimaryColor = (color: { value: string; darken: string }) => {
  selectedPrimaryColor.value = color.value

  // Apply to both light and dark modes
  theme.themes.value.light.colors.primary = color.value
  theme.themes.value.light.colors['primary-darken-1'] = color.darken
  theme.themes.value.dark.colors.primary = color.value
  theme.themes.value.dark.colors['primary-darken-1'] = color.darken

  persistThemeSettings()
}

const updateDarkBackground = (color: { value: string }) => {
  selectedDarkBackground.value = color.value
  theme.themes.value.dark.colors.background = color.value
  theme.themes.value.dark.colors['skin-bordered-background'] = color.value

  persistThemeSettings()
}

const updateDarkSurface = (color: { value: string }) => {
  selectedDarkSurface.value = color.value
  theme.themes.value.dark.colors.surface = color.value
  theme.themes.value.dark.colors['skin-bordered-surface'] = color.value
  theme.themes.value.dark.colors['expansion-panel-text-custom-bg'] = color.value
  theme.themes.value.dark.colors['track-bg'] = color.value
  theme.themes.value.dark.colors['chat-bg'] = color.value

  persistThemeSettings()
}

onMounted(() => {
  if (typeof localStorage === 'undefined')
    return

  const raw = localStorage.getItem(storageKey)
  if (!raw)
    return

  try {
    const settings = JSON.parse(raw) as {
      primary?: string
      primaryDarken?: string
      // Legacy support
      lightPrimary?: string
      lightPrimaryDarken?: string
      darkPrimary?: string
      darkPrimaryDarken?: string
      darkBackground?: string
      darkSurface?: string
    }

    // Use new primary field, or fall back to lightPrimary for legacy support
    const primaryColor = settings.primary || settings.lightPrimary
    const primaryDarken = settings.primaryDarken || settings.lightPrimaryDarken

    if (primaryColor) {
      selectedPrimaryColor.value = primaryColor
      theme.themes.value.light.colors.primary = primaryColor
      theme.themes.value.light.colors['primary-darken-1'] = primaryDarken || primaryColor
      theme.themes.value.dark.colors.primary = primaryColor
      theme.themes.value.dark.colors['primary-darken-1'] = primaryDarken || primaryColor
    }

    if (settings.darkBackground) {
      selectedDarkBackground.value = settings.darkBackground
      theme.themes.value.dark.colors.background = settings.darkBackground
      theme.themes.value.dark.colors['skin-bordered-background'] = settings.darkBackground
    }

    if (settings.darkSurface) {
      selectedDarkSurface.value = settings.darkSurface
      theme.themes.value.dark.colors.surface = settings.darkSurface
      theme.themes.value.dark.colors['skin-bordered-surface'] = settings.darkSurface
      theme.themes.value.dark.colors['expansion-panel-text-custom-bg'] = settings.darkSurface
      theme.themes.value.dark.colors['track-bg'] = settings.darkSurface
      theme.themes.value.dark.colors['chat-bg'] = settings.darkSurface
    }
  } catch {
    // Ignore invalid stored data
  }
})
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard title="Theme Customization">
        <VCardText>
          <h6 class="text-h6 mb-4">Primary Color</h6>
          <p class="text-body-2 mb-6">Choose a primary color (applies to both light and dark modes)</p>

          <VRow>
            <VCol
              v-for="color in colorOptions"
              :key="color.value"
              cols="6"
              sm="4"
              md="3"
            >
              <VCard
                :color="selectedPrimaryColor === color.value ? 'primary' : 'default'"
                :variant="selectedPrimaryColor === color.value ? 'tonal' : 'outlined'"
                class="cursor-pointer pa-4"
                @click="updatePrimaryColor(color)"
              >
                <div class="d-flex align-center">
                  <VAvatar
                    :color="color.value"
                    size="40"
                    class="me-3"
                  />
                  <div>
                    <div class="text-body-1 font-weight-medium">
                      {{ color.name }}
                    </div>
                    <div class="text-caption text-disabled">
                      {{ color.value }}
                    </div>
                  </div>
                  <VSpacer />
                  <VIcon
                    v-if="selectedPrimaryColor === color.value"
                    icon="ri-check-line"
                    color="primary"
                  />
                </div>
              </VCard>
            </VCol>
          </VRow>

          <VDivider class="my-6" />

          <h6 class="text-h6 mb-4">Dark Mode Background</h6>
          <p class="text-body-2 mb-6">Choose a background color for dark mode</p>

          <VRow>
            <VCol
              v-for="color in darkBackgroundOptions"
              :key="color.value"
              cols="6"
              sm="4"
              md="3"
            >
              <VCard
                :color="selectedDarkBackground === color.value ? 'primary' : 'default'"
                :variant="selectedDarkBackground === color.value ? 'tonal' : 'outlined'"
                class="cursor-pointer pa-4"
                @click="updateDarkBackground(color)"
              >
                <div class="d-flex align-center">
                  <VAvatar
                    :color="color.value"
                    size="40"
                    class="me-3"
                  />
                  <div>
                    <div class="text-body-1 font-weight-medium">
                      {{ color.name }}
                    </div>
                    <div class="text-caption text-disabled">
                      {{ color.value }}
                    </div>
                  </div>
                  <VSpacer />
                  <VIcon
                    v-if="selectedDarkBackground === color.value"
                    icon="ri-check-line"
                    color="primary"
                  />
                </div>
              </VCard>
            </VCol>
          </VRow>

          <VDivider class="my-6" />

          <h6 class="text-h6 mb-4">Dark Mode Surface</h6>
          <p class="text-body-2 mb-6">Choose a surface color for dark mode</p>

          <VRow>
            <VCol
              v-for="color in darkSurfaceOptions"
              :key="color.value"
              cols="6"
              sm="4"
              md="3"
            >
              <VCard
                :color="selectedDarkSurface === color.value ? 'primary' : 'default'"
                :variant="selectedDarkSurface === color.value ? 'tonal' : 'outlined'"
                class="cursor-pointer pa-4"
                @click="updateDarkSurface(color)"
              >
                <div class="d-flex align-center">
                  <VAvatar
                    :color="color.value"
                    size="40"
                    class="me-3"
                  />
                  <div>
                    <div class="text-body-1 font-weight-medium">
                      {{ color.name }}
                    </div>
                    <div class="text-caption text-disabled">
                      {{ color.value }}
                    </div>
                  </div>
                  <VSpacer />
                  <VIcon
                    v-if="selectedDarkSurface === color.value"
                    icon="ri-check-line"
                    color="primary"
                  />
                </div>
              </VCard>
            </VCol>
          </VRow>
        </VCardText>
      </VCard>
    </VCol>

    <VCol cols="12">
      <VCard title="Preview">
        <VCardText>
          <p class="text-body-2 mb-4">
            See how your selected color looks with different components
          </p>

          <div class="d-flex flex-wrap gap-4">
            <VBtn color="primary">
              Primary Button
            </VBtn>
            <VBtn
              color="primary"
              variant="outlined"
            >
              Outlined Button
            </VBtn>
            <VBtn
              color="primary"
              variant="text"
            >
              Text Button
            </VBtn>
          </div>

          <div class="mt-6">
            <VAlert
              color="primary"
              variant="tonal"
            >
              <VAlertTitle>Primary Alert</VAlertTitle>
              This is how alerts look with your selected primary color.
            </VAlert>
          </div>

          <div class="mt-4">
            <VChip
              color="primary"
              class="me-2"
            >
              Primary Chip
            </VChip>
            <VBadge
              color="primary"
              content="99+"
            >
              <VIcon icon="ri-notification-line" />
            </VBadge>
          </div>
        </VCardText>
      </VCard>
    </VCol>
  </VRow>
</template>
