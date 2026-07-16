import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api, getAuthToken, setAuthToken } from '../api/client'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(getAuthToken())
  const user = ref(null)
  const ready = ref(false)
  const loading = ref(false)
  const isAuthenticated = computed(() => Boolean(token.value && user.value))

  function setSession(session) {
    token.value = session.token
    user.value = session.user
    setAuthToken(session.token)
    ready.value = true
  }

  function clearSession() {
    token.value = null
    user.value = null
    setAuthToken(null)
    ready.value = true
  }

  async function bootstrap() {
    if (ready.value) return user.value
    if (!token.value) {
      ready.value = true
      return null
    }
    loading.value = true
    try {
      user.value = await api.get('/auth/me')
      return user.value
    } catch {
      clearSession()
      return null
    } finally {
      loading.value = false
      ready.value = true
    }
  }

  async function login(credentials) {
    loading.value = true
    try {
      const session = await api.post('/auth/login', credentials)
      setSession(session)
      return session.user
    } finally {
      loading.value = false
    }
  }

  async function signup(payload) {
    loading.value = true
    try {
      const session = await api.post('/auth/signup', payload)
      setSession(session)
      return session.user
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      if (token.value) await api.post('/auth/logout')
    } finally {
      clearSession()
    }
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('seoulmates:auth-expired', clearSession)
  }

  return {
    token,
    user,
    ready,
    loading,
    isAuthenticated,
    bootstrap,
    login,
    signup,
    logout,
    clearSession,
  }
})
