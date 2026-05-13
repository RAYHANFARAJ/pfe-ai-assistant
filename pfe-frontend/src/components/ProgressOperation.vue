<template>
  <div class="progress-op" v-if="active || forceShow">

    <!-- Header: icon pulse + title + time -->
    <div class="po-header">
      <div class="po-pulse">
        <div class="po-pulse-ring"></div>
        <div class="po-pulse-core">
          <span class="po-phase-icon">{{ currentIcon }}</span>
        </div>
      </div>

      <div class="po-info">
        <div class="po-title">{{ title }}</div>
        <div class="po-phase-label">{{ currentLabel }}</div>
      </div>

      <div class="po-timer">
        <div class="po-elapsed">{{ elapsed }}s</div>
        <div class="po-remaining">{{ remainingLabel }}</div>
      </div>
    </div>

    <!-- Progress bar -->
    <div class="po-bar-wrap">
      <div class="po-bar-track">
        <div class="po-bar-fill" :style="{ width: pct + '%' }"></div>
        <div class="po-bar-glow" :style="{ left: pct + '%' }"></div>
      </div>
      <span class="po-bar-pct">{{ Math.round(pct) }}%</span>
    </div>

    <!-- Phase checklist -->
    <div class="po-phases">
      <div
        v-for="(phase, i) in phases"
        :key="i"
        class="po-phase"
        :class="{
          'po-phase-done':   phase.done,
          'po-phase-active': i === currentPhase && !phase.done,
          'po-phase-waiting': i > currentPhase,
        }"
      >
        <div class="po-phase-bullet">
          <svg v-if="phase.done" width="10" height="10" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          <span v-else-if="i === currentPhase" class="po-phase-spin"></span>
          <span v-else class="po-phase-dot"></span>
        </div>
        <span class="po-phase-text">
          <span class="po-phase-emoji">{{ phase.icon }}</span>
          {{ phase.label }}
        </span>
        <span v-if="i === currentPhase && !phase.done" class="po-phase-badge">En cours</span>
        <span v-if="phase.done" class="po-phase-done-badge">✓</span>
      </div>
    </div>

    <!-- Extra slot (e.g. mini product grid for batch) -->
    <slot />

  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title:        { type: String, default: 'Opération en cours…' },
  phases:       { type: Array,  default: () => [] },
  currentPhase: { type: Number, default: 0 },
  pct:          { type: Number, default: 0 },
  elapsed:      { type: Number, default: 0 },
  remainingLabel:{ type: String, default: '' },
  active:       { type: Boolean, default: true },
  forceShow:    { type: Boolean, default: false },
})

const currentIcon  = computed(() => props.phases[props.currentPhase]?.icon  || '⚙️')
const currentLabel = computed(() => props.phases[props.currentPhase]?.label || 'Traitement en cours…')
</script>

<style scoped>
.progress-op {
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(232,98,44,0.18);
  border-radius: 18px;
  padding: 24px 24px 20px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* ── Header ── */
.po-header { display: flex; align-items: center; gap: 16px; }

.po-pulse { position: relative; width: 52px; height: 52px; flex-shrink: 0; }
.po-pulse-ring {
  position: absolute; inset: 0; border-radius: 50%;
  border: 2px solid rgba(232,98,44,0.3);
  animation: po-ring 2s ease-out infinite;
}
.po-pulse-core {
  position: absolute; inset: 10px;
  background: rgba(232,98,44,0.1);
  border: 1px solid rgba(232,98,44,0.3);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px;
  animation: po-glow 2s ease-in-out infinite;
}
@keyframes po-ring { 0% { transform: scale(1); opacity:.6 } 100% { transform: scale(1.55); opacity:0 } }
@keyframes po-glow { 0%,100% { box-shadow: 0 0 0 0 rgba(232,98,44,0) } 50% { box-shadow: 0 0 16px 4px rgba(232,98,44,.25) } }

.po-info { flex: 1; min-width: 0; }
.po-title       { font-size: 15px; font-weight: 700; color: #fff; margin-bottom: 3px; }
.po-phase-label { font-size: 13px; color: rgba(255,255,255,0.5); }

.po-timer { text-align: right; flex-shrink: 0; }
.po-elapsed   { font-size: 20px; font-weight: 800; color: #fff; font-variant-numeric: tabular-nums; }
.po-remaining { font-size: 11px; color: rgba(255,255,255,0.35); margin-top: 2px; }

/* ── Progress bar ── */
.po-bar-wrap { display: flex; align-items: center; gap: 12px; }
.po-bar-track {
  flex: 1; height: 8px;
  background: rgba(255,255,255,0.06);
  border-radius: 99px;
  overflow: visible;
  position: relative;
}
.po-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #E8622C, #ff9a6c);
  border-radius: 99px;
  transition: width 0.9s cubic-bezier(0.4,0,0.2,1);
}
.po-bar-glow {
  position: absolute; top: 50%;
  transform: translate(-50%, -50%);
  width: 12px; height: 12px;
  background: #ff9a6c;
  border-radius: 50%;
  box-shadow: 0 0 10px 4px rgba(232,98,44,0.6);
  transition: left 0.9s cubic-bezier(0.4,0,0.2,1);
  pointer-events: none;
}
.po-bar-pct { font-size: 13px; font-weight: 800; color: #E8622C; width: 38px; text-align: right; flex-shrink: 0; }

/* ── Phase list ── */
.po-phases { display: flex; flex-direction: column; gap: 6px; }

.po-phase {
  display: flex; align-items: center; gap: 10px;
  padding: 7px 10px;
  border-radius: 9px;
  transition: all 0.25s;
}
.po-phase-active  { background: rgba(232,98,44,0.08); border: 1px solid rgba(232,98,44,0.2); }
.po-phase-done    { opacity: 0.55; }
.po-phase-waiting { opacity: 0.25; }

.po-phase-bullet {
  width: 18px; height: 18px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.po-phase-done    .po-phase-bullet { background: rgba(34,197,94,0.2); color: #22c55e; }
.po-phase-active  .po-phase-bullet { background: rgba(232,98,44,0.15); }
.po-phase-waiting .po-phase-bullet { background: rgba(255,255,255,0.05); }

.po-phase-dot  { width: 6px; height: 6px; background: rgba(255,255,255,0.3); border-radius: 50%; }
.po-phase-spin {
  width: 10px; height: 10px;
  border: 2px solid rgba(232,98,44,0.3);
  border-top-color: #E8622C;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: block;
}
@keyframes spin { to { transform: rotate(360deg); } }

.po-phase-text  { flex: 1; font-size: 12.5px; color: rgba(255,255,255,0.7); }
.po-phase-emoji { margin-right: 4px; }

.po-phase-badge      { font-size: 10px; font-weight: 700; color: #E8622C; background: rgba(232,98,44,0.15); padding: 2px 7px; border-radius: 99px; }
.po-phase-done-badge { font-size: 11px; color: #22c55e; font-weight: 700; }
</style>
