import { defineStore } from 'pinia'
import { login as apiLogin, logout as apiLogout, getMe } from '@/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    loading: false,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin',
    currentUser: (state) => state.user,
  },

  actions: {
    async login(credentials, redirect) {
      this.loading = true
      try {
        const res = await apiLogin(credentials, redirect)
        this.token = res.data.token
        this.user = res.data.user
        localStorage.setItem('token', this.token)
        localStorage.setItem('user', JSON.stringify(this.user))
        return res.data
      } finally {
        this.loading = false
      }
    },

    async logout() {
      await apiLogout().catch(() => {})
      this.token = null
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },

    async fetchMe() {
      try {
        const res = await getMe()
        this.user = res.data
        localStorage.setItem('user', JSON.stringify(this.user))
      } catch {
        this.logout()
      }
    },
  },
})
