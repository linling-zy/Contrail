import { defineStore } from 'pinia'
import { get, post } from '@/utils/request'
import { encryptWithPublicKey } from '@/utils/rsa'

export const useUserStore = defineStore('user', {
    state: () => {
        // 从 localStorage 读取用户信息
        const storedUserInfo = localStorage.getItem('userInfo')
        let userInfo = null
        if (storedUserInfo) {
            try {
                userInfo = JSON.parse(storedUserInfo)
            } catch (e) {
                console.error('解析用户信息失败:', e)
                // 如果解析失败，清除无效数据
                localStorage.removeItem('userInfo')
            }
        }

        return {
            token: localStorage.getItem('token') || '',
            userInfo: userInfo
        }
    },

    actions: {
        async login(username, password) {
            try {
                // 1. 获取 RSA 公钥
                const publicKeyRes = await get('/api/admin/auth/public-key', null, {
                    headers: {} // 登录接口不需要 Token
                })
                const publicKeyPem = publicKeyRes?.public_key
                if (!publicKeyPem) {
                    throw new Error('获取公钥失败')
                }

                // 2. 使用 RSA 公钥加密密码
                const encryptedPassword = await encryptWithPublicKey(password, publicKeyPem)

                // 3. 调用登录接口
                const loginRes = await post(
                    '/api/admin/auth/login',
                    {
                        username: username.trim(),
                        password: encryptedPassword
                    },
                    {
                        headers: {} // 登录接口不需要 Token
                    }
                )

                // 4. 保存 Token 和用户信息
                const token = loginRes?.access_token
                const adminInfo = loginRes?.admin

                if (!token) {
                    throw new Error('登录失败：未返回 Token')
                }

                this.token = token
                this.userInfo = adminInfo || {}
                localStorage.setItem('token', token)
                if (adminInfo) {
                    localStorage.setItem('userInfo', JSON.stringify(adminInfo))
                }

                return {
                    code: 200,
                    data: {
                        token,
                        ...adminInfo
                    },
                    message: '登录成功'
                }
            } catch (error) {
                // 处理错误信息
                const errorMessage = error.message || error.data?.error || '登录失败，请稍后重试'
                throw new Error(errorMessage)
            }
        },

        logout() {
            this.token = ''
            this.userInfo = null
            localStorage.removeItem('token')
            localStorage.removeItem('userInfo')
        }
    }
})
