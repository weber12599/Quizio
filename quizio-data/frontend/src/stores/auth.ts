import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
    const token = ref<string | null>(localStorage.getItem('token'))
    const user = ref<any>(null) // Store user details (name, email, role)
    const router = useRouter()

    const isAuthenticated = () => !!token.value

    const login = async (username: string, password: string) => {
        try {
            const formData = new URLSearchParams()
            formData.append('username', username)
            formData.append('password', password)

            // Use the custom api instance
            const response = await api.post('/auth/login', formData, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            })

            token.value = response.data.access_token
            localStorage.setItem('token', token.value as string)

            // Fetch user details immediately after successful login
            await fetchUserProfile()

            return true
        } catch (error) {
            console.error('Login failed:', error)
            return false
        }
    }

    const fetchUserProfile = async () => {
        try {
            const response = await api.get('/users/me')
            user.value = response.data
        } catch (error) {
            console.error('Failed to fetch profile:', error)
            logout() // Clear state if token is invalid
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
