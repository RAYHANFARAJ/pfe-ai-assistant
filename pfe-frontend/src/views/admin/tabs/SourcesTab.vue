<template>
  <div class="sources-page">

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div><span>Loading…</span>
    </div>

    <template v-else>

      <!-- ── Section 1: Pipeline Tools ── -->
      <div class="section-card">
      <div class="section-header">
        <div class="section-title-wrap">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="rgba(232,98,44,.8)" stroke-width="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
          <h2>Scoring Pipeline</h2>
        </div>
        <p class="section-sub">These 5 tools run in parallel on every scoring request. Toggle to enable or disable each one.</p>
      </div>

      <!-- Pipeline flow visual -->
      <div class="pipeline-flow">
        <template v-for="(tool, i) in pipelineTools" :key="tool.id">
          <div class="flow-node" :class="{ off: !tool.enabled }">
            <div class="flow-icon" :class="tool.tool_key">
              <span v-html="getIcon(tool.tool_key)"></span>
            </div>
            <span class="flow-label">{{ tool.label }}</span>
            <span class="flow-status" :class="tool.enabled ? 'on' : 'off'">
              {{ tool.enabled ? 'ON' : 'OFF' }}
            </span>
          </div>
          <div v-if="i < pipelineTools.length - 1" class="flow-arrow">
            <svg width="20" height="12" viewBox="0 0 24 14" fill="none">
              <path d="M1 7h20M15 1l6 6-6 6" stroke="rgba(255,255,255,.2)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </template>
      </div>

      <!-- Tools config table -->
      <div class="tools-table-wrap">
        <table class="tools-table">
          <thead>
            <tr>
              <th>Tool</th>
              <th>Description</th>
              <th>Configuration</th>
              <th class="th-center">Enabled</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="tool in pipelineTools" :key="tool.id" :class="{ 'row-off': !tool.enabled }">
              <!-- Tool name -->
              <td class="td-tool">
                <div class="tool-name-cell">
                  <div class="tool-icon-sm" :class="tool.tool_key">
                    <span v-html="getIcon(tool.tool_key)"></span>
                  </div>
                  <span class="tool-name">{{ tool.label }}</span>
                </div>
              </td>

              <!-- Description -->
              <td class="td-desc">{{ tool.description }}</td>

              <!-- Inline config fields -->
              <td class="td-config">
                <div class="config-fields">
                  <template v-if="tool.tool_key === 'website'">
                    <div class="cfg-item">
                      <span class="cfg-label">Max pages</span>
                      <input type="number" v-model.number="tool.config.max_pages" min="1" max="50" @change="saveTool(tool)" class="cfg-input short" />
                    </div>
                    <div class="cfg-item">
                      <span class="cfg-label">Timeout</span>
                      <input type="number" v-model.number="tool.config.timeout_seconds" min="5" max="120" @change="saveTool(tool)" class="cfg-input short" /><span class="cfg-unit">s</span>
                    </div>
                  </template>
                  <template v-else-if="tool.tool_key === 'linkedin'">
                    <div class="cfg-item">
                      <span class="cfg-label">Browser</span>
                      <select v-model="tool.config.use_playwright" @change="saveTool(tool)" class="cfg-select">
                        <option :value="true">Playwright</option>
                        <option :value="false">HTTP</option>
                      </select>
                    </div>
                    <div class="cfg-item">
                      <span class="cfg-label">Timeout</span>
                      <input type="number" v-model.number="tool.config.timeout_seconds" min="5" max="120" @change="saveTool(tool)" class="cfg-input short" /><span class="cfg-unit">s</span>
                    </div>
                  </template>
                  <template v-else-if="tool.tool_key === 'news'">
                    <div class="cfg-item">
                      <span class="cfg-label">Max articles</span>
                      <input type="number" v-model.number="tool.config.max_articles" min="1" max="20" @change="saveTool(tool)" class="cfg-input short" />
                    </div>
                    <div class="cfg-item">
                      <span class="cfg-label">Timeout</span>
                      <input type="number" v-model.number="tool.config.timeout_seconds" min="5" max="120" @change="saveTool(tool)" class="cfg-input short" /><span class="cfg-unit">s</span>
                    </div>
                  </template>
                  <template v-else-if="tool.tool_key === 'pdf'">
                    <div class="cfg-item">
                      <span class="cfg-label">Max results</span>
                      <input type="number" v-model.number="tool.config.max_results" min="1" max="10" @change="saveTool(tool)" class="cfg-input short" />
                    </div>
                    <div class="cfg-item">
                      <span class="cfg-label">Timeout</span>
                      <input type="number" v-model.number="tool.config.timeout_seconds" min="5" max="120" @change="saveTool(tool)" class="cfg-input short" /><span class="cfg-unit">s</span>
                    </div>
                  </template>
                  <template v-else-if="tool.tool_key === 'documents'">
                    <div class="cfg-item">
                      <span class="cfg-label">OCR</span>
                      <select v-model="tool.config.use_ocr_vision" @change="saveTool(tool)" class="cfg-select">
                        <option :value="true">OpenAI Vision</option>
                        <option :value="false">Tesseract</option>
                      </select>
                    </div>
                    <div class="cfg-item">
                      <span class="cfg-label">Auto-routing</span>
                      <select v-model="tool.config.auto_routing" @change="saveTool(tool)" class="cfg-select">
                        <option :value="true">Enabled</option>
                        <option :value="false">Disabled</option>
                      </select>
                    </div>
                  </template>
                </div>
              </td>

              <!-- Toggle -->
              <td class="td-toggle">
                <label class="toggle">
                  <input type="checkbox" v-model="tool.enabled" @change="saveTool(tool)" />
                  <span class="toggle-track" :class="{ on: tool.enabled }">
                    <span class="toggle-dot"></span>
                  </span>
                </label>
                <span v-if="saving === tool.id" class="saving-badge">saving…</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      </div><!-- end section-card -->

      <!-- ── Section 2: Extra Sources ── -->
      <div class="section-card extra-section">
      <div class="section-header">
        <div class="section-title-wrap">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="rgba(96,165,250,.8)" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <h2>Client-Specific Sources</h2>
        </div>
        <div class="section-actions">
          <p class="section-sub">Extra sources for specific clients (CRM endpoints, SharePoint URLs, etc.).</p>
          <button class="btn-primary" @click="showAddForm = true">
            <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
              <path d="M7 1v12M1 7h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            Add Source
          </button>
        </div>
      </div>

      <div v-if="extraSources.length" class="extra-table-wrap">
        <table class="extra-table">
          <thead>
            <tr>
              <th>Type</th><th>Label</th><th>Client / Scope</th><th>URL</th><th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in extraSources" :key="s.id">
              <td><span class="type-badge" :class="s.source_type">{{ s.source_type }}</span></td>
              <td class="extra-label">{{ s.label }}</td>
              <td>
                <span v-if="s.client_id" class="scope-client" :title="s.client_id">{{ s.client_id.slice(0,14) }}…</span>
                <span v-else class="scope-global">Global</span>
              </td>
              <td class="extra-url">{{ s.url || '—' }}</td>
              <td>
                <button class="del-btn" @click="deleteExtra(s.id)">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
                  </svg>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty-extra">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="1.5">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
        <p>No additional sources configured.</p>
      </div>
      </div><!-- end section-card -->

    </template>

    <!-- Add source modal -->
    <div v-if="showAddForm" class="modal-overlay" @click.self="showAddForm = false">
      <div class="modal">
        <div class="modal-header">
          <h2>Add Client Source</h2>
          <button class="close-btn" @click="showAddForm = false">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>Type</label>
              <select v-model="newSource.source_type">
                <option value="website">Website</option>
                <option value="linkedin">LinkedIn</option>
                <option value="document">Document</option>
                <option value="crm">CRM</option>
              </select>
            </div>
            <div class="form-group">
              <label>Label</label>
              <input v-model="newSource.label" placeholder="Name" />
            </div>
          </div>
          <div class="form-group">
            <label>Client ID <span class="hint">— leave empty for global</span></label>
            <input v-model="newSource.client_id" placeholder="e.g. 001W500000P6AY6IAN" />
          </div>
          <div class="form-group">
            <label>URL</label>
            <input v-model="newSource.url" placeholder="https://…" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="showAddForm = false">Cancel</button>
          <button class="btn-primary" :disabled="addSaving" @click="addExtra">
            {{ addSaving ? 'Saving…' : 'Add Source' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import api from '../../../services/api'

const notify    = inject('notify', { success: () => {}, error: () => {} })
const sources   = ref([])
const loading   = ref(false)
const saving    = ref(null)
const addSaving = ref(false)
const showAddForm = ref(false)
const newSource = ref({ source_type: 'website', label: '', client_id: '', url: '' })

const pipelineTools = computed(() => sources.value.filter(s => s.source === 'pipeline_tool'))
const extraSources  = computed(() => sources.value.filter(s => s.source !== 'pipeline_tool'))

const iconMap = {
  website:   `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>`,
  linkedin:  `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>`,
  news:      `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 22h16a2 2 0 002-2V4a2 2 0 00-2-2H8a2 2 0 00-2 2v16a2 2 0 01-2 2zm0 0a2 2 0 01-2-2v-9c0-1.1.9-2 2-2h2"/><path d="M18 14h-8M15 18h-5M10 6h8v4h-8z"/></svg>`,
  pdf:       `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="9" y1="13" x2="15" y2="13"/></svg>`,
  documents: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>`,
}

function getIcon(key) { return iconMap[key] || iconMap.documents }

async function load() {
  loading.value = true
  try {
    const { data } = await api.admin.listSources()
    sources.value = data
  } finally { loading.value = false }
}

async function saveTool(tool) {
  saving.value = tool.id
  try {
    await api.admin.updateSource(tool.id, { enabled: tool.enabled, config: tool.config, label: tool.label })
    notify.success(`${tool.label} updated`)
  } catch (err) {
    notify.error(err?.response?.data?.detail || 'Save failed')
  } finally { saving.value = null }
}

async function addExtra() {
  if (!newSource.value.label.trim()) return
  addSaving.value = true
  try {
    await api.admin.createSource({ ...newSource.value, client_id: newSource.value.client_id?.trim() || null, enabled: true })
    showAddForm.value = false
    newSource.value = { source_type: 'website', label: '', client_id: '', url: '' }
    notify.success('Source added')
    await load()
  } catch (err) { notify.error(err?.response?.data?.detail || 'Failed') }
  finally { addSaving.value = false }
}

async function deleteExtra(id) {
  try {
    await api.admin.deleteSource(id)
    notify.success('Source deleted')
    await load()
  } catch { notify.error('Failed to delete') }
}

onMounted(load)
</script>

<style scoped>
*, *::before, *::after { box-sizing: border-box; }
.sources-page { font-family: Inter, sans-serif; color: #fff; max-width: 1100px; }

.page-header { margin-bottom: 28px; }
h1 { font-size: 1.5rem; font-weight: 700; color: #fff; margin: 0 0 4px; }
.page-sub { font-size: .85rem; color: rgba(255,255,255,.35); margin: 0; }

/* Section header */
.section-header { margin-bottom: 16px; }
.section-title-wrap { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
h2 { font-size: 1rem; font-weight: 700; color: rgba(255,255,255,.85); margin: 0; }
.section-sub { font-size: .82rem; color: rgba(255,255,255,.3); margin: 0; }
.section-actions { display: flex; justify-content: space-between; align-items: center; }

/* Pipeline flow */
.pipeline-flow {
  display: flex; align-items: center; flex-wrap: wrap; gap: 4px;
  background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.07);
  border-radius: 12px; padding: 16px 20px; margin-bottom: 16px;
}
.flow-node {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  padding: 10px 14px; border-radius: 10px;
  background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.08);
  transition: opacity .2s;
}
.flow-node.off { opacity: .4; }
.flow-icon {
  width: 36px; height: 36px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
}
.flow-icon.website   { background: rgba(96,165,250,.15);  color: #60a5fa; }
.flow-icon.linkedin  { background: rgba(99,102,241,.15);  color: #818cf8; }
.flow-icon.news      { background: rgba(250,204,21,.12);  color: #facc15; }
.flow-icon.pdf       { background: rgba(251,146,60,.12);  color: #fb923c; }
.flow-icon.documents { background: rgba(74,222,128,.12);  color: #4ade80; }
.flow-label  { font-size: .72rem; font-weight: 600; color: rgba(255,255,255,.55); white-space: nowrap; }
.flow-status { font-size: .65rem; font-weight: 800; letter-spacing: .06em; padding: 2px 7px; border-radius: 10px; }
.flow-status.on  { background: rgba(74,222,128,.15); color: #4ade80; }
.flow-status.off { background: rgba(255,255,255,.06); color: rgba(255,255,255,.3); }
.flow-arrow { flex-shrink: 0; padding: 0 4px; }

/* Tools table */
.tools-table-wrap {
  background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.08);
  border-radius: 12px; overflow: hidden;
}
.tools-table { width: 100%; border-collapse: collapse; font-size: .875rem; }
.tools-table thead tr { background: rgba(255,255,255,.03); border-bottom: 1px solid rgba(255,255,255,.07); }
.tools-table th {
  padding: 11px 18px; font-size: .72rem; font-weight: 700;
  color: rgba(255,255,255,.3); text-transform: uppercase; letter-spacing: .05em; text-align: left;
}
.th-center { text-align: center; }
.tools-table tbody tr { border-bottom: 1px solid rgba(255,255,255,.05); transition: background .12s; }
.tools-table tbody tr:last-child { border-bottom: none; }
.tools-table tbody tr:hover { background: rgba(255,255,255,.025); }
.tools-table tbody tr.row-off { opacity: .55; }
.tools-table td { padding: 14px 18px; vertical-align: middle; }

.td-tool { width: 200px; }
.tool-name-cell { display: flex; align-items: center; gap: 10px; }
.tool-icon-sm {
  width: 32px; height: 32px; border-radius: 8px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.tool-icon-sm.website   { background: rgba(96,165,250,.15);  color: #60a5fa; }
.tool-icon-sm.linkedin  { background: rgba(99,102,241,.15);  color: #818cf8; }
.tool-icon-sm.news      { background: rgba(250,204,21,.12);  color: #facc15; }
.tool-icon-sm.pdf       { background: rgba(251,146,60,.12);  color: #fb923c; }
.tool-icon-sm.documents { background: rgba(74,222,128,.12);  color: #4ade80; }
.tool-name { font-weight: 600; color: rgba(255,255,255,.9); font-size: .88rem; }

.td-desc { color: rgba(255,255,255,.4); font-size: .8rem; line-height: 1.4; max-width: 280px; }

.td-config { }
.config-fields { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.cfg-item { display: flex; align-items: center; gap: 6px; }
.cfg-label { font-size: .75rem; color: rgba(255,255,255,.35); white-space: nowrap; }
.cfg-input {
  background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1);
  border-radius: 6px; padding: 4px 8px; font-size: .8rem; color: #fff;
  outline: none; color-scheme: dark; transition: border-color .15s;
}
.cfg-input.short { width: 60px; text-align: center; }
.cfg-input:focus { border-color: #E8622C; }
.cfg-select {
  background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1);
  border-radius: 6px; padding: 4px 8px; font-size: .8rem; color: #fff;
  outline: none; color-scheme: dark; cursor: pointer;
}
.cfg-select:focus { border-color: #E8622C; }
.cfg-select option { background: #0f172a; }
.cfg-unit { font-size: .72rem; color: rgba(255,255,255,.3); }

.td-toggle { text-align: center; width: 110px; }
.saving-badge { display: block; font-size: .68rem; color: #E8622C; margin-top: 4px; }

/* Toggle switch */
.toggle { cursor: pointer; display: inline-flex; flex-direction: column; align-items: center; gap: 4px; }
.toggle input { display: none; }
.toggle-track {
  width: 42px; height: 23px; background: rgba(255,255,255,.12);
  border-radius: 12px; position: relative; transition: background .2s;
}
.toggle-track.on { background: rgba(74,222,128,.35); }
.toggle-dot {
  position: absolute; top: 3px; left: 3px;
  width: 17px; height: 17px; border-radius: 50%;
  background: rgba(255,255,255,.45); transition: transform .2s, background .2s;
}
.toggle-track.on .toggle-dot { transform: translateX(19px); background: #4ade80; }

/* Extra sources table */
.extra-table-wrap {
  background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.07);
  border-radius: 12px; overflow: hidden;
}
.extra-table { width: 100%; border-collapse: collapse; font-size: .85rem; }
.extra-table th { padding: 10px 16px; font-size: .7rem; font-weight: 700; color: rgba(255,255,255,.25); text-transform: uppercase; letter-spacing: .05em; text-align: left; border-bottom: 1px solid rgba(255,255,255,.06); }
.extra-table td { padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,.04); color: rgba(255,255,255,.7); }
.extra-table tr:last-child td { border-bottom: none; }
.extra-label { font-weight: 600; color: rgba(255,255,255,.85); }
.extra-url { color: rgba(255,255,255,.3); font-size: .78rem; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.type-badge { border-radius: 4px; padding: 2px 8px; font-size: .7rem; font-weight: 700; }
.type-badge.website   { background: rgba(96,165,250,.15); color: #60a5fa; }
.type-badge.linkedin  { background: rgba(99,102,241,.15); color: #818cf8; }
.type-badge.document  { background: rgba(74,222,128,.12); color: #4ade80; }
.type-badge.crm       { background: rgba(192,132,252,.12);color: #c084fc; }

.scope-client { font-family: monospace; font-size: .75rem; background: rgba(250,204,21,.1); color: #facc15; border-radius: 4px; padding: 2px 7px; }
.scope-global { font-size: .75rem; background: rgba(255,255,255,.06); color: rgba(255,255,255,.4); border-radius: 4px; padding: 2px 7px; }

.del-btn { background: rgba(239,68,68,.1); border: 1px solid rgba(239,68,68,.2); color: #f87171; border-radius: 6px; cursor: pointer; padding: 5px 7px; display: flex; align-items: center; transition: background .15s; }
.del-btn:hover { background: rgba(239,68,68,.25); }

.empty-extra { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 36px; color: rgba(255,255,255,.2); font-size: .875rem; text-align: center; }
.extra-section { margin-top: 32px; }

/* Loading */
.loading-state { display: flex; align-items: center; gap: 12px; padding: 80px; color: rgba(255,255,255,.35); justify-content: center; }
.spinner { width: 20px; height: 20px; border: 2px solid rgba(255,255,255,.1); border-top-color: #E8622C; border-radius: 50%; animation: spin .7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Buttons */
.btn-primary { display: flex; align-items: center; gap: 6px; background: linear-gradient(135deg,#E8622C,#ff8c5a); color: #fff; border: none; border-radius: 8px; padding: 8px 16px; cursor: pointer; font-weight: 600; font-size: .875rem; white-space: nowrap; }
.btn-primary:hover { opacity: .9; }
.btn-primary:disabled { opacity: .4; cursor: default; }
.btn-ghost { background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1); color: rgba(255,255,255,.7); border-radius: 8px; padding: 8px 16px; cursor: pointer; font-size: .875rem; }
.btn-ghost:hover { background: rgba(255,255,255,.1); }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.7); backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; z-index: 300; }
.modal { background: rgba(15,23,42,.97); border: 1px solid rgba(255,255,255,.1); border-radius: 16px; width: 500px; display: flex; flex-direction: column; box-shadow: 0 32px 80px rgba(0,0,0,.6); }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px 0; }
.modal-header h2 { font-size: 1.05rem; font-weight: 700; color: #fff; margin: 0; }
.close-btn { background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1); color: rgba(255,255,255,.5); cursor: pointer; width: 28px; height: 28px; border-radius: 7px; display: flex; align-items: center; justify-content: center; }
.modal-body { padding: 18px 24px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 14px 24px; border-top: 1px solid rgba(255,255,255,.07); flex-shrink: 0; }
.form-group { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
.form-group label { font-size: .82rem; font-weight: 600; color: rgba(255,255,255,.45); }
.form-group input, .form-group select { background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1); border-radius: 8px; padding: 9px 12px; font-size: .9rem; color: #fff; outline: none; color-scheme: dark; }
.form-group input:focus, .form-group select:focus { border-color: #E8622C; }
.form-group select option { background: #0f172a; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.hint { font-weight: 400; color: rgba(255,255,255,.3); font-size: .75rem; }

/* Section card wrapper */
.section-card {
  background: rgba(255,255,255,.04);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 14px;
  padding: 20px 24px;
  margin-bottom: 20px;
}
.section-card .pipeline-flow {
  background: rgba(255,255,255,.03);
  border-color: rgba(255,255,255,.06);
  margin-bottom: 16px;
}
.section-card .tools-table-wrap {
  border-color: rgba(255,255,255,.06);
}

/* ══ LIGHT MODE ══════════════════════════════ */
[data-theme="light"] .sources-page { color: #0D1B2E; }
[data-theme="light"] h1  { color: #0D1B2E; }
[data-theme="light"] h2  { color: #0D1B2E; }
[data-theme="light"] .page-sub    { color: #3D5068; }
[data-theme="light"] .section-sub { color: #3D5068; }
[data-theme="light"] .hint        { color: #7C93AE; }

/* Section card — fond unifié blanc */
[data-theme="light"] .section-card {
  background: #FFFFFF;
  border-color: rgba(13,27,46,0.09);
  box-shadow: 0 2px 10px rgba(13,27,46,0.06);
}

/* Pipeline flow intégré dans la card */
[data-theme="light"] .section-card .pipeline-flow {
  background: #F8FAFC;
  border-color: rgba(13,27,46,0.08);
}
[data-theme="light"] .flow-node   { background: #FFFFFF; border-color: rgba(13,27,46,0.10); }
[data-theme="light"] .flow-label  { color: #3D5068; }
[data-theme="light"] .flow-status.off { background: rgba(13,27,46,0.07); color: #7C93AE; }

/* Tools table intégrée dans la card */
[data-theme="light"] .section-card .tools-table-wrap {
  background: transparent;
  border-color: rgba(13,27,46,0.08);
  box-shadow: none;
}
[data-theme="light"] .tools-table thead tr { background: rgba(13,27,46,0.03); border-bottom-color: rgba(13,27,46,0.08); }
[data-theme="light"] .tools-table th { color: #7C93AE; }
[data-theme="light"] .tools-table tbody tr { border-bottom-color: rgba(13,27,46,0.06); }
[data-theme="light"] .tools-table tbody tr:hover { background: rgba(13,27,46,0.025); }
[data-theme="light"] .tool-name { color: #0D1B2E; }
[data-theme="light"] .td-desc   { color: #3D5068; }

/* Config inputs (number + select) */
[data-theme="light"] .cfg-label  { color: #7C93AE; }
[data-theme="light"] .cfg-unit   { color: #7C93AE; }
[data-theme="light"] .cfg-input  {
  background: #F8FAFC; border-color: rgba(13,27,46,0.15);
  color: #0D1B2E; color-scheme: light;
}
[data-theme="light"] .cfg-select {
  background: #F8FAFC; border-color: rgba(13,27,46,0.15);
  color: #0D1B2E; color-scheme: light;
}
[data-theme="light"] .cfg-select option { background: #FFFFFF; color: #0D1B2E; }

/* Source cards */
[data-theme="light"] [class*="-card"] {
  background: #FFFFFF; border-color: rgba(13,27,46,0.09);
  box-shadow: 0 2px 8px rgba(13,27,46,0.06); backdrop-filter: none;
}

/* Modal */
[data-theme="light"] .modal {
  background: #FFFFFF; border-color: rgba(13,27,46,0.12);
  box-shadow: 0 24px 64px rgba(13,27,46,0.15);
}
[data-theme="light"] .modal h2 { color: #0D1B2E; }
[data-theme="light"] .modal-header {
  background: #FFFFFF;
  padding-bottom: 16px;
  border-radius: 14px 14px 0 0;
  border-bottom: 1px solid rgba(13,27,46,0.08);
}
[data-theme="light"] .close-btn { background: transparent; border: none; color: #7C93AE; }
[data-theme="light"] .close-btn:hover { background: rgba(13,27,46,0.06); color: #0D1B2E; }
[data-theme="light"] .form-group label { color: #3D5068; }
[data-theme="light"] .form-group input, [data-theme="light"] .form-group select {
  background: #F8FAFC; border-color: rgba(13,27,46,0.15); color: #0D1B2E; color-scheme: light;
}
[data-theme="light"] .form-group select option { background: #FFFFFF; color: #0D1B2E; }
</style>
