<template>
  <AppLayout :title="pageTitle" :subtitle="pageSubtitle">
    <div class="page">

      <!-- ── STEP 1: Search company ─────────────────────────── -->
      <template v-if="step === 1">
        <div class="step-center">
          <div class="step-icon">
            <svg width="28" height="28" fill="none" stroke="#E8622C" stroke-width="2" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35" stroke-linecap="round"/>
            </svg>
          </div>
          <h2 class="step-title">Search for a Company</h2>
          <p class="step-desc">Type a company name or paste a Salesforce ID</p>

          <div class="autocomplete-wrap" ref="acWrap">
            <div class="input-icon-wrap">
              <svg class="input-icon" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35" stroke-linecap="round"/>
              </svg>
              <input
                v-model="searchQuery"
                @input="onInput"
                @focus="onFocus"
                @keydown.down.prevent="moveDown"
                @keydown.up.prevent="moveUp"
                @keydown.enter.prevent="selectHighlighted"
                @keydown.esc="showDropdown = false"
                placeholder="Search by name or Salesforce ID…"
                class="search-input"
                autocomplete="off"
              />
              <span v-if="searching" class="input-spin"></span>
            </div>

            <div v-if="showDropdown && suggestions.length > 0" class="dropdown">
              <div
                v-for="(item, i) in suggestions"
                :key="item.client_id"
                class="dropdown-item"
                :class="{ highlighted: i === highlightedIndex }"
                @mousedown.prevent="pickClient(item)"
              >
                <div class="item-avatar">{{ initials(item.client_name) }}</div>
                <div class="item-info">
                  <div class="item-name">{{ item.client_name }}</div>
                  <div class="item-meta">
                    <span class="item-id">{{ item.client_id }}</span>
                    <span v-if="item.sector" class="item-sector">{{ item.sector }}</span>
                    <span v-if="item.employees" class="item-emp">{{ item.employees }} emp.</span>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="showDropdown && suggestions.length === 0 && searchQuery.length > 1 && !searching" class="dropdown no-results">
              <span>No company found for "{{ searchQuery }}"</span>
            </div>
          </div>
        </div>
      </template>

      <!-- ── STEP 2: Product selection ─────────────────────── -->
      <template v-else-if="step === 2">

        <!-- Client recap bar -->
        <div class="client-bar">
          <div class="client-bar-left">
            <div class="client-avatar-lg">{{ initials(client.client_name) }}</div>
            <div>
              <div class="client-bar-name">{{ client.client_name }}</div>
              <div class="client-bar-meta">
                <span class="client-bar-id">{{ client.client_id }}</span>
                <span v-if="client.sector" class="client-bar-sector">{{ client.sector }}</span>
                <span v-if="client.employees" class="client-bar-emp">{{ client.employees }} employees</span>
              </div>
            </div>
          </div>
          <button class="change-btn" @click="resetToStep1">
            <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6"/></svg>
            Change company
          </button>
        </div>

        <div class="products-section">
          <div class="products-header">
            <div>
              <div class="products-title">Available Products</div>
              <div class="products-sub">Select a product to run the AI qualification pipeline</div>
            </div>
            <div class="products-count">{{ products.length }} products</div>
          </div>

          <div v-if="loadingProducts" class="products-loading">
            <span class="spinner"></span> Loading products…
          </div>

          <div v-else class="products-grid">
            <div
              v-for="product in products"
              :key="product.id"
              class="product-card"
              @click="pickProduct(product)"
            >
              <div class="product-card-top">
                <div class="product-icon">
                  <svg width="18" height="18" fill="none" stroke="#E8622C" stroke-width="1.8" viewBox="0 0 24 24">
                    <path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/>
                    <polyline points="13 2 13 9 20 9"/>
                  </svg>
                </div>
                <div class="product-id-badge">{{ product.id }}</div>
              </div>
              <div class="product-name">{{ product.name }}</div>
              <div class="product-criteria">{{ product.criteria_count }} criteria</div>
              <div class="product-cta">
                Run Scoring
                <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- ── STEP 3: Running / result ───────────────────────── -->
      <template v-else-if="step === 3">

        <!-- Client + product recap bar -->
        <div class="client-bar">
          <div class="client-bar-left">
            <div class="client-avatar-lg">{{ initials(client.client_name) }}</div>
            <div>
              <div class="client-bar-name">{{ client.client_name }}</div>
              <div class="client-bar-meta">
                <span class="client-bar-id">{{ client.client_id }}</span>
                <span v-if="client.sector" class="client-bar-sector">{{ client.sector }}</span>
              </div>
            </div>
          </div>
          <div class="product-pill">
            <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>
            {{ selectedProduct?.name }}
          </div>
          <button class="change-btn" @click="step = 2">
            <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6"/></svg>
            Change product
          </button>
        </div>

        <!-- Loading state -->
        <div v-if="scoring" class="scoring-loading">
          <div class="scoring-pulse"></div>
          <div class="scoring-steps">
            <div v-for="(s, i) in loadingSteps" :key="i" class="scoring-step"
              :class="{ active: i === currentStep, done: i < currentStep }">
              <span class="step-dot"></span>{{ s }}
            </div>
          </div>
        </div>

        <!-- Error -->
        <div v-else-if="scoreError" class="error-bar">
          ⚠️ {{ scoreError }}
          <button class="retry-btn" @click="runScoring">Retry</button>
        </div>

        <!-- Result -->
        <div v-else-if="result" class="result-wrap">

          <!-- Summary card -->
          <div class="summary-card">
            <div class="summary-left">
              <div class="summary-label">GLOBAL SCORE</div>
              <div class="summary-score" :class="scoreClass">
                {{ pct }}<span class="summary-pct">%</span>
              </div>
              <div class="summary-bar-track">
                <div class="summary-bar-fill" :style="{ width: pct + '%', background: scoreColor }"></div>
              </div>
              <div class="summary-pts">{{ result.summary?.total_score }} / {{ result.summary?.max_score }} pts</div>
            </div>
            <div class="summary-right">
              <div class="eligibility-badge" :class="eligClass">{{ eligLabel }}</div>
              <div class="summary-meta">
                <div class="smeta-row"><span>Criteria evaluated</span><strong>{{ result.summary?.criteria_count }}</strong></div>
                <div class="smeta-row"><span>Blocking triggered</span><strong>{{ result.summary?.blocking_triggered ? 'Yes' : 'No' }}</strong></div>
                <div class="smeta-row"><span>Product</span><strong>{{ result.product?.product_name }}</strong></div>
              </div>
            </div>
          </div>

          <!-- Criteria breakdown -->
          <div class="criteria-section">
            <div class="section-title">Criteria Breakdown</div>
            <div class="criteria-list">
              <div v-for="c in result.criteria_results" :key="c.criterion_id" class="criterion-row" @click="openDetail(c)">
                <div class="cr-left">
                  <div class="cr-label">{{ c.label }}</div>
                  <div class="cr-answer">
                    <span class="cr-type">{{ c.answer_type }}</span>
                    <span class="cr-val" :class="c.predicted_answer === 'unknown' ? 'dim' : ''">
                      {{ c.predicted_answer === 'unknown' ? 'Not found' : c.predicted_answer }}
                    </span>
                  </div>
                </div>
                <div class="cr-right">
                  <div class="cr-conf" :class="confClass(c)">{{ Math.round((c.confidence||0)*100) }}%</div>
                  <div class="cr-score">{{ c.score }}/{{ c.max_score }}</div>
                  <svg width="14" height="14" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="2" viewBox="0 0 24 24"><path d="M9 18l6-6-6-6"/></svg>
                </div>
              </div>
            </div>
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

          <!-- Actions -->
          <div class="result-actions">
            <button class="action-secondary" @click="step = 2">← Try another product</button>
            <button class="action-primary" @click="goToRecommendations">View Full Report →</button>
          </div>
        </div>
      </template>

      <!-- Criterion detail modal -->
      <div v-if="detailCriterion" class="modal-backdrop" @click.self="detailCriterion = null">
        <div class="modal">
          <div class="modal-header">
            <div class="modal-title">{{ detailCriterion.label }}</div>
            <button class="modal-close" @click="detailCriterion = null">✕</button>
          </div>
          <div class="modal-body">
            <div class="modal-row"><span class="ml">Answer</span><span class="mv">{{ detailCriterion.predicted_answer }}</span></div>
            <div class="modal-row"><span class="ml">Confidence</span><span class="mv">{{ Math.round((detailCriterion.confidence||0)*100) }}%</span></div>
            <div class="modal-row"><span class="ml">Score</span><span class="mv">{{ detailCriterion.score }} / {{ detailCriterion.max_score }} pts</span></div>
            <div v-if="detailCriterion.justification?.reasoning" class="modal-section">
              <div class="ml">Reasoning</div>
              <p class="modal-text">{{ detailCriterion.justification.reasoning }}</p>
            </div>
            <div v-if="detailCriterion.evidence?.exact_quote" class="modal-section">
              <div class="ml">Evidence</div>
              <blockquote class="modal-quote">{{ detailCriterion.evidence.exact_quote }}</blockquote>
              <a v-if="detailCriterion.evidence.source_url" :href="detailCriterion.evidence.source_url" target="_blank" class="modal-link">
                {{ detailCriterion.evidence.source_label }} ↗
              </a>
            </div>
          </div>
        </div>
      </div>

    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import api from '../services/api'
