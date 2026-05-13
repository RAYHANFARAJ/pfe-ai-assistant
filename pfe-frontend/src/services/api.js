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
  // ── App ────────────────────────────────────────────────────────────────────
  health:           ()                    => api.get('/api/health'),
  listProducts:     ()                    => api.get('/api/products'),
  searchAccounts:   (q)                   => api.get('/api/accounts/search', { params: { q } }),
  runScoring:       (clientId, productId) => api.post('/api/scoring/agent-demo', { client_id: clientId, product_id: productId }),
  runBatchScoring:  (clientId, docs)      => api.post('/api/scoring/batch', { client_id: clientId, documents: docs || [] }, { timeout: 600_000 }),
  uploadDocument:   (file, clientId)      => { const fd = new FormData(); fd.append('file', file); const url = clientId ? `/api/documents/upload?client_id=${clientId}` : '/api/documents/upload'; return api.post(url, fd, { headers: { 'Content-Type': 'multipart/form-data' } }) },
  getClientDocuments: (clientId)         => api.get(`/api/documents/client/${clientId}`),
  removeClientDocument: (clientId, label) => api.delete(`/api/documents/client/${clientId}/${encodeURIComponent(label)}`),
  downloadPdfReport:(client, batchResult) => api.post('/api/reports/pdf', { client, batch_result: batchResult }, { responseType: 'blob', timeout: 120_000 }),
  getReportHistory:     ()          => api.get('/api/reports/history'),
  getRecommendations:   ()          => api.get('/api/recommendations'),
  redownloadPdf:     (reportId)  => api.get(`/api/reports/download/${reportId}`, { responseType: 'blob' }),
  deleteReport:      (reportId)  => api.delete(`/api/reports/${reportId}`),

  // ── Campaigns ──────────────────────────────────────────────────────────────
  listCampaigns:       ()                              => api.get('/api/campaigns'),
  getCampaignTargets:  (campaignId)                   => api.get(`/api/campaigns/${encodeURIComponent(campaignId)}/targets`),
  scoreCampaignTargets:(campaignId, accountIds, productId) => api.post(`/api/campaigns/${encodeURIComponent(campaignId)}/score`, { account_ids: accountIds, product_id: productId }, { timeout: 600_000 }),
  esHealth:         ()                    => api.get('/api/debug/es/health'),
  debugClient:      (clientId)            => api.get(`/api/debug/es/client/${clientId}`),

  // ── Admin — Products ───────────────────────────────────────────────────────
  admin: {
    // Products
    listProducts:   ()                       => api.get('/api/admin/products'),
    createProduct:  (data)                   => api.post('/api/admin/products', data),
    updateProduct:  (id, data)               => api.put(`/api/admin/products/${id}`, data),
    deleteProduct:  (id)                     => api.delete(`/api/admin/products/${id}`),
    // Criteria
    listCriteria:   (productId)              => api.get(`/api/admin/products/${productId}/criteria`),
    createCriterion:(productId, data)        => api.post(`/api/admin/products/${productId}/criteria`, data),
    updateCriterion:(id, data)               => api.put(`/api/admin/criteria/${id}`, data),
    deleteCriterion:(id)                     => api.delete(`/api/admin/criteria/${id}`),
    // Choices
    listChoices:    (criterionId)            => api.get(`/api/admin/criteria/${criterionId}/choices`),
    createChoice:   (criterionId, data)      => api.post(`/api/admin/criteria/${criterionId}/choices`, data),
    updateChoice:   (id, data)               => api.put(`/api/admin/choices/${id}`, data),
    deleteChoice:   (id)                     => api.delete(`/api/admin/choices/${id}`),
    // Campaigns
    listCampaigns:  ()                       => api.get('/api/admin/campaigns'),
    createCampaign: (data)                   => api.post('/api/admin/campaigns', data),
    updateCampaign: (id, data)               => api.put(`/api/admin/campaigns/${id}`, data),
    deleteCampaign: (id)                     => api.delete(`/api/admin/campaigns/${id}`),
    getCampaignTargets: (id)                 => api.get(`/api/admin/campaigns/${id}/targets`),
    // Users & roles
    listUsers:      ()                       => api.get('/api/admin/users'),
    makeAdmin:      (userId)                 => api.post(`/api/admin/users/${userId}/make-admin`),
    removeAdmin:    (userId)                 => api.delete(`/api/admin/users/${userId}/remove-admin`),
    // Sources
    listSources:    (clientId)               => api.get('/api/admin/sources', { params: clientId ? { client_id: clientId } : {} }),
    createSource:   (data)                   => api.post('/api/admin/sources', data),
    updateSource:   (id, data)               => api.put(`/api/admin/sources/${id}`, data),
    deleteSource:   (id)                     => api.delete(`/api/admin/sources/${id}`),
  },
}
