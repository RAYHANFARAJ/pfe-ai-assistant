<template>
  <div class="detail-shell">

    <!-- Background -->
    <div class="bg-canvas" aria-hidden="true">
      <div class="bg-solid"></div>
      <div class="blob blob-a"></div>
      <div class="blob blob-b"></div>
      <div class="blob blob-c"></div>
    </div>

    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
          </svg>
        </div>
        <span class="brand-name">Admin</span>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/admin?tab=products" class="nav-item active">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>
          </svg>
          Products & Criteria
        </router-link>
        <router-link to="/admin?tab=campaigns" class="nav-item">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
          </svg>
          Campaigns
        </router-link>
        <router-link to="/admin?tab=sources" class="nav-item">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
          </svg>
          Data Sources
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <router-link to="/search" class="back-link">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/>
          </svg>
          Back to app
        </router-link>
      </div>
    </aside>

    <!-- Main -->
    <main class="detail-main">

      <div v-if="loading" class="loading-state">
        <div class="spinner"></div><span>Loading product…</span>
      </div>

      <template v-else-if="product">

        <!-- Topbar -->
        <header class="detail-topbar">
          <button class="back-btn" @click="$router.push('/admin?tab=products')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/>
            </svg>
            Products
          </button>
          <span class="breadcrumb-sep">/</span>
          <span class="breadcrumb-current">{{ product.name }}</span>
        </header>

        <div class="content-wrap">

          <!-- Hero card -->
          <div class="hero-card">
            <div class="hero-left">
              <span class="product-id-badge">{{ product.id }}</span>
              <h1>{{ product.name }}</h1>
              <p class="hero-sub">{{ criteria.length }} criteria · {{ totalChoices }} choices defined</p>
            </div>
            <div class="hero-stats">
              <div class="stat-card">
                <span class="stat-value">{{ criteria.length }}</span>
                <span class="stat-label">Total</span>
              </div>
              <div class="stat-card">
                <span class="stat-value accent-blue">{{ typeCount('single_choice') }}</span>
                <span class="stat-label">Single choice</span>
              </div>
              <div class="stat-card">
                <span class="stat-value accent-green">{{ typeCount('numeric') }}</span>
                <span class="stat-label">Numeric</span>
              </div>
              <div class="stat-card">
                <span class="stat-value accent-purple">{{ typeCount('multiple_choice') }}</span>
                <span class="stat-label">Multiple</span>
              </div>
            </div>
          </div>

          <!-- Criteria section -->
          <div class="section-header">
            <div class="section-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,.5)" stroke-width="2">
                <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
              </svg>
              <h2>Criteria</h2>
            </div>
            <button class="btn-primary" @click="openCriterionForm()">
              <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
                <path d="M7 1v12M1 7h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              Add Criterion
            </button>
          </div>

          <div v-if="!criteria.length" class="empty-criteria">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,.15)" stroke-width="1.5">
              <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
            </svg>
            <p>No criteria for this product yet.</p>
          </div>

          <div class="criteria-list">
            <div v-for="c in criteria" :key="c.id" class="criterion-card">

              <!-- Criterion header -->
              <div class="criterion-header">
                <div class="criterion-left">
                  <span class="order-num">#{{ c.order }}</span>
                  <div class="criterion-body">
                    <p class="criterion-label">{{ c.label }}</p>
                    <div class="criterion-tags">
                      <span class="type-tag" :class="c.answer_type">{{ c.answer_type }}</span>
                      <span v-if="c.unit" class="unit-tag">{{ c.unit }}</span>
                      <span v-if="c.is_main" class="main-tag">Main</span>
                    </div>
                  </div>
                </div>
                <div class="criterion-actions">
                  <button class="pill-btn" @click="toggleChoices(c.id)">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
                      <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
                    </svg>
                    Choices
                    <span class="choices-count">{{ choicesMap[c.id]?.length ?? 0 }}</span>
                    <svg class="chevron" :class="{ rotated: expandedCriterion === c.id }" width="10" height="10" viewBox="0 0 12 12" fill="none">
                      <path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                  <button class="icon-btn" title="Edit" @click="openCriterionForm(c)">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                  <button class="icon-btn danger" title="Delete" @click="confirmDeleteCriterion(c)">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
                      <path d="M10 11v6M14 11v6"/>
                    </svg>
                  </button>
                </div>
              </div>

              <!-- Prompt -->
              <div v-if="c.agent_prompt" class="criterion-prompt">
                <span class="prompt-pill">Prompt</span>
                <span class="prompt-text">{{ c.agent_prompt }}</span>
              </div>

              <!-- Choices panel -->
              <div v-if="expandedCriterion === c.id" class="choices-panel">
                <div v-if="choicesLoading" class="loading-sm">
                  <div class="spinner-sm"></div> Loading…
                </div>
                <template v-else>
                  <div v-if="!choicesMap[c.id]?.length" class="empty-choices">No choices defined yet.</div>
                  <table v-else class="choices-table">
                    <thead>
                      <tr>
                        <th>Label</th><th>Score</th><th>Rule</th><th>Condition</th><th></th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="ch in choicesMap[c.id]" :key="ch.id">
                        <td class="ch-label">{{ ch.label }}</td>
                        <td>
                          <span class="score-chip" :class="ch.score > 0 ? 'pos' : 'zero'">
                            {{ ch.score }} pts
                          </span>
                        </td>
                        <td>
                          <span class="rule-chip" :class="ch.is_blocking ? 'blocking' : 'pass'">
                            {{ ch.is_blocking ? 'Blocking' : 'Pass' }}
                          </span>
                        </td>
                        <td class="ch-condition"><code>{{ ch.condition?.body || '—' }}</code></td>
                        <td>
                          <button class="icon-btn danger sm" @click="deleteChoice(c.id, ch.id)">
                            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                              <path d="M18 6L6 18M6 6l12 12"/>
                            </svg>
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>

                  <!-- Add choice row -->
                  <div class="add-choice-row">
                    <input v-model="newChoice.label" class="add-input flex-1" placeholder="Choice label…" />
                    <input v-model.number="newChoice.score" type="number" class="add-input score-input" placeholder="Score" />
                    <label class="blocking-toggle">
                      <input type="checkbox" v-model="newChoice.is_blocking" />
                      <span>Blocking</span>
                    </label>
                    <button class="btn-add" @click="addChoice(c.id)">
                      <svg width="12" height="12" viewBox="0 0 14 14" fill="none">
                        <path d="M7 1v12M1 7h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                      </svg>
                      Add
                    </button>
                  </div>
                </template>
              </div>

            </div>
          </div>

        </div>
      </template>

      <div v-else class="loading-state"><span>Product not found.</span></div>

    </main>

    <!-- Criterion form modal -->
    <div v-if="showCriterionForm" class="modal-overlay" @click.self="showCriterionForm = false">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editingCriterion ? 'Edit Criterion' : 'New Criterion' }}</h2>
          <button class="close-btn" @click="showCriterionForm = false">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Label</label>
            <input v-model="criterionForm.label" placeholder="Question asked to the client" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Answer type</label>
              <select v-model="criterionForm.answer_type">
                <option value="single_choice">single_choice</option>
                <option value="numeric">numeric</option>
                <option value="multiple_choice">multiple_choice</option>
                <option value="text">text</option>
              </select>
            </div>
            <div class="form-group">
              <label>Unit</label>
              <input v-model="criterionForm.unit" placeholder="e.g. personnes, €" />
            </div>
            <div class="form-group">
              <label>Order</label>
              <input v-model.number="criterionForm.order" type="number" min="1" />
            </div>
          </div>
          <div class="form-group">
            <label>Agent prompt</label>
            <textarea v-model="criterionForm.agent_prompt" rows="2" placeholder="Custom AI prompt…" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="showCriterionForm = false">Cancel</button>
          <button class="btn-primary" :disabled="saving" @click="saveCriterion">
            {{ saving ? 'Saving…' : 'Save' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete confirm -->
    <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
      <div class="modal modal-sm">
        <div class="modal-header">
          <h2>Delete criterion</h2>
          <button class="close-btn" @click="deleteTarget = null">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <p class="del-msg">Delete <strong>{{ deleteTarget?.label }}</strong>?</p>
          <p class="del-warn">All choices will also be removed.</p>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="deleteTarget = null">Cancel</button>
          <button class="btn-danger-solid" :disabled="saving" @click="execDeleteCriterion">
            {{ saving ? '…' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../services/api'

const route = useRoute()
const pid   = route.params.id

const product           = ref(null)
const criteria          = ref([])
const choicesMap        = ref({})
const loading           = ref(true)
const choicesLoading    = ref(false)
const saving            = ref(false)
const expandedCriterion = ref(null)
const showCriterionForm = ref(false)
const editingCriterion  = ref(null)
const deleteTarget      = ref(null)
const newChoice         = ref({ label: '', score: 0, is_blocking: false })
const criterionForm     = ref({ label: '', answer_type: 'single_choice', unit: '', order: 1, agent_prompt: '' })

const totalChoices = computed(() => Object.values(choicesMap.value).reduce((s, a) => s + a.length, 0))
function typeCount(type) { return criteria.value.filter(c => c.answer_type === type).length }

async function load() {
  loading.value = true
  try {
    const [prods, crits] = await Promise.all([api.admin.listProducts(), api.admin.listCriteria(pid)])
    product.value  = prods.data.find(p => p.id === pid) || null
    criteria.value = crits.data
    await Promise.all(crits.data.map(c => loadChoices(c.id)))
  } finally { loading.value = false }
}

async function loadChoices(criterionId) {
  const { data } = await api.admin.listChoices(criterionId)
  choicesMap.value[criterionId] = data
}

async function toggleChoices(criterionId) {
  if (expandedCriterion.value === criterionId) { expandedCriterion.value = null; return }
  expandedCriterion.value = criterionId
  if (!choicesMap.value[criterionId]) {
    choicesLoading.value = true
    await loadChoices(criterionId)
    choicesLoading.value = false
  }
}

function openCriterionForm(c = null) {
  editingCriterion.value = c
  criterionForm.value = { label: c?.label||'', answer_type: c?.answer_type||'single_choice', unit: c?.unit||'', order: c?.order||criteria.value.length+1, agent_prompt: c?.agent_prompt||'' }
  showCriterionForm.value = true
}

async function saveCriterion() {
  if (!criterionForm.value.label.trim()) return
  saving.value = true
  try {
    if (editingCriterion.value) await api.admin.updateCriterion(editingCriterion.value.id, criterionForm.value)
    else await api.admin.createCriterion(pid, criterionForm.value)
    showCriterionForm.value = false
    await load()
  } finally { saving.value = false }
}

function confirmDeleteCriterion(c) { deleteTarget.value = c }

async function execDeleteCriterion() {
  saving.value = true
  try {
    await api.admin.deleteCriterion(deleteTarget.value.id)
    deleteTarget.value = null
    await load()
  } finally { saving.value = false }
}

async function addChoice(criterionId) {
  if (!newChoice.value.label.trim()) return
  await api.admin.createChoice(criterionId, newChoice.value)
  newChoice.value = { label: '', score: 0, is_blocking: false }
  await loadChoices(criterionId)
}

async function deleteChoice(criterionId, choiceId) {
  await api.admin.deleteChoice(choiceId)
  await loadChoices(criterionId)
}

onMounted(load)
</script>

<style scoped>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.detail-shell {
  display: flex;
  height: 100vh;
  font-family: 'Inter', 'Segoe UI', sans-serif;
  color: #fff;
  background: #060E1A;
  overflow: hidden;
  color-scheme: dark;
}

/* Background */
.bg-canvas { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
.bg-solid   { position: absolute; inset: 0; background: #060E1A; }
.blob { position: absolute; border-radius: 50%; filter: blur(120px); pointer-events: none; }
.blob-a { width: 600px; height: 600px; background: radial-gradient(circle, rgba(59,91,219,.18) 0%, transparent 70%); bottom: -10%; left: -5%; }
.blob-b { width: 400px; height: 400px; background: radial-gradient(circle, rgba(232,98,44,.12) 0%, transparent 70%); top: 10%; right: 5%; }
.blob-c { width: 350px; height: 350px; background: radial-gradient(circle, rgba(124,58,237,.12) 0%, transparent 70%); top: 50%; left: 35%; }

/* Sidebar */
.sidebar {
  width: 240px; flex-shrink: 0;
  background: rgba(6,14,26,.8);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid rgba(255,255,255,.07);
  display: flex; flex-direction: column;
  position: relative; z-index: 10;
}
.sidebar-brand { display: flex; align-items: center; gap: 12px; padding: 24px 20px 20px; border-bottom: 1px solid rgba(255,255,255,.06); }
.brand-icon { width: 36px; height: 36px; background: linear-gradient(135deg,#E8622C,#ff8c5a); border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #fff; box-shadow: 0 0 20px rgba(232,98,44,.35); }
.brand-name { font-size: 1rem; font-weight: 700; color: #fff; }
.sidebar-nav { flex: 1; padding: 16px 12px; display: flex; flex-direction: column; gap: 4px; }
.nav-item { display: flex; align-items: center; gap: 12px; padding: 11px 14px; border-radius: 10px; color: rgba(255,255,255,.4); font-size: .875rem; font-weight: 500; text-decoration: none; transition: all .18s; }
.nav-item:hover { color: rgba(255,255,255,.85); background: rgba(255,255,255,.06); }
.nav-item.active { color: #fff; background: rgba(232,98,44,.15); border: 1px solid rgba(232,98,44,.2); }
.sidebar-footer { padding: 16px 20px; border-top: 1px solid rgba(255,255,255,.06); }
.back-link { display: flex; align-items: center; gap: 8px; color: rgba(255,255,255,.3); font-size: .82rem; text-decoration: none; transition: color .18s; }
.back-link:hover { color: rgba(255,255,255,.65); }

/* Main */
.detail-main { flex: 1; overflow-y: auto; position: relative; z-index: 1; scrollbar-width: thin; scrollbar-color: rgba(255,255,255,.08) transparent; }

/* Topbar */
.detail-topbar {
  display: flex; align-items: center; gap: 10px;
  padding: 20px 48px 16px;
  border-bottom: 1px solid rgba(255,255,255,.06);
  background: rgba(6,14,26,.5);
  backdrop-filter: blur(16px);
  position: sticky; top: 0; z-index: 5;
}
.back-btn {
  display: flex; align-items: center; gap: 6px;
  background: none; border: none; color: rgba(255,255,255,.4);
  font-size: .82rem; cursor: pointer; transition: color .15s;
}
.back-btn:hover { color: #E8622C; }
.breadcrumb-sep { color: rgba(255,255,255,.2); font-size: .85rem; }
.breadcrumb-current { color: rgba(255,255,255,.75); font-size: .85rem; font-weight: 600; }

/* Content */
.content-wrap { max-width: 860px; margin: 0 auto; padding: 32px 48px 60px; }

/* Hero */
.hero-card {
  display: flex; justify-content: space-between; align-items: center;
  gap: 28px; flex-wrap: wrap;
  background: rgba(255,255,255,.04);
  border: 1px solid rgba(255,255,255,.08);
  backdrop-filter: blur(12px);
  border-radius: 16px; padding: 28px 32px;
  margin-bottom: 28px;
}
.product-id-badge {
  display: inline-block; font-family: monospace; font-size: .78rem;
  background: rgba(232,98,44,.15); color: #E8622C;
  border: 1px solid rgba(232,98,44,.25); border-radius: 6px;
  padding: 2px 10px; margin-bottom: 10px; font-weight: 700;
}
h1 { font-size: 1.6rem; font-weight: 800; color: #fff; margin-bottom: 6px; }
.hero-sub { font-size: .85rem; color: rgba(255,255,255,.35); }
.hero-stats { display: flex; gap: 12px; flex-wrap: wrap; }
.stat-card {
  background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.08);
  border-radius: 10px; padding: 14px 20px; text-align: center; min-width: 80px;
}
.stat-value { display: block; font-size: 1.6rem; font-weight: 800; color: #fff; }
.stat-value.accent-blue   { color: #60a5fa; }
.stat-value.accent-green  { color: #4ade80; }
.stat-value.accent-purple { color: #c084fc; }
.stat-label { display: block; font-size: .68rem; color: rgba(255,255,255,.35); margin-top: 2px; text-transform: uppercase; letter-spacing: .06em; }

/* Section header */
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.section-title { display: flex; align-items: center; gap: 8px; }
h2 { font-size: 1rem; font-weight: 700; color: rgba(255,255,255,.8); }

/* Criterion cards */
.criteria-list { display: flex; flex-direction: column; gap: 10px; }
.criterion-card {
  background: rgba(255,255,255,.03);
  border: 1px solid rgba(255,255,255,.07);
  border-radius: 12px; overflow: hidden;
  transition: border-color .18s;
}
.criterion-card:hover { border-color: rgba(255,255,255,.13); }

.criterion-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 18px; gap: 12px;
}
.criterion-left { display: flex; align-items: flex-start; gap: 14px; flex: 1; min-width: 0; }
.order-num {
  background: rgba(255,255,255,.06); color: rgba(255,255,255,.4);
  border-radius: 6px; padding: 3px 9px; font-size: .75rem; font-weight: 700;
  white-space: nowrap; flex-shrink: 0; margin-top: 2px;
}
.criterion-body { min-width: 0; }
.criterion-label { font-weight: 600; color: rgba(255,255,255,.9); font-size: .9rem; margin-bottom: 7px; line-height: 1.4; }
.criterion-tags { display: flex; flex-wrap: wrap; gap: 5px; }

.type-tag { border-radius: 4px; padding: 2px 8px; font-size: .7rem; font-weight: 700; }
.type-tag.single_choice   { background: rgba(96,165,250,.15);  color: #60a5fa; border: 1px solid rgba(96,165,250,.2); }
.type-tag.numeric         { background: rgba(74,222,128,.15);  color: #4ade80; border: 1px solid rgba(74,222,128,.2); }
.type-tag.multiple_choice { background: rgba(192,132,252,.15); color: #c084fc; border: 1px solid rgba(192,132,252,.2); }
.type-tag.text            { background: rgba(250,204,21,.12);  color: #facc15; border: 1px solid rgba(250,204,21,.2); }
.unit-tag { background: rgba(255,255,255,.06); color: rgba(255,255,255,.45); border-radius: 4px; padding: 2px 8px; font-size: .7rem; border: 1px solid rgba(255,255,255,.08); }
.main-tag { background: rgba(232,98,44,.15); color: #E8622C; border-radius: 4px; padding: 2px 8px; font-size: .7rem; font-weight: 700; border: 1px solid rgba(232,98,44,.2); }

.criterion-actions { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }

.pill-btn {
  display: flex; align-items: center; gap: 6px;
  background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1);
  border-radius: 8px; padding: 6px 12px;
  color: rgba(255,255,255,.6); font-size: .78rem; font-weight: 600;
  cursor: pointer; transition: all .15s;
}
.pill-btn:hover { background: rgba(255,255,255,.1); color: #fff; }
.choices-count { background: rgba(255,255,255,.1); border-radius: 10px; padding: 1px 7px; font-size: .7rem; }
.chevron { transition: transform .2s; }
.chevron.rotated { transform: rotate(180deg); }

.icon-btn {
  width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.08);
  border-radius: 7px; cursor: pointer; color: rgba(255,255,255,.45); transition: all .15s;
}
.icon-btn:hover { background: rgba(255,255,255,.1); color: #fff; }
.icon-btn.danger:hover { background: rgba(239,68,68,.15); border-color: rgba(239,68,68,.3); color: #f87171; }
.icon-btn.sm { width: 24px; height: 24px; border-radius: 5px; }

/* Prompt */
.criterion-prompt {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 8px 18px 10px;
  border-top: 1px solid rgba(255,255,255,.05);
  background: rgba(0,0,0,.15);
}
.prompt-pill { background: rgba(255,255,255,.07); color: rgba(255,255,255,.35); border-radius: 4px; padding: 2px 8px; font-size: .68rem; font-weight: 700; white-space: nowrap; margin-top: 1px; }
.prompt-text { font-size: .78rem; color: rgba(255,255,255,.35); line-height: 1.5; }

/* Choices panel */
.choices-panel {
  border-top: 1px solid rgba(255,255,255,.06);
  padding: 14px 18px;
  background: rgba(0,0,0,.2);
}
.choices-table { width: 100%; border-collapse: collapse; font-size: .8rem; margin-bottom: 12px; }
.choices-table th { padding: 7px 10px; font-size: .68rem; text-transform: uppercase; letter-spacing: .06em; color: rgba(255,255,255,.3); font-weight: 700; text-align: left; border-bottom: 1px solid rgba(255,255,255,.06); }
.choices-table td { padding: 9px 10px; border-bottom: 1px solid rgba(255,255,255,.04); color: rgba(255,255,255,.75); vertical-align: middle; }
.choices-table tr:last-child td { border-bottom: none; }
.ch-label { font-weight: 500; }
.score-chip { border-radius: 4px; padding: 2px 8px; font-size: .72rem; font-weight: 700; }
.score-chip.pos  { background: rgba(74,222,128,.15); color: #4ade80; }
.score-chip.zero { background: rgba(255,255,255,.06); color: rgba(255,255,255,.35); }
.rule-chip { border-radius: 4px; padding: 2px 8px; font-size: .72rem; font-weight: 700; }
.rule-chip.blocking { background: rgba(239,68,68,.15); color: #f87171; }
.rule-chip.pass     { background: rgba(74,222,128,.12); color: #4ade80; }
.ch-condition code { font-family: monospace; font-size: .72rem; background: rgba(255,255,255,.06); padding: 2px 7px; border-radius: 4px; color: rgba(255,255,255,.45); }

.add-choice-row {
  display: flex; align-items: center; gap: 8px;
  padding-top: 10px; border-top: 1px dashed rgba(255,255,255,.08);
}
.add-input {
  background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1);
  border-radius: 7px; padding: 6px 10px; font-size: .82rem; color: #fff;
  outline: none; transition: border-color .15s;
}
.add-input::placeholder { color: rgba(255,255,255,.25); }
.add-input:focus { border-color: #E8622C; }
.add-input.flex-1 { flex: 1; }
.add-input.score-input { width: 80px; }
.blocking-toggle { display: flex; align-items: center; gap: 6px; font-size: .78rem; color: rgba(255,255,255,.45); white-space: nowrap; cursor: pointer; }
.blocking-toggle input[type="checkbox"] { accent-color: #E8622C; width: 14px; height: 14px; }
.btn-add {
  display: flex; align-items: center; gap: 6px;
  background: rgba(232,98,44,.2); border: 1px solid rgba(232,98,44,.3);
  border-radius: 7px; padding: 6px 14px; font-size: .8rem; font-weight: 600;
  color: #E8622C; cursor: pointer; transition: background .15s; white-space: nowrap;
}
.btn-add:hover { background: rgba(232,98,44,.35); }

.empty-choices { color: rgba(255,255,255,.25); font-size: .82rem; padding: 8px 0; text-align: center; }
.empty-criteria { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 40px; color: rgba(255,255,255,.2); font-size: .875rem; text-align: center; }

/* Loading */
.loading-state { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 80px; color: rgba(255,255,255,.3); }
.loading-sm { display: flex; align-items: center; gap: 8px; color: rgba(255,255,255,.3); font-size: .82rem; padding: 6px 0; }
.spinner { width: 20px; height: 20px; border: 2px solid rgba(255,255,255,.1); border-top-color: #E8622C; border-radius: 50%; animation: spin .7s linear infinite; }
.spinner-sm { width: 14px; height: 14px; border: 2px solid rgba(255,255,255,.1); border-top-color: #E8622C; border-radius: 50%; animation: spin .7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Buttons */
.btn-primary {
  display: flex; align-items: center; gap: 7px;
  background: linear-gradient(135deg,#E8622C,#ff8c5a);
  color: #fff; border: none; border-radius: 8px;
  padding: 9px 18px; cursor: pointer; font-weight: 600; font-size: .875rem;
  transition: opacity .15s; white-space: nowrap;
}
.btn-primary:hover { opacity: .9; }
.btn-primary:disabled { opacity: .4; cursor: default; }
.btn-ghost {
  background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1);
  color: rgba(255,255,255,.7); border-radius: 8px; padding: 8px 18px;
  cursor: pointer; font-size: .875rem; transition: background .15s;
}
.btn-ghost:hover { background: rgba(255,255,255,.1); color: #fff; }
.btn-danger-solid { background: rgba(239,68,68,.2); border: 1px solid rgba(239,68,68,.3); color: #f87171; border-radius: 8px; padding: 8px 18px; cursor: pointer; font-size: .875rem; font-weight: 600; transition: background .15s; }
.btn-danger-solid:hover { background: rgba(239,68,68,.35); }
.btn-danger-solid:disabled { opacity: .4; cursor: default; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.7); backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; z-index: 300; }
.modal { background: rgba(15,23,42,.97); border: 1px solid rgba(255,255,255,.1); border-radius: 16px; width: 540px; max-height: 90vh; display: flex; flex-direction: column; box-shadow: 0 32px 80px rgba(0,0,0,.6); }
.modal-sm { width: 400px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px 0; }
.modal-header h2 { font-size: 1.05rem; font-weight: 700; color: #fff; }
.close-btn { background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1); color: rgba(255,255,255,.5); cursor: pointer; width: 28px; height: 28px; border-radius: 7px; display: flex; align-items: center; justify-content: center; transition: all .15s; }
.close-btn:hover { background: rgba(255,255,255,.1); color: #fff; }
.modal-body { padding: 18px 24px; overflow-y: auto; flex: 1; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 14px 24px; border-top: 1px solid rgba(255,255,255,.07); }

.form-group { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
.form-group label { font-size: .8rem; font-weight: 600; color: rgba(255,255,255,.45); text-transform: uppercase; letter-spacing: .05em; }
.form-group input, .form-group select, .form-group textarea {
  background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1);
  border-radius: 8px; padding: 9px 12px; font-size: .9rem; color: #fff;
  outline: none; font-family: inherit; transition: border-color .15s;
}
.form-group input::placeholder, .form-group textarea::placeholder { color: rgba(255,255,255,.25); }
.form-group input:focus, .form-group select:focus, .form-group textarea:focus { border-color: #E8622C; }
.form-group select option { background: #0f172a; color: #fff; }
.form-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }

.del-msg { color: rgba(255,255,255,.75); margin-bottom: 8px; font-size: .9rem; }
.del-warn { color: rgba(239,68,68,.7); font-size: .82rem; }

/* Highlighted product */
.criterion-card.highlighted { box-shadow: 0 0 0 2px #E8622C; }
</style>