import { useScoringStore } from '../stores/scoring'

const router = useRouter()
const store  = useScoringStore()

// ── Step state ───────────────────────────────────────────────
const step = ref(1)

// ── Step 1: search ───────────────────────────────────────────
const searchQuery      = ref('')
const suggestions      = ref([])
const searching        = ref(false)
const showDropdown     = ref(false)
const highlightedIndex = ref(-1)
const acWrap           = ref(null)
let debounceTimer = null

// ── Step 2: products ─────────────────────────────────────────
const client          = ref(null)
const products        = ref([])
const loadingProducts = ref(false)
const selectedProduct = ref(null)

// ── Step 3: scoring ──────────────────────────────────────────
const scoring      = ref(false)
const scoreError   = ref('')
const result       = ref(null)
const currentStep  = ref(0)
const detailCriterion = ref(null)

const loadingSteps = [
  'Loading product criteria…',
  'Fetching client data…',
  'Crawling company website…',
  'Resolving LinkedIn…',
  'Evaluating criteria with AI…',
  'Computing final score…',
]

// ── Page header ──────────────────────────────────────────────
const pageTitle = computed(() => {
  if (step.value === 1) return 'Search Opportunities'
  if (step.value === 2) return client.value?.client_name || 'Select Product'
  return result.value ? 'Scoring Result' : 'Running Analysis…'
})
const pageSubtitle = computed(() => {
  if (step.value === 1) return 'Find AI qualification scores across your client accounts'
  if (step.value === 2) return 'Select a product to run the AI qualification pipeline'
  return `${client.value?.client_name} — ${selectedProduct.value?.name}`
})

