import { defineStore } from 'pinia'
import { ofetch } from 'ofetch'

export const useUserStore = defineStore('user', {
  state: () => ({
    isLoggedIn: false,
  }),
  actions: {
    async refreshUser() {
      try {
        await ofetch('/api/login/check', { method: 'POST' })
        this.isLoggedIn = true
      } catch {
        this.isLoggedIn = false
      }
    }
  }
})