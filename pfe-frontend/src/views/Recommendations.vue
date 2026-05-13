<template>
  <AppLayout title="Recommandations" subtitle="Meilleures opportunités détectées par l'IA sur l'ensemble des clients scorés">

    <!-- Loading -->
    <div v-if="loading" class="loading-center">
      <div class="loading-spinner"></div>
      <span>Analyse des opportunités en cours…</span>
    </div>

    <!-- Empty — no scoring done yet -->
    <div v-else-if="!data || data.stats?.total_scorings === 0" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="1.5" viewBox="0 0 24 24">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
        </svg>
      </div>
      <p class="empty-title">Aucune opportunité détectée</p>
      <p class="empty-sub">Scorez des clients depuis la page "Search Client" — les meilleures opportunités apparaîtront ici automatiquement.</p>
      <RouterLink to="/search" class="empty-cta">
        <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        Lancer un scoring
      </RouterLink>
    </div>

    <template v-else>

      <!-- ── KPI Banner ────────────────────────────────────────── -->
      <div class="kpi-banner">
        <div class="kpi-card">
          <div class="kpi-icon blue">
            <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          </div>
          <div>
            <div class="kpi-val">{{ data.stats.unique_clients }}</div>
            <div class="kpi-lbl">Clients scorés</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon green">
            <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
          </div>
          <div>
            <div class="kpi-val green">{{ data.stats.eligible_matches }}</div>
            <div class="kpi-lbl">Correspondances éligibles</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon amber">
            <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          </div>
          <div>
            <div class="kpi-val amber">{{ data.stats.to_review_matches }}</div>
            <div class="kpi-lbl">À examiner</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon orange">
            <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
          </div>
          <div>
            <div class="kpi-val">{{ data.stats.unique_products }}</div>
            <div class="kpi-lbl">Produits évalués</div>
          </div>
        </div>
      </div>

      <!-- ── Tabs ──────────────────────────────────────────────── -->
      <div class="tabs">
        <button class="tab" :class="{ active: tab === 'top' }"      @click="tab = 'top'">
          <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
          Meilleures opportunités
        </button>
        <button class="tab" :class="{ active: tab === 'clients' }"  @click="tab = 'clients'">
          <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>
          Par client
        </button>
        <button class="tab" :class="{ active: tab === 'products' }" @click="tab = 'products'">
          <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          Par produit
        </button>
      </div>

      <!-- ── TAB 1 : Top opportunities ─────────────────────────── -->
      <div v-if="tab === 'top'" class="section">
        <div class="section-title">
          Top {{ data.top_matches.length }} opportunités — clients éligibles ou à examiner
        </div>

        <div v-if="data.top_matches.length === 0" class="empty-tab">
          Aucune opportunité éligible trouvée. Scorez plus de clients.
        </div>

        <div v-else class="opp-list">
          <div
            v-for="(m, i) in pagedTop"
            :key="m.client_id + m.product_id"
            class="opp-card"
            :class="m.eligibility"
          >
            <div class="opp-rank">{{ i + 1 }}</div>

            <div class="opp-main">
              <div class="opp-client">
                <div class="opp-avatar">{{ initials(m.client_name) }}</div>
                <div>
                  <div class="opp-name">{{ m.client_name }}</div>
                  <div class="opp-sector">{{ m.sector }}</div>
                </div>
              </div>
              <div class="opp-arrow">→</div>
              <div class="opp-product">
                <div class="opp-product-id">{{ m.product_id }}</div>
                <div class="opp-product-name">{{ m.product_name }}</div>
              </div>
            </div>

            <div class="opp-right">
              <div class="opp-score-bar">
                <div class="opp-bar-fill" :style="{ width: Math.round(m.normalized_score * 100) + '%', background: scoreColor(m) }"></div>
              </div>
              <div class="opp-score-pct" :style="{ color: scoreColor(m) }">
                {{ Math.round(m.normalized_score * 100) }}%
              </div>
              <span class="elig-badge" :class="m.eligibility">
                {{ m.eligibility === 'eligible' ? '✓ Éligible' : '~ À revoir' }}
              </span>
            </div>
          </div>
        </div>
        <Pagination v-model:page="topPage" v-model:perPage="topPerPage"
          :total="data.top_matches.length" :per-page-options="[10, 20, 50]" />
      </div>

      <!-- ── TAB 2 : By client ──────────────────────────────────── -->
      <div v-if="tab === 'clients'" class="section">
        <div class="section-title">
          {{ data.clients.length }} client(s) scoré(s) — classés par nombre de produits éligibles
        </div>
        <div class="client-list">
          <div v-for="c in pagedClients" :key="c.client_id" class="client-card">
            <div class="cl-header">
              <div class="opp-avatar large">{{ initials(c.client_name) }}</div>
              <div class="cl-info">
                <div class="cl-name">{{ c.client_name }}</div>
                <div class="cl-sector">{{ c.sector }}</div>
                <div class="cl-id">{{ c.client_id }}</div>
              </div>
              <div class="cl-summary">
                <span class="cl-pill eligible">{{ c.eligible.length }} éligibles</span>
                <span class="cl-pill review">{{ c.to_review.length }} à revoir</span>
                <span class="cl-pill total">{{ c.total }} scorés</span>
              </div>
            </div>

            <!-- Eligible products -->
            <div v-if="c.eligible.length" class="cl-products">
              <div class="cl-products-label">Produits éligibles</div>
              <div class="cl-chips">
                <span v-for="p in c.eligible" :key="p.product_id" class="cl-chip eligible">
                  {{ p.product_id }} <em>{{ p.score }}%</em>
                </span>
              </div>
            </div>

            <!-- To review -->
            <div v-if="c.to_review.length" class="cl-products">
              <div class="cl-products-label review">À examiner</div>
              <div class="cl-chips">
                <span v-for="p in c.to_review" :key="p.product_id" class="cl-chip review">
                  {{ p.product_id }} <em>{{ p.score }}%</em>
                </span>
              </div>
            </div>
          </div>
        </div>
        <Pagination v-model:page="clientPage" v-model:perPage="clientPerPage"
          :total="data.clients.length" :per-page-options="[10, 20, 50]" />
      </div>

      <!-- ── TAB 3 : By product ─────────────────────────────────── -->
      <div v-if="tab === 'products'" class="section">
        <div class="section-title">
          {{ data.by_product.length }} produit(s) évalués — classés par nombre de clients éligibles
        </div>
        <div class="product-list">
          <div v-for="p in pagedProducts" :key="p.product_id" class="product-card">
            <div class="pc-left">
              <div class="pc-id">{{ p.product_id }}</div>
              <div class="pc-name">{{ p.product_name }}</div>
            </div>
            <div class="pc-stats">
              <div class="pc-stat eligible">
                <div class="pc-val">{{ p.eligible }}</div>
                <div class="pc-lbl">Éligibles</div>
              </div>
              <div class="pc-stat review">
                <div class="pc-val">{{ p.to_review }}</div>
                <div class="pc-lbl">À revoir</div>
              </div>
              <div class="pc-stat not">
                <div class="pc-val">{{ p.not_eligible }}</div>
                <div class="pc-lbl">Non élig.</div>
              </div>
              <div class="pc-stat total">
                <div class="pc-val">{{ p.total }}</div>
                <div class="pc-lbl">Total</div>
              </div>
            </div>
            <div class="pc-bar-wrap">
              <div class="pc-bar">
                <div class="pc-seg eligible" :style="{ width: pct(p.eligible, p.total) + '%' }"></div>
                <div class="pc-seg review"   :style="{ width: pct(p.to_review, p.total) + '%' }"></div>
              </div>
              <span class="pc-pct">{{ Math.round(pct(p.eligible, p.total)) }}%</span>
            </div>
          </div>
        </div>
        <Pagination v-model:page="productPage" v-model:perPage="productPerPage"
          :total="data.by_product.length" :per-page-options="[10, 20, 50]" />
      </div>

    </template>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { RouterLink } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import Pagination from '../components/Pagination.vue'
