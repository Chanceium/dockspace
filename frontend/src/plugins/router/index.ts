import type { App } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { routes } from './routes'
import { useAuthStore } from '@/stores/auth'
import { authService } from '@/services/auth'

const AUTH_PAGES = ['/login', '/register', '/two-factor-required', '/two-factor-missing']
const PUBLIC_PATHS = ['/login', '/register', '/setup', '/reset-password', '/two-factor-required', '/two-factor-missing']

const normalizePath = (path: string) => {
  if (!path) return '/'
  const trimmed = path.replace(/\/+$/, '')
  return trimmed === '' ? '/' : trimmed
}

const router = createRouter({
  history: createWebHistory('/'),
  routes,
})

let authInitialized = false
let authInitPromise: Promise<void> | null = null
let needsSetup: boolean | null = null

router.beforeEach(async (to, from, next) => {
  console.log(`[Router Guard] Navigating from ${from.path} to ${to.path}`)
  const authStore = useAuthStore()
  const normalizedToPath = normalizePath(to.path)

  // Initialize auth store on first navigation
  if (!authInitialized) {
    console.log('[Router Guard] Initializing auth store')
    if (!authInitPromise) {
      authInitPromise = authStore.init().finally(() => {
        authInitialized = true
        authInitPromise = null
      })
    }
    await authInitPromise
  }

  // Refresh session if not authenticated
  if (!authStore.isAuthenticated) {
    console.log('[Router Guard] Checking session')
    const session = await authService.checkSession()
    console.log('[Router Guard] Session result:', session)
    if (session.authenticated && session.user) {
      authStore.$patch({ user: session.user })
    }
  }

  // Check setup status (only if not cached and user is not authenticated)
  if (needsSetup === null && !authStore.isAuthenticated) {
    console.log('[Router Guard] Checking setup status')
    const setupStatus = await authService.checkSetup()
    console.log('[Router Guard] Setup status:', setupStatus)
    needsSetup = setupStatus.needsSetup
  }

  // If authenticated, setup must be complete
  if (authStore.isAuthenticated) {
    needsSetup = false
  }

  console.log('[Router Guard] State - needsSetup:', needsSetup, 'isAuthenticated:', authStore.isAuthenticated)

  // RULE 1: If setup needed, only /setup is allowed
  if (needsSetup && to.path !== '/setup') {
    console.log('[Router Guard] Redirecting to /setup (setup required)')
    next('/setup')
    return
  }

  // RULE 2: If setup complete and trying to access /setup, redirect to login
  if (!needsSetup && to.path === '/setup') {
    console.log('[Router Guard] Redirecting away from /setup (setup already complete)')
    next(authStore.isAdmin ? '/management' : '/mail')
    return
  }

  // RULE 3: If authenticated and trying to access auth pages, redirect to management
  if (authStore.isAuthenticated && AUTH_PAGES.includes(normalizedToPath)) {
    console.log('[Router Guard] Redirecting to home (already authenticated)')
    next(authStore.isAdmin ? '/management' : '/mail')
    return
  }

  // RULE 4: Admin-only management page
  if (normalizedToPath.startsWith('/management') && !authStore.isAdmin) {
    console.log('[Router Guard] Redirecting to /access-denied (admin only)')
    next('/access-denied')
    return
  }

  // RULE 5: If not authenticated and accessing protected route, redirect to login
  const isPublicRoute = PUBLIC_PATHS.includes(normalizedToPath)
  if (!authStore.isAuthenticated && !isPublicRoute) {
    console.log('[Router Guard] Redirecting to /login (authentication required)')
    next('/login')
    return
  }

  console.log('[Router Guard] Allowing navigation to', to.path)
  next()
})

export default function (app: App) {
  app.use(router)
}

export { router }
