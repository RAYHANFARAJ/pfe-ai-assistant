<template>
  <AppLayout title="My Reports" subtitle="Manage and access all your generated scoring reports">

    <!-- Toolbar -->
    <div class="toolbar">
      <div class="search-wrap">
        <svg class="search-icon-svg" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35" stroke-linecap="round"/></svg>
        <input v-model="search" placeholder="Search reports…" class="search-input" />
      </div>
      <div class="filter-tabs">
        <button v-for="f in filters" :key="f.key" class="filter-tab" :class="{ active: activeFilter === f.key }" @click="activeFilter = f.key">
          {{ f.label }}
          <span class="filter-count">{{ filterCount(f.key) }}</span>
        </button>
      </div>
      <button class="export-btn" @click="exportCSV">
        <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" stroke-linecap="round"/><polyline points="7 10 12 15 17 10" stroke-linecap="round" stroke-linejoin="round"/><line x1="12" y1="15" x2="12" y2="3" stroke-linecap="round"/></svg>
        Export All
      </button>
    </div>

    <!-- Table -->
    <div class="table-section">
      <div class="table-meta">
        <span class="table-title">Reports Overview</span>
        <span class="table-count">{{ filtered.length }} report{{ filtered.length !== 1 ? 's' : '' }} found</span>
      </div>

      <!-- Empty -->
      <div v-if="filtered.length === 0" class="empty">
        <div class="empty-icon">
          <svg width="40" height="40" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1.5" viewBox="0 0 24 24"><path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>
        </div>
        <p class="empty-text">No reports yet.</p>
        <RouterLink to="/search" class="empty-btn">Run a Scoring</RouterLink>
      </div>

      <table v-else class="table">
        <thead>
          <tr>
            <th>COMPANY</th>
            <th>PRODUCT</th>
            <th>STATUS</th>
            <th>GENERATED DATE</th>
            <th>SCORE</th>
            <th>ACTION</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in filtered" :key="r.id" class="table-row">

            <td class="td-company">
              <div class="company-avatar">{{ avatarText(r) }}</div>
              <div>
                <div class="company-name">{{ r.client_name }}</div>
                <div class="company-id">{{ r.client_id }}</div>
              </div>
            </td>

            <td class="td-product">{{ r.product || r.product_id }}</td>

            <td>
              <span class="status-badge" :class="statusClass(r)">
                <span class="status-dot"></span>
                {{ statusLabel(r) }}
              </span>
            </td>

            <td class="td-date">{{ r.date }}</td>

            <td class="td-score">
              <div v-if="r.report_status === 'completed' && r.normalized != null" class="score-row">
                <span class="score-pct" :class="scoreClass(r)">{{ Math.round((r.normalized || 0) * 100) }}%</span>
                <div class="score-bar-bg">
                  <div class="score-bar-fill" :style="{ width: Math.round((r.normalized||0)*100)+'%', background: scoreColor(r) }"></div>
                </div>
              </div>
              <div v-else-if="r.report_status === 'generating'" class="generating-indicator">
                <span class="mini-spin"></span>
                <span class="gen-text">Generating…</span>
              </div>
              <span v-else class="no-data">—</span>
            </td>

            <td>
              <button
                v-if="r.report_status === 'completed'"
                class="action-btn"
                @click="viewReport(r)"
              >Open Report</button>
              <button
                v-else-if="r.report_status === 'generating'"
                class="action-btn-disabled"
                disabled
              >In Progress</button>
              <span v-else class="no-data">—</span>
            </td>

          </tr>
        </tbody>
      </table>
    </div>

  </AppLayout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import { useScoringStore } from '../stores/scoring'

const router = useRouter()
const { state } = useScoringStore()
const search = ref('')
const activeFilter = ref('all')

const filters = [
  { key: 'all', label: 'All' },
  { key: 'generating', label: 'Generating' },
  { key: 'completed', label: 'Completed' },
  { key: 'failed', label: 'Failed' },
]

const filtered = computed(() => {
  let h = state.history
  if (activeFilter.value !== 'all') h = h.filter(r => r.report_status === activeFilter.value)
  if (search.value) {
    const q = search.value.toLowerCase()
    h = h.filter(r => (r.client_name + r.product + r.client_id).toLowerCase().includes(q))
  }
  return h
})

function filterCount(key) {
  if (key === 'all') return state.history.length
  return state.history.filter(r => r.report_status === key).length
}

function avatarText(r) {
  const n = r.client_name || ''
  return n.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase() || '?'
}

function statusClass(r) {
  if (r.report_status === 'generating') return 'st-generating'
  if (r.report_status === 'completed') return 'st-completed'
  return 'st-failed'
}

function statusLabel(r) {
  if (r.report_status === 'generating') return 'Generating'
  if (r.report_status === 'completed') return 'Completed'
  return 'Failed'
}

function scoreClass(r) {
  const p = r.normalized || 0
  return p >= 0.75 ? 'green' : p >= 0.4 ? 'amber' : 'orange'
}

function scoreColor(r) {
  const p = r.normalized || 0
  return p >= 0.75 ? '#22c55e' : p >= 0.4 ? '#f59e0b' : '#E8622C'
}

function viewReport(r) { router.push('/recommendations') }

function exportCSV() {
  const rows = [['Company', 'Product', 'Status', 'Date', 'Score %']]
  state.history.forEach(r => rows.push([
    r.client_name, r.product || r.product_id,
    statusLabel(r), r.date,
    r.normalized != null ? Math.round((r.normalized||0)*100)+'%' : '—'
  ]))
  const csv = rows.map(r => r.join(',')).join('\n')
  const a = document.createElement('a')
  a.href = 'data:text/csv,' + encodeURIComponent(csv)
  a.download = 'reports.csv'
  a.click()
}
</script>

