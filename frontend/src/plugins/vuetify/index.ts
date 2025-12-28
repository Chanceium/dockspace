import type { App } from 'vue'

import { createVuetify } from 'vuetify'
import { VBtn } from 'vuetify/components/VBtn'
import defaults from './defaults'
import { icons } from './icons'
import { themes } from './theme'

const themeNameStorageKey = 'dockspace-theme'
const themeSettingsStorageKey = 'dockspace-theme-settings'

const applyStoredThemeSettings = () => {
  if (typeof localStorage === 'undefined')
    return

  const raw = localStorage.getItem(themeSettingsStorageKey)
  if (!raw)
    return

  try {
    const settings = JSON.parse(raw) as {
      lightPrimary?: string
      lightPrimaryDarken?: string
      darkPrimary?: string
      darkPrimaryDarken?: string
      darkBackground?: string
      darkSurface?: string
    }

    if (settings.lightPrimary) {
      themes.light.colors.primary = settings.lightPrimary
      themes.light.colors['primary-darken-1'] = settings.lightPrimaryDarken || settings.lightPrimary
    }

    if (settings.darkPrimary) {
      themes.dark.colors.primary = settings.darkPrimary
      themes.dark.colors['primary-darken-1'] = settings.darkPrimaryDarken || settings.darkPrimary
    }

    if (settings.darkBackground) {
      themes.dark.colors.background = settings.darkBackground
      themes.dark.colors['skin-bordered-background'] = settings.darkBackground
    }

    if (settings.darkSurface) {
      themes.dark.colors.surface = settings.darkSurface
      themes.dark.colors['skin-bordered-surface'] = settings.darkSurface
      themes.dark.colors['expansion-panel-text-custom-bg'] = settings.darkSurface
      themes.dark.colors['track-bg'] = settings.darkSurface
      themes.dark.colors['chat-bg'] = settings.darkSurface
    }
  } catch {
    // Ignore invalid stored data
  }
}

// Styles

import '@core/scss/template/libs/vuetify/index.scss'
import 'vuetify/styles'

export default function (app: App) {
  applyStoredThemeSettings()

  const storedThemeName = typeof localStorage !== 'undefined'
    ? localStorage.getItem(themeNameStorageKey)
    : null

  const vuetify = createVuetify({
    aliases: {
      IconBtn: VBtn,
    },
    defaults,
    icons,
    theme: {
      defaultTheme: storedThemeName || 'light',
      themes,
    },
  })

  app.use(vuetify)
}
