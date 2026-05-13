<template>
  <AppLayout title="Rapports" subtitle="Historique de tous les rapports PDF générés et téléchargés">

    <!-- Toolbar -->
    <div class="toolbar">
      <div class="search-wrap">
        <svg width="14" height="14" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="2" viewBox="0 0 24 24">
          <circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/>
        </svg>
        <input v-model="search" placeholder="Rechercher un client…" class="search-input" />
      </div>
      <div class="stat-pills">
        <span class="stat-pill total">{{ history.length }} rapport{{ history.length > 1 ? 's' : '' }}</span>
        <span class="stat-pill eligible">{{ eligibleTotal }} éligibles au total</span>
      </div>
      <button class="refresh-btn" @click="loadHistory" :disabled="loading">
        <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"
          :class="{ spinning: loading }">
          <path d="M23 4v6h-6"/><path d="M1 20v-6h6"/>
          <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
        </svg>
        Actualiser
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-center">
      <div class="loading-spinner"></div>
      <span>Chargement de l'historique…</span>
    </div>

    <!-- Empty -->
    <div v-else-if="filtered.length === 0 && !search" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="1.5" viewBox="0 0 24 24">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
        </svg>
      </div>
      <p class="empty-title">Aucun rapport enregistré</p>
      <p class="empty-sub">Chaque PDF téléchargé depuis la page de scoring apparaîtra ici automatiquement.</p>
      <RouterLink to="/search" class="empty-cta">
        <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>
        Lancer un scoring
      </RouterLink>
    </div>

    <!-- No search results -->
    <div v-else-if="filtered.length === 0" class="empty-state">
      <p class="empty-title">Aucun résultat pour "{{ search }}"</p>
    </div>

    <!-- Reports list -->
    <div v-else class="reports-list">
      <div v-for="r in paged" :key="r.id" class="report-card">

        <!-- Left: avatar + client info -->
        <div class="rc-left">
          <div class="rc-avatar">{{ initials(r.client_name) }}</div>
          <div class="rc-client">
            <div class="rc-name">{{ r.client_name }}</div>
            <div class="rc-sub">
              <span class="rc-id">{{ r.client_id }}</span>
              <span v-if="r.sector" class="rc-sector">{{ r.sector.slice(0, 40) }}{{ r.sector.length > 40 ? '…' : '' }}</span>
            </div>
          </div>
        </div>

        <!-- Center: score pills -->
        <div class="rc-scores">
          <div class="score-pill eligible">
            <span class="sp-val">{{ r.eligible_count }}</span>
            <span class="sp-lbl">Éligibles</span>
          </div>
          <div class="score-pill review">
            <span class="sp-val">{{ r.to_review_count }}</span>
            <span class="sp-lbl">À revoir</span>
          </div>
          <div class="score-pill not-elig">
            <span class="sp-val">{{ r.not_eligible_count }}</span>
            <span class="sp-lbl">Non élig.</span>
          </div>
          <div class="score-pill total">
            <span class="sp-val">{{ r.products_scored }}</span>
            <span class="sp-lbl">Produits</span>
          </div>
        </div>

        <!-- Progress bar -->
        <div class="rc-bar-col">
          <div class="rc-bar">
            <div class="bar-seg eligible" :style="{ width: pct(r.eligible_count, r.products_scored) + '%' }"></div>
            <div class="bar-seg review"   :style="{ width: pct(r.to_review_count, r.products_scored) + '%' }"></div>
          </div>
          <div class="rc-bar-label">{{ Math.round(pct(r.eligible_count, r.products_scored)) }}% éligible</div>
        </div>

        <!-- Right: date + actions -->
        <div class="rc-right">
          <div class="rc-meta">
            <div class="rc-date">
              <svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
              </svg>
              {{ formatDate(r.downloaded_at) }}
            </div>
            <div class="rc-user">
              <svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>
              </svg>
              {{ r.user }}
            </div>
            <div class="rc-duration">
              <svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
              </svg>
              {{ r.duration_seconds }}s d'analyse
            </div>
          </div>
          <div class="rc-actions">
            <!-- PDF exists on server → direct re-download -->
            <button
              v-if="r.has_pdf"
              class="btn-download"
              @click="redownload(r)"
              :disabled="downloading === r.id"
              :title="`Télécharger ${r.filename}`"
            >
              <svg v-if="downloading !== r.id" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              <span v-else class="mini-spin"></span>
              Télécharger PDF
            </button>

            <!-- No PDF stored → show tooltip explaining why -->
            <div v-else class="no-pdf-wrap">
              <span class="no-pdf-badge" title="Ce rapport a été généré avant la sauvegarde automatique. Refaites le scoring du client pour obtenir un nouveau PDF.">
                <svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                PDF non sauvegardé
              </span>
            </div>

            <button class="btn-delete" @click="confirmDelete(r)" title="Supprimer ce rapport">
              <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/>
              </svg>
            </button>
          </div>
        </div>

      </div>

      <Pagination
        v-model:page="page"
        v-model:perPage="perPage"
        :total="filtered.length"
        :per-page-options="[10, 20, 50]"
      />
    </div>

    <!-- Delete confirmation modal -->
    <div v-if="deleteTarget" class="modal-backdrop" @click.self="deleteTarget = null">
      <div class="modal-confirm">
        <div class="modal-confirm-title">Supprimer ce rapport ?</div>
        <div class="modal-confirm-sub">
          Le rapport de <b>{{ deleteTarget.client_name }}</b> du {{ formatDate(deleteTarget.downloaded_at) }} sera définitivement supprimé.
        </div>
        <div class="modal-confirm-actions">
          <button class="btn-cancel" @click="deleteTarget = null">Annuler</button>
          <button class="btn-confirm-delete" @click="doDelete">Supprimer</button>
        </div>
      </div>
    </div>

  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { RouterLink } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import Pagination from '../components/Pagination.vue'
