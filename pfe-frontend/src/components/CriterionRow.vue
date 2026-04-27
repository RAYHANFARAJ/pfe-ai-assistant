<template>
  <div class="criterion" :class="{ expanded: open }">
    <div class="criterion-header" @click="open = !open">

      <div class="score-col">
        <div class="score-bar-wrap">
          <div class="score-bar" :style="{ width: barWidth, background: barColor }"></div>
        </div>
        <span class="score-text">{{ criterion.score }}<span class="score-max-txt">/{{ criterion.max_score }}</span></span>
      </div>

      <div class="label-col">
        <div class="label-topline">
          <span class="criterion-id">{{ criterion.criterion_id }}</span>
          <span class="type-badge">{{ criterion.answer_type }}</span>
        </div>
        <span class="label-text">{{ criterion.label }}</span>
      </div>

      <div class="answer-col">
        <span class="answer-val" :class="{ unknown: criterion.predicted_answer === 'unknown' }">
          {{ criterion.predicted_answer }}
        </span>
        <div class="answer-meta">
          <span class="conf">{{ Math.round((criterion.confidence || 0) * 100) }}%</span>
          <span class="tier-badge" :class="'tier-' + (criterion.quality_tier || 'UNKNOWN').toLowerCase()">
            {{ criterion.quality_tier || '?' }}
          </span>
        </div>
      </div>

      <span class="chevron">{{ open ? '▲' : '▼' }}</span>
    </div>

    <div v-if="open" class="detail">

      <div class="detail-block">
        <div class="dl">Justification</div>
        <p class="dt">{{ criterion.justification }}</p>
        <div v-if="criterion.evidence?.source_url" class="evidence">
          <span class="src-badge">{{ srcLabel }}</span>
          <a :href="criterion.evidence.source_url" target="_blank" class="src-link">
            {{ criterion.evidence.source_label || criterion.evidence.source_url }} ↗
          </a>
          <blockquote v-if="criterion.evidence.exact_quote" class="snippet">{{ criterion.evidence.exact_quote }}</blockquote>
        </div>
        <div v-else-if="criterion.evidence?.source_label" class="evidence"
             :class="{ 'doc-evidence': criterion.evidence.source_type === 'document' }">
          <span class="src-badge">{{ srcLabel }}</span>
          <span class="src-plain">{{ criterion.evidence.source_label }}</span>
          <blockquote v-if="criterion.evidence.exact_quote" class="snippet doc-quote">
            {{ criterion.evidence.exact_quote }}
          </blockquote>
        </div>
      </div>

      <div class="detail-block" v-if="criterion.extracted_value !== null && criterion.extracted_value !== undefined">
        <div class="dl">Extracted value</div>
        <code class="code-val">{{ criterion.extracted_value }}</code>
      </div>

      <div class="detail-block" v-if="criterion.choices?.length">
        <div class="dl">Scoring choices</div>
        <div class="choices">
          <div v-for="ch in criterion.choices" :key="ch.label" class="choice" :class="{ matched: isMatched(ch) }">
            <span class="choice-label">{{ ch.label }}</span>
            <span class="choice-pts" :class="{ blocking: ch.is_blocking }">
              {{ ch.is_blocking ? '🚫 blocking' : ch.score + ' pts' }}
            </span>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
const props = defineProps({ criterion: Object })
const open = ref(false)

const barWidth = computed(() => {
  const max = props.criterion.max_score
  if (!max) return '0%'
  return Math.round((props.criterion.score / max) * 100) + '%'
})
const barColor = computed(() => {
  const pct = props.criterion.max_score ? props.criterion.score / props.criterion.max_score : 0
  if (pct >= 0.75) return '#22c55e'
  if (pct >= 0.4) return '#f59e0b'
  return '#E8622C'
})
const srcLabel = computed(() => {
  const t = props.criterion.evidence?.source_type
  if (t === 'crm') return '🗄 CRM'
  if (t === 'website') return '🌐 Web'
  if (t === 'linkedin') return '💼 LinkedIn'
  if (t === 'news') return '📰 News'
  if (t === 'crm_description') return '📄 Description'
  if (t === 'document') return '📑 Document'
  return '📌'
})
function isMatched(ch) {
  return String(ch.label).toLowerCase() === String(props.criterion.predicted_answer).toLowerCase()
}
</script>

<style scoped>
.criterion { background: rgba(255,255,255,0.025); border: 1px solid rgba(255,255,255,0.07); border-radius: 14px; overflow: hidden; transition: border-color 0.2s, transform 0.2s, background 0.2s; }
.criterion:hover { border-color: rgba(232,98,44,0.2); transform: translateY(-1px); }
.criterion.expanded { border-color: rgba(232,98,44,0.35); background: rgba(232,98,44,0.04); }