import api from '../services/api'

const data    = ref(null)
const loading = ref(false)
const tab     = ref('top')

// Pagination state per tab
const topPage     = ref(1); const topPerPage     = ref(10)
const clientPage  = ref(1); const clientPerPage  = ref(10)
const productPage = ref(1); const productPerPage = ref(10)

watch(tab, () => {
  topPage.value = 1; clientPage.value = 1; productPage.value = 1
})

const pagedTop = computed(() => {
  if (!data.value) return []
  const start = (topPage.value - 1) * topPerPage.value
  return data.value.top_matches.slice(start, start + topPerPage.value)
})
const pagedClients = computed(() => {
  if (!data.value) return []
  const start = (clientPage.value - 1) * clientPerPage.value
  return data.value.clients.slice(start, start + clientPerPage.value)
})
const pagedProducts = computed(() => {
  if (!data.value) return []
  const start = (productPage.value - 1) * productPerPage.value
  return data.value.by_product.slice(start, start + productPerPage.value)
})

async function load() {
  loading.value = true
  try {
    const res = await api.getRecommendations()
    data.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function initials(name) {
  return (name || '').split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase() || '?'
}

function scoreColor(m) {
  const s = m.normalized_score
  return s >= 0.75 ? '#22c55e' : s >= 0.4 ? '#f59e0b' : '#E8622C'
}

function pct(count, total) {
  return total ? Math.min(100, Math.round((count / total) * 100)) : 0
}

onMounted(load)
</script>

<style scoped>
/* ── Loading / Empty ── */
.loading-center { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 80px 0; color: rgba(255,255,255,0.4); font-size: 14px; }
.loading-spinner { width: 20px; height: 20px; border: 2px solid rgba(255,255,255,0.1); border-top-color: #E8622C; border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.empty-state { display: flex; flex-direction: column; align-items: center; gap: 14px; padding: 80px 20px; text-align: center; }
.empty-icon { width: 90px; height: 90px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 24px; display: flex; align-items: center; justify-content: center; }
.empty-title { font-size: 18px; font-weight: 700; color: rgba(255,255,255,0.5); }
.empty-sub { font-size: 13px; color: rgba(255,255,255,0.3); max-width: 380px; line-height: 1.6; }
.empty-cta { display: flex; align-items: center; gap: 8px; padding: 10px 22px; background: linear-gradient(135deg, #E8622C, #ff7a45); border-radius: 10px; color: #fff; font-size: 13px; font-weight: 700; text-decoration: none; }
.empty-tab { text-align: center; padding: 40px; color: rgba(255,255,255,0.3); font-size: 14px; }

/* ── KPI Banner ── */
.kpi-banner { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }
.kpi-card { display: flex; align-items: center; gap: 14px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 18px 20px; }
.kpi-icon { width: 40px; height: 40px; border-radius: 11px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.kpi-icon.blue   { background: rgba(99,179,237,0.12); color: #63b3ed; }
.kpi-icon.green  { background: rgba(34,197,94,0.12);  color: #22c55e; }
.kpi-icon.amber  { background: rgba(245,158,11,0.12); color: #f59e0b; }
.kpi-icon.orange { background: rgba(232,98,44,0.12);  color: #E8622C; }
.kpi-val { font-size: 26px; font-weight: 800; color: #fff; line-height: 1.2; }
.kpi-val.green { color: #22c55e; }
.kpi-val.amber { color: #f59e0b; }
.kpi-lbl { font-size: 11px; color: rgba(255,255,255,0.35); margin-top: 2px; }

/* ── Tabs ── */
.tabs { display: flex; gap: 6px; margin-bottom: 20px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.07); border-radius: 12px; padding: 6px; }
.tab { flex: 1; display: flex; align-items: center; justify-content: center; gap: 7px; padding: 9px 16px; border-radius: 8px; border: none; background: none; color: rgba(255,255,255,0.4); font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.18s; }
.tab:hover { color: rgba(255,255,255,0.7); }
.tab.active { background: rgba(232,98,44,0.12); color: #fff; border: 1px solid rgba(232,98,44,0.25); }

/* ── Section ── */
.section { }
.section-title { font-size: 13px; color: rgba(255,255,255,0.35); margin-bottom: 16px; }

/* ── Opportunities list ── */
.opp-list { display: flex; flex-direction: column; gap: 10px; }
.opp-card { display: flex; align-items: center; gap: 16px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-radius: 14px; padding: 16px 18px; border-left: 3px solid transparent; transition: all 0.18s; }
.opp-card:hover { background: rgba(255,255,255,0.05); }
.opp-card.eligible { border-left-color: #22c55e; }
.opp-card.to_review { border-left-color: #f59e0b; }
.opp-rank { width: 28px; height: 28px; border-radius: 8px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 800; color: rgba(255,255,255,0.5); flex-shrink: 0; }
.opp-card.eligible .opp-rank { background: rgba(34,197,94,0.1); border-color: rgba(34,197,94,0.2); color: #22c55e; }
.opp-card.to_review .opp-rank { background: rgba(245,158,11,0.1); border-color: rgba(245,158,11,0.2); color: #f59e0b; }
.opp-main { flex: 1; display: flex; align-items: center; gap: 14px; min-width: 0; }
.opp-client { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; }
.opp-avatar { width: 36px; height: 36px; border-radius: 9px; flex-shrink: 0; background: linear-gradient(135deg, #1B2A4A, #2d4270); border: 1px solid rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 800; color: #fff; }
.opp-avatar.large { width: 44px; height: 44px; font-size: 14px; }
.opp-name { font-size: 13px; font-weight: 700; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.opp-sector { font-size: 11px; color: rgba(255,255,255,0.3); margin-top: 2px; }
.opp-arrow { color: rgba(255,255,255,0.2); font-size: 16px; flex-shrink: 0; }
.opp-product { flex-shrink: 0; }
.opp-product-id { font-size: 11px; font-weight: 800; color: #E8622C; font-family: monospace; }
.opp-product-name { font-size: 11px; color: rgba(255,255,255,0.4); max-width: 160px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.opp-right { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
.opp-score-bar { width: 80px; height: 5px; background: rgba(255,255,255,0.06); border-radius: 99px; overflow: hidden; }
.opp-bar-fill { height: 100%; border-radius: 99px; }
.opp-score-pct { font-size: 14px; font-weight: 800; width: 40px; text-align: right; }
.elig-badge { font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 99px; white-space: nowrap; }
.elig-badge.eligible  { background: rgba(34,197,94,0.12);  color: #22c55e; border: 1px solid rgba(34,197,94,0.2); }
.elig-badge.to_review { background: rgba(245,158,11,0.12); color: #f59e0b; border: 1px solid rgba(245,158,11,0.2); }

/* ── Client cards ── */
.client-list { display: flex; flex-direction: column; gap: 12px; }
.client-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-radius: 14px; padding: 18px 20px; display: flex; flex-direction: column; gap: 12px; }
.cl-header { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.cl-info { flex: 1; min-width: 0; }
.cl-name { font-size: 15px; font-weight: 700; color: #fff; }
.cl-sector { font-size: 12px; color: rgba(255,255,255,0.35); margin-top: 2px; }
.cl-id { font-size: 10px; color: rgba(255,255,255,0.2); font-family: monospace; }
.cl-summary { display: flex; gap: 8px; flex-wrap: wrap; }
.cl-pill { font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 99px; border: 1px solid; }
.cl-pill.eligible { background: rgba(34,197,94,0.1); color: #22c55e; border-color: rgba(34,197,94,0.2); }
.cl-pill.review   { background: rgba(245,158,11,0.1); color: #f59e0b; border-color: rgba(245,158,11,0.2); }
.cl-pill.total    { background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.4); border-color: rgba(255,255,255,0.1); }
.cl-products { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.cl-products-label { font-size: 11px; font-weight: 700; color: rgba(255,255,255,0.3); text-transform: uppercase; letter-spacing: 0.4px; white-space: nowrap; }
.cl-products-label.review { color: #f59e0b; }
.cl-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.cl-chip { font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 8px; font-family: monospace; }
.cl-chip.eligible { background: rgba(34,197,94,0.1); color: #22c55e; border: 1px solid rgba(34,197,94,0.2); }
.cl-chip.review   { background: rgba(245,158,11,0.1); color: #f59e0b; border: 1px solid rgba(245,158,11,0.2); }
.cl-chip em { font-style: normal; opacity: 0.7; margin-left: 4px; }

/* ── Product cards ── */
.product-list { display: flex; flex-direction: column; gap: 10px; }
.product-card { display: flex; align-items: center; gap: 20px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-radius: 12px; padding: 14px 18px; flex-wrap: wrap; }
.pc-left { min-width: 120px; flex-shrink: 0; }
.pc-id { font-size: 13px; font-weight: 800; color: #E8622C; font-family: monospace; }
.pc-name { font-size: 12px; color: rgba(255,255,255,0.4); margin-top: 2px; }
.pc-stats { display: flex; gap: 16px; }
.pc-stat { text-align: center; }
.pc-val { font-size: 20px; font-weight: 800; color: #fff; line-height: 1.2; }
.pc-lbl { font-size: 9px; color: rgba(255,255,255,0.3); text-transform: uppercase; letter-spacing: 0.3px; }
.pc-stat.eligible .pc-val { color: #22c55e; }
.pc-stat.review   .pc-val { color: #f59e0b; }
.pc-stat.not      .pc-val { color: rgba(255,255,255,0.3); }
.pc-bar-wrap { flex: 1; display: flex; align-items: center; gap: 10px; min-width: 120px; }
.pc-bar { flex: 1; height: 6px; background: rgba(255,255,255,0.06); border-radius: 99px; overflow: hidden; display: flex; }
.pc-seg { height: 100%; }
.pc-seg.eligible { background: #22c55e; }
.pc-seg.review   { background: #f59e0b; }
.pc-pct { font-size: 12px; font-weight: 700; color: #22c55e; white-space: nowrap; }
</style>
