<template>
  <AppLayout title="Search Opportunities" subtitle="Find AI qualification scores across your client accounts">

    <div class="search-page">

      <!-- Glow -->
      <div class="bg-glow"></div>

      <div class="search-center">
        <div class="search-icon-wrap">
          <svg width="26" height="26" fill="none" stroke="#E8622C" stroke-width="2" viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35" stroke-linecap="round"/>
          </svg>
        </div>
        <h2 class="search-heading">Search for a Company</h2>
        <p class="search-desc">Enter a Salesforce Account ID to run the full AI qualification pipeline</p>

        <form @submit.prevent="runScoring" class="search-form">
          <div class="input-group">
            <input
              v-model="clientId"
              placeholder="Enter client ID…"
              class="search-input"
              required
            />
            <div class="input-divider"></div>
            <input
              v-model="productId"
              placeholder="Product ID"
              class="search-input product-input"
            />
            <button type="submit" class="search-btn" :disabled="loading">
              <span v-if="!loading">Search</span>
              <span v-else class="mini-spin"></span>
            </button>
          </div>
        </form>

        <!-- Quick examples -->
        <div class="examples">
          <span class="examples-label">Try:</span>
          <button v-for="ex in examples" :key="ex.id" class="example-chip" @click="pick(ex)">
            {{ ex.label }}
          </button>
        </div>

        <!-- Error -->
        <div v-if="error" class="error-bar">⚠️ {{ error }}</div>
      </div>

      <!-- ES status -->
      <div class="es-status" :class="esStatus">
        <span class="es-dot"></span>
        {{ esStatus === 'ok' ? 'Elasticsearch Connected' : esStatus === 'checking' ? 'Checking…' : 'ES Unreachable' }}
      </div>
    </div>

  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import api from '../services/api'
import { useScoringStore } from '../stores/scoring'

const router = useRouter()
const store = useScoringStore()
const clientId = ref('')
const productId = ref('P001')
const loading = ref(false)
const error = ref('')
const esStatus = ref('checking')

const examples = [
  { id: '0016700005gBzdBAAS', label: 'Tech Solutions SAS', productId: 'P001' },
  { id: '0016700005gBzd7AAC', label: 'Charlotte Fryer', productId: 'P001' },
]

function pick(ex) { clientId.value = ex.id; productId.value = ex.productId }

onMounted(async () => {
  try {
    const res = await api.esHealth()
    esStatus.value = res.data.status === 'connected' ? 'ok' : 'error'
  } catch { esStatus.value = 'error' }
})

async function runScoring() {
  if (!clientId.value) return
  loading.value = true; error.value = ''
  const reportId = store.addPendingReport(clientId.value, productId.value || 'P001')
  try {
    const res = await api.runScoring(clientId.value, productId.value || 'P001')
    if (res.data.error) {
      store.failReport(reportId)
      error.value = res.data.detail || res.data.error
      return
    }
    store.updateReport(reportId, res.data)
    store.setResult(res.data)
    router.push('/recommendations')
  } catch (e) {
    store.failReport(reportId)
    error.value = e.response?.data?.detail || e.message || 'Unexpected error'
  } finally { loading.value = false }
}
</script>

<style scoped>
.search-page { min-height: 70vh; display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; }
.bg-glow { position: absolute; width: 600px; height: 400px; background: radial-gradient(ellipse, rgba(232,98,44,0.07) 0%, transparent 70%); top: 50%; left: 50%; transform: translate(-50%, -50%); pointer-events: none; }

.search-center { display: flex; flex-direction: column; align-items: center; gap: 20px; width: 100%; max-width: 680px; position: relative; z-index: 1; }

.search-icon-wrap { width: 60px; height: 60px; background: rgba(232,98,44,0.12); border: 1px solid rgba(232,98,44,0.25); border-radius: 16px; display: flex; align-items: center; justify-content: center; }
.search-heading { font-size: 28px; font-weight: 800; color: #fff; text-align: center; }
.search-desc { font-size: 14px; color: rgba(255,255,255,0.35); text-align: center; line-height: 1.6; }

.search-form { width: 100%; }
.input-group {
  display: flex; align-items: center;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 14px; overflow: hidden;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.input-group:focus-within { border-color: rgba(232,98,44,0.5); box-shadow: 0 0 0 3px rgba(232,98,44,0.08); }
.search-input { flex: 1; padding: 16px 20px; background: none; border: none; outline: none; color: #fff; font-size: 14.5px; }
.search-input::placeholder { color: rgba(255,255,255,0.25); }
.product-input { max-width: 140px; }
.input-divider { width: 1px; height: 24px; background: rgba(255,255,255,0.1); flex-shrink: 0; }
.search-btn { padding: 12px 28px; margin: 6px; background: linear-gradient(135deg, #E8622C, #ff7a45); color: #fff; font-size: 14px; font-weight: 700; border: none; border-radius: 10px; cursor: pointer; white-space: nowrap; transition: all 0.2s; display: flex; align-items: center; gap: 6px; }
.search-btn:hover:not(:disabled) { transform: scale(1.02); box-shadow: 0 4px 20px rgba(232,98,44,0.4); }
.search-btn:disabled { opacity: 0.6; }

.examples { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: center; }
.examples-label { font-size: 12px; color: rgba(255,255,255,0.25); }
.example-chip { padding: 6px 14px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 99px; color: rgba(255,255,255,0.5); font-size: 12.5px; cursor: pointer; transition: all 0.2s; }
.example-chip:hover { border-color: rgba(232,98,44,0.4); color: #E8622C; background: rgba(232,98,44,0.07); }

.error-bar { padding: 12px 18px; background: rgba(232,98,44,0.1); border: 1px solid rgba(232,98,44,0.3); border-radius: 10px; color: #fb8c5a; font-size: 13px; width: 100%; text-align: center; }

.es-status { position: fixed; bottom: 24px; right: 32px; display: flex; align-items: center; gap: 7px; font-size: 12px; font-weight: 500; padding: 7px 14px; border-radius: 99px; background: rgba(10,22,40,0.8); border: 1px solid rgba(255,255,255,0.08); backdrop-filter: blur(8px); }
.es-status.ok { color: #4ade80; }
.es-status.error { color: #f87171; }
.es-status.checking { color: rgba(255,255,255,0.4); }
.es-dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }

.mini-spin { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.7s linear infinite; display: inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
