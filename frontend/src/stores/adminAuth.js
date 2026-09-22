import { defineStore } from 'pinia'

import { adminLogin, fetchAdminProfile } from '../api/adminPanel'

const ADMIN_TOKEN_KEY = 'admin_access_token'
const ADMIN_USER_KEY = 'admin_user'

function readStoredAdminUser() {
  try {
    return JSON.parse(localStorage.getItem(ADMIN_USER_KEY) || 'null')
  } catch {
    localStorage.removeItem(ADMIN_USER_KEY)
    return null
  }
}

export const useAdminAuthStore = defineStore('adminAuth', {
  state: () => ({
    token: localStorage.getItem(ADMIN_TOKEN_KEY) || '',
    user: readStoredAdminUser(),
    loading: false,
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },

  actions: {
    setSession(payload) {
      this.token = payload.access
      this.user = payload.user
      localStorage.setItem(ADMIN_TOKEN_KEY, payload.access)
      localStorage.setItem(ADMIN_USER_KEY, JSON.stringify(payload.user))
    },

    clearSession() {
      this.token = ''
      this.user = null
      localStorage.removeItem(ADMIN_TOKEN_KEY)
      localStorage.removeItem(ADMIN_USER_KEY)
    },

    async login(payload) {
      this.loading = true
      try {
        const { data } = await adminLogin(payload)
        this.setSession(data.data)
        return data.data
      } finally {
        this.loading = false
      }
    },

    async loadProfile() {
      if (!this.token) {
        return null
      }

      try {
        const { data } = await fetchAdminProfile()
        this.user = data.data
        localStorage.setItem(ADMIN_USER_KEY, JSON.stringify(data.data))
        return data.data
      } catch {
        this.clearSession()
        return null
      }
    },

    logout() {
      this.clearSession()
    },
  },
})
