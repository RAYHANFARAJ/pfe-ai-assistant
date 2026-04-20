<template>
  <div class="scoring-page">

    <!-- Ambient -->
    <div class="glow glow-1"></div>
    <div class="glow glow-2"></div>

    <!-- Navbar -->
    <nav class="navbar">
      <div class="nav-brand">
        <div class="nav-icon">⚡</div>
        <img src="/sellynx-logo.svg" alt="SELLYNX" class="nav-logo" />
      </div>
      <div class="nav-tabs">
        <RouterLink to="/" class="nav-tab">Home</RouterLink>
        <RouterLink to="/scoring" class="nav-tab active">Scoring</RouterLink>
      </div>
    </nav>

    <!-- Layout -->
    <div class="layout">

      <!-- LEFT: Results area -->
      <div class="results-area">

        <!-- Empty state -->
        <div v-if="!result && !loading && !error" class="empty-state">
          <div class="empty-icon">⚡</div>
          <h2>AI Client Qualification</h2>
          <p>Enter a Client ID below to run the full AI scoring pipeline.<br/>Results will appear here with evidence links.</p>
          <div class="quick-chips">
            <button v-for="ex in examples" :key="ex.id" class="chip" @click="useExample(ex)">
              {{ ex.label }}
            </button>
          </div>
        </div>

        <!-- Loading -->
        <div v-else-if="loading" class="loading-state">
          <div class="pulse-ring"></div>
          <div class="loading-steps">
            <div v-for="(step, i) in loadingSteps" :key="i"
              class="load-step" :class="{ active: i === currentStep, done: i < currentStep }">
              <span class="step-dot"></span>
              <span>{{ step }}</span>
            </div>
          </div>
        </div>

        <!-- Error -->
        <div v-else-if="error" class="error-state">
          <div class="error-icon">⚠️</div>
          <p>{{ error }}</p>
          <button class="retry-btn" @click="error = ''">Try again</button>
        </div>

        <!-- Results -->
        <div v-else-if="result" class="result-content">

          <!-- Summary header -->
          <div class="result-header">
            <div class="result-client">
              <div class="client-avatar">{{ initials }}</div>
              <div>
                <div class="client-name">{{ result.client?.client_name }}</div>
                <div class="client-meta">
                  <span class="sector-tag">{{ result.client?.sector }}</span>
                  <a v-if="result.client?.website" :href="result.client.website" target="_blank" class="meta-link">🌐 Website</a>
                  <a v-if="result.client?.linkedin" :href="result.client.linkedin" target="_blank" class="meta-link">💼 LinkedIn</a>
                </div>
              </div>
            </div>
            <div class="eligibility-badge" :class="eligibilityClass">
              {{ eligibilityLabel }}
            </div>
          </div>

          <!-- Score bar -->
          <div class="score-overview">
            <div class="score-numbers">
              <span class="score-big">{{ result.summary?.total_score }}</span>
              <span class="score-sep">/</span>
              <span class="score-max">{{ result.summary?.max_score }}</span>
              <span class="score-pct">{{ Math.round((result.summary?.normalized_score || 0) * 100) }}%</span>
            </div>
            <div class="score-track">
              <div class="score-fill" :style="{ width: Math.round((result.summary?.normalized_score || 0) * 100) + '%', background: scoreColor }"></div>
            </div>
          </div>

          <!-- Criteria list -->
          <div class="criteria-section">
            <div class="criteria-header">
              Criteria Breakdown
              <span class="criteria-count">{{ result.criteria_results?.length }}</span>
            </div>
            <CriterionRow v-for="c in result.criteria_results" :key="c.criterion_id" :criterion="c" />
          </div>

          <!-- Trace -->
          <details class="trace">
            <summary>Pipeline trace</summary>
            <div class="trace-body">
              <div v-for="(s,i) in result.trace" :key="i" class="trace-line">
                <span class="trace-dot"></span>{{ s }}
              </div>
            </div>
          </details>
        </div>
      </div>

      <!-- RIGHT: Context panel -->
      <aside class="context-panel">

        <!-- ES Status -->
        <div class="panel-card">
          <div class="panel-card-title">
            <span>🔌</span> Connection Status
          </div>
          <div class="status-row" :class="esStatus">
            <span class="status-dot"></span>
            <span>{{ esStatus === 'ok' ? 'Elasticsearch Connected' : esStatus === 'checking' ? 'Checking…' : 'Unreachable' }}</span>
          </div>
        </div>

        <!-- Last result quick stats -->
        <div v-if="result" class="panel-card">
          <div class="panel-card-title"><span>📊</span> Last Result</div>
          <div class="stat-row"><span>Score</span><span class="stat-val">{{ result.summary?.total_score }} / {{ result.summary?.max_score }}</span></div>
          <div class="stat-row"><span>Criteria</span><span class="stat-val">{{ result.summary?.criteria_count }}</span></div>
          <div class="stat-row"><span>Status</span><span class="stat-val" :class="eligibilityClass">{{ eligibilityLabel }}</span></div>
        </div>

        <!-- Product info -->
        <div v-if="result" class="panel-card">
          <div class="panel-card-title"><span>🎯</span> Product</div>
          <div class="panel-item">{{ result.product?.product_name }}</div>
          <div class="panel-item dim">ID: {{ result.product?.product_id }}</div>
        </div>

        <!-- Tips -->
        <div class="panel-card tip-card">
          <div class="panel-card-title"><span>⚡</span> Pro Tip</div>
          <p class="tip-text">{{ currentTip }}</p>
        </div>

      </aside>
    </div>

    <!-- Input bar -->
    <div class="input-bar">
      <div class="input-wrap">
        <form @submit.prevent="runScoring" class="input-form">
          <input v-model="clientId" placeholder="Client ID — e.g. 0016700005gBzdBAAS" class="input-field" />
          <input v-model="productId" placeholder="Product ID — e.g. P001" class="input-field input-small" />
          <button type="submit" class="send-btn" :disabled="loading">
            <span v-if="!loading">⚡</span>
            <span v-else class="mini-spinner"></span>
          </button>
        </form>
        <div class="chips-row">
          <button v-for="ex in examples" :key="ex.id" class="chip" @click="useExample(ex)">{{ ex.label }}</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../services/api'