// ── Helpers ──────────────────────────────────────────────────
function initials(name) {
  return (name || '').split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase() || '?'
}
const pct       = computed(() => Math.round((result.value?.summary?.normalized_score || 0) * 100))
const scoreColor = computed(() => pct.value >= 75 ? '#22c55e' : pct.value >= 40 ? '#f59e0b' : '#E8622C')
const scoreClass = computed(() => pct.value >= 75 ? 'green' : pct.value >= 40 ? 'amber' : 'orange')
const eligClass  = computed(() => {
  const s = result.value?.summary?.eligibility_status
  return s === 'eligible' ? 'elig-green' : s === 'to_review' ? 'elig-amber' : 'elig-red'
})
const eligLabel  = computed(() => {
  const s = result.value?.summary?.eligibility_status
  return s === 'eligible' ? '✓ Eligible' : s === 'to_review' ? '~ To Review' : '✗ Not Eligible'
})
function confClass(c) {
  const v = c.confidence || 0
  return v >= 0.8 ? 'conf-high' : v >= 0.5 ? 'conf-mid' : 'conf-low'
}
function openDetail(c) { detailCriterion.value = c }
function goToRecommendations() { store.setResult(result.value); router.push('/recommendations') }

// ── Step 1: search logic ─────────────────────────────────────
function onInput() {
  highlightedIndex.value = -1
  clearTimeout(debounceTimer)
  if (!searchQuery.value.trim()) { suggestions.value = []; showDropdown.value = false; return }
  debounceTimer = setTimeout(fetchSuggestions, 280)
}
async function onFocus() { await fetchSuggestions() }
async function fetchSuggestions() {
  searching.value = true; showDropdown.value = true
  try {
    const res = await api.searchAccounts(searchQuery.value)
    suggestions.value = res.data || []
  } catch { suggestions.value = [] }
  finally { searching.value = false }
}
function moveDown() { highlightedIndex.value = Math.min(highlightedIndex.value + 1, suggestions.value.length - 1) }
function moveUp()   { highlightedIndex.value = Math.max(highlightedIndex.value - 1, 0) }
function selectHighlighted() {
  if (suggestions.value[highlightedIndex.value]) pickClient(suggestions.value[highlightedIndex.value])
}
function handleClickOutside(e) {
  if (acWrap.value && !acWrap.value.contains(e.target)) showDropdown.value = false
}

