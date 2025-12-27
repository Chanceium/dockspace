import { ref } from 'vue'

export interface AuthProvider {
  id: string
  name: string
  icon: string
  url: string
  color?: string
}

// This would normally come from your backend API
const authProviders = ref<AuthProvider[]>([])

export function useAuthProviders() {
  const fetchProviders = async () => {
    // TODO: Replace with actual API call to your backend
    // const response = await fetch('/api/auth/providers')
    // authProviders.value = await response.json()

    // For now, return empty array (no providers)
    // You can populate this with your backend data
    authProviders.value = []
  }

  const setProviders = (providers: AuthProvider[]) => {
    authProviders.value = providers
  }

  return {
    authProviders,
    fetchProviders,
    setProviders,
  }
}
