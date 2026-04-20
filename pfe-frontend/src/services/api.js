import axios from 'axios'
import { useAuth } from '../auth/useAuth'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach the Keycloak Bearer token to every request
api.interceptors.request.use((config) => {
  const { getToken } = useAuth()
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// On 401 → session expired, redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export default {
  health:      ()               => api.get('/api/health'),
  runScoring:  (clientId, productId) =>
    api.post('/api/scoring/agent-demo', { client_id: clientId, product_id: productId }),
  esHealth:    ()               => api.get('/api/debug/es/health'),
  debugClient: (clientId)       => api.get(`/api/debug/es/client/${clientId}`),
}
