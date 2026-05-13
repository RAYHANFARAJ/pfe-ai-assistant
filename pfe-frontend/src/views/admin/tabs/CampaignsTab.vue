<template>
  <div class="campaigns-page">

    <!-- Actions bar -->
    <div class="page-header">
      <p class="page-sub">{{ campaigns.length }} campaigns in Elasticsearch · {{ totalTargets.toLocaleString() }} targets</p>
      <button class="btn-primary" @click="openForm()">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M7 1v12M1 7h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        New Campaign
      </button>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <div class="search-wrap">
        <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
        </svg>
        <input v-model="search" class="search-input" placeholder="Search by title or ID…" />
      </div>
      <select v-model="filterPole" class="filter-select">
        <option value="">All poles</option>
        <option v-for="p in poles" :key="p" :value="p">{{ p }}</option>
      </select>
      <select v-model="filterStatus" class="filter-select">
        <option value="">All statuses</option>
        <option value="active">Active</option>
        <option value="archive">Archive</option>
        <option value="draft">Draft</option>
      </select>
      <span class="filter-count">{{ filtered.length }} result{{ filtered.length !== 1 ? 's' : '' }}</span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div><span>Loading campaigns…</span>
    </div>

    <!-- Table -->
    <div v-else class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Pole</th>
            <th>Product</th>
            <th>Interlocutor</th>
            <th>Dates</th>
            <th>Targets</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!filtered.length">
            <td colspan="9" class="empty-row">No campaigns match your filters.</td>
          </tr>
          <template v-for="c in filtered" :key="c.id">
            <tr class="data-row" :class="{ expanded: expandedRow === c.id }">
              <td class="cell-id">
                <span class="id-chip" :title="c.id">{{ c.id.slice(0, 8) }}…</span>
              </td>
              <td class="cell-title">{{ c.title || c.name }}</td>
              <td><span v-if="c.pole" class="badge pole">{{ c.pole }}</span></td>
              <td>
                <span
                  v-for="pid in c.product_ids" :key="pid"
                  class="product-chip clickable"
                  :title="'View ' + productName(pid)"
                  @click="goToProduct(pid)"
                >
                  <b>{{ pid }}</b> · {{ productName(pid) }}
                  <svg class="chip-arrow" width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path d="M7 17L17 7M7 7h10v10"/>
                  </svg>
                </span>
                <span v-if="!c.product_ids?.length" class="no-product">—</span>
              </td>
              <td class="cell-interlocutor">{{ c.interlocutor || '—' }}</td>
              <td class="cell-dates">
                <span v-if="c.start_date || c.end_date">
                  {{ c.start_date || '?' }}<br/>
                  <span class="date-end">→ {{ c.end_date || '?' }}</span>
                </span>
                <span v-else class="cell-muted">—</span>
              </td>
              <td>
                <button class="targets-btn" @click="toggleTargets(c)">
                  <span v-if="targetData[c.id]">{{ targetData[c.id].total.toLocaleString() }}</span>
                  <span v-else class="load-targets">View</span>
                  <svg class="targets-icon" width="10" height="10" viewBox="0 0 12 12" fill="none">
                    <path v-if="expandedRow !== c.id" d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                    <path v-else d="M10 8L6 4 2 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
              </td>
              <td><span class="status-badge" :class="c.status">{{ c.status }}</span></td>
              <td class="cell-actions">
                <button class="icon-btn" title="Edit" @click="openForm(c)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                </button>
                <button class="icon-btn danger" title="Delete" @click="confirmDelete(c)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
                    <path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/>
                  </svg>
                </button>
              </td>
            </tr>
            <!-- Targets sub-panel -->
            <tr v-if="expandedRow === c.id" class="targets-row">
              <td colspan="9">
                <div v-if="targetsLoading" class="targets-loading">
                  <div class="spinner-sm"></div> Loading targets…
                </div>
                <div v-else-if="targetData[c.id]" class="targets-panel">
                  <!-- Status breakdown -->
                  <div class="targets-stats">
                    <div
                      v-for="(count, status) in targetData[c.id].status_breakdown"
                      :key="status"
                      class="stat-chip"
                    >
                      <span class="stat-label">{{ status }}</span>
                      <span class="stat-count">{{ count }}</span>
                    </div>
                  </div>
                  <!-- Account list -->
                  <table class="inner-table">
                    <thead>
                      <tr>
                        <th>Account</th>
                        <th>Status</th>
                        <th>Type</th>
                        <th>Market</th>
                        <th>RC</th>
                        <th>Calls</th>
                        <th>Prospecteur</th>
                        <th>Active</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="t in targetData[c.id].targets" :key="t.id">
                        <td class="acc-name">{{ t.campaign_name || t.account_id }}</td>
                        <td><span class="target-status">{{ t.status }}</span></td>
                        <td class="cell-muted">{{ t.type_statut || '—' }}</td>
                        <td>
                          <span v-if="t.market" class="market-badge">{{ t.market }}</span>
                          <span v-else class="cell-muted">—</span>
                        </td>
                        <td class="cell-muted">{{ t.rc2 || t.rc1 || '—' }}</td>
                        <td class="score-cell">{{ t.nb_appels ?? 0 }}</td>
                        <td class="cell-muted">{{ t.prospecteur || '—' }}</td>
                        <td>
                          <span class="dot" :class="t.active ? 'green' : 'red'"></span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <p v-if="targetData[c.id].total > 50" class="targets-more">
                    Showing 50 of {{ targetData[c.id].total.toLocaleString() }} targets
                  </p>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- ── Campaign form modal ── -->
    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editing ? 'Edit Campaign' : 'New Campaign' }}</h2>
          <button class="close-btn" @click="showForm = false">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Title</label>
            <input v-model="form.name" placeholder="Campaign title" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Pole</label>
              <select v-model="form.pole">
                <option value="">—</option>
                <option value="EFFI">EFFI</option>
                <option value="NRJ">NRJ</option>
                <option value="INNO">INNO</option>
                <option value="INTER">INTER</option>
              </select>
            </div>
            <div class="form-group">
              <label>Type</label>
              <select v-model="form.type">
                <option value="national">National</option>
                <option value="international">International</option>
              </select>
            </div>
            <div class="form-group">
              <label>Status</label>
              <select v-model="form.status">
                <option value="draft">Draft</option>
                <option value="active">Active</option>
                <option value="archive">Archive</option>
              </select>
            </div>
          </div>
          <div class="form-row two-col">
            <div class="form-group">
              <label>Start date</label>
              <input v-model="form.start_date" type="date" />
            </div>
            <div class="form-group">
              <label>End date</label>
              <input v-model="form.end_date" type="date" />
            </div>
          </div>
          <div class="form-group">
            <label>Interlocutor</label>
            <input v-model="form.interlocutor" placeholder="e.g. DAF / DRH" />
          </div>
          <!-- Product association -->
          <div class="form-group">
            <label>Associated products</label>
            <div class="product-checkboxes">
              <label v-for="p in allProducts" :key="p.id" class="checkbox-row">
                <input type="checkbox" :value="p.id" v-model="form.product_ids" />
                <span class="product-label">
                  <span class="pid">{{ p.id }}</span> {{ p.name }}
                </span>
              </label>
            </div>
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="form.description" rows="3" placeholder="Optional description"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="showForm = false">Cancel</button>
          <button class="btn-primary" :disabled="saving" @click="save">
            <div v-if="saving" class="spinner-xs"></div>
            {{ saving ? 'Saving…' : 'Save Campaign' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── Delete confirm ── -->
    <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
      <div class="modal modal-sm">
        <div class="modal-header">
          <h2>Delete campaign</h2>
          <button class="close-btn" @click="deleteTarget = null">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="delete-icon-wrap">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#f87171" stroke-width="1.5">
              <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
              <path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/>
            </svg>
          </div>
          <p class="delete-msg">Delete <strong>{{ deleteTarget.title || deleteTarget.name }}</strong>?</p>
          <p class="warn-text">This action cannot be undone.</p>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="deleteTarget = null">Cancel</button>
          <button class="btn-danger" :disabled="saving" @click="executeDelete">
            <div v-if="saving" class="spinner-xs"></div>
            {{ saving ? 'Deleting…' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../../services/api'
const notify = inject('notify', { success: () => {}, error: () => {} })

const router = useRouter()

const campaigns     = ref([])
const allProducts   = ref([])
const loading       = ref(false)
const saving        = ref(false)
const targetsLoading= ref(false)
const showForm      = ref(false)
const editing       = ref(null)
const deleteTarget  = ref(null)
const expandedRow   = ref(null)
const targetData    = ref({})
const search        = ref('')
const filterPole    = ref('')
const filterStatus  = ref('')

const form = ref({
  name: '', description: '', status: 'draft',
  pole: '', type: 'national', interlocutor: '',
  start_date: '', end_date: '', product_ids: [],
})

const poles = computed(() => [...new Set(campaigns.value.map(c => c.pole).filter(Boolean))].sort())

const totalTargets = computed(() =>
  Object.values(targetData.value).reduce((s, d) => s + (d.total || 0), 0)
)

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  return campaigns.value.filter(c => {
    const matchSearch = !q || (c.title || c.name || '').toLowerCase().includes(q) || (c.id || '').toLowerCase().includes(q)
    const matchPole   = !filterPole.value   || c.pole   === filterPole.value
    const matchStatus = !filterStatus.value || c.status === filterStatus.value
    return matchSearch && matchPole && matchStatus
  })
})

async function load() {
  loading.value = true
  try {
    const [camp, prod] = await Promise.all([api.admin.listCampaigns(), api.admin.listProducts()])
    campaigns.value   = camp.data
    allProducts.value = prod.data
  } finally {
    loading.value = false
  }
}

function productName(pid) {
  return allProducts.value.find(p => p.id === pid)?.name || pid
}

async function toggleTargets(campaign) {
  if (expandedRow.value === campaign.id) {
    expandedRow.value = null
    return
  }
  expandedRow.value = campaign.id
  if (!targetData.value[campaign.id]) {
    targetsLoading.value = true
    try {
      const { data } = await api.admin.getCampaignTargets(campaign.id)
      targetData.value[campaign.id] = data
    } finally {
      targetsLoading.value = false
    }
  }
}

function openForm(campaign = null) {
  editing.value = campaign
  form.value = {
    name:         campaign?.title || campaign?.name || '',
    description:  campaign?.description || '',
    status:       campaign?.status || 'draft',
    pole:         campaign?.pole || '',
    type:         campaign?.type || 'national',
    interlocutor: campaign?.interlocutor || '',
    start_date:   campaign?.start_date || '',
    end_date:     campaign?.end_date || '',
    product_ids:  [...(campaign?.product_ids || [])],
  }
  showForm.value = true
}

async function save() {
  if (!form.value.name.trim()) return
  saving.value = true
  try {
    if (editing.value) {
      await api.admin.updateCampaign(editing.value.id, form.value)
      notify.success('Campaign updated')
    } else {
      await api.admin.createCampaign(form.value)
      notify.success('Campaign created')
    }
    showForm.value = false
    await load()
  } catch (err) {
    notify.error(err?.response?.data?.detail || 'Failed to save campaign')
  } finally {
    saving.value = false
  }
}

function goToProduct(pid) {
  router.push(`/admin/products/${pid}`)
}

function confirmDelete(campaign) { deleteTarget.value = campaign }

async function executeDelete() {
  saving.value = true
  try {
    await api.admin.deleteCampaign(deleteTarget.value.id)
    deleteTarget.value = null
    notify.success('Campaign deleted')
    await load()
  } catch (err) {
    notify.error(err?.response?.data?.detail || 'Failed to delete campaign')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
*, *::before, *::after { box-sizing: border-box; }
.campaigns-page { font-family: Inter, sans-serif; color: #fff; }

/* ── Header ── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}
h1 { font-size: 1.5rem; font-weight: 700; color: #fff; margin: 0 0 4px; }
.page-sub { font-size: .85rem; color: rgba(255,255,255,.4); margin: 0; }

/* ── Filter bar ── */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.search-wrap {
  flex: 1;
  min-width: 220px;
  position: relative;
  display: flex;
  align-items: center;
}
.search-icon {
  position: absolute;
  left: 12px;
  color: rgba(255,255,255,.3);
  pointer-events: none;
}
.search-input {
  width: 100%;
  background: rgba(255,255,255,.05);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 8px;
  padding: 8px 14px 8px 36px;
  font-size: .875rem;
  color: #fff;
  outline: none;
  color-scheme: dark;
  transition: border-color .15s;
}
.search-input::placeholder { color: rgba(255,255,255,.3); }
.search-input:focus { border-color: #E8622C; }

.filter-select {
  background: rgba(255,255,255,.05);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: .875rem;
  color: #fff;
  outline: none;
  cursor: pointer;
  color-scheme: dark;
  transition: border-color .15s;
}
.filter-select option { background: #0f172a; color: #fff; }
.filter-select:focus { border-color: #E8622C; }

.filter-count { font-size: .82rem; color: rgba(255,255,255,.35); white-space: nowrap; margin-left: 4px; }

/* ── Table wrapper ── */
.table-wrap {
  background: rgba(255,255,255,.04);
  border: 1px solid rgba(255,255,255,.08);
  backdrop-filter: blur(12px);
  border-radius: 12px;
  overflow-x: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,.1) transparent;
}
.table { min-width: 900px; }
.table { width: 100%; border-collapse: collapse; font-size: .875rem; }
.table thead tr { background: rgba(255,255,255,.03); }
.table th {
  text-align: left;
  padding: 11px 16px;
  font-size: .72rem;
  font-weight: 700;
  color: rgba(255,255,255,.4);
  text-transform: uppercase;
  letter-spacing: .06em;
  white-space: nowrap;
  border-bottom: 1px solid rgba(255,255,255,.06);
}
.data-row { border-bottom: 1px solid rgba(255,255,255,.05); transition: background .12s; }
.data-row:hover { background: rgba(255,255,255,.03); }
.data-row.expanded { background: rgba(59,130,246,.05); border-bottom: none; }
.table td { padding: 12px 16px; color: rgba(255,255,255,.8); vertical-align: middle; }

/* Cells */
.cell-id { white-space: nowrap; }
.id-chip {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: .72rem;
  background: rgba(255,255,255,.07);
  color: rgba(255,255,255,.45);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 5px;
  padding: 2px 7px;
  cursor: default;
  white-space: nowrap;
}
.cell-title { font-weight: 600; color: #fff; max-width: 200px; }
.cell-interlocutor { font-size: .82rem; color: rgba(255,255,255,.5); white-space: nowrap; }
.cell-dates { font-size: .78rem; color: rgba(255,255,255,.5); white-space: nowrap; line-height: 1.7; }
.date-end { color: rgba(255,255,255,.3); }
.cell-muted { color: rgba(255,255,255,.25); }
.cell-actions { display: flex; gap: 4px; white-space: nowrap; }
.empty-row { text-align: center; padding: 40px; color: rgba(255,255,255,.3); font-size: .9rem; }

/* Badges */
.badge { border-radius: 5px; padding: 2px 8px; font-size: .72rem; font-weight: 700; white-space: nowrap; }
.badge.pole { background: rgba(168,85,247,.18); color: #c084fc; }

.status-badge { border-radius: 20px; padding: 3px 10px; font-size: .72rem; font-weight: 700; white-space: nowrap; }
.status-badge.active  { background: rgba(34,197,94,.15);  color: #4ade80; }
.status-badge.archive { background: rgba(255,255,255,.08); color: rgba(255,255,255,.4); }
.status-badge.draft   { background: rgba(251,191,36,.15);  color: #fbbf24; }

/* Product chips */
.product-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(59,130,246,.15);
  color: #60a5fa;
  border: 1px solid rgba(59,130,246,.2);
  border-radius: 5px;
  padding: 2px 8px;
  font-size: .72rem;
  white-space: nowrap;
  margin-right: 4px;
}
.product-chip b { font-weight: 700; }
.product-chip.clickable { cursor: pointer; transition: background .12s, border-color .12s; }
.product-chip.clickable:hover { background: rgba(59,130,246,.25); border-color: rgba(59,130,246,.5); }
.chip-arrow { opacity: 0; transition: opacity .12s; flex-shrink: 0; }
.product-chip.clickable:hover .chip-arrow { opacity: 1; }
.no-product { color: rgba(255,255,255,.25); }

/* Targets button */
.targets-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: .78rem;
  font-weight: 600;
  color: rgba(255,255,255,.6);
  cursor: pointer;
  transition: background .12s, border-color .12s;
  white-space: nowrap;
}
.targets-btn:hover { background: rgba(59,130,246,.15); border-color: rgba(59,130,246,.3); color: #60a5fa; }
.load-targets { color: #60a5fa; }
.targets-icon { color: rgba(255,255,255,.35); }

/* Targets sub-panel */
.targets-row td {
  padding: 0;
  border-bottom: 1px solid rgba(59,130,246,.15);
  background: rgba(10,18,40,.5);
}
.targets-panel { padding: 16px 20px; }
.targets-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px;
  color: rgba(255,255,255,.4);
  font-size: .875rem;
}

.targets-stats { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }
.stat-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255,255,255,.05);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 8px;
  padding: 5px 12px;
  font-size: .78rem;
}
.stat-label { color: rgba(255,255,255,.5); }
.stat-count {
  font-weight: 700;
  color: #fff;
  background: rgba(255,255,255,.08);
  border-radius: 4px;
  padding: 1px 7px;
}

.inner-table {
  width: 100%;
  border-collapse: collapse;
  font-size: .8rem;
  background: rgba(255,255,255,.03);
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,.07);
}
.inner-table th {
  padding: 8px 14px;
  font-size: .7rem;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: rgba(255,255,255,.35);
  font-weight: 700;
  background: rgba(255,255,255,.03);
  border-bottom: 1px solid rgba(255,255,255,.06);
  text-align: left;
}
.inner-table td {
  padding: 8px 14px;
  border-bottom: 1px solid rgba(255,255,255,.04);
  color: rgba(255,255,255,.7);
}
.inner-table tr:last-child td { border-bottom: none; }
.inner-table tbody tr:hover td { background: rgba(255,255,255,.025); }
.acc-name { font-weight: 500; max-width: 260px; color: rgba(255,255,255,.85); }

.target-status {
  background: rgba(255,255,255,.07);
  color: rgba(255,255,255,.5);
  border-radius: 4px;
  padding: 1px 7px;
  font-size: .72rem;
  white-space: nowrap;
}
.quiz-bar {
  width: 60px; height: 5px;
  background: rgba(255,255,255,.1);
  border-radius: 3px;
  display: inline-block;
  vertical-align: middle;
  margin-right: 6px;
}
.quiz-fill { height: 100%; background: #E8622C; border-radius: 3px; transition: width .3s; }
.quiz-pct { font-size: .72rem; color: rgba(255,255,255,.4); }
.score-cell { font-weight: 600; color: #fff; }
.market-badge { background: rgba(232,98,44,.15); color: #E8622C; border-radius: 4px; padding: 2px 7px; font-size: .72rem; font-weight: 700; border: 1px solid rgba(232,98,44,.2); }
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; }
.dot.green { background: #22c55e; }
.dot.red   { background: rgba(255,255,255,.12); }
.targets-more { margin-top: 10px; font-size: .78rem; color: rgba(255,255,255,.35); text-align: center; }

/* ── Spinners ── */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px;
  color: rgba(255,255,255,.4);
}
.spinner {
  width: 20px; height: 20px;
  border: 2px solid rgba(255,255,255,.1);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .7s linear infinite;
}
.spinner-sm {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,.1);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .7s linear infinite;
  flex-shrink: 0;
}
.spinner-xs {
  width: 12px; height: 12px;
  border: 2px solid rgba(255,255,255,.2);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .7s linear infinite;
  flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Buttons ── */
.btn-primary {
  display: inline-flex; align-items: center; gap: 6px;
  background: linear-gradient(135deg, #E8622C, #ff8c5a);
  color: #fff; border: none; border-radius: 8px;
  padding: 9px 18px; cursor: pointer; font-weight: 600;
  font-size: .875rem; transition: opacity .15s, transform .1s;
  white-space: nowrap;
}
.btn-primary:hover { opacity: .9; transform: translateY(-1px); }
.btn-primary:active { transform: translateY(0); }
.btn-primary:disabled { opacity: .45; cursor: default; transform: none; }

.btn-ghost {
  display: inline-flex; align-items: center; gap: 5px;
  background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1);
  color: #fff; border-radius: 7px; padding: 7px 14px;
  cursor: pointer; font-size: .875rem; transition: background .15s;
}
.btn-ghost:hover { background: rgba(255,255,255,.1); }

.btn-danger {
  display: inline-flex; align-items: center; gap: 5px;
  background: rgba(239,68,68,.15); border: 1px solid rgba(239,68,68,.3);
  color: #f87171; border-radius: 7px; padding: 7px 14px;
  cursor: pointer; font-size: .875rem; font-weight: 600;
  transition: background .15s;
}
.btn-danger:hover { background: rgba(239,68,68,.25); }
.btn-danger:disabled { opacity: .45; cursor: default; }

.icon-btn {
  background: rgba(255,255,255,.08);
  border: 1px solid rgba(255,255,255,.12);
  border-radius: 7px;
  cursor: pointer;
  padding: 6px;
  color: rgba(255,255,255,.7);
  display: flex; align-items: center; justify-content: center;
  transition: background .12s, color .12s;
}
.icon-btn:hover { background: rgba(255,255,255,.12); color: #fff; }
.icon-btn.danger:hover { background: rgba(239,68,68,.15); border-color: rgba(239,68,68,.3); color: #f87171; }

/* ── Modals ── */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.7);
  backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center;
  z-index: 200;
  padding: 20px;
}
.modal {
  background: rgba(15,23,42,.95);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 16px;
  width: 580px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 80px rgba(0,0,0,.6);
}
.modal-sm { width: 400px; }

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 0;
}
.modal-header h2 { font-size: 1.1rem; font-weight: 700; color: #fff; margin: 0; }
.close-btn {
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 7px;
  color: rgba(255,255,255,.5);
  cursor: pointer;
  padding: 5px;
  display: flex; align-items: center; justify-content: center;
  transition: background .15s;
  flex-shrink: 0;
}
.close-btn:hover { background: rgba(255,255,255,.12); color: #fff; }

.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
  flex: 1;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,.1) transparent;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid rgba(255,255,255,.07);
}

/* ── Forms ── */
.form-group { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
.form-group label { font-size: .82rem; font-weight: 600; color: rgba(255,255,255,.55); }

.form-group input,
.form-group select,
.form-group textarea {
  background: rgba(255,255,255,.05);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 8px;
  padding: 9px 12px;
  font-size: .9rem;
  color: #fff;
  outline: none;
  font-family: inherit;
  color-scheme: dark;
  transition: border-color .15s;
}
.form-group input::placeholder,
.form-group textarea::placeholder { color: rgba(255,255,255,.3); }
.form-group select option { background: #0f172a; color: #fff; }
.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus { border-color: #E8622C; }
.form-group textarea { resize: vertical; min-height: 70px; }

.form-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.form-row.two-col { grid-template-columns: 1fr 1fr; }

/* Product checkboxes */
.product-checkboxes {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 180px;
  overflow-y: auto;
  background: rgba(255,255,255,.04);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 8px;
  padding: 10px;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,.1) transparent;
}
.checkbox-row {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-size: .875rem;
  padding: 4px 6px;
  border-radius: 6px;
  transition: background .12s;
}
.checkbox-row:hover { background: rgba(255,255,255,.05); }
.checkbox-row input[type="checkbox"] {
  width: 15px; height: 15px;
  cursor: pointer;
  accent-color: #E8622C;
  flex-shrink: 0;
}
.product-label { display: flex; align-items: center; gap: 8px; color: rgba(255,255,255,.75); }
.pid {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: .75rem;
  color: rgba(255,255,255,.35);
}

/* Delete modal */
.delete-icon-wrap {
  display: flex; align-items: center; justify-content: center;
  width: 64px; height: 64px;
  background: rgba(239,68,68,.1);
  border: 1px solid rgba(239,68,68,.2);
  border-radius: 50%;
  margin: 0 auto 16px;
}
.delete-msg { color: rgba(255,255,255,.8); text-align: center; margin: 0 0 6px; font-size: .95rem; }
.delete-msg strong { color: #fff; }
.warn-text { color: rgba(248,113,113,.7); font-size: .82rem; text-align: center; margin: 0; }

/* ══ LIGHT MODE ══════════════════════════════ */
[data-theme="light"] .campaigns-page { color: #0D1B2E; }
[data-theme="light"] h1  { color: #0D1B2E; }

/* Icon buttons (edit / delete) */
[data-theme="light"] .icon-btn {
  background: rgba(13,27,46,0.06);
  border-color: rgba(13,27,46,0.12);
  color: #3D5068;
}
[data-theme="light"] .icon-btn:hover { background: rgba(13,27,46,0.12); color: #0D1B2E; }
[data-theme="light"] .icon-btn.danger:hover { background: rgba(239,68,68,0.10); border-color: rgba(239,68,68,0.25); color: #dc2626; }
[data-theme="light"] h2, [data-theme="light"] h3 { color: #0D1B2E; }
[data-theme="light"] .page-sub     { color: #3D5068; }
[data-theme="light"] .filter-count { color: #7C93AE; }

/* Search & filters */
[data-theme="light"] .search-icon   { color: #7C93AE; }
[data-theme="light"] .search-input  {
  background: #FFFFFF; border-color: rgba(13,27,46,0.15);
  color: #0D1B2E; color-scheme: light;
}
[data-theme="light"] .search-input::placeholder { color: #94A3B8; }
[data-theme="light"] .filter-select {
  background: #FFFFFF; border-color: rgba(13,27,46,0.15);
  color: #0D1B2E; color-scheme: light;
}
[data-theme="light"] .filter-select option { background: #FFFFFF; color: #0D1B2E; }

/* Table wrapper */
[data-theme="light"] .table-wrap {
  background: #FFFFFF; border-color: rgba(13,27,46,0.09);
  box-shadow: 0 2px 10px rgba(13,27,46,0.06); backdrop-filter: none;
}
[data-theme="light"] .table thead tr { background: rgba(13,27,46,0.03); }
[data-theme="light"] .table th {
  color: #7C93AE; border-bottom-color: rgba(13,27,46,0.08);
}
[data-theme="light"] .data-row      { border-bottom-color: rgba(13,27,46,0.06); }
[data-theme="light"] .data-row:hover { background: rgba(13,27,46,0.025); }
[data-theme="light"] .data-row.expanded { background: rgba(59,130,246,0.04); }
[data-theme="light"] .table td      { color: #0D1B2E; }

/* Cells */
[data-theme="light"] .id-chip {
  background: rgba(13,27,46,0.05); color: #7C93AE; border-color: rgba(13,27,46,0.10);
}
[data-theme="light"] .cell-title        { color: #0D1B2E; }
[data-theme="light"] .cell-interlocutor { color: #3D5068; }
[data-theme="light"] .cell-dates        { color: #3D5068; }
[data-theme="light"] .date-end          { color: #7C93AE; }
[data-theme="light"] .cell-muted        { color: #7C93AE; }
[data-theme="light"] .empty-row         { color: #7C93AE; }

/* Badges */
[data-theme="light"] .status-badge.active  { background: rgba(22,163,74,0.12);  color: #16a34a; }
[data-theme="light"] .status-badge.archive { background: rgba(13,27,46,0.07);   color: #7C93AE; }
[data-theme="light"] .status-badge.draft   { background: rgba(217,119,6,0.12);  color: #d97706; }

/* Targets btn */
[data-theme="light"] .targets-btn {
  background: rgba(13,27,46,0.05); border-color: rgba(13,27,46,0.12); color: #3D5068;
}
[data-theme="light"] .targets-icon { color: #7C93AE; }
[data-theme="light"] .no-product   { color: #94A3B8; }

/* Product label */
[data-theme="light"] .product-label { color: #3D5068; }
[data-theme="light"] .pid           { color: #7C93AE; }

/* Modal */
[data-theme="light"] .modal {
  background: #FFFFFF; border-color: rgba(13,27,46,0.12);
  box-shadow: 0 24px 64px rgba(13,27,46,0.15);
}
[data-theme="light"] .modal-header {
  background: #FFFFFF;
  padding-bottom: 16px;
  border-radius: 14px 14px 0 0;
  border-bottom: 1px solid rgba(13,27,46,0.08);
}
[data-theme="light"] .modal h2         { color: #0D1B2E; }
[data-theme="light"] .delete-msg        { color: #3D5068; }
[data-theme="light"] .delete-msg strong { color: #0D1B2E; }
[data-theme="light"] .close-btn { background: transparent; border: none; color: #7C93AE; }
[data-theme="light"] .close-btn:hover { background: rgba(13,27,46,0.06); color: #0D1B2E; }
[data-theme="light"] .form-group label  { color: #3D5068; }
[data-theme="light"] .form-group input,
[data-theme="light"] .form-group select,
[data-theme="light"] .form-group textarea {
  background: #F8FAFC; border-color: rgba(13,27,46,0.15); color: #0D1B2E; color-scheme: light;
}
[data-theme="light"] .form-group select option { background: #FFFFFF; color: #0D1B2E; }
</style>
