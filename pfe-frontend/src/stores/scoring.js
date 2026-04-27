import { reactive } from 'vue'

const state = reactive({ result: null, history: [] })

export function useScoringStore() {
  function addPendingReport(clientId, productId) {
    const id = Date.now()
    state.history.unshift({
      id,
      client_name: clientId,
      client_id: clientId,
      product: productId,
      product_id: productId,
      score: null,
      max_score: null,
      normalized: null,
      eligibility_status: null,
      report_status: 'generating',
      date: new Date().toLocaleDateString('fr-FR'),
    })
    if (state.history.length > 50) state.history.pop()
    return id
  }

  function updateReport(id, data) {
    const idx = state.history.findIndex(r => r.id === id)
    if (idx === -1) return
    state.history[idx] = {
      ...state.history[idx],
      client_name: data.client?.client_name || data.client?.client_id,
      client_id: data.client?.client_id,
      product: data.product?.product_name || data.product?.product_id,
      product_id: data.product?.product_id,
      score: data.summary?.total_score,
      max_score: data.summary?.max_score,
      normalized: data.summary?.normalized_score,
      eligibility_status: data.summary?.eligibility_status,
      report_status: 'completed',
    }
  }

  function failReport(id) {
    const idx = state.history.findIndex(r => r.id === id)
    if (idx !== -1) state.history[idx].report_status = 'failed'
  }

  function setResult(data) {
    state.result = data
  }

  return { state, setResult, addPendingReport, updateReport, failReport }
}