<style scoped>
.toolbar { display: flex; align-items: center; gap: 14px; margin-bottom: 24px; flex-wrap: wrap; }

.search-wrap { position: relative; flex: 1; min-width: 200px; }
.search-icon-svg { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: rgba(255,255,255,0.3); pointer-events: none; }
.search-input { width: 100%; padding: 10px 14px 10px 36px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 9px; color: #fff; font-size: 13.5px; outline: none; }
.search-input:focus { border-color: rgba(232,98,44,0.4); }
.search-input::placeholder { color: rgba(255,255,255,0.2); }

.filter-tabs { display: flex; gap: 6px; flex-wrap: wrap; }
.filter-tab { display: flex; align-items: center; gap: 6px; padding: 8px 14px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; color: rgba(255,255,255,0.5); font-size: 13px; cursor: pointer; transition: all 0.18s; }
.filter-tab:hover { color: #fff; }
.filter-tab.active { background: #E8622C; border-color: #E8622C; color: #fff; font-weight: 700; }
.filter-count { background: rgba(255,255,255,0.15); padding: 1px 7px; border-radius: 99px; font-size: 11px; }
.filter-tab.active .filter-count { background: rgba(255,255,255,0.25); }

.export-btn { display: flex; align-items: center; gap: 7px; padding: 9px 18px; background: rgba(232,98,44,0.1); border: 1px solid rgba(232,98,44,0.3); border-radius: 8px; color: #E8622C; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.18s; white-space: nowrap; }
.export-btn:hover { background: rgba(232,98,44,0.2); }

.table-section { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.07); border-radius: 14px; overflow: hidden; }
.table-meta { display: flex; align-items: center; justify-content: space-between; padding: 18px 24px; border-bottom: 1px solid rgba(255,255,255,0.06); }
.table-title { font-size: 15px; font-weight: 700; color: #fff; }
.table-count { font-size: 12.5px; color: rgba(255,255,255,0.3); }

.empty { display: flex; flex-direction: column; align-items: center; padding: 60px; gap: 12px; }
.empty-text { color: rgba(255,255,255,0.35); font-size: 14px; }
.empty-btn { padding: 9px 20px; background: linear-gradient(135deg, #E8622C, #ff7a45); color: #fff; font-size: 13px; font-weight: 700; border-radius: 8px; text-decoration: none; transition: all 0.2s; }
.empty-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(232,98,44,0.35); }

.table { width: 100%; border-collapse: collapse; }
.table thead tr { background: rgba(255,255,255,0.03); }
.table th { padding: 12px 20px; text-align: left; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; color: rgba(255,255,255,0.3); white-space: nowrap; }
.table-row { border-top: 1px solid rgba(255,255,255,0.04); transition: background 0.15s; }
.table-row:hover { background: rgba(232,98,44,0.03); }
.table td { padding: 14px 20px; vertical-align: middle; }

.td-company { display: flex; align-items: center; gap: 12px; }
.company-avatar { width: 36px; height: 36px; border-radius: 9px; background: linear-gradient(135deg, #0d2540, #1a3a5c); border: 1px solid rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; color: rgba(255,255,255,0.7); flex-shrink: 0; }
.company-name { font-size: 13.5px; font-weight: 600; color: #fff; }
.company-id { font-size: 11px; color: rgba(255,255,255,0.25); font-family: monospace; margin-top: 1px; }
.td-product { font-size: 13px; color: rgba(255,255,255,0.55); }
.td-date { font-size: 13px; color: rgba(255,255,255,0.4); white-space: nowrap; }

.status-badge { display: inline-flex; align-items: center; gap: 7px; padding: 5px 12px; border-radius: 99px; font-size: 12px; font-weight: 600; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; flex-shrink: 0; }
.st-completed { background: rgba(34,197,94,0.12); color: #4ade80; border: 1px solid rgba(34,197,94,0.2); }
.st-generating { background: rgba(59,130,246,0.12); color: #60a5fa; border: 1px solid rgba(59,130,246,0.2); }
.st-failed { background: rgba(239,68,68,0.12); color: #f87171; border: 1px solid rgba(239,68,68,0.2); }

.td-score .score-row { display: flex; align-items: center; gap: 8px; }
.score-pct { font-size: 13.5px; font-weight: 800; min-width: 36px; }
.score-bar-bg { width: 80px; height: 5px; background: rgba(255,255,255,0.08); border-radius: 99px; overflow: hidden; }
.score-bar-fill { height: 100%; border-radius: 99px; }
.green { color: #4ade80; }
.amber { color: #fbbf24; }
.orange { color: #E8622C; }
.no-data { color: rgba(255,255,255,0.2); }

.generating-indicator { display: flex; align-items: center; gap: 8px; color: #60a5fa; font-size: 12.5px; }
.gen-text { font-size: 12px; }

.action-btn { padding: 7px 16px; background: linear-gradient(135deg, #E8622C, #ff7a45); color: #fff; font-size: 12.5px; font-weight: 700; border: none; border-radius: 7px; cursor: pointer; transition: all 0.18s; white-space: nowrap; }
.action-btn:hover { transform: scale(1.03); box-shadow: 0 4px 16px rgba(232,98,44,0.35); }
.action-btn-disabled { padding: 7px 16px; background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.3); font-size: 12.5px; font-weight: 600; border: 1px solid rgba(255,255,255,0.08); border-radius: 7px; cursor: not-allowed; white-space: nowrap; }

.mini-spin { width: 12px; height: 12px; border: 2px solid rgba(96,165,250,0.3); border-top-color: #60a5fa; border-radius: 50%; animation: spin 0.7s linear infinite; display: inline-block; flex-shrink: 0; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
