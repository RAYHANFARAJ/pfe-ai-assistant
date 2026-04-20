<template>
  <AppLayout title="Recommendations" subtitle="AI-powered qualification analysis for your client">

    <!-- No result yet -->
    <div v-if="!result" class="no-result">
      <div class="no-icon">
        <svg width="48" height="48" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1.5" viewBox="0 0 24 24">
          <path d="M9 17H7a4 4 0 010-8h2" stroke-linecap="round"/><path d="M15 17h2a4 4 0 000-8h-2" stroke-linecap="round"/><line x1="9" y1="12" x2="15" y2="12" stroke-linecap="round"/>
        </svg>
      </div>
      <p class="no-text">No analysis yet.</p>
      <RouterLink to="/search" class="no-btn">Search a Client</RouterLink>
    </div>

    <template v-else>

      <!-- Company card -->
      <div class="company-card">
        <div class="card-left">
          <div class="company-logo">{{ initials }}</div>
          <div class="company-info">
            <h2 class="company-name">{{ result.client?.client_name }}</h2>
            <div class="company-meta">
              <span v-if="result.client?.sector" class="meta-item">
                <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>
                {{ result.client.sector }}
              </span>
              <span v-if="result.client?.city || result.client?.country" class="meta-item">
                <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>
                {{ [result.client.city, result.client.country].filter(Boolean).join(', ') }}
              </span>
              <span v-if="result.client?.website" class="meta-link">
                <a :href="result.client.website" target="_blank">
                  <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 010 20M12 2a15.3 15.3 0 000 20"/></svg>
                  Website
                </a>
              </span>
            </div>
            <div class="eligibility-badge" :class="eligClass">{{ eligLabel }}</div>
          </div>
        </div>
        <div class="card-score">
          <div class="score-label">GLOBAL SCORE</div>
          <div class="score-big" :class="scoreClass">{{ pct }}<span class="score-pct-sm">%</span></div>
          <div class="score-bar-track">
            <div class="score-bar-fill" :style="{ width: pct + '%', background: scoreBarColor }"></div>
          </div>
        </div>
      </div>

      <!-- Products table -->
      <div class="table-section">
        <div class="table-header">
          <div>
            <div class="table-title">Product Scoring Results</div>
            <div class="table-sub">{{ result.criteria_results?.length }} criteria evaluated</div>
          </div>
          <button class="detail-toggle-btn" @click="showCriteriaModal = true">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/></svg>
            View Criteria Details
          </button>
        </div>

        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>PRODUCT</th>
                <th>SCORE</th>
                <th>REPORT STATUS</th>
                <th>ACTION</th>
              </tr>
            </thead>
            <tbody>
              <tr class="table-row">
                <td class="td-product">
                  <div class="product-icon">
                    <svg width="16" height="16" fill="none" stroke="#E8622C" stroke-width="1.8" viewBox="0 0 24 24"><path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>
                  </div>
                  <div>
                    <div class="product-name">{{ result.product?.product_name || result.product?.product_id }}</div>
                    <div class="product-id">{{ result.product?.product_id }}</div>
                  </div>
                </td>
                <td class="td-score">
                  <div class="score-row">
                    <span class="score-pct-text" :class="scoreClass">{{ pct }}%</span>
                    <div class="progress-track">
                      <div class="progress-fill" :style="{ width: pct + '%', background: scoreBarColor }"></div>
                    </div>
                    <span class="score-pts">{{ result.summary?.total_score }}/{{ result.summary?.max_score }}</span>
                  </div>
                </td>
                <td>
                  <span class="status-badge st-completed">
                    <span class="status-dot"></span>
                    Completed
                  </span>
                </td>
                <td>
                  <button class="action-btn" @click="showCriteriaModal = true">View Report</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </template>

    <!-- Criteria detail modal -->
    <div v-if="showCriteriaModal" class="modal-backdrop" @click.self="showCriteriaModal = false">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">Criteria Details — {{ result?.product?.product_name || result?.product?.product_id }}</div>
          <button class="modal-close" @click="showCriteriaModal = false">✕</button>
        </div>
        <div class="modal-body">
          <div v-for="c in result?.criteria_results" :key="c.criterion_id" class="criterion-card" @click="openCriterion(c)">
            <div class="cc-left">
              <div class="cc-name">{{ c.label }}</div>
              <div class="cc-type">{{ c.answer_type }}</div>
            </div>
            <div class="cc-mid">
              <div class="cc-score-row">
                <span class="cc-pct" :class="scoreRowClass(c)">{{ c.max_score ? Math.round((c.score / c.max_score) * 100) + '%' : '—' }}</span>
                <div class="cc-bar-bg">
                  <div class="cc-bar-fill" :style="{ width: barWidth(c), background: barColor(c) }"></div>
                </div>
              </div>
              <div class="cc-pts">{{ c.score }} / {{ c.max_score }} pts</div>
            </div>
            <div class="cc-right">
              <div class="conf-badge" :class="confClass(c)">{{ Math.round((c.confidence || 0) * 100) }}%</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Criterion detail modal (inside criteria modal) -->
    <div v-if="selected" class="modal-backdrop" @click.self="selected = null" style="z-index: 210;">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">{{ selected.label }}</div>
          <button class="modal-close" @click="selected = null">✕</button>
        </div>
        <div class="modal-body modal-detail">
          <div class="modal-row"><span class="ml">Answer</span><span class="mv">{{ selected.predicted_answer }}</span></div>
          <div class="modal-row"><span class="ml">Extracted value</span><span class="mv code">{{ selected.extracted_value ?? '—' }}</span></div>
          <div class="modal-row"><span class="ml">Confidence</span><span class="mv">{{ Math.round((selected.confidence||0)*100) }}%</span></div>
          <div class="modal-row"><span class="ml">Score</span><span class="mv">{{ selected.score }} / {{ selected.max_score }}</span></div>
          <div class="modal-section">
            <div class="ml mb4">Justification</div>
            <p class="modal-just">{{ selected.justification }}</p>
          </div>
          <div v-if="selected.evidence?.source_url" class="modal-section">
            <div class="ml mb4">Evidence source</div>
            <a :href="selected.evidence.source_url" target="_blank" class="ev-link-big">{{ selected.evidence.source_label }} ↗</a>
            <blockquote v-if="selected.evidence.snippet" class="modal-snippet">{{ selected.evidence.snippet }}</blockquote>
          </div>
          <div v-if="selected.choices?.length" class="modal-section">
            <div class="ml mb4">Choices</div>
            <div v-for="ch in selected.choices" :key="ch.label" class="choice-row" :class="{ matched: isMatched(ch, selected) }">
              <span>{{ ch.label }}</span>
              <span class="choice-pts">{{ ch.is_blocking ? '🚫' : ch.score + ' pts' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

  </AppLayout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { RouterLink } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import { useScoringStore } from '../stores/scoring'

const { state } = useScoringStore()
const result = computed(() => state.result)
const selected = ref(null)
const showCriteriaModal = ref(false)

const pct = computed(() => Math.round((result.value?.summary?.normalized_score || 0) * 100))
const initials = computed(() => {
  const n = result.value?.client?.client_name || ''
  return n.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase() || '?'
})

const scoreBarColor = computed(() => {
  const p = (result.value?.summary?.normalized_score || 0)
  return p >= 0.75 ? '#22c55e' : p >= 0.4 ? '#f59e0b' : '#E8622C'
})

const scoreClass = computed(() => {
  const s = result.value?.summary?.eligibility_status
  return s === 'eligible' ? 'green' : s === 'to_review' ? 'amber' : 'orange'
})

const eligClass = computed(() => {
  const s = result.value?.summary?.eligibility_status
  return s === 'eligible' ? 'elig-green' : s === 'to_review' ? 'elig-amber' : 'elig-red'
})

const eligLabel = computed(() => {
  const s = result.value?.summary?.eligibility_status
  return s === 'eligible' ? '✓ Eligible' : s === 'to_review' ? '~ To Review' : '✗ Not Eligible'
})

function barWidth(c) {
  if (!c.max_score) return '0%'
  return Math.round((c.score / c.max_score) * 100) + '%'
}
function barColor(c) {
  const p = c.max_score ? c.score / c.max_score : 0
  return p >= 0.75 ? '#22c55e' : p >= 0.4 ? '#f59e0b' : '#E8622C'
}
function scoreRowClass(c) {
  const p = c.max_score ? c.score / c.max_score : 0
  return p >= 0.75 ? 'green' : p >= 0.4 ? 'amber' : 'orange'
}
function confClass(c) {
  const v = c.confidence || 0
  return v >= 0.8 ? 'conf-high' : v >= 0.5 ? 'conf-mid' : 'conf-low'
}
function openCriterion(c) { selected.value = c }
function isMatched(ch, c) {
  return String(ch.label).toLowerCase() === String(c.predicted_answer).toLowerCase()
}
</script>

<style scoped>
/* Empty state */
.no-result { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 50vh; gap: 16px; text-align: center; }
.no-text { color: rgba(255,255,255,0.35); font-size: 15px; }
.no-btn { padding: 10px 22px; background: linear-gradient(135deg, #E8622C, #ff7a45); color: #fff; font-size: 13.5px; font-weight: 700; border-radius: 10px; text-decoration: none; transition: all 0.2s; }
.no-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(232,98,44,0.35); }

/* Company card */
.company-card {
  display: flex; align-items: center; justify-content: space-between;
  padding: 24px 28px; margin-bottom: 24px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  gap: 24px;
}
.card-left { display: flex; align-items: flex-start; gap: 18px; flex: 1; min-width: 0; }
.company-logo {
  width: 54px; height: 54px; border-radius: 14px; flex-shrink: 0;
  background: linear-gradient(135deg, #1a3a5c, #0d2540);
  border: 1px solid rgba(255,255,255,0.1);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; font-weight: 800; color: rgba(255,255,255,0.85);
}
.company-info { min-width: 0; }
.company-name { font-size: 20px; font-weight: 700; color: #fff; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.company-meta { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 10px; }
.meta-item { display: flex; align-items: center; gap: 5px; font-size: 12.5px; color: rgba(255,255,255,0.4); }
.meta-link a { display: flex; align-items: center; gap: 5px; font-size: 12.5px; color: #E8622C; text-decoration: none; }
.meta-link a:hover { text-decoration: underline; }

.eligibility-badge { display: inline-flex; align-items: center; padding: 4px 12px; border-radius: 99px; font-size: 12px; font-weight: 700; }
.elig-green { background: rgba(34,197,94,0.12); color: #4ade80; border: 1px solid rgba(34,197,94,0.2); }
.elig-amber { background: rgba(245,158,11,0.12); color: #fbbf24; border: 1px solid rgba(245,158,11,0.2); }
.elig-red { background: rgba(232,98,44,0.12); color: #E8622C; border: 1px solid rgba(232,98,44,0.2); }

/* Score panel */
.card-score { text-align: right; flex-shrink: 0; min-width: 160px; }
.score-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; color: rgba(255,255,255,0.25); margin-bottom: 4px; }
.score-big { font-size: 52px; font-weight: 900; line-height: 1; }
.score-pct-sm { font-size: 24px; font-weight: 600; }
.score-bar-track { width: 100%; height: 4px; background: rgba(255,255,255,0.08); border-radius: 99px; overflow: hidden; margin-top: 8px; }
.score-bar-fill { height: 100%; border-radius: 99px; transition: width 0.6s ease; }
.green { color: #4ade80; }
.amber { color: #fbbf24; }
.orange { color: #E8622C; }

/* Table */
.table-section { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.07); border-radius: 14px; overflow: hidden; }
.table-header { display: flex; align-items: center; justify-content: space-between; padding: 18px 24px; border-bottom: 1px solid rgba(255,255,255,0.06); }
.table-title { font-size: 15px; font-weight: 700; color: #fff; }
.table-sub { font-size: 12.5px; color: rgba(255,255,255,0.3); margin-top: 2px; }

.detail-toggle-btn {
  display: flex; align-items: center; gap: 7px;
  padding: 8px 16px; border-radius: 8px;
  background: rgba(232,98,44,0.1); border: 1px solid rgba(232,98,44,0.25);
  color: #E8622C; font-size: 13px; font-weight: 600; cursor: pointer;
  transition: all 0.18s;
}
.detail-toggle-btn:hover { background: rgba(232,98,44,0.18); }

.table-wrap { overflow-x: auto; }
.table { width: 100%; border-collapse: collapse; }
.table thead tr { background: rgba(255,255,255,0.03); }
.table th { padding: 12px 20px; text-align: left; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; color: rgba(255,255,255,0.3); white-space: nowrap; }
.table-row { border-top: 1px solid rgba(255,255,255,0.04); transition: background 0.15s; }
.table-row:hover { background: rgba(232,98,44,0.03); }
.table td { padding: 18px 20px; vertical-align: middle; }

.td-product { display: flex; align-items: center; gap: 12px; }
.product-icon { width: 36px; height: 36px; border-radius: 9px; background: rgba(232,98,44,0.1); border: 1px solid rgba(232,98,44,0.2); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.product-name { font-size: 14px; font-weight: 600; color: #fff; }
.product-id { font-size: 11px; color: rgba(255,255,255,0.25); font-family: monospace; margin-top: 2px; }

.td-score .score-row { display: flex; align-items: center; gap: 10px; }
.score-pct-text { font-size: 15px; font-weight: 800; min-width: 40px; }
.progress-track { flex: 1; max-width: 140px; height: 6px; background: rgba(255,255,255,0.08); border-radius: 99px; overflow: hidden; }
.progress-fill { height: 100%; border-radius: 99px; transition: width 0.6s ease; }
.score-pts { font-size: 11.5px; color: rgba(255,255,255,0.3); white-space: nowrap; }

.status-badge { display: inline-flex; align-items: center; gap: 7px; padding: 6px 14px; border-radius: 99px; font-size: 12.5px; font-weight: 600; }
.st-completed { background: rgba(34,197,94,0.12); color: #4ade80; border: 1px solid rgba(34,197,94,0.2); }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

.action-btn { padding: 8px 18px; background: linear-gradient(135deg, #E8622C, #ff7a45); color: #fff; font-size: 13px; font-weight: 700; border: none; border-radius: 8px; cursor: pointer; transition: all 0.18s; white-space: nowrap; }
.action-btn:hover { transform: scale(1.03); box-shadow: 0 4px 16px rgba(232,98,44,0.35); }

/* Criteria list modal */
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.72); backdrop-filter: blur(4px); z-index: 200; display: flex; align-items: center; justify-content: center; padding: 24px; }
.modal { background: #0A1628; border: 1px solid rgba(232,98,44,0.2); border-radius: 16px; width: 100%; max-width: 640px; max-height: 82vh; overflow-y: auto; }
.modal-header { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.07); position: sticky; top: 0; background: #0A1628; z-index: 1; }
.modal-title { font-size: 15px; font-weight: 700; color: #fff; flex: 1; padding-right: 16px; line-height: 1.4; }
.modal-close { background: none; border: none; color: rgba(255,255,255,0.4); font-size: 16px; cursor: pointer; padding: 2px; }
.modal-close:hover { color: #fff; }
.modal-body { padding: 16px 20px; display: flex; flex-direction: column; gap: 8px; }

.criterion-card {
  display: flex; align-items: center; gap: 16px;
  padding: 14px 16px; border-radius: 10px;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  cursor: pointer; transition: all 0.15s;
}
.criterion-card:hover { background: rgba(232,98,44,0.06); border-color: rgba(232,98,44,0.2); }
.cc-left { flex: 1; min-width: 0; }
.cc-name { font-size: 13px; font-weight: 600; color: rgba(255,255,255,0.85); margin-bottom: 3px; }
.cc-type { font-size: 10.5px; color: rgba(232,98,44,0.6); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
.cc-mid { min-width: 160px; }
.cc-score-row { display: flex; align-items: center; gap: 8px; margin-bottom: 3px; }
.cc-pct { font-size: 13px; font-weight: 800; min-width: 34px; }
.cc-bar-bg { flex: 1; height: 4px; background: rgba(255,255,255,0.08); border-radius: 99px; overflow: hidden; }
.cc-bar-fill { height: 100%; border-radius: 99px; }
.cc-pts { font-size: 10.5px; color: rgba(255,255,255,0.25); }
.cc-right { flex-shrink: 0; }

.conf-badge { display: inline-flex; padding: 3px 9px; border-radius: 99px; font-size: 11.5px; font-weight: 700; }
.conf-high { background: rgba(34,197,94,0.12); color: #4ade80; }
.conf-mid { background: rgba(245,158,11,0.12); color: #fbbf24; }
.conf-low { background: rgba(232,98,44,0.12); color: #E8622C; }

/* Detail modal */
.modal-detail { padding: 20px 24px; gap: 14px; }
.modal-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
.ml { font-size: 12px; color: rgba(255,255,255,0.35); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.mv { font-size: 13.5px; color: #fff; font-weight: 600; }
.mv.code { font-family: monospace; color: #E8622C; }
.modal-section { display: flex; flex-direction: column; gap: 8px; }
.mb4 { margin-bottom: 4px; }
.modal-just { font-size: 13px; color: rgba(255,255,255,0.55); line-height: 1.7; }
.ev-link-big { font-size: 13px; color: #E8622C; text-decoration: none; font-weight: 600; }
.ev-link-big:hover { text-decoration: underline; }
.modal-snippet { margin: 0; padding: 10px 14px; background: rgba(232,98,44,0.06); border-left: 2px solid #E8622C; border-radius: 4px; font-size: 12px; color: rgba(255,255,255,0.4); font-style: italic; line-height: 1.6; }
.choice-row { display: flex; justify-content: space-between; padding: 8px 12px; border-radius: 7px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); font-size: 13px; color: rgba(255,255,255,0.55); }
.choice-row.matched { background: rgba(232,98,44,0.1); border-color: rgba(232,98,44,0.3); color: #fff; }
.choice-pts { font-weight: 700; color: #4ade80; }
</style>
