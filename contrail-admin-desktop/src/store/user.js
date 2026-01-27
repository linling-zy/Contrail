import { defineStore } from 'pinia'
import { login as loginApi } from '@/api/mock/auth'

export const useUserStore = defineStore('user', {
    state: () => ({
        token: localStorage.getItem('token') || '',
        userInfo: null
    }),

    actions: {
        async login(username, password) {
            try {
                const res = await loginApi(username, password)
                const { token, ...info } = res.data
                this.token = token
                this.userInfo = info
                localStorage.setItem('token', token)
                return res
            } catch (error) {
                throw error
            }
        },

        logout() {
            this.token = ''
            this.userInfo = null
            localStorage.removeItem('token')
        }
    }
})