.criterion-header { display: flex; align-items: center; gap: 14px; padding: 14px 16px; cursor: pointer; }

.score-col { display: flex; align-items: center; gap: 8px; min-width: 104px; }
.score-bar-wrap { width: 52px; height: 6px; background: rgba(255,255,255,0.08); border-radius: 99px; overflow: hidden; }
.score-bar { height: 100%; border-radius: 99px; transition: width 0.4s ease; }
.score-text { font-size: 12px; font-weight: 700; color: #fff; white-space: nowrap; }
.score-max-txt { color: rgba(255,255,255,0.3); font-weight: 400; }

.label-col { flex: 1; display: flex; flex-direction: column; gap: 3px; }
.label-topline { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.criterion-id { font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px; color: rgba(255,255,255,0.3); font-weight: 700; }
.type-badge { font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px; color: rgba(232,98,44,0.75); font-weight: 700; }
.label-text { font-size: 13px; color: rgba(255,255,255,0.86); font-weight: 600; line-height: 1.45; }

.answer-col { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; min-width: 120px; }
.answer-val { font-size: 13px; font-weight: 700; color: #fff; text-align: right; }
.answer-val.unknown { color: rgba(255,255,255,0.3); font-style: italic; }
.answer-meta { display: flex; align-items: center; gap: 5px; }
.conf { font-size: 11px; color: rgba(255,255,255,0.42); }
.tier-badge { font-size: 9px; font-weight: 700; padding: 1px 6px; border-radius: 20px; letter-spacing: 0.5px; }
.tier-high { background: rgba(34,197,94,0.15); color: #4ade80; }
.tier-medium { background: rgba(245,158,11,0.15); color: #fbbf24; }
.tier-low { background: rgba(251,191,36,0.12); color: #f59e0b; }
.tier-unknown { background: rgba(255,255,255,0.06); color: rgba(255,255,255,0.25); }
.chevron { font-size: 9px; color: rgba(255,255,255,0.2); margin-left: 6px; }

.detail { border-top: 1px solid rgba(255,255,255,0.06); padding: 16px; display: flex; flex-direction: column; gap: 14px; }
.detail-block { display: flex; flex-direction: column; gap: 6px; }
.dl { font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px; color: rgba(255,255,255,0.25); font-weight: 600; }
.dt { font-size: 12.5px; color: rgba(255,255,255,0.62); line-height: 1.6; }

.evidence { display: flex; flex-direction: column; gap: 5px; margin-top: 4px; }
.src-badge { font-size: 11px; font-weight: 700; color: rgba(255,255,255,0.4); }
.src-link { font-size: 12.5px; color: #E8622C; text-decoration: none; font-weight: 500; }
.src-link:hover { text-decoration: underline; }
.src-plain { font-size: 12.5px; color: rgba(255,255,255,0.4); }
.snippet { margin: 0; padding: 8px 12px; background: rgba(232,98,44,0.06); border-left: 2px solid #E8622C; border-radius: 4px; font-size: 12px; color: rgba(255,255,255,0.4); font-style: italic; line-height: 1.5; }
.doc-evidence { background: rgba(99,179,237,0.04); border: 1px solid rgba(99,179,237,0.15); border-radius: 8px; padding: 10px 12px; }
.doc-quote { background: rgba(99,179,237,0.08); border-left: 2px solid #63b3ed; color: rgba(255,255,255,0.6); font-style: normal; white-space: pre-wrap; max-height: 200px; overflow-y: auto; }

.code-val { background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 6px; font-size: 12px; color: #E8622C; font-family: monospace; }

.choices { display: flex; flex-direction: column; gap: 4px; }
.choice { display: flex; justify-content: space-between; align-items: center; padding: 7px 10px; border-radius: 6px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); font-size: 12.5px; }
.choice.matched { background: rgba(232,98,44,0.1); border-color: rgba(232,98,44,0.3); }
.choice-label { color: rgba(255,255,255,0.6); font-weight: 500; }
.choice-pts { font-size: 11.5px; font-weight: 700; color: #4ade80; }
.choice-pts.blocking { color: #f87171; }

@media (max-width: 720px) {
  .criterion-header { align-items: flex-start; flex-wrap: wrap; }
  .score-col { min-width: auto; }
  .answer-col { width: 100%; align-items: flex-start; min-width: auto; }
  .answer-val { text-align: left; }
  .chevron { margin-left: auto; }
}
</style>
