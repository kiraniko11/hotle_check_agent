import { defineStore } from 'pinia'
import { loginAccount, registerUser, fetchProfile } from '../api/auth'

const TOKEN_KEY = 'access_token'
const USER_KEY = 'user'

function readStoredUser() {
  try {
    const stored = localStorage.getItem(USER_KEY)
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: readStoredUser(),
    loading: false,
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },

  actions: {
    setSession(payload) {
      this.token = payload.access
      this.user = payload.user
      localStorage.setItem(TOKEN_KEY, payload.access)
      localStorage.setItem(USER_KEY, JSON.stringify(payload.user))
    },

    clearSession() {
      this.token = ''
      this.user = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },

    async login(payload) {
      this.loading = true
      try {
        const { data } = await loginAccount(payload)
        this.setSession(data)
        return data
      } finally {
        this.loading = false
      }
    },

    async register(payload) {
      this.loading = true
      try {
        const { data } = await registerUser(payload)
        this.setSession(data)
        return data
      } finally {
        this.loading = false
      }
    },

    async loadProfile() {
      try {
        const { data } = await fetchProfile()
        this.user = data
        localStorage.setItem(USER_KEY, JSON.stringify(data))
      } catch {
        this.clearSession()
      }
    },

    logout() {
      this.clearSession()
    },
  },
})