import api from '../services/api'

const history     = ref([])
const loading     = ref(false)
const search      = ref('')
const downloading = ref(null)
const deleteTarget= ref(null)
const page        = ref(1)
const perPage     = ref(10)

const filtered = computed(() => {
  if (!search.value) return history.value
  const q = search.value.toLowerCase()
  return history.value.filter(r =>
    r.client_name?.toLowerCase().includes(q) ||
    r.client_id?.toLowerCase().includes(q) ||
    r.sector?.toLowerCase().includes(q) ||
    r.user?.toLowerCase().includes(q)
  )
})

watch(search, () => { page.value = 1 })

const paged = computed(() => {
  const start = (page.value - 1) * perPage.value
  return filtered.value.slice(start, start + perPage.value)
})

const eligibleTotal = computed(() =>
  history.value.reduce((s, r) => s + (r.eligible_count || 0), 0)
)

async function loadHistory() {
  loading.value = true
  try {
    const res = await api.getReportHistory()
    history.value = res.data || []
  } catch (e) {
    console.error('Failed to load report history', e)
  } finally {
    loading.value = false
  }
}

async function redownload(r) {
  downloading.value = r.id
  try {
    const res = await api.redownloadPdf(r.id)
    const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
    const a   = document.createElement('a')
    a.href     = url
    a.download = r.filename || `sellynx_${r.client_name}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    alert('Impossible de télécharger ce rapport.')
    console.error(e)
  } finally {
    downloading.value = null
  }
}

function confirmDelete(r) { deleteTarget.value = r }

async function doDelete() {
  if (!deleteTarget.value) return
  try {
    await api.deleteReport(deleteTarget.value.id)
    history.value = history.value.filter(r => r.id !== deleteTarget.value.id)
  } catch (e) { console.error(e) }
  finally { deleteTarget.value = null }
}

function initials(name) {
  return (name || '').split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase() || '?'
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('fr-FR', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function pct(count, total) {
  return total ? Math.min(100, Math.round((count / total) * 100)) : 0
}

onMounted(loadHistory)
</script>

<style scoped>
/* ── Toolbar ── */
.toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; }
.search-wrap { display: flex; align-items: center; gap: 8px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 9px 14px; flex: 1; min-width: 200px; }
.search-input { background: none; border: none; outline: none; color: #fff; font-size: 13px; width: 100%; }
.search-input::placeholder { color: rgba(255,255,255,0.25); }
.stat-pills { display: flex; gap: 8px; }
.stat-pill { font-size: 12px; font-weight: 600; padding: 5px 12px; border-radius: 99px; border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.04); color: rgba(255,255,255,0.5); }
.stat-pill.eligible { background: rgba(34,197,94,0.08); color: #22c55e; border-color: rgba(34,197,94,0.2); }
.refresh-btn { display: flex; align-items: center; gap: 7px; padding: 8px 14px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 9px; color: rgba(255,255,255,0.5); font-size: 12.5px; cursor: pointer; transition: all 0.18s; }
.refresh-btn:hover { color: #fff; }
.spinning { animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Loading / Empty ── */
.loading-center { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 80px 0; color: rgba(255,255,255,0.4); font-size: 14px; }
.loading-spinner { width: 20px; height: 20px; border: 2px solid rgba(255,255,255,0.1); border-top-color: #E8622C; border-radius: 50%; animation: spin 0.7s linear infinite; }
.empty-state { display: flex; flex-direction: column; align-items: center; gap: 14px; padding: 80px 20px; text-align: center; }
.empty-icon { width: 90px; height: 90px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 24px; display: flex; align-items: center; justify-content: center; }
.empty-title { font-size: 18px; font-weight: 700; color: rgba(255,255,255,0.5); }
.empty-sub { font-size: 13px; color: rgba(255,255,255,0.3); max-width: 360px; line-height: 1.6; }
.empty-cta { display: flex; align-items: center; gap: 8px; padding: 10px 22px; background: linear-gradient(135deg, #E8622C, #ff7a45); border-radius: 10px; color: #fff; font-size: 13px; font-weight: 700; text-decoration: none; transition: all 0.2s; }
.empty-cta:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(232,98,44,0.35); }

/* ── Reports list ── */
.reports-list { display: flex; flex-direction: column; gap: 10px; }

/* ── Report card ── */
.report-card { display: flex; align-items: center; gap: 20px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-radius: 14px; padding: 18px 20px; transition: all 0.2s; flex-wrap: wrap; }
.report-card:hover { background: rgba(255,255,255,0.05); border-color: rgba(232,98,44,0.15); }

/* Left */
.rc-left { display: flex; align-items: center; gap: 12px; min-width: 220px; flex: 1.2; }
.rc-avatar { width: 42px; height: 42px; border-radius: 11px; flex-shrink: 0; background: linear-gradient(135deg, #1B2A4A, #2d4270); border: 1px solid rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 800; color: #fff; }
.rc-client { min-width: 0; }
.rc-name { font-size: 14px; font-weight: 700; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rc-sub { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 3px; }
.rc-id { font-size: 10px; color: rgba(255,255,255,0.25); font-family: monospace; }
.rc-sector { font-size: 11px; color: rgba(232,98,44,0.6); }

/* Score pills */
.rc-scores { display: flex; gap: 6px; flex-shrink: 0; }
.score-pill { display: flex; flex-direction: column; align-items: center; padding: 6px 10px; border-radius: 9px; border: 1px solid; min-width: 52px; }
.score-pill.eligible   { background: rgba(34,197,94,0.08);  border-color: rgba(34,197,94,0.2);  }
.score-pill.review     { background: rgba(245,158,11,0.08); border-color: rgba(245,158,11,0.2); }
.score-pill.not-elig   { background: rgba(239,68,68,0.06);  border-color: rgba(239,68,68,0.15); }
.score-pill.total      { background: rgba(255,255,255,0.04);border-color: rgba(255,255,255,0.1);}
.sp-val { font-size: 18px; font-weight: 800; color: #fff; line-height: 1.2; }
.score-pill.eligible   .sp-val { color: #22c55e; }
.score-pill.review     .sp-val { color: #f59e0b; }
.score-pill.not-elig   .sp-val { color: #f87171; }
.sp-lbl { font-size: 9px; color: rgba(255,255,255,0.35); text-transform: uppercase; letter-spacing: 0.3px; }

/* Bar */
.rc-bar-col { flex: 1; min-width: 100px; }
.rc-bar { height: 5px; background: rgba(255,255,255,0.06); border-radius: 99px; overflow: hidden; display: flex; margin-bottom: 5px; }
.bar-seg { height: 100%; }
.bar-seg.eligible { background: #22c55e; }
.bar-seg.review   { background: #f59e0b; }
.rc-bar-label { font-size: 11px; font-weight: 700; color: #22c55e; }

/* Right */
.rc-right { display: flex; flex-direction: column; gap: 10px; align-items: flex-end; flex-shrink: 0; }
.rc-meta { display: flex; flex-direction: column; gap: 4px; align-items: flex-end; }
.rc-date, .rc-user, .rc-duration { display: flex; align-items: center; gap: 5px; font-size: 11px; color: rgba(255,255,255,0.35); }
.rc-actions { display: flex; align-items: center; gap: 8px; }

.btn-download { display: flex; align-items: center; gap: 6px; padding: 7px 14px; background: linear-gradient(135deg, #1B2A4A, #243558); border: 1px solid rgba(232,98,44,0.3); border-radius: 8px; color: #fff; font-size: 12.5px; font-weight: 600; cursor: pointer; transition: all 0.18s; white-space: nowrap; }
.btn-download:hover:not(:disabled) { background: linear-gradient(135deg, #E8622C, #ff7a45); border-color: transparent; box-shadow: 0 4px 14px rgba(232,98,44,0.3); }
.btn-download:disabled { opacity: 0.5; cursor: not-allowed; }
.mini-spin { display: inline-block; width: 12px; height: 12px; border: 2px solid rgba(255,255,255,0.2); border-top-color: #fff; border-radius: 50%; animation: spin 0.7s linear infinite; }

.no-pdf-wrap { display: flex; align-items: center; }
.no-pdf-badge { display: flex; align-items: center; gap: 4px; font-size: 11px; color: rgba(255,255,255,0.25); font-style: italic; cursor: help; padding: 4px 8px; border: 1px dashed rgba(255,255,255,0.1); border-radius: 6px; }

.btn-delete { display: flex; align-items: center; justify-content: center; width: 30px; height: 30px; background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.2); border-radius: 7px; color: rgba(239,68,68,0.6); cursor: pointer; transition: all 0.18s; }
.btn-delete:hover { background: rgba(239,68,68,0.15); color: #f87171; border-color: rgba(239,68,68,0.4); }

/* ── Delete modal ── */
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); z-index: 1000; display: flex; align-items: center; justify-content: center; }
.modal-confirm { background: #0d1f38; border: 1px solid rgba(255,255,255,0.12); border-radius: 16px; padding: 28px; max-width: 380px; width: 90%; }
.modal-confirm-title { font-size: 17px; font-weight: 700; color: #fff; margin-bottom: 10px; }
.modal-confirm-sub { font-size: 13px; color: rgba(255,255,255,0.5); line-height: 1.6; margin-bottom: 24px; }
.modal-confirm-sub b { color: rgba(255,255,255,0.8); }
.modal-confirm-actions { display: flex; gap: 10px; justify-content: flex-end; }
.btn-cancel { padding: 8px 18px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; color: rgba(255,255,255,0.6); font-size: 13px; cursor: pointer; transition: all 0.18s; }
.btn-cancel:hover { color: #fff; }
.btn-confirm-delete { padding: 8px 18px; background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.3); border-radius: 8px; color: #f87171; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.18s; }
.btn-confirm-delete:hover { background: rgba(239,68,68,0.25); }
</style>
