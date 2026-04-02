import axios from 'axios'

// Create an Axios instance
const api = axios.create({
    baseURL: '/api', // Proxied by Vite to Game Backend
    timeout: 10000
})

// Request Interceptor: Attach token automatically
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('host_token')
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
            // Future: You can emit an event here to trigger a logout UI flow
            localStorage.removeItem('host_token')
        }
        return Promise.reject(error)
    }
)

export default api