import CriterionRow from '../components/CriterionRow.vue'

const clientId = ref('')
const productId = ref('P001')
const loading = ref(false)
const error = ref('')
const result = ref(null)
const esStatus = ref('checking')
const currentStep = ref(0)

const examples = [
  { id: '0016700005gBzdBAAS', label: 'Tech Solutions SAS', productId: 'P001' },
  { id: '0016700005gBzd7AAC', label: 'Charlotte Fryer', productId: 'P001' },
]

const tips = [
  'Use the Salesforce Account ID from your CRM to run scoring.',
  'If LinkedIn is missing from CRM, the AI will scrape it from the website.',
  'Low confidence scores mean the data was not found in any source.',
  'Click on any criterion row to see evidence and source links.',
]
const currentTip = computed(() => tips[Math.floor(Math.random() * tips.length)])

const loadingSteps = [
  'Loading product criteria…',
  'Fetching client from Elasticsearch…',
  'Crawling company website…',
  'Resolving LinkedIn…',
  'Evaluating criteria with AI…',
  'Computing final score…',
]

const initials = computed(() => {
  const name = result.value?.client?.client_name || ''
  return name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()
})

const eligibilityClass = computed(() => {
  const s = result.value?.summary?.eligibility_status
  if (s === 'eligible') return 'eligible'
  if (s === 'to_review') return 'review'
  return 'not-eligible'
})
const eligibilityLabel = computed(() => {
  const s = result.value?.summary?.eligibility_status
  if (s === 'eligible') return '✅ Eligible'
  if (s === 'to_review') return '🔎 To Review'
  return '❌ Not Eligible'
})
const scoreColor = computed(() => {
  const pct = result.value?.summary?.normalized_score || 0
  if (pct >= 0.75) return '#22c55e'
  if (pct >= 0.4) return '#f59e0b'
  return '#E8622C'
})

