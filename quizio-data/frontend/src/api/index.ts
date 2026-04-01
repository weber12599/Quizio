import axios from 'axios'
import router from '../router'

// Create a centralized Axios instance
const api = axios.create({
    baseURL: '',
    timeout: 10000
})

// Request Interceptor: Auto-attach token to headers
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token')
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Response Interceptor: Global error handling (e.g., 401 Unauthorized)
api.interceptors.response.use(
    (response) => {
        return response
    },
    (error) => {
        if (error.response && error.response.status === 401) {
            console.warn('Unauthorized. Redirecting to login...')
            localStorage.removeItem('token')
            // Prevent infinite loop if already on login page
            if (router.currentRoute.value.path !== '/login') {
                router.push('/login')
            }
        }
        return Promise.reject(error)
    }
)

export default api
