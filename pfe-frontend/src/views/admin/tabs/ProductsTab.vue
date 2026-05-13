<template>
  <div class="products-page">

    <!-- Actions bar -->
    <div class="page-header">
      <div></div>
      <button class="btn-primary" @click="openProductForm()">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M7 1v12M1 7h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        New Product
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Loading products…</span>
    </div>

    <!-- Product list -->
    <div v-else class="product-list">
      <div v-if="!products.length" class="empty-state">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,.2)" stroke-width="1.5">
          <rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>
        </svg>
        <p>No products yet. Create your first product to get started.</p>
        <button class="btn-primary" @click="openProductForm()">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M7 1v12M1 7h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          New Product
        </button>
      </div>

      <div
        v-for="product in products"
        :key="product.id"
        :id="`product-${product.id}`"
        class="product-card"
        :class="{ highlighted: route.query.product === product.id }"
      >
        <!-- Product header row -->
        <div class="product-header">
          <div class="product-info">
            <span class="product-id">{{ product.id }}</span>
            <span class="product-name">{{ product.name }}</span>
          </div>
          <div class="product-actions">
            <button class="btn-sm btn-ghost criteria-toggle" @click="toggleCriteria(product.id)">
              <svg v-if="expanded !== product.id" width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <svg v-else width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M10 8L6 4 2 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Criteria
              <span class="badge">{{ criteriaCounts[product.id] ?? '…' }}</span>
            </button>
            <button class="btn-sm btn-ghost" @click="openProductForm(product)">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
              Edit
            </button>
            <button class="btn-sm btn-danger" @click="confirmDelete('product', product.id, product.name)">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
                <path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/>
              </svg>
              Delete
            </button>
          </div>
        </div>

        <!-- Criteria panel -->
        <div v-if="expanded === product.id" class="criteria-panel">
          <div class="criteria-toolbar">
            <span class="section-label">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,.5)" stroke-width="2" style="vertical-align:middle;margin-right:5px">
                <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
              </svg>
              Criteria
            </span>
            <button class="btn-sm btn-primary" @click="openCriterionForm(product.id)">
              <svg width="11" height="11" viewBox="0 0 14 14" fill="none">
                <path d="M7 1v12M1 7h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              Add Criterion
            </button>
          </div>

          <div v-if="criteriaLoading" class="loading-sm">
            <div class="spinner-sm"></div> Loading criteria…
          </div>
          <table v-else-if="criteria[product.id]?.length" class="table">
            <thead>
              <tr>
                <th>#</th>
                <th>Label</th>
                <th>Type</th>
                <th>Unit</th>
                <th>Choices</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in criteria[product.id]" :key="c.id">
                <td class="cell-order">{{ c.order }}</td>
                <td class="cell-label">{{ c.label }}</td>
                <td><span class="type-tag" :class="c.answer_type">{{ c.answer_type }}</span></td>
                <td class="cell-muted">{{ c.unit || '—' }}</td>
                <td>
                  <button class="btn-xs btn-ghost" @click="openChoicesModal(c)">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>
                    </svg>
                    Choices
                  </button>
                </td>
                <td class="actions-cell">
                  <button class="btn-xs btn-ghost" @click="openCriterionForm(product.id, c)">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                  <button class="btn-xs btn-danger" @click="confirmDelete('criterion', c.id, c.label)">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
                    </svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <p v-else class="empty-criteria">No criteria yet.</p>
        </div>
      </div>
    </div>

    <!-- ── Product form modal ── -->
    <div v-if="showProductForm" class="modal-overlay" @click.self="showProductForm = false">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editingProduct ? 'Edit Product' : 'New Product' }}</h2>
          <button class="close-btn" @click="showProductForm = false">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Product name</label>
            <input v-model="productForm.name" placeholder="e.g. CIR" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="showProductForm = false">Cancel</button>
          <button class="btn-primary" :disabled="saving" @click="saveProduct">
            <div v-if="saving" class="spinner-xs"></div>
            {{ saving ? 'Saving…' : 'Save' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── Criterion form modal ── -->
    <div v-if="showCriterionForm" class="modal-overlay" @click.self="showCriterionForm = false">
      <div class="modal modal-wide">
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
              <input v-model="criterionForm.unit" placeholder="e.g. personnes, €, MWh" />
            </div>
            <div class="form-group">
              <label>Order</label>
              <input v-model.number="criterionForm.order" type="number" min="1" />
            </div>
          </div>
          <div class="form-group">
            <label>Agent prompt <span class="label-hint">optional</span></label>
            <textarea v-model="criterionForm.agent_prompt" rows="3" placeholder="Custom prompt for the AI…"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="showCriterionForm = false">Cancel</button>
          <button class="btn-primary" :disabled="saving" @click="saveCriterion">
            <div v-if="saving" class="spinner-xs"></div>
            {{ saving ? 'Saving…' : 'Save' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── Choices modal ── -->
    <div v-if="showChoicesModal" class="modal-overlay" @click.self="showChoicesModal = false">
      <div class="modal modal-wide">
        <div class="modal-header">
          <div>
            <h2>Choices</h2>
            <p class="modal-sub">{{ choicesCriterion?.label }}</p>
          </div>
          <button class="close-btn" @click="showChoicesModal = false">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <!-- Column headers -->
          <div class="choices-header">
            <span class="ch-label-h">Label</span>
            <span class="ch-score-h">Score</span>
            <span class="ch-blocking-h">Blocking</span>
            <span></span>
          </div>
          <!-- Existing choices -->
          <div class="choices-list">
            <div v-for="ch in choices" :key="ch.id" class="choice-row">
              <input v-model="ch.label" class="choice-input" @blur="patchChoice(ch)" placeholder="Choice label" />
              <input v-model.number="ch.score" type="number" class="choice-score" @blur="patchChoice(ch)" />
              <label class="choice-blocking">
                <input type="checkbox" v-model="ch.is_blocking" @change="patchChoice(ch)" />
                <span class="blocking-track" :class="{ active: ch.is_blocking }">
                  <span class="blocking-dot"></span>
                </span>
              </label>
              <button class="btn-xs btn-danger" @click="removeChoice(ch.id)">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
                </svg>
              </button>
            </div>
            <p v-if="!choices.length" class="empty-criteria">No choices yet.</p>
          </div>

          <!-- Add new choice -->
          <div class="choices-add">
            <input v-model="newChoice.label" placeholder="New choice label" class="choice-input" />
            <input v-model.number="newChoice.score" type="number" placeholder="Score" class="choice-score" />
            <label class="choice-blocking">
              <input type="checkbox" v-model="newChoice.is_blocking" />
              <span class="blocking-track" :class="{ active: newChoice.is_blocking }">
                <span class="blocking-dot"></span>
              </span>
            </label>
            <button class="btn-sm btn-primary" @click="addChoice">
              <svg width="11" height="11" viewBox="0 0 14 14" fill="none">
                <path d="M7 1v12M1 7h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              Add
            </button>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="showChoicesModal = false">Close</button>
        </div>
      </div>
    </div>

    <!-- ── Delete confirm modal ── -->
    <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
      <div class="modal modal-sm">
        <div class="modal-header">
          <h2>Confirm Delete</h2>
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
          <p class="delete-msg">Delete <strong>{{ deleteTarget.name }}</strong>?</p>
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
import { ref, inject, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import api from '../../../services/api'

const route = useRoute()
const notify = inject('notify', { success: () => {}, error: () => {} })

const products       = ref([])
const criteria       = ref({})
const criteriaCounts = ref({})
const choices        = ref([])
const loading        = ref(false)
const criteriaLoading= ref(false)
const saving         = ref(false)
const expanded       = ref(null)

const showProductForm  = ref(false)
const showCriterionForm= ref(false)
const showChoicesModal = ref(false)
const deleteTarget     = ref(null)

const editingProduct   = ref(null)
const editingCriterion = ref(null)
const choicesCriterion = ref(null)
const currentProductId = ref(null)

const productForm   = ref({ name: '' })
const criterionForm = ref({ label: '', answer_type: 'single_choice', unit: '', order: 1, agent_prompt: '' })
const newChoice     = ref({ label: '', score: 0, is_blocking: false })

async function loadProducts() {
  loading.value = true
  try {
    const { data } = await api.admin.listProducts()
    products.value = data
    for (const p of data) {
      const { data: crit } = await api.admin.listCriteria(p.id)
      criteriaCounts.value[p.id] = crit.length
    }
  } finally {
    loading.value = false
  }
}

async function toggleCriteria(productId) {
  if (expanded.value === productId) { expanded.value = null; return }
  expanded.value = productId
  criteriaLoading.value = true
  try {
    const { data } = await api.admin.listCriteria(productId)
    criteria.value[productId] = data
  } finally {
    criteriaLoading.value = false
  }
}

function openProductForm(product = null) {
  editingProduct.value = product
  productForm.value = { name: product?.name || '' }
  showProductForm.value = true
}

async function saveProduct() {
  if (!productForm.value.name.trim()) return
  saving.value = true
  try {
    if (editingProduct.value) {
      await api.admin.updateProduct(editingProduct.value.id, productForm.value)
      notify.success('Product updated successfully')
    } else {
      await api.admin.createProduct(productForm.value)
      notify.success('Product created successfully')
    }
    showProductForm.value = false
    await loadProducts()
  } catch (err) {
    notify.error(err?.response?.data?.detail || 'Failed to save product')
  } finally {
    saving.value = false
  }
}

function openCriterionForm(productId, criterion = null) {
  currentProductId.value = productId
  editingCriterion.value = criterion
  criterionForm.value = {
    label:        criterion?.label || '',
    answer_type:  criterion?.answer_type || 'single_choice',
    unit:         criterion?.unit || '',
    order:        criterion?.order || 1,
    agent_prompt: criterion?.agent_prompt || '',
  }
  showCriterionForm.value = true
}

async function saveCriterion() {
  if (!criterionForm.value.label.trim()) return
  saving.value = true
  try {
    if (editingCriterion.value) {
      await api.admin.updateCriterion(editingCriterion.value.id, criterionForm.value)
      notify.success('Criterion updated')
    } else {
      await api.admin.createCriterion(currentProductId.value, criterionForm.value)
      notify.success('Criterion created')
    }
    showCriterionForm.value = false
    const { data } = await api.admin.listCriteria(currentProductId.value)
    criteria.value[currentProductId.value] = data
    criteriaCounts.value[currentProductId.value] = data.length
  } catch (err) {
    notify.error(err?.response?.data?.detail || 'Failed to save criterion')
  } finally {
    saving.value = false
  }
}

async function openChoicesModal(criterion) {
  choicesCriterion.value = criterion
  const { data } = await api.admin.listChoices(criterion.id)
  choices.value = data
  newChoice.value = { label: '', score: 0, is_blocking: false }
  showChoicesModal.value = true
}

async function addChoice() {
  if (!newChoice.value.label.trim()) return
  try {
    const { data } = await api.admin.createChoice(choicesCriterion.value.id, newChoice.value)
    choices.value.push(data)
    newChoice.value = { label: '', score: 0, is_blocking: false }
    notify.success('Choice added')
  } catch (err) {
    notify.error(err?.response?.data?.detail || 'Failed to add choice')
  }
}

async function patchChoice(choice) {
  try {
    await api.admin.updateChoice(choice.id, {
      label: choice.label, score: choice.score, is_blocking: choice.is_blocking,
    })
    notify.success('Choice saved')
  } catch (err) {
    notify.error(err?.response?.data?.detail || 'Failed to update choice')
  }
}

async function removeChoice(choiceId) {
  try {
    await api.admin.deleteChoice(choiceId)
    choices.value = choices.value.filter(c => c.id !== choiceId)
    notify.success('Choice deleted')
  } catch (err) {
    notify.error(err?.response?.data?.detail || 'Failed to delete choice')
  }
}

function confirmDelete(type, id, name) {
  deleteTarget.value = { type, id, name }
}

async function executeDelete() {
  saving.value = true
  try {
    const { type, id, name } = deleteTarget.value
    if (type === 'product')   await api.admin.deleteProduct(id)
    if (type === 'criterion') await api.admin.deleteCriterion(id)
    deleteTarget.value = null
    notify.success(`${type === 'product' ? 'Product' : 'Criterion'} deleted`)
    await loadProducts()
    expanded.value = null
  } catch (err) {
    notify.error(err?.response?.data?.detail || 'Failed to delete')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadProducts()
  if (route.query.product) {
    const pid = route.query.product
    await toggleCriteria(pid)
    setTimeout(() => {
      const el = document.getElementById(`product-${pid}`)
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 100)
  }
})
</script>

<style scoped>
*, *::before, *::after { box-sizing: border-box; }
.products-page { font-family: Inter, sans-serif; color: #fff; }

/* ── Header ── */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}
h1 { font-size: 1.5rem; font-weight: 700; color: #fff; margin: 0 0 4px; }
.page-sub { font-size: .85rem; color: rgba(255,255,255,.4); margin: 0; }

/* ── Loading ── */
.loading-state {
  display: flex; align-items: center; justify-content: center;
  gap: 12px; padding: 60px; color: rgba(255,255,255,.4);
}
.loading-sm {
  display: flex; align-items: center; gap: 8px;
  padding: 20px; color: rgba(255,255,255,.4); font-size: .875rem;
}

/* ── Spinners ── */
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

/* ── Empty state ── */
.empty-state {
  text-align: center;
  padding: 60px 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  color: rgba(255,255,255,.4);
}
.empty-state p { font-size: .9rem; margin: 0; }
.empty-criteria {
  color: rgba(255,255,255,.25);
  font-size: .875rem;
  text-align: center;
  padding: 20px 0;
  margin: 0;
}

/* ── Product list ── */
.product-list { display: flex; flex-direction: column; gap: 10px; }

.product-card {
  background: rgba(255,255,255,.04);
  border: 1px solid rgba(255,255,255,.08);
  backdrop-filter: blur(12px);
  border-radius: 12px;
  overflow: hidden;
  transition: border-color .2s;
}
.product-card:hover { border-color: rgba(255,255,255,.14); }

.product-card.highlighted {
  border-color: #3b82f6;
  box-shadow: 0 0 0 1px rgba(59,130,246,.3), 0 0 24px rgba(59,130,246,.12);
  animation: highlight-fade 2.5s ease forwards;
}
@keyframes highlight-fade {
  0%   { border-color: #3b82f6; box-shadow: 0 0 0 1px rgba(59,130,246,.4), 0 0 24px rgba(59,130,246,.2); }
  100% { border-color: rgba(255,255,255,.08); box-shadow: none; }
}

/* ── Product header ── */
.product-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
}
.product-info { display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0; }
.product-id {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: .78rem;
  color: rgba(255,255,255,.3);
  background: rgba(255,255,255,.04);
  border: 1px solid rgba(255,255,255,.07);
  border-radius: 5px;
  padding: 2px 7px;
  white-space: nowrap;
  flex-shrink: 0;
}
.product-name { font-weight: 600; color: #fff; font-size: .95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.product-actions { display: flex; gap: 7px; align-items: center; flex-shrink: 0; }

/* ── Criteria panel ── */
.criteria-panel {
  border-top: 1px solid rgba(255,255,255,.06);
  padding: 16px 20px;
  background: rgba(0,0,0,.12);
}
.criteria-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.section-label {
  font-size: .82rem;
  font-weight: 600;
  color: rgba(255,255,255,.5);
  text-transform: uppercase;
  letter-spacing: .06em;
}

/* ── Table ── */
.table {
  width: 100%;
  border-collapse: collapse;
  font-size: .875rem;
}
.table thead tr { background: rgba(255,255,255,.03); }
.table th {
  text-align: left;
  padding: 8px 10px;
  font-size: .72rem;
  font-weight: 700;
  color: rgba(255,255,255,.4);
  text-transform: uppercase;
  letter-spacing: .06em;
  border-bottom: 1px solid rgba(255,255,255,.06);
}
.table td {
  padding: 10px 10px;
  color: rgba(255,255,255,.8);
  border-bottom: 1px solid rgba(255,255,255,.05);
  vertical-align: middle;
}
.table tr:last-child td { border-bottom: none; }
.table tbody tr:hover td { background: rgba(255,255,255,.025); }

.cell-order { color: rgba(255,255,255,.3); font-size: .82rem; width: 36px; }
.cell-label { font-weight: 500; color: #fff; }
.cell-muted { color: rgba(255,255,255,.3); font-size: .82rem; }
.actions-cell { display: flex; gap: 4px; }

/* ── Type tags ── */
.type-tag {
  border-radius: 5px;
  padding: 2px 8px;
  font-size: .72rem;
  font-weight: 700;
  white-space: nowrap;
}
.type-tag.single_choice   { background: rgba(59,130,246,.18);  color: #60a5fa; }
.type-tag.numeric         { background: rgba(232,98,44,.18);   color: #fb923c; }
.type-tag.multiple_choice { background: rgba(168,85,247,.18);  color: #c084fc; }
.type-tag.text            { background: rgba(34,197,94,.18);   color: #4ade80; }

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
  color: #fff; border-radius: 7px; padding: 7px 13px;
  cursor: pointer; font-size: .875rem; transition: background .15s;
  white-space: nowrap;
}
.btn-ghost:hover { background: rgba(255,255,255,.1); }

.btn-danger {
  display: inline-flex; align-items: center; gap: 5px;
  background: rgba(239,68,68,.15); border: 1px solid rgba(239,68,68,.3);
  color: #f87171; border-radius: 7px; padding: 7px 13px;
  cursor: pointer; font-size: .875rem; font-weight: 600;
  transition: background .15s; white-space: nowrap;
}
.btn-danger:hover { background: rgba(239,68,68,.25); }
.btn-danger:disabled { opacity: .45; cursor: default; }

/* sm / xs variants */
.btn-sm { padding: 5px 10px; font-size: .8rem; border-radius: 6px; }
.btn-xs { padding: 4px 8px; font-size: .75rem; border-radius: 5px; }
.btn-sm.btn-primary { background: linear-gradient(135deg, #E8622C, #ff8c5a); border: none; color: #fff; }
.btn-sm.btn-ghost   { background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1); color: #fff; }
.btn-sm.btn-ghost:hover { background: rgba(255,255,255,.1); }
.btn-sm.btn-danger  { background: rgba(239,68,68,.15); border: 1px solid rgba(239,68,68,.3); color: #f87171; }
.btn-xs.btn-ghost   { background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1); color: rgba(255,255,255,.8); }
.btn-xs.btn-ghost:hover { background: rgba(255,255,255,.1); }
.btn-xs.btn-danger  { background: rgba(239,68,68,.15); border: 1px solid rgba(239,68,68,.3); color: #f87171; }
.criteria-toggle { gap: 6px; }

/* Badge */
.badge {
  background: rgba(255,255,255,.1);
  color: rgba(255,255,255,.6);
  border-radius: 20px;
  padding: 1px 7px;
  font-size: .7rem;
  font-weight: 600;
  margin-left: 2px;
}

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
  width: 460px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 80px rgba(0,0,0,.6);
}
.modal-wide { width: 620px; }
.modal-sm   { width: 360px; }

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px 24px 0;
}
.modal-header h2 { font-size: 1.1rem; font-weight: 700; color: #fff; margin: 0; }
.modal-sub { font-size: .82rem; color: rgba(255,255,255,.4); margin: 4px 0 0; }
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
.form-group { display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px; }
.form-group label {
  font-size: .82rem;
  font-weight: 600;
  color: rgba(255,255,255,.55);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.label-hint { font-weight: 400; color: rgba(255,255,255,.3); font-size: .75rem; }

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

/* ── Delete modal specifics ── */
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

/* ── Choices ── */
.choices-header {
  display: grid;
  grid-template-columns: 1fr 80px 80px 40px;
  gap: 8px;
  padding: 0 0 6px;
  margin-bottom: 8px;
  border-bottom: 1px solid rgba(255,255,255,.07);
}
.ch-label-h, .ch-score-h, .ch-blocking-h {
  font-size: .72rem;
  font-weight: 700;
  color: rgba(255,255,255,.35);
  text-transform: uppercase;
  letter-spacing: .06em;
}
.ch-blocking-h { text-align: center; }

.choices-list { display: flex; flex-direction: column; gap: 7px; margin-bottom: 14px; }
.choice-row {
  display: grid;
  grid-template-columns: 1fr 80px 80px 40px;
  gap: 8px;
  align-items: center;
}
.choice-input {
  background: rgba(255,255,255,.05);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 7px;
  padding: 7px 10px;
  font-size: .875rem;
  color: #fff;
  outline: none;
  color-scheme: dark;
  transition: border-color .15s;
  width: 100%;
}
.choice-input::placeholder { color: rgba(255,255,255,.3); }
.choice-input:focus { border-color: #E8622C; }
.choice-score {
  background: rgba(255,255,255,.05);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 7px;
  padding: 7px 10px;
  font-size: .875rem;
  color: #fff;
  outline: none;
  color-scheme: dark;
  transition: border-color .15s;
  width: 100%;
  text-align: center;
}
.choice-score::placeholder { color: rgba(255,255,255,.3); }
.choice-score:focus { border-color: #E8622C; }

/* Pill toggle for blocking */
.choice-blocking { display: flex; align-items: center; justify-content: center; cursor: pointer; }
.choice-blocking input[type="checkbox"] { display: none; }
.blocking-track {
  width: 32px; height: 18px;
  background: rgba(255,255,255,.1);
  border: 1px solid rgba(255,255,255,.15);
  border-radius: 9px;
  position: relative;
  transition: background .2s, border-color .2s;
  cursor: pointer;
}
.blocking-track.active { background: rgba(232,98,44,.4); border-color: #E8622C; }
.blocking-dot {
  position: absolute;
  top: 2px; left: 2px;
  width: 12px; height: 12px;
  background: rgba(255,255,255,.5);
  border-radius: 50%;
  transition: transform .2s, background .2s;
}
.blocking-track.active .blocking-dot {
  transform: translateX(14px);
  background: #fff;
}

.choices-add {
  display: grid;
  grid-template-columns: 1fr 80px 80px auto;
  gap: 8px;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid rgba(255,255,255,.07);
}

/* ══ LIGHT MODE ══════════════════════════════ */
[data-theme="light"] .products-page { color: #0D1B2E; }
[data-theme="light"] h1             { color: #0D1B2E; }
[data-theme="light"] .page-sub      { color: #3D5068; }

/* Criteria count badge */
[data-theme="light"] .badge {
  background: rgba(232,98,44,0.12);
  color: #E8622C;
}

/* Product cards */
[data-theme="light"] .product-card {
  background: #FFFFFF;
  border-color: rgba(13,27,46,0.09);
  box-shadow: 0 2px 8px rgba(13,27,46,0.06);
  backdrop-filter: none;
}
[data-theme="light"] .product-card:hover { border-color: rgba(232,98,44,0.25); }
[data-theme="light"] .product-name { color: #0D1B2E; }

/* Criteria panel */
[data-theme="light"] .criteria-panel {
  background: rgba(13,27,46,0.03);
  border-top-color: rgba(13,27,46,0.08);
}
[data-theme="light"] .section-label { color: #7C93AE; }

/* Criteria table */
[data-theme="light"] .table thead tr   { background: rgba(13,27,46,0.04); }
[data-theme="light"] .table th {
  color: #7C93AE;
  border-bottom-color: rgba(13,27,46,0.08);
}
[data-theme="light"] .table td {
  color: #0D1B2E;
  border-bottom-color: rgba(13,27,46,0.06);
}
[data-theme="light"] .table tbody tr:hover td { background: rgba(13,27,46,0.03); }
[data-theme="light"] .cell-order { color: #7C93AE; }
[data-theme="light"] .cell-label { color: #0D1B2E; }
[data-theme="light"] .cell-muted { color: #7C93AE; }

/* Buttons */
[data-theme="light"] .btn-ghost {
  background: rgba(13,27,46,0.05);
  border-color: rgba(13,27,46,0.15);
  color: #3D5068;
}
[data-theme="light"] .btn-ghost:hover { background: rgba(13,27,46,0.10); color: #0D1B2E; }
[data-theme="light"] .btn-sm.btn-ghost { background: rgba(13,27,46,0.05); border-color: rgba(13,27,46,0.15); color: #3D5068; }
[data-theme="light"] .btn-xs.btn-ghost { background: rgba(13,27,46,0.05); border-color: rgba(13,27,46,0.12); color: #3D5068; }
[data-theme="light"] .btn-sm.btn-ghost:hover,
[data-theme="light"] .btn-xs.btn-ghost:hover { background: rgba(13,27,46,0.10); color: #0D1B2E; }

/* Modal */
[data-theme="light"] .modal {
  background: #FFFFFF;
  border-color: rgba(13,27,46,0.12);
  box-shadow: 0 24px 64px rgba(13,27,46,0.15);
}
[data-theme="light"] .modal-header {
  background: #FFFFFF;
  padding-bottom: 16px;
  border-radius: 14px 14px 0 0;
  border-bottom: 1px solid rgba(13,27,46,0.08);
}
[data-theme="light"] .modal-header h2 { color: #0D1B2E; }
[data-theme="light"] .modal-sub       { color: #3D5068; }
[data-theme="light"] .close-btn {
  background: transparent;
  border: none;
  color: #7C93AE;
}
[data-theme="light"] .close-btn:hover { background: rgba(13,27,46,0.06); color: #0D1B2E; }
[data-theme="light"] .modal-footer { border-top-color: rgba(13,27,46,0.08); }

/* Forms */
[data-theme="light"] .form-group label { color: #3D5068; }
[data-theme="light"] .label-hint       { color: #7C93AE; }
[data-theme="light"] .form-group input,
[data-theme="light"] .form-group select,
[data-theme="light"] .form-group textarea {
  background: #F8FAFC;
  border-color: rgba(13,27,46,0.15);
  color: #0D1B2E;
  color-scheme: light;
}
[data-theme="light"] .form-group input::placeholder,
[data-theme="light"] .form-group textarea::placeholder { color: #94A3B8; }
[data-theme="light"] .form-group select option { background: #FFFFFF; color: #0D1B2E; }

/* Choice inputs */
[data-theme="light"] .choice-input,
[data-theme="light"] .choice-score { background: #F8FAFC; border-color: rgba(13,27,46,0.15); color: #0D1B2E; }
[data-theme="light"] .choices-add  { border-top-color: rgba(13,27,46,0.08); }

/* Delete message */
[data-theme="light"] .delete-msg        { color: #3D5068; }
[data-theme="light"] .delete-msg strong { color: #0D1B2E; }
</style>