async function pickClient(item) {
  client.value = item
  searchQuery.value = item.client_name
  showDropdown.value = false
  step.value = 2
  loadingProducts.value = true
  try {
    const res = await api.listProducts()
    products.value = res.data || []
  } catch { products.value = [] }
  finally { loadingProducts.value = false }
}

function resetToStep1() {
  step.value = 1; client.value = null; result.value = null
  scoreError.value = ''; searchQuery.value = ''; suggestions.value = []
}

// ── Step 2: pick product ─────────────────────────────────────
async function pickProduct(product) {
  selectedProduct.value = product
  step.value = 3
  await runScoring()
}

// ── Step 3: run scoring ──────────────────────────────────────
async function runScoring() {
  scoring.value = true; scoreError.value = ''; result.value = null; currentStep.value = 0
  const stepTimer = setInterval(() => {
    if (currentStep.value < loadingSteps.length - 1) currentStep.value++
  }, 1400)
  const reportId = store.addPendingReport(client.value.client_id, selectedProduct.value.id)
  try {
    const res = await api.runScoring(client.value.client_id, selectedProduct.value.id)
    clearInterval(stepTimer)
    if (res.data.error) { store.failReport(reportId); scoreError.value = res.data.detail || res.data.error; return }
    store.updateReport(reportId, res.data)
    result.value = res.data
  } catch (e) {
    clearInterval(stepTimer)
    store.failReport(reportId)
    scoreError.value = e.response?.data?.detail || e.message || 'Unexpected error'
  } finally { scoring.value = false }
}

onMounted(() => document.addEventListener('mousedown', handleClickOutside))
onBeforeUnmount(() => document.removeEventListener('mousedown', handleClickOutside))
</script>

<style scoped>
.page { position: relative; z-index: 1; }

