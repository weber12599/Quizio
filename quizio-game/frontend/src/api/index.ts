import axios from 'axios'
import { storage } from '../utils/storage'

// Create an Axios instance
const api = axios.create({
    baseURL: '/api', // Proxied by Vite to Game Backend
    timeout: 10000
})

// Request Interceptor: Attach token automatically
api.interceptors.request.use(
    (config) => {
        const token = storage.hostToken.get()
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Response Interceptor: Extract data & handle errors
api.interceptors.response.use(
    (response) => {
        // Directly return the data payload for cleaner components
        return response.data
    },
    (error) => {
        if (error.response && error.response.status === 401) {
            console.warn('Unauthorized. Token might be invalid or expired.')
            storage.hostToken.clear()
        }
        return Promise.reject(error)
    }
)

export default api
