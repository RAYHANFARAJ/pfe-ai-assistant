<template>
  <div class="page">

    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="brand">
        <img src="/sellynx-logo.svg" alt="SELLYNX" class="brand-logo" />
      </div>
      <nav class="nav">
        <RouterLink to="/dashboard" class="nav-item active">
          <span class="icon">⚡</span> Scoring
        </RouterLink>
      </nav>
    </aside>

    <!-- Main -->
    <main class="main">

      <!-- Back -->
      <RouterLink to="/dashboard" class="back-link">← New analysis</RouterLink>

      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <div class="big-spinner"></div>
        <p>Running AI qualification pipeline…</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="alert-error">
        <strong>Error:</strong> {{ error }}
      </div>

      <template v-else-if="result">

        <!-- Client + Summary -->
        <div class="top-grid">

          <!-- Client card -->
          <div class="card client-card">
            <div class="card-label">Client Account</div>
            <h2 class="client-name">{{ result.client?.client_name || result.client?.client_id }}</h2>
            <div class="client-meta">
              <span class="tag">{{ result.client?.sector }}</span>
            </div>
            <div class="client-links">
              <a v-if="result.client?.website" :href="result.client.website" target="_blank" class="link-chip">🌐 Website</a>
              <a v-if="result.client?.linkedin" :href="result.client.linkedin" target="_blank" class="link-chip">💼 LinkedIn</a>
            </div>
          </div>

          <!-- Summary card -->
          <SummaryCard :summary="result.summary" :client="result.client" :product="result.product" />
        </div>

        <!-- Criteria results -->
        <div class="card">
          <h2 class="card-title">Criteria Breakdown <span class="count">{{ result.criteria_results?.length }}</span></h2>
          <div class="criteria-list">
            <CriterionRow
              v-for="c in result.criteria_results"
              :key="c.criterion_id"
              :criterion="c"
            />
          </div>
        </div>

        <!-- Trace log -->
        <details class="trace-block">
          <summary>Pipeline trace log</summary>
          <ul class="trace-list">
            <li v-for="(step, i) in result.trace" :key="i">{{ step }}</li>
          </ul>
        </details>

      </template>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../services/api'
import SummaryCard from '../components/SummaryCard.vue'
import CriterionRow from '../components/CriterionRow.vue'

const props = defineProps({ clientId: String, productId: String })

const loading = ref(true)
const error = ref('')
const result = ref(null)

onMounted(async () => {
  try {
    const res = await api.runScoring(props.clientId, props.productId)
    if (res.data.error) {
      error.value = res.data.detail || res.data.error
    } else {
      result.value = res.data
    }
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || 'Unexpected error'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page { display: flex; min-height: 100vh; background: #F4F6FA; font-family: 'Inter', 'Segoe UI', Arial, sans-serif; }
.sidebar { width: 220px; background: #0A2D4A; display: flex; flex-direction: column; padding: 0; flex-shrink: 0; }
.brand { padding: 24px 20px 20px; border-bottom: 1px solid rgba(255,255,255,0.08); }
.brand-logo { width: 140px; }
.nav { flex: 1; padding: 16px 12px; }
.nav-item { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: 8px; color: rgba(255,255,255,0.6); text-decoration: none; font-size: 14px; font-weight: 500; }
.nav-item.active { background: rgba(232,98,44,0.18); color: #fff; }
.icon { font-size: 16px; }

.main { flex: 1; padding: 32px 40px; display: flex; flex-direction: column; gap: 24px; overflow-y: auto; }
.back-link { color: #8A9BB0; text-decoration: none; font-size: 13.5px; font-weight: 500; }
.back-link:hover { color: #0A2D4A; }

/* Top grid */
.top-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

/* Card */
.card { background: #fff; border-radius: 14px; padding: 24px 28px; box-shadow: 0 2px 16px rgba(10,45,74,0.07); }
.card-title { font-size: 16px; font-weight: 700; color: #0A2D4A; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }
.count { background: #F4F6FA; color: #8A9BB0; font-size: 12px; padding: 2px 8px; border-radius: 20px; font-weight: 600; }

/* Client */
.card-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #8A9BB0; margin-bottom: 8px; font-weight: 600; }
.client-name { font-size: 22px; font-weight: 700; color: #0A2D4A; margin-bottom: 10px; }
.client-meta { margin-bottom: 14px; }
.tag { background: #EEF2FF; color: #4338CA; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 20px; }
.client-links { display: flex; gap: 10px; flex-wrap: wrap; }
.link-chip { display: inline-flex; align-items: center; gap: 5px; padding: 6px 12px; background: #F4F6FA; color: #0A2D4A; text-decoration: none; font-size: 13px; font-weight: 500; border-radius: 8px; border: 1px solid #DDE3EC; transition: all 0.15s; }
.link-chip:hover { background: #E8622C; color: #fff; border-color: #E8622C; }

/* Criteria list */
.criteria-list { display: flex; flex-direction: column; gap: 10px; }

/* Trace */
.trace-block { background: #fff; border-radius: 14px; padding: 16px 24px; box-shadow: 0 2px 16px rgba(10,45,74,0.07); }
.trace-block summary { font-size: 13px; font-weight: 600; color: #8A9BB0; cursor: pointer; }
.trace-list { margin-top: 12px; padding-left: 16px; display: flex; flex-direction: column; gap: 4px; }
.trace-list li { font-size: 12.5px; color: #4A5E72; font-family: monospace; }

/* Loading */
.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; gap: 16px; color: #8A9BB0; font-size: 14px; padding: 80px 0; }
.big-spinner { width: 40px; height: 40px; border: 3px solid #DDE3EC; border-top-color: #E8622C; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Alert */
.alert-error { background: #fef2f2; border: 1.5px solid #fca5a5; color: #b91c1c; padding: 14px 18px; border-radius: 10px; font-size: 14px; }
</style>