function useExample(ex) {
  clientId.value = ex.id
  productId.value = ex.productId
}

onMounted(async () => {
  try {
    const res = await api.esHealth()
    esStatus.value = res.data.status === 'connected' ? 'ok' : 'error'
  } catch { esStatus.value = 'error' }
})

async function runScoring() {
  if (!clientId.value || !productId.value) return
  loading.value = true
  error.value = ''
  result.value = null
  currentStep.value = 0

  // Animate steps
  const stepTimer = setInterval(() => {
    if (currentStep.value < loadingSteps.length - 1) currentStep.value++
  }, 1200)

  try {
    const res = await api.runScoring(clientId.value, productId.value)
    clearInterval(stepTimer)
    if (res.data.error) { error.value = res.data.detail || res.data.error; return }
    result.value = res.data
  } catch (e) {
    clearInterval(stepTimer)
    error.value = e.response?.data?.detail || e.message || 'Unexpected error'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.scoring-page { min-height: 100vh; background: #060E1A; color: #fff; display: flex; flex-direction: column; position: relative; overflow: hidden; }

/* Glows */
.glow { position: fixed; border-radius: 50%; filter: blur(140px); pointer-events: none; z-index: 0; }
.glow-1 { width: 500px; height: 500px; background: radial-gradient(circle, rgba(232,98,44,0.1) 0%, transparent 70%); top: -150px; right: -100px; }
.glow-2 { width: 400px; height: 400px; background: radial-gradient(circle, rgba(10,45,74,0.5) 0%, transparent 70%); bottom: 100px; left: -100px; }

/* Navbar */
.navbar { position: fixed; top: 0; left: 0; right: 0; z-index: 100; display: flex; align-items: center; justify-content: space-between; padding: 14px 40px; background: rgba(6,14,26,0.9); backdrop-filter: blur(16px); border-bottom: 1px solid rgba(232,98,44,0.1); }
.nav-brand { display: flex; align-items: center; gap: 10px; }
.nav-icon { width: 32px; height: 32px; background: linear-gradient(135deg, #E8622C, #ff8c5a); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 14px; }
.nav-logo { height: 26px; }
.nav-tabs { display: flex; gap: 6px; }
.nav-tab { padding: 7px 18px; border-radius: 8px; font-size: 13.5px; font-weight: 500; text-decoration: none; color: rgba(255,255,255,0.5); border: 1px solid transparent; transition: all 0.2s; }
.nav-tab:hover { color: #fff; }
.nav-tab.active { color: #fff; border-color: rgba(232,98,44,0.4); background: rgba(232,98,44,0.1); }

/* Layout */
.layout { display: flex; gap: 0; flex: 1; padding-top: 64px; padding-bottom: 140px; min-height: 100vh; position: relative; z-index: 1; }

/* Results area */
.results-area { flex: 1; padding: 32px 40px; overflow-y: auto; }

/* Empty state */
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 60vh; text-align: center; gap: 16px; }
.empty-icon { width: 72px; height: 72px; background: linear-gradient(135deg, rgba(232,98,44,0.2), rgba(232,98,44,0.05)); border: 1px solid rgba(232,98,44,0.3); border-radius: 20px; display: flex; align-items: center; justify-content: center; font-size: 32px; margin-bottom: 8px; }
.empty-state h2 { font-size: 24px; font-weight: 700; color: #fff; }
.empty-state p { color: rgba(255,255,255,0.45); font-size: 14px; line-height: 1.7; max-width: 380px; }

/* Quick chips */
.quick-chips { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; margin-top: 8px; }
.chip { padding: 7px 16px; background: rgba(232,98,44,0.1); border: 1px solid rgba(232,98,44,0.25); border-radius: 99px; color: rgba(255,255,255,0.7); font-size: 12.5px; cursor: pointer; transition: all 0.2s; }
.chip:hover { background: rgba(232,98,44,0.2); color: #fff; border-color: rgba(232,98,44,0.5); }

/* Loading */
.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 60vh; gap: 40px; }
.pulse-ring { width: 64px; height: 64px; border-radius: 50%; border: 2px solid rgba(232,98,44,0.3); position: relative; }
.pulse-ring::after { content: '⚡'; position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 24px; animation: pulse 1.5s ease-in-out infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(0.9)} }
.loading-steps { display: flex; flex-direction: column; gap: 10px; }
.load-step { display: flex; align-items: center; gap: 10px; font-size: 13.5px; color: rgba(255,255,255,0.3); transition: color 0.3s; }
.load-step.active { color: #E8622C; }
.load-step.done { color: rgba(255,255,255,0.6); }
.step-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; flex-shrink: 0; }

/* Error */
.error-state { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 40vh; gap: 16px; text-align: center; }
.error-icon { font-size: 40px; }
.error-state p { color: rgba(255,255,255,0.6); font-size: 14px; max-width: 400px; padding: 16px 20px; background: rgba(10,45,74,0.6); border: 1px solid rgba(10,45,74,0.9); border-radius: 12px; }
.retry-btn { padding: 9px 24px; background: #0A2D4A; border: 1px solid rgba(232,98,44,0.4); border-radius: 8px; color: #E8622C; cursor: pointer; font-size: 13px; font-weight: 600; transition: all 0.2s; }
.retry-btn:hover { background: rgba(232,98,44,0.15); }

/* Result content */
.result-content { display: flex; flex-direction: column; gap: 20px; }

/* Result header */
.result-header { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px; background: rgba(255,255,255,0.03); border: 1px solid rgba(232,98,44,0.15); border-radius: 14px; }
.result-client { display: flex; align-items: center; gap: 14px; }
.client-avatar { width: 44px; height: 44px; background: linear-gradient(135deg, #E8622C, #ff8c5a); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: 800; flex-shrink: 0; }
.client-name { font-size: 18px; font-weight: 700; color: #fff; margin-bottom: 6px; }
.client-meta { display: flex; align-items: center; gap: 10px; }
.sector-tag { padding: 3px 10px; background: rgba(232,98,44,0.15); border-radius: 99px; font-size: 11px; color: #E8622C; font-weight: 600; }
.meta-link { font-size: 12px; color: rgba(255,255,255,0.45); text-decoration: none; }
.meta-link:hover { color: #E8622C; }

/* Eligibility */
.eligibility-badge { padding: 8px 18px; border-radius: 99px; font-size: 13px; font-weight: 700; }
.eligibility-badge.eligible { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.25); }
.eligibility-badge.review { background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.25); }
.eligibility-badge.not-eligible { background: rgba(232,98,44,0.15); color: #fb8c5a; border: 1px solid rgba(232,98,44,0.3); }

/* Score overview */
.score-overview { padding: 20px 24px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; }
.score-numbers { display: flex; align-items: baseline; gap: 6px; margin-bottom: 12px; }
.score-big { font-size: 40px; font-weight: 800; color: #fff; }
.score-sep { font-size: 24px; color: rgba(255,255,255,0.3); }
.score-max { font-size: 24px; color: rgba(255,255,255,0.4); }
.score-pct { margin-left: 12px; padding: 4px 12px; background: rgba(232,98,44,0.15); border-radius: 99px; font-size: 14px; font-weight: 700; color: #E8622C; }
.score-track { height: 8px; background: rgba(255,255,255,0.08); border-radius: 99px; overflow: hidden; }
.score-fill { height: 100%; border-radius: 99px; transition: width 0.8s ease; }

/* Criteria */
.criteria-section { display: flex; flex-direction: column; gap: 8px; }
.criteria-header { font-size: 13px; font-weight: 700; color: rgba(255,255,255,0.5); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; display: flex; align-items: center; gap: 10px; }
.criteria-count { background: rgba(232,98,44,0.15); color: #E8622C; font-size: 11px; padding: 2px 8px; border-radius: 99px; }

/* Trace */
.trace { padding: 16px 20px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; }
.trace summary { font-size: 12px; color: rgba(255,255,255,0.3); cursor: pointer; font-weight: 600; letter-spacing: 0.5px; }
.trace-body { margin-top: 12px; display: flex; flex-direction: column; gap: 6px; }
.trace-line { display: flex; align-items: flex-start; gap: 8px; font-size: 12px; color: rgba(255,255,255,0.35); font-family: monospace; }
.trace-dot { width: 5px; height: 5px; border-radius: 50%; background: #E8622C; flex-shrink: 0; margin-top: 5px; }

/* Context panel */
.context-panel { width: 280px; flex-shrink: 0; border-left: 1px solid rgba(255,255,255,0.05); padding: 24px 20px; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; }
.panel-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-radius: 12px; padding: 16px; }
.panel-card-title { display: flex; align-items: center; gap: 7px; font-size: 13px; font-weight: 700; color: rgba(255,255,255,0.7); margin-bottom: 12px; }
.status-row { display: flex; align-items: center; gap: 8px; font-size: 12.5px; font-weight: 500; }
.status-row.ok { color: #4ade80; }
.status-row.error { color: #f87171; }
.status-row.checking { color: rgba(255,255,255,0.4); }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; flex-shrink: 0; }
.stat-row { display: flex; justify-content: space-between; align-items: center; font-size: 12.5px; color: rgba(255,255,255,0.4); padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
.stat-row:last-child { border-bottom: none; }
.stat-val { font-weight: 700; color: #fff; }
.stat-val.eligible { color: #4ade80; }
.stat-val.review { color: #fbbf24; }
.stat-val.not-eligible { color: #fb8c5a; }
.panel-item { font-size: 13px; color: rgba(255,255,255,0.6); padding: 4px 0; }
.panel-item.dim { font-size: 11px; color: rgba(255,255,255,0.25); font-family: monospace; }
.tip-card { background: rgba(232,98,44,0.07); border-color: rgba(232,98,44,0.2); }
.tip-text { font-size: 12.5px; color: rgba(255,255,255,0.5); line-height: 1.6; }

/* Input bar */
.input-bar { position: fixed; bottom: 0; left: 0; right: 0; z-index: 100; padding: 16px 40px 24px; background: linear-gradient(to top, #060E1A 60%, transparent); }
.input-wrap { max-width: 860px; }
.input-form { display: flex; gap: 10px; align-items: center; background: rgba(255,255,255,0.05); border: 1px solid rgba(232,98,44,0.2); border-radius: 14px; padding: 8px 8px 8px 16px; backdrop-filter: blur(10px); }
.input-form:focus-within { border-color: rgba(232,98,44,0.5); box-shadow: 0 0 0 3px rgba(232,98,44,0.08); }
.input-field { flex: 1; background: none; border: none; outline: none; color: #fff; font-size: 14px; }
.input-field::placeholder { color: rgba(255,255,255,0.3); }
.input-small { max-width: 130px; border-left: 1px solid rgba(255,255,255,0.08); padding-left: 12px; }
.send-btn { width: 40px; height: 40px; background: linear-gradient(135deg, #E8622C, #ff7a45); border: none; border-radius: 10px; color: #fff; font-size: 16px; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: all 0.2s; }
.send-btn:hover:not(:disabled) { transform: scale(1.05); box-shadow: 0 4px 16px rgba(232,98,44,0.4); }
.send-btn:disabled { opacity: 0.5; }
.chips-row { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
.mini-spinner { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
