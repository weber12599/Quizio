// src/stores/auth.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

export const useAuthStore = defineStore('auth', () => {
    // Initialize token from localStorage if it exists
    const token = ref<string | null>(localStorage.getItem('token'))
    const router = useRouter()

    // Computed property to check if user is logged in
    const isAuthenticated = () => !!token.value

    const login = async (username: string, password: string) => {
        try {
            // OAuth2 requires form data (application/x-www-form-urlencoded)
            const formData = new URLSearchParams()
            formData.append('username', username)
            formData.append('password', password)

            const response = await axios.post('/api/auth/login', formData, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            })

            // Save token to state and localStorage
            token.value = response.data.access_token
            localStorage.setItem('token', token.value as string)

            return true
        } catch (error) {
            console.error('Login failed:', error)
            return false
        }
    }

    const logout = () => {
        token.value = null
        localStorage.removeItem('token')
    }

    return { token, isAuthenticated, login, logout }
})
