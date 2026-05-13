<template>
  <AppLayout title="Campaigns" subtitle="Select a campaign, choose a product and rank clients by AI score">
    <div class="page">

      <!-- ── STEP 1 : Campaign list ───────────────────────────────────────── -->
      <template v-if="step === 1">
        <div class="step-header">
          <div class="step-icon">
            <svg width="26" height="26" fill="none" stroke="#E8622C" stroke-width="2" viewBox="0 0 24 24">
              <path d="M3 3h18v4H3z"/><path d="M3 9h18v4H3z"/><path d="M3 15h10v4H3z"/>
            </svg>
          </div>
          <h2 class="step-title">Select a Campaign</h2>
          <p class="step-desc">Choose a Salesforce campaign to score its client targets</p>
        </div>

        <div class="search-bar">
          <svg width="15" height="15" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="2" viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/>
          </svg>
          <input v-model="campSearch" placeholder="Filter campaigns by name…" class="search-input" />
        </div>

        <div v-if="loadingCampaigns" class="loading-center">
          <span class="spin"></span> Loading campaigns…
        </div>
        <div v-else-if="campaignError" class="error-bar">⚠️ {{ campaignError }}</div>
        <div v-else>
          <!-- Result count -->
          <div class="camp-result-info" v-if="!loadingCampaigns">
            <span>{{ filteredCampaigns.length }} campagne{{ filteredCampaigns.length > 1 ? 's' : '' }}</span>
          </div>

          <div class="campaign-grid">
            <div
              v-for="c in pagedCampaigns"
              :key="c.id || c.title"
              class="campaign-card"
              @click="selectCampaign(c)"
            >
              <div class="cc-top">
                <span class="cc-status" :class="statusClass(c.status)">{{ c.status || 'Active' }}</span>
                <span class="cc-count">{{ c.total_targets }} targets</span>
              </div>
              <div class="cc-title">{{ c.title }}</div>
              <div class="cc-meta">
                <span v-if="c.pole">{{ c.pole }}</span>
                <span v-if="c.sf_campaign_id" class="cc-id">{{ c.sf_campaign_id }}</span>
              </div>
              <div v-if="c.product_ids?.length" class="cc-products">
                <span v-for="pid in c.product_ids.slice(0,4)" :key="pid" class="cc-chip">{{ pid }}</span>
                <span v-if="c.product_ids.length > 4" class="cc-chip dim">+{{ c.product_ids.length - 4 }}</span>
              </div>
            </div>
            <div v-if="filteredCampaigns.length === 0" class="empty-state">
              No campaigns match "{{ campSearch }}"
            </div>
          </div>

          <Pagination
            v-model:page="campPage"
            v-model:perPage="campPerPage"
            :total="filteredCampaigns.length"
            :per-page-options="[12, 24, 48]"
          />
        </div>
      </template>

      <!-- ── STEP 2 : Targets + product selection ──────────────────────────── -->
      <template v-else-if="step === 2">
        <!-- Campaign bar -->
        <div class="client-bar">
          <div class="client-bar-left">
            <div class="camp-avatar">
              <svg width="18" height="18" fill="none" stroke="#fff" stroke-width="2" viewBox="0 0 24 24">
                <path d="M3 3h18v4H3z"/><path d="M3 9h18v4H3z"/><path d="M3 15h10v4H3z"/>
              </svg>
            </div>
            <div>
              <div class="client-bar-name">{{ campaign.title }}</div>
              <div class="client-bar-meta">
                <span v-if="campaign.sf_campaign_id" class="client-bar-id">{{ campaign.sf_campaign_id }}</span>
                <span v-if="campaign.pole" class="client-bar-sector">{{ campaign.pole }}</span>
                <span class="client-bar-emp">{{ targets.length }} clients</span>
              </div>
            </div>
          </div>
          <button class="change-btn" @click="step = 1; campaign = null; targets = []">
            <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6"/></svg>
            Change
          </button>
        </div>

        <!-- Product config row -->
        <div class="config-row">

          <!-- CASE 1 : campaign has linked products → show them, no dropdown -->
          <div v-if="campaign.product_ids?.length" class="config-block">
            <label class="config-label">Produit(s) lié(s) à cette campagne</label>
            <div class="linked-products">
              <span
                v-for="pid in campaign.product_ids"
                :key="pid"
                class="linked-chip"
                :class="{ 'linked-chip-active': selectedProduct === pid }"
                @click="selectedProduct = pid"
              >
                <svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                {{ pid }}
                <span class="linked-chip-name">{{ products.find(p => p.id === pid)?.name }}</span>
                <svg v-if="selectedProduct === pid" width="11" height="11" fill="none" stroke="#22c55e" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
              </span>
              <span v-if="campaign.product_ids.length > 1" class="linked-hint">
                Cliquez sur un produit pour le sélectionner
              </span>
            </div>
          </div>

          <!-- CASE 2 : no linked products → show full selector -->
          <div v-else class="config-block">
            <label class="config-label">Produit à scorer</label>
            <select v-model="selectedProduct" class="config-select">
              <option value="" disabled>Sélectionner un produit…</option>
              <option v-for="p in products" :key="p.id" :value="p.id">{{ p.id }} — {{ p.name }}</option>
            </select>
          </div>

          <!-- Clients selected -->
          <div class="config-block">
            <label class="config-label">Clients sélectionnés</label>
            <div class="config-count">
              <b>{{ selectedIds.length }}</b> / {{ targets.length }}
              <button class="sel-all-btn" @click="toggleAll">{{ allSelected ? 'Tout désélectionner' : 'Tout sélectionner' }}</button>
            </div>
          </div>

          <!-- Run button -->
          <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px">
            <button
              class="score-btn"
              :disabled="!selectedProduct || selectedIds.length === 0 || scoring"
              @click="runScoring"
            >
              <svg v-if="!scoring" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              <span v-if="scoring" class="spin" style="width:13px;height:13px;border-width:2px"></span>
              {{ scoring ? 'Scoring…' : 'Run Scoring' }}
            </button>
            <span v-if="!selectedProduct" class="btn-hint">⚠ Sélectionner un produit</span>
            <span v-else-if="selectedIds.length === 0" class="btn-hint">⚠ Sélectionner au moins un client</span>
          </div>
        </div>

        <div v-if="scoringError" class="error-bar" style="margin-bottom:16px">⚠️ {{ scoringError }}</div>

        <!-- Targets table -->
        <div v-if="loadingTargets" class="loading-center"><span class="spin"></span> Loading targets…</div>
        <div v-else-if="targets.length === 0" class="empty-state">No clients found for this campaign.</div>
        <div v-else class="targets-table-wrap">
          <table class="targets-table">
            <thead>
              <tr>
                <th style="width:36px">
                  <input type="checkbox" :checked="allSelected" @change="toggleAll" class="cb" />
                </th>
                <th>Client</th>
                <th>Market</th>
                <th>Status</th>
                <th>Calls</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in targets" :key="t.id || t.account_id" :class="{ selected: isSelected(t.account_id) }">
                <td>
                  <input type="checkbox" :checked="isSelected(t.account_id)" @change="toggleId(t.account_id)" class="cb" />
                </td>
                <td>
                  <div class="t-name">{{ t.account_name || t.account_id || '—' }}</div>
                  <div class="t-id">{{ t.account_id }}</div>
                </td>
                <td><span class="t-market">{{ t.market || '—' }}</span></td>
                <td><span class="t-status" :class="statusClass(t.status)">{{ t.status || '—' }}</span></td>
                <td class="t-calls">{{ t.nb_appels ?? '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <!-- ── STEP 3 : Scoring results ──────────────────────────────────────── -->
      <template v-else-if="step === 3">
        <!-- Bar -->
        <div class="client-bar">
          <div class="client-bar-left">
            <div class="camp-avatar">
              <svg width="18" height="18" fill="none" stroke="#fff" stroke-width="2" viewBox="0 0 24 24">
                <path d="M3 3h18v4H3z"/><path d="M3 9h18v4H3z"/><path d="M3 15h10v4H3z"/>
              </svg>
            </div>
            <div>
              <div class="client-bar-name">{{ campaign.title }}</div>
              <div class="client-bar-meta">
                <span class="client-bar-sector">{{ selectedProduct }}</span>
                <span v-if="scoreResult" class="client-bar-emp">
                  {{ scoreResult.succeeded }}/{{ scoreResult.total }} scored
                </span>
              </div>
            </div>
          </div>
          <button class="change-btn" @click="step = 2; scoreResult = null; scoring = false">
            <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6"/></svg>
            Back
          </button>
        </div>

        <!-- Progress operation (campaign scoring) -->
        <ProgressOperation
          v-if="scoring"
          :title="`Scoring de ${selectedIds.length} client(s) — ${selectedProduct}`"
          :phases="campProgress.phases.value"
          :currentPhase="campProgress.currentPhase.value"
          :pct="campProgress.pct.value"
          :elapsed="campProgress.elapsed.value"
          :remainingLabel="campProgress.remainingLabel.value"
          :active="campProgress.active.value"
        />

        <!-- Error -->
        <div v-else-if="scoringError" class="error-bar">⚠️ {{ scoringError }}</div>

        <!-- Results once available -->
        <template v-else-if="scoreResult">
          <!-- KPI row -->
          <div class="kpi-row">
            <div class="kpi-card"><div class="kpi-val">{{ scoreResult.total }}</div><div class="kpi-lbl">Scored</div></div>
            <div class="kpi-card success"><div class="kpi-val">{{ eligibleCount }}</div><div class="kpi-lbl">Eligible</div></div>
            <div class="kpi-card amber"><div class="kpi-val">{{ reviewCount }}</div><div class="kpi-lbl">To Review</div></div>
            <div class="kpi-card danger"><div class="kpi-val">{{ scoreResult.failed }}</div><div class="kpi-lbl">Failed</div></div>
            <div class="kpi-card cached"><div class="kpi-val">{{ scoreResult.from_cache || 0 }}</div><div class="kpi-lbl">From Cache</div></div>
          </div>

          <!-- Ranked results -->
          <div class="results-section">
            <div class="results-title">
              Clients ranked by priority
              <span class="results-sub">— {{ selectedProduct }} · {{ campaign.title }}</span>
            </div>

            <div
              v-for="(r, rank) in scoreResult.results"
              :key="r.client_id"
              class="result-row"
              :class="eligClass(r)"
            >
            <div class="rank-badge" :class="eligClass(r)">{{ rank + 1 }}</div>
            <div class="rr-main">
              <div class="rr-name">
                {{ clientName(r) }}
                <span class="rr-id">{{ r.client_id }}</span>
                <span v-if="r.cache_hit" class="cache-badge">⚡ cached</span>
              </div>
              <div class="rr-meta" v-if="r.status === 'success'">
                <span class="rr-elig" :class="eligClass(r)">{{ eligLabel(r) }}</span>
                <span class="rr-pts">{{ r.summary?.total_score }}/{{ r.summary?.max_score }} pts</span>
                <span class="rr-count">{{ r.summary?.criteria_count }} criteria</span>
              </div>
              <div v-else class="rr-error">{{ r.error }}</div>
            </div>
            <div class="rr-score" v-if="r.status === 'success'">
              <div class="score-bar">
                <div class="score-fill" :style="{ width: scorePct(r) + '%', background: scoreColor(r) }"></div>
              </div>
              <div class="score-pct" :style="{ color: scoreColor(r) }">{{ scorePct(r) }}<span>%</span></div>
            </div>
          </div>

          </div>
        </template>
      </template>

    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import Pagination from '../components/Pagination.vue'
import api from '../services/api'
import { useNotifications } from '../composables/useNotifications'
import { useProgress }      from '../composables/useProgress'
import ProgressOperation    from '../components/ProgressOperation.vue'

const { notify }      = useNotifications()
const campProgress    = useProgress()

// ── State ──────────────────────────────────────────────────────────────────
const step           = ref(1)
const campaigns      = ref([])
const campaign       = ref(null)
const targets        = ref([])
const products       = ref([])
const selectedProduct= ref('')
const selectedIds    = ref([])
const scoreResult    = ref(null)
const campSearch     = ref('')
const campPage       = ref(1)
const campPerPage    = ref(12)

const loadingCampaigns = ref(false)
const loadingTargets   = ref(false)
const scoring          = ref(false)
const campaignError    = ref('')
const scoringError     = ref('')

// ── Computed ───────────────────────────────────────────────────────────────
const filteredCampaigns = computed(() => {
  const q = campSearch.value.toLowerCase()
  if (!q) return campaigns.value
  return campaigns.value.filter(c =>
    (c.title || '').toLowerCase().includes(q) ||
    (c.sf_campaign_id || '').toLowerCase().includes(q) ||
    (c.pole || '').toLowerCase().includes(q)
  )
})

// Reset to page 1 when search changes
watch(campSearch, () => { campPage.value = 1 })

const pagedCampaigns = computed(() => {
  const start = (campPage.value - 1) * campPerPage.value
  return filteredCampaigns.value.slice(start, start + campPerPage.value)
})

const allSelected = computed(() =>
  targets.value.length > 0 && selectedIds.value.length === targets.value.length
)

const eligibleCount = computed(() =>
  (scoreResult.value?.results || []).filter(r => r.summary?.eligibility_status === 'eligible').length
)
const reviewCount = computed(() =>
  (scoreResult.value?.results || []).filter(r => r.summary?.eligibility_status === 'to_review').length
)

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(async () => {
  loadingCampaigns.value = true
  try {
    const [campRes, prodRes] = await Promise.all([api.listCampaigns(), api.listProducts()])
    campaigns.value = campRes.data || []
    products.value  = prodRes.data || []
  } catch (e) {
    campaignError.value = e.response?.data?.detail || e.message || 'Failed to load campaigns'
  } finally {
    loadingCampaigns.value = false
  }
})

// ── Actions ────────────────────────────────────────────────────────────────
async function selectCampaign(c) {
  campaign.value = c
  step.value = 2
  loadingTargets.value = true
  selectedIds.value = []
  targets.value = []
  // Auto-select product: if campaign has exactly one → select it directly
  if (c.product_ids?.length === 1) {
    selectedProduct.value = c.product_ids[0]
  } else {
    selectedProduct.value = ''   // reset so user picks manually
  }

  try {
    const res = await api.getCampaignTargets(c.id || c.title)
    targets.value = (res.data?.targets || []).filter(t => t.account_id)
    // Auto-select all by default
    selectedIds.value = targets.value.map(t => t.account_id)
  } catch (e) {
    console.error('Failed to load targets', e)
  } finally {
    loadingTargets.value = false
  }
}

function toggleAll() {
  if (allSelected.value) selectedIds.value = []
  else selectedIds.value = targets.value.map(t => t.account_id)
}

function isSelected(id) { return selectedIds.value.includes(id) }

function toggleId(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx === -1) selectedIds.value.push(id)
  else selectedIds.value.splice(idx, 1)
}

async function runScoring() {
  if (!selectedProduct.value || selectedIds.value.length === 0) return
  scoring.value = true
  scoringError.value = ''
  step.value = 3
  scoreResult.value = null
  campProgress.start('campaign_scoring')
  try {
    const res = await api.scoreCampaignTargets(
      campaign.value.id || campaign.value.title,
      selectedIds.value,
      selectedProduct.value,
    )
    scoreResult.value = res.data
    campProgress.finish()
    const d = res.data
    notify('✅ Scoring campagne terminé !', {
      body: `${campaign.value.title} — ${d.succeeded}/${d.total} clients scorés`,
      type: 'success',
    })
  } catch (e) {
    scoringError.value = e.response?.data?.detail || e.message || 'Scoring failed'
    notify('❌ Erreur scoring campagne', { body: scoringError.value, type: 'error' })
    step.value = 2
  } finally {
    scoring.value = false
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function statusClass(s) {
  if (!s) return ''
  const l = s.toLowerCase()
  if (l.includes('actif') || l.includes('active') || l.includes('en cours')) return 'st-green'
  if (l.includes('prospect') || l.includes('qualif')) return 'st-amber'
  return 'st-grey'
}

function eligClass(r) {
  const s = r.summary?.eligibility_status
  return s === 'eligible' ? 'elig-green' : s === 'to_review' ? 'elig-amber' : 'elig-red'
}

function eligLabel(r) {
  const s = r.summary?.eligibility_status
  return s === 'eligible' ? '✓ Eligible' : s === 'to_review' ? '~ To Review' : '✗ Not Eligible'
}

function scorePct(r) {
  const s = r.summary
  if (!s || !s.max_score) return 0
  return Math.round((s.total_score / s.max_score) * 100)
}

function scoreColor(r) {
  const p = scorePct(r)
  return p >= 75 ? '#22c55e' : p >= 40 ? '#f59e0b' : '#E8622C'
}

function clientName(r) {
  const t = targets.value.find(t => t.account_id === r.client_id)
  return t?.account_name || r.client_id
}
</script>

<style scoped>
.page { position: relative; z-index: 1; }

/* ── Step header ── */
.step-header { display: flex; flex-direction: column; align-items: center; gap: 14px; max-width: 560px; margin: 40px auto 32px; text-align: center; }
.step-icon { width: 60px; height: 60px; background: rgba(232,98,44,0.12); border: 1px solid rgba(232,98,44,0.25); border-radius: 18px; display: flex; align-items: center; justify-content: center; }
.step-title { font-size: 26px; font-weight: 800; color: #fff; }
.step-desc { font-size: 14px; color: rgba(255,255,255,0.35); }

/* ── Search ── */
.search-bar { display: flex; align-items: center; gap: 10px; max-width: 480px; margin: 0 auto 28px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 12px 16px; }
.search-input { flex: 1; background: none; border: none; outline: none; color: #fff; font-size: 14px; }
.search-input::placeholder { color: rgba(255,255,255,0.2); }

/* ── Campaign grid ── */
.camp-result-info { font-size: 12px; color: rgba(255,255,255,0.3); margin-bottom: 12px; }
.campaign-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(270px, 1fr)); gap: 14px; }
.campaign-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 18px; cursor: pointer; transition: all 0.2s; display: flex; flex-direction: column; gap: 8px; }
.campaign-card:hover { background: rgba(232,98,44,0.07); border-color: rgba(232,98,44,0.3); transform: translateY(-2px); box-shadow: 0 8px 28px rgba(0,0,0,0.25); }
.cc-top { display: flex; align-items: center; justify-content: space-between; }
.cc-status { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 99px; }
.cc-count { font-size: 11px; color: rgba(255,255,255,0.4); }
.cc-title { font-size: 14px; font-weight: 700; color: #fff; line-height: 1.4; }
.cc-meta { display: flex; gap: 8px; flex-wrap: wrap; }
.cc-meta span { font-size: 11px; color: rgba(255,255,255,0.35); }
.cc-id { font-family: monospace; }
.cc-products { display: flex; flex-wrap: wrap; gap: 4px; }
.cc-chip { font-size: 10px; font-weight: 700; background: rgba(232,98,44,0.12); border: 1px solid rgba(232,98,44,0.2); color: #E8622C; padding: 2px 7px; border-radius: 6px; }
.cc-chip.dim { color: rgba(255,255,255,0.3); background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.1); }

/* ── Status badges ── */
.st-green { background: rgba(34,197,94,0.15); color: #22c55e; }
.st-amber { background: rgba(245,158,11,0.15); color: #f59e0b; }
.st-grey  { background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.4); }

/* ── Client bar ── */
.client-bar { display: flex; align-items: center; gap: 16px; padding: 16px 20px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; margin-bottom: 20px; }
.client-bar-left { display: flex; align-items: center; gap: 14px; flex: 1; min-width: 0; }
.camp-avatar { width: 42px; height: 42px; border-radius: 12px; flex-shrink: 0; background: linear-gradient(135deg, #E8622C, #ff7a45); display: flex; align-items: center; justify-content: center; }
.client-bar-name { font-size: 15px; font-weight: 700; color: #fff; }
.client-bar-meta { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 3px; }
.client-bar-id { font-size: 11px; color: rgba(255,255,255,0.25); font-family: monospace; }
.client-bar-sector { font-size: 11px; color: rgba(232,98,44,0.7); }
.client-bar-emp { font-size: 11px; color: rgba(255,255,255,0.35); }
.change-btn { display: flex; align-items: center; gap: 6px; padding: 8px 14px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: rgba(255,255,255,0.5); font-size: 12.5px; cursor: pointer; white-space: nowrap; transition: all 0.18s; flex-shrink: 0; }
.change-btn:hover { color: #fff; border-color: rgba(255,255,255,0.2); }

/* ── Config row ── */
.config-row { display: flex; align-items: flex-end; gap: 16px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.07); border-radius: 12px; padding: 16px 20px; margin-bottom: 20px; flex-wrap: wrap; }
.config-block { display: flex; flex-direction: column; gap: 6px; flex: 1; min-width: 180px; }
.config-label { font-size: 11px; font-weight: 700; color: rgba(255,255,255,0.4); letter-spacing: 0.5px; text-transform: uppercase; }
.config-select { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; color: #fff; font-size: 13px; padding: 9px 12px; outline: none; cursor: pointer; }
.config-select:focus { border-color: rgba(232,98,44,0.5); }
.config-count { display: flex; align-items: center; gap: 10px; font-size: 13px; color: rgba(255,255,255,0.6); }
.config-count b { color: #fff; font-size: 16px; }
.sel-all-btn { font-size: 11px; color: #E8622C; background: none; border: none; cursor: pointer; padding: 0; text-decoration: underline; }
.score-btn { display: flex; align-items: center; gap: 8px; padding: 10px 22px; background: linear-gradient(135deg, #E8622C, #ff7a45); border: none; border-radius: 10px; color: #fff; font-size: 13px; font-weight: 700; cursor: pointer; white-space: nowrap; transition: all 0.18s; flex-shrink: 0; box-shadow: 0 4px 16px rgba(232,98,44,0.3); }
.score-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(232,98,44,0.4); }
.score-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-hint { font-size: 11px; color: #f59e0b; }

/* ── Linked products ── */
.linked-products { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 4px; }
.linked-chip {
  display: flex; align-items: center; gap: 6px;
  padding: 7px 12px; border-radius: 10px; cursor: pointer;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.12);
  color: rgba(255,255,255,0.6); font-size: 12.5px; font-weight: 600;
  transition: all 0.18s;
}
.linked-chip:hover { background: rgba(232,98,44,0.08); border-color: rgba(232,98,44,0.3); color: #fff; }
.linked-chip-active { background: rgba(34,197,94,0.1); border-color: rgba(34,197,94,0.35); color: #22c55e; }
.linked-chip-name { font-size: 11px; font-weight: 400; color: inherit; opacity: 0.7; }
.linked-hint { font-size: 11px; color: rgba(255,255,255,0.25); font-style: italic; width: 100%; }

/* ── Targets table ── */
.targets-table-wrap { border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; overflow: hidden; }
.targets-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.targets-table thead { background: rgba(27,42,74,0.8); }
.targets-table th { padding: 11px 14px; text-align: left; font-size: 11px; font-weight: 700; color: rgba(255,255,255,0.4); letter-spacing: 0.5px; text-transform: uppercase; }
.targets-table td { padding: 10px 14px; border-top: 1px solid rgba(255,255,255,0.05); vertical-align: middle; }
.targets-table tr:hover td { background: rgba(255,255,255,0.03); }
.targets-table tr.selected td { background: rgba(232,98,44,0.06); }
.cb { width: 15px; height: 15px; cursor: pointer; accent-color: #E8622C; }
.t-name { font-weight: 600; color: #fff; font-size: 13px; }
.t-id { font-size: 10px; color: rgba(255,255,255,0.25); font-family: monospace; margin-top: 2px; }
.t-market { font-size: 11px; color: rgba(232,98,44,0.7); }
.t-status { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 6px; }
.t-calls { color: rgba(255,255,255,0.4); font-size: 12px; text-align: center; }

/* ── KPI row ── */
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
.kpi-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px; text-align: center; }
.kpi-card.success { background: rgba(34,197,94,0.06); border-color: rgba(34,197,94,0.2); }
.kpi-card.amber { background: rgba(245,158,11,0.06); border-color: rgba(245,158,11,0.2); }
.kpi-card.danger  { background: rgba(239,68,68,0.06);  border-color: rgba(239,68,68,0.2); }
.kpi-card.cached  { background: rgba(99,179,237,0.06); border-color: rgba(99,179,237,0.2); }
.kpi-val { font-size: 28px; font-weight: 800; color: #fff; }
.kpi-lbl { font-size: 11px; color: rgba(255,255,255,0.4); margin-top: 2px; }

/* ── Results ── */
.results-section { display: flex; flex-direction: column; gap: 10px; }
.results-title { font-size: 15px; font-weight: 700; color: #fff; margin-bottom: 6px; }
.results-sub { font-size: 12px; font-weight: 400; color: rgba(255,255,255,0.3); }

.result-row { display: flex; align-items: center; gap: 14px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px 18px; transition: all 0.15s; }
.result-row.elig-green { border-left: 3px solid #22c55e; }
.result-row.elig-amber { border-left: 3px solid #f59e0b; }
.result-row.elig-red   { border-left: 3px solid #E8622C; }

.rank-badge { width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 800; flex-shrink: 0; }
.rank-badge.elig-green { background: rgba(34,197,94,0.15); color: #22c55e; }
.rank-badge.elig-amber { background: rgba(245,158,11,0.15); color: #f59e0b; }
.rank-badge.elig-red   { background: rgba(232,98,44,0.15); color: #E8622C; }

.rr-main { flex: 1; min-width: 0; }
.rr-name { font-size: 14px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.rr-id { font-size: 10px; color: rgba(255,255,255,0.25); font-family: monospace; font-weight: 400; }
.rr-meta { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 4px; }
.rr-elig { font-size: 11px; font-weight: 700; }
.elig-green .rr-elig { color: #22c55e; }
.elig-amber .rr-elig { color: #f59e0b; }
.elig-red   .rr-elig { color: #E8622C; }
.rr-pts { font-size: 11px; color: rgba(255,255,255,0.4); }
.rr-count { font-size: 11px; color: rgba(255,255,255,0.3); }
.rr-error { font-size: 11px; color: #f87171; margin-top: 4px; }

.rr-score { display: flex; align-items: center; gap: 10px; flex-shrink: 0; width: 140px; }
.score-bar { flex: 1; height: 5px; background: rgba(255,255,255,0.1); border-radius: 99px; overflow: hidden; }
.score-fill { height: 100%; border-radius: 99px; transition: width 0.4s; }
.score-pct { font-size: 15px; font-weight: 800; width: 40px; text-align: right; }
.score-pct span { font-size: 10px; opacity: 0.6; }

/* ── Shared ── */
.loading-center { display: flex; align-items: center; gap: 10px; color: rgba(255,255,255,0.4); font-size: 14px; justify-content: center; padding: 60px 0; }
.error-bar { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); border-radius: 10px; padding: 12px 16px; color: #f87171; font-size: 13px; }
.empty-state { text-align: center; color: rgba(255,255,255,0.3); font-size: 14px; padding: 60px 0; }
.cap-notice  { font-size: 12px; color: rgba(245,158,11,0.8); background: rgba(245,158,11,0.06); border: 1px solid rgba(245,158,11,0.2); border-radius: 8px; padding: 10px 14px; margin-top: 8px; }
.cache-badge { font-size: 10px; font-weight: 700; color: #63b3ed; background: rgba(99,179,237,0.12); border: 1px solid rgba(99,179,237,0.3); padding: 2px 7px; border-radius: 6px; letter-spacing: 0.3px; }

/* ── Scoring loading block ── */
.scoring-loading-block { display: flex; align-items: center; gap: 20px; background: rgba(232,98,44,0.06); border: 1px solid rgba(232,98,44,0.2); border-radius: 14px; padding: 24px 28px; margin: 8px 0 24px; }
.scoring-pulse { width: 40px; height: 40px; border-radius: 50%; border: 3px solid rgba(232,98,44,0.2); border-top-color: #E8622C; animation: spin 0.8s linear infinite; flex-shrink: 0; }
.sl-title { font-size: 15px; font-weight: 700; color: #fff; margin-bottom: 4px; }
.sl-sub { font-size: 13px; color: rgba(255,255,255,0.4); }

.spin { display: inline-block; width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.15); border-top-color: #E8622C; border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
