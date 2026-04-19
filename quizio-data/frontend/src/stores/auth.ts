import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import dataAPI from '../api'
import type { UserResponse } from '../api/types/users'

export const useAuthStore = defineStore('auth', () => {
    const token = ref<string | null>(localStorage.getItem('token'))
    const user = ref<UserResponse | null>(null)
    const router = useRouter()

    const isAuthenticated = () => !!token.value

    const login = async (username: string, password: string) => {
        try {
            const response = await dataAPI.verifyUser(username, password)
            token.value = response.data.access_token

            localStorage.setItem('token', token.value as string)
            await fetchUserProfile()
            return true
        } catch (error) {
            console.error('Login failed:', error)
            return false
        }
    }

    const fetchUserProfile = async () => {
        try {
            const response = await dataAPI.getMe()
            user.value = response.data
        } catch (error) {
            console.error('Failed to fetch profile:', error)
            logout()
        }
    }

    const logout = () => {
        token.value = null
        user.value = null
        localStorage.removeItem('token')
        router.push('/login')
    }

    return { token, user, isAuthenticated, login, logout, fetchUserProfile }
})
