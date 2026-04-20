<template>
  <div class="card summary-card">
    <div class="card-label">{{ product?.product_name || 'Product' }} — Score Summary</div>

    <!-- Eligibility badge -->
    <div class="eligibility" :class="statusClass">
      {{ statusLabel }}
    </div>

    <!-- Score ring + numbers -->
    <div class="score-row">
      <div class="score-ring-wrap">
        <svg viewBox="0 0 80 80" class="ring-svg">
          <circle cx="40" cy="40" r="32" fill="none" stroke="#EEF2FF" stroke-width="8"/>
          <circle
            cx="40" cy="40" r="32" fill="none"
            :stroke="ringColor" stroke-width="8"
            stroke-linecap="round"
            :stroke-dasharray="`${ringFill} 201`"
            stroke-dashoffset="50"
            style="transition: stroke-dasharray 0.6s ease"
          />
        </svg>
        <div class="ring-label">{{ Math.round((summary?.normalized_score || 0) * 100) }}<small>%</small></div>
      </div>

      <div class="score-stats">
        <div class="stat">
          <span class="stat-val">{{ summary?.total_score }}</span>
          <span class="stat-key">Total score</span>
        </div>
        <div class="stat">
          <span class="stat-val">{{ summary?.max_score }}</span>
          <span class="stat-key">Max score</span>
        </div>
        <div class="stat">
          <span class="stat-val">{{ summary?.criteria_count }}</span>
          <span class="stat-key">Criteria</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  summary: Object,
  client: Object,
  product: Object,
})

const statusClass = computed(() => {
  const s = props.summary?.eligibility_status
  if (s === 'eligible') return 'eligible'
  if (s === 'to_review') return 'review'
  return 'not-eligible'
})

const statusLabel = computed(() => {
  const s = props.summary?.eligibility_status
  if (s === 'eligible') return '✅ Eligible'
  if (s === 'to_review') return '🔎 To Review'
  return '❌ Not Eligible'
})

const ringColor = computed(() => {
  const s = props.summary?.eligibility_status
  if (s === 'eligible') return '#22c55e'
  if (s === 'to_review') return '#f59e0b'
  return '#E8622C'
})

const ringFill = computed(() => {
  const pct = (props.summary?.normalized_score || 0)
  return Math.round(pct * 201)
})
</script>

<style scoped>
.card { background: #fff; border-radius: 14px; padding: 24px 28px; box-shadow: 0 2px 16px rgba(10,45,74,0.07); }
.card-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #8A9BB0; margin-bottom: 12px; font-weight: 600; }

.eligibility { display: inline-flex; align-items: center; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 700; margin-bottom: 20px; }
.eligibility.eligible { background: #dcfce7; color: #15803d; }
.eligibility.review { background: #fef9c3; color: #a16207; }
.eligibility.not-eligible { background: #fee2e2; color: #b91c1c; }

.score-row { display: flex; align-items: center; gap: 24px; }
.score-ring-wrap { position: relative; width: 80px; height: 80px; flex-shrink: 0; }
.ring-svg { width: 80px; height: 80px; transform: rotate(-90deg); }
.ring-label { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 800; color: #0A2D4A; }
.ring-label small { font-size: 11px; font-weight: 600; margin-top: 2px; }

.score-stats { display: flex; gap: 20px; }
.stat { display: flex; flex-direction: column; gap: 2px; }
.stat-val { font-size: 22px; font-weight: 800; color: #0A2D4A; }
.stat-key { font-size: 11px; color: #8A9BB0; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
</style>
