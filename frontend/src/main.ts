import { createApp } from 'vue'

import App from '@/App.vue'
import { registerPlugins } from '@core/utils/plugins'
import { useAuthStore } from '@/stores/auth'

// Styles
import '@core/scss/template/index.scss'
import '@layouts/styles/index.scss'

// Create vue app
const app = createApp(App)

// Register plugins
registerPlugins(app)

// Initialize authentication before mounting
const authStore = useAuthStore()
authStore.init().then(() => {
  // Mount vue app after auth is initialized
  app.mount('#app')
})