/* ── Step center layout ── */
.step-center { display: flex; flex-direction: column; align-items: center; gap: 20px; max-width: 560px; margin: 60px auto 0; }
.step-icon { width: 64px; height: 64px; background: rgba(232,98,44,0.12); border: 1px solid rgba(232,98,44,0.25); border-radius: 18px; display: flex; align-items: center; justify-content: center; }
.step-title { font-size: 28px; font-weight: 800; color: #fff; text-align: center; }
.step-desc { font-size: 14px; color: rgba(255,255,255,0.35); text-align: center; }

/* ── Autocomplete ── */
.autocomplete-wrap { position: relative; width: 100%; }
.input-icon-wrap { position: relative; }
.input-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: rgba(255,255,255,0.3); pointer-events: none; }
.search-input { width: 100%; padding: 15px 44px 15px 42px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; color: #fff; font-size: 15px; outline: none; transition: border-color 0.2s, box-shadow 0.2s; }
.search-input:focus { border-color: rgba(232,98,44,0.5); box-shadow: 0 0 0 3px rgba(232,98,44,0.08); }
.search-input::placeholder { color: rgba(255,255,255,0.2); }
.input-spin { position: absolute; right: 14px; top: 50%; transform: translateY(-50%); width: 14px; height: 14px; border: 2px solid rgba(255,255,255,0.15); border-top-color: #E8622C; border-radius: 50%; animation: spin 0.7s linear infinite; }

.dropdown { position: absolute; top: calc(100% + 6px); left: 0; right: 0; z-index: 200; background: #0d1f38; border: 1px solid rgba(232,98,44,0.25); border-radius: 12px; overflow: hidden; box-shadow: 0 16px 48px rgba(0,0,0,0.5); max-height: 300px; overflow-y: auto; }
.dropdown-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.04); transition: background 0.12s; }
.dropdown-item:last-child { border-bottom: none; }
.dropdown-item:hover, .dropdown-item.highlighted { background: rgba(232,98,44,0.1); }
.item-avatar { width: 36px; height: 36px; border-radius: 9px; flex-shrink: 0; background: linear-gradient(135deg, #1a3a5c, #0d2540); border: 1px solid rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; color: rgba(255,255,255,0.8); }
.item-info { flex: 1; min-width: 0; }
.item-name { font-size: 14px; font-weight: 600; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 3px; }
.item-meta { display: flex; gap: 8px; flex-wrap: wrap; }
.item-id { font-size: 11px; color: rgba(255,255,255,0.25); font-family: monospace; }
.item-sector { font-size: 11px; color: rgba(232,98,44,0.7); }
.item-emp { font-size: 11px; color: rgba(255,255,255,0.3); }
.no-results { padding: 20px; color: rgba(255,255,255,0.3); font-size: 13px; text-align: center; }

/* ── Client bar ── */
.client-bar { display: flex; align-items: center; gap: 16px; padding: 16px 20px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; margin-bottom: 28px; }
.client-bar-left { display: flex; align-items: center; gap: 14px; flex: 1; min-width: 0; }
.client-avatar-lg { width: 44px; height: 44px; border-radius: 12px; flex-shrink: 0; background: linear-gradient(135deg, #E8622C, #ff7a45); display: flex; align-items: center; justify-content: center; font-size: 15px; font-weight: 800; color: #fff; }
.client-bar-name { font-size: 16px; font-weight: 700; color: #fff; }
.client-bar-meta { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 3px; }
.client-bar-id { font-size: 11px; color: rgba(255,255,255,0.25); font-family: monospace; }
.client-bar-sector { font-size: 11px; color: rgba(232,98,44,0.7); }
.client-bar-emp { font-size: 11px; color: rgba(255,255,255,0.35); }
.change-btn { display: flex; align-items: center; gap: 6px; padding: 8px 14px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: rgba(255,255,255,0.5); font-size: 12.5px; cursor: pointer; white-space: nowrap; transition: all 0.18s; flex-shrink: 0; }
.change-btn:hover { color: #fff; border-color: rgba(255,255,255,0.2); }
.product-pill { display: flex; align-items: center; gap: 6px; padding: 6px 12px; background: rgba(232,98,44,0.1); border: 1px solid rgba(232,98,44,0.25); border-radius: 99px; color: #E8622C; font-size: 12.5px; font-weight: 600; white-space: nowrap; }

/* ── Products grid ── */
.products-section { }
.products-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.products-title { font-size: 18px; font-weight: 700; color: #fff; }
.products-sub { font-size: 13px; color: rgba(255,255,255,0.35); margin-top: 3px; }
.products-count { font-size: 12px; color: rgba(255,255,255,0.3); background: rgba(255,255,255,0.06); padding: 5px 12px; border-radius: 99px; }
.products-loading { display: flex; align-items: center; gap: 10px; color: rgba(255,255,255,0.4); font-size: 14px; padding: 40px 0; justify-content: center; }
.spinner { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.15); border-top-color: #E8622C; border-radius: 50%; animation: spin 0.7s linear infinite; flex-shrink: 0; }

.products-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 14px; }
.product-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 20px; cursor: pointer; transition: all 0.2s; display: flex; flex-direction: column; gap: 10px; }
.product-card:hover { background: rgba(232,98,44,0.07); border-color: rgba(232,98,44,0.3); transform: translateY(-2px); box-shadow: 0 8px 28px rgba(0,0,0,0.25); }
.product-card-top { display: flex; align-items: center; justify-content: space-between; }
.product-icon { width: 38px; height: 38px; background: rgba(232,98,44,0.1); border: 1px solid rgba(232,98,44,0.2); border-radius: 10px; display: flex; align-items: center; justify-content: center; }
.product-id-badge { font-size: 11px; font-weight: 700; color: rgba(255,255,255,0.3); font-family: monospace; background: rgba(255,255,255,0.05); padding: 3px 8px; border-radius: 6px; }
.product-name { font-size: 14px; font-weight: 700; color: #fff; line-height: 1.4; flex: 1; }
.product-criteria { font-size: 12px; color: rgba(255,255,255,0.3); }
.product-cta { display: flex; align-items: center; gap: 6px; font-size: 12.5px; font-weight: 700; color: #E8622C; margin-top: 4px; }

/* ── Scoring loading ── */
.scoring-loading { display: flex; flex-direction: column; align-items: center; gap: 32px; padding: 60px 0; }
.scoring-pulse { width: 64px; height: 64px; border-radius: 50%; border: 2px solid rgba(232,98,44,0.3); position: relative; }
.scoring-pulse::after { content: '⚡'; position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 24px; animation: pulse 1.4s ease-in-out infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.88)} }
.scoring-steps { display: flex; flex-direction: column; gap: 10px; }
.scoring-step { display: flex; align-items: center; gap: 10px; font-size: 13.5px; color: rgba(255,255,255,0.25); transition: color 0.3s; }
.scoring-step.active { color: #E8622C; }
.scoring-step.done { color: rgba(255,255,255,0.55); }
.step-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; flex-shrink: 0; }

/* ── Result ── */
.result-wrap { display: flex; flex-direction: column; gap: 22px; }
.summary-card { display: flex; gap: 32px; padding: 24px 28px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; }
.summary-left { display: flex; flex-direction: column; gap: 8px; min-width: 160px; }
.summary-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; color: rgba(255,255,255,0.25); }
.summary-score { font-size: 54px; font-weight: 900; line-height: 1; }
.summary-pct { font-size: 26px; font-weight: 600; }
.summary-bar-track { height: 6px; background: rgba(255,255,255,0.08); border-radius: 99px; overflow: hidden; }
.summary-bar-fill { height: 100%; border-radius: 99px; transition: width 0.8s ease; }
.summary-pts { font-size: 12px; color: rgba(255,255,255,0.35); }
.summary-right { flex: 1; display: flex; flex-direction: column; gap: 16px; justify-content: center; }
.eligibility-badge { display: inline-flex; align-self: flex-start; padding: 6px 14px; border-radius: 99px; font-size: 13px; font-weight: 700; }
.elig-green { background: rgba(34,197,94,0.12); color: #4ade80; border: 1px solid rgba(34,197,94,0.2); }
.elig-amber { background: rgba(245,158,11,0.12); color: #fbbf24; border: 1px solid rgba(245,158,11,0.2); }
.elig-red   { background: rgba(232,98,44,0.12);  color: #E8622C;  border: 1px solid rgba(232,98,44,0.2); }
.summary-meta { display: flex; flex-direction: column; gap: 6px; }
.smeta-row { display: flex; justify-content: space-between; font-size: 13px; color: rgba(255,255,255,0.4); padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
.smeta-row:last-child { border-bottom: none; }
.smeta-row strong { color: #fff; }
.green { color: #4ade80; } .amber { color: #fbbf24; } .orange { color: #E8622C; }

/* ── Criteria list ── */
.section-title { font-size: 13px; font-weight: 700; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }
.criteria-list { display: flex; flex-direction: column; gap: 6px; }
.criterion-row { display: flex; align-items: center; gap: 14px; padding: 14px 16px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; cursor: pointer; transition: all 0.15s; }
.criterion-row:hover { background: rgba(232,98,44,0.05); border-color: rgba(232,98,44,0.2); }
.cr-left { flex: 1; min-width: 0; }
.cr-label { font-size: 13.5px; font-weight: 600; color: rgba(255,255,255,0.85); margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cr-answer { display: flex; align-items: center; gap: 8px; }
.cr-type { font-size: 10px; color: rgba(232,98,44,0.6); text-transform: uppercase; font-weight: 700; letter-spacing: 0.4px; }
.cr-val { font-size: 12.5px; color: rgba(255,255,255,0.55); }
.cr-val.dim { color: rgba(255,255,255,0.2); font-style: italic; }
.cr-right { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
.cr-conf { font-size: 12px; font-weight: 700; padding: 2px 8px; border-radius: 99px; }
.conf-high { background: rgba(34,197,94,0.12); color: #4ade80; }
.conf-mid  { background: rgba(245,158,11,0.12); color: #fbbf24; }
.conf-low  { background: rgba(232,98,44,0.12);  color: #E8622C; }
.cr-score { font-size: 13px; font-weight: 700; color: rgba(255,255,255,0.6); white-space: nowrap; }

/* ── Trace ── */
.trace { padding: 16px 20px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; }
.trace summary { font-size: 12px; color: rgba(255,255,255,0.3); cursor: pointer; font-weight: 600; }
.trace-body { margin-top: 12px; display: flex; flex-direction: column; gap: 5px; }
.trace-line { display: flex; align-items: flex-start; gap: 8px; font-size: 11.5px; color: rgba(255,255,255,0.3); font-family: monospace; }
.trace-dot { width: 4px; height: 4px; border-radius: 50%; background: #E8622C; flex-shrink: 0; margin-top: 5px; }

/* ── Actions ── */
.result-actions { display: flex; gap: 12px; justify-content: flex-end; }
.action-primary { padding: 11px 24px; background: linear-gradient(135deg, #E8622C, #ff7a45); color: #fff; font-size: 14px; font-weight: 700; border: none; border-radius: 10px; cursor: pointer; transition: all 0.2s; }
.action-primary:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(232,98,44,0.4); }
.action-secondary { padding: 11px 20px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); color: rgba(255,255,255,0.6); font-size: 14px; font-weight: 600; border-radius: 10px; cursor: pointer; transition: all 0.18s; }
.action-secondary:hover { color: #fff; border-color: rgba(255,255,255,0.2); }

/* ── Error ── */
.error-bar { padding: 14px 18px; background: rgba(232,98,44,0.1); border: 1px solid rgba(232,98,44,0.3); border-radius: 10px; color: #fb8c5a; font-size: 13px; display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.retry-btn { padding: 6px 14px; background: rgba(232,98,44,0.2); border: 1px solid rgba(232,98,44,0.4); border-radius: 7px; color: #E8622C; font-size: 12.5px; cursor: pointer; }

/* ── Modal ── */
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.72); backdrop-filter: blur(4px); z-index: 300; display: flex; align-items: center; justify-content: center; padding: 24px; }
.modal { background: #0A1628; border: 1px solid rgba(232,98,44,0.2); border-radius: 16px; width: 100%; max-width: 560px; max-height: 82vh; overflow-y: auto; }
.modal-header { display: flex; align-items: flex-start; justify-content: space-between; padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.07); position: sticky; top: 0; background: #0A1628; z-index: 1; gap: 16px; }
.modal-title { font-size: 14.5px; font-weight: 700; color: #fff; line-height: 1.5; }
.modal-close { background: none; border: none; color: rgba(255,255,255,0.35); font-size: 16px; cursor: pointer; flex-shrink: 0; }
.modal-body { padding: 20px 24px; display: flex; flex-direction: column; gap: 14px; }
.modal-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
.ml { font-size: 11.5px; color: rgba(255,255,255,0.35); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
.mv { font-size: 13.5px; color: #fff; font-weight: 600; }
.modal-section { display: flex; flex-direction: column; gap: 8px; }
.modal-text { font-size: 13px; color: rgba(255,255,255,0.5); line-height: 1.7; }
.modal-quote { margin: 0; padding: 10px 14px; background: rgba(232,98,44,0.06); border-left: 2px solid #E8622C; border-radius: 4px; font-size: 12.5px; color: rgba(255,255,255,0.45); font-style: italic; line-height: 1.6; }
.modal-link { font-size: 13px; color: #E8622C; text-decoration: none; font-weight: 600; }
.modal-link:hover { text-decoration: underline; }

@keyframes spin { to { transform: rotate(360deg); } }
</style>
