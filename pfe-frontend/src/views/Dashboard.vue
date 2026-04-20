<template>
  <div class="page">

    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="brand">
        <img src="/sellynx-logo.svg" alt="SELLYNX" class="brand-logo" />
      </div>
      <nav class="nav">
        <RouterLink to="/dashboard" class="nav-item active">
          <span class="icon">⚡</span> Scoring
        </RouterLink>
      </nav>
      <div class="sidebar-footer">
        <div class="es-badge" :class="esStatus">
          <span class="dot"></span>
          {{ esStatus === 'ok' ? 'ES Connected' : esStatus === 'checking' ? 'Checking ES…' : 'ES Unreachable' }}
        </div>
      </div>
    </aside>

    <!-- Main -->
    <main class="main">
      <div class="topbar">
        <div>
          <h1 class="page-title">Client Scoring</h1>
          <p class="page-sub">Run the AI qualification pipeline on any client account</p>
        </div>
      </div>

      <!-- Search card -->
      <div class="card search-card">
        <h2 class="card-title">Run Scoring</h2>
        <form @submit.prevent="runScoring" class="search-form">
          <div class="field">
            <label>Client ID <span class="hint">(Salesforce Account ID)</span></label>
            <input v-model="clientId" placeholder="e.g. 0016700005gBzdBAAS" required />
          </div>
          <div class="field">
            <label>Product ID</label>
            <input v-model="productId" placeholder="e.g. P001" required />
          </div>
          <button type="submit" class="btn-primary" :disabled="loading">
            <span v-if="!loading">▶ Run Analysis</span>
            <span v-else class="spinner"></span>
          </button>
        </form>
      </div>

      <!-- Error -->
      <div v-if="error" class="alert-error">
        <strong>Error:</strong> {{ error }}
      </div>

      <!-- Results -->
      <RouterLink
        v-if="resultId"
        :to="`/scoring/${resultClientId}/${resultProductId}`"
        class="btn-view"
      >
        View last result →
      </RouterLink>

      <!-- Quick result preview -->
      <SummaryCard v-if="summary" :summary="summary" :client="client" :product="product" />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'
import SummaryCard from '../components/SummaryCard.vue'

const router = useRouter()
const clientId = ref('0016700005gBzdBAAS')
const productId = ref('P001')
const loading = ref(false)
const error = ref('')
const esStatus = ref('checking')
const summary = ref(null)
const client = ref(null)
const product = ref(null)
const resultClientId = ref('')
const resultProductId = ref('')
const resultId = ref(false)

onMounted(async () => {
  try {
    const res = await api.esHealth()
    esStatus.value = res.data.status === 'connected' ? 'ok' : 'error'
  } catch {
    esStatus.value = 'error'
  }
})

async function runScoring() {
  loading.value = true
  error.value = ''
  summary.value = null
  resultId.value = false
  try {
    const res = await api.runScoring(clientId.value, productId.value)
    if (res.data.error) {
      error.value = res.data.detail || res.data.error
      return
    }
    summary.value = res.data.summary
    client.value = res.data.client
    product.value = res.data.product
    resultClientId.value = clientId.value
    resultProductId.value = productId.value
    resultId.value = true
    // Navigate to full result page
    router.push(`/scoring/${clientId.value}/${productId.value}`)
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || 'Unexpected error'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page { display: flex; min-height: 100vh; background: #F4F6FA; font-family: 'Inter', 'Segoe UI', Arial, sans-serif; }

/* Sidebar */
.sidebar { width: 220px; background: #0A2D4A; display: flex; flex-direction: column; padding: 0; flex-shrink: 0; }
.brand { padding: 24px 20px 20px; border-bottom: 1px solid rgba(255,255,255,0.08); }
.brand-logo { width: 140px; }
.nav { flex: 1; padding: 16px 12px; display: flex; flex-direction: column; gap: 4px; }
.nav-item { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: 8px; color: rgba(255,255,255,0.6); text-decoration: none; font-size: 14px; font-weight: 500; transition: all 0.15s; }
.nav-item:hover, .nav-item.active { background: rgba(232,98,44,0.18); color: #fff; }
.icon { font-size: 16px; }
.sidebar-footer { padding: 16px 20px; border-top: 1px solid rgba(255,255,255,0.08); }
.es-badge { display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 500; }
.es-badge.ok { color: #4ade80; }
.es-badge.error { color: #f87171; }
.es-badge.checking { color: #94a3b8; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; flex-shrink: 0; }

/* Main */
.main { flex: 1; padding: 36px 40px; display: flex; flex-direction: column; gap: 24px; overflow-y: auto; }
.topbar { display: flex; align-items: flex-start; justify-content: space-between; }
.page-title { font-size: 24px; font-weight: 700; color: #0A2D4A; }
.page-sub { font-size: 13.5px; color: #8A9BB0; margin-top: 4px; }

/* Card */
.card { background: #fff; border-radius: 14px; padding: 28px 32px; box-shadow: 0 2px 16px rgba(10,45,74,0.07); }
.card-title { font-size: 16px; font-weight: 700; color: #0A2D4A; margin-bottom: 20px; }

/* Form */
.search-form { display: flex; gap: 16px; align-items: flex-end; flex-wrap: wrap; }
.field { display: flex; flex-direction: column; gap: 6px; flex: 1; min-width: 200px; }
.field label { font-size: 13px; font-weight: 600; color: #0A2D4A; }
.hint { font-weight: 400; color: #8A9BB0; font-size: 11px; }
.field input { padding: 11px 14px; border: 1.5px solid #DDE3EC; border-radius: 8px; font-size: 14px; color: #0A2D4A; background: #F8FAFC; outline: none; transition: border-color 0.2s; }
.field input:focus { border-color: #E8622C; background: #fff; }

.btn-primary { padding: 11px 28px; background: #E8622C; color: #fff; font-size: 14px; font-weight: 700; border: none; border-radius: 8px; cursor: pointer; white-space: nowrap; height: 44px; display: flex; align-items: center; transition: background 0.2s; }
.btn-primary:hover:not(:disabled) { background: #cf5224; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-view { display: inline-flex; align-items: center; color: #E8622C; font-size: 14px; font-weight: 600; text-decoration: none; }
.btn-view:hover { text-decoration: underline; }

/* Alert */
.alert-error { background: #fef2f2; border: 1.5px solid #fca5a5; color: #b91c1c; padding: 14px 18px; border-radius: 10px; font-size: 14px; }

/* Spinner */
.spinner { width: 18px; height: 18px; border: 2.5px solid rgba(255,255,255,0.4); border-top-color: #fff; border-radius: 50%; animation: spin 0.7s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
