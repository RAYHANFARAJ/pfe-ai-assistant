/**
 * useProgress — phase-based progress tracking for long operations.
 *
 * Provides:
 *  - phases[]        : list of steps with label, icon, duration estimate
 *  - currentPhase    : index of active phase
 *  - pct             : 0–100 smooth progress percentage
 *  - elapsed         : seconds since start
 *  - remaining       : estimated seconds left
 *  - start(preset)   : begin operation with a named phase set
 *  - advance()       : move to next phase (called by real events)
 *  - finish()        : complete all phases
 *  - reset()         : clear state
 */
import { ref, computed, readonly } from 'vue'

// ── Phase presets ──────────────────────────────────────────────────────────────
export const PRESETS = {
  batch_scoring: [
    { label: 'Identification du client',        icon: '🔍', seconds: 1,  pct: 5  },
    { label: 'Collecte — web, LinkedIn, news',  icon: '🌐', seconds: 12, pct: 25 },
    { label: 'Vectorisation des sources',       icon: '🧠', seconds: 5,  pct: 40 },
    { label: 'Évaluation des critères par IA',  icon: '🤖', seconds: 35, pct: 88 },
    { label: 'Calcul des scores finaux',        icon: '📊', seconds: 3,  pct: 96 },
    { label: 'Finalisation',                    icon: '✅', seconds: 1,  pct: 100 },
  ],

  pdf_generation: [
    { label: 'Préparation du rapport',           icon: '📋', seconds: 2,  pct: 15 },
    { label: 'Génération des explications IA',   icon: '🤖', seconds: 18, pct: 70 },
    { label: 'Mise en forme PDF',                icon: '🎨', seconds: 5,  pct: 92 },
    { label: 'Sauvegarde dans l\'historique',    icon: '💾', seconds: 1,  pct: 100 },
  ],

  campaign_scoring: [
    { label: 'Chargement des clients',           icon: '👥', seconds: 2,  pct: 10 },
    { label: 'Vérification du cache',            icon: '⚡', seconds: 1,  pct: 20 },
    { label: 'Scoring IA des clients',           icon: '🤖', seconds: 45, pct: 90 },
    { label: 'Classement par priorité',          icon: '📊', seconds: 1,  pct: 100 },
  ],
}

// ── Composable ────────────────────────────────────────────────────────────────
export function useProgress() {
  const phases        = ref([])
  const currentPhase  = ref(-1)
  const pct           = ref(0)
  const elapsed       = ref(0)
  const active        = ref(false)

  let _elapsedTimer  = null
  let _phaseTimer    = null
  let _smoothTimer   = null
  let _startedAt     = 0
  let _targetPct     = 0

  // ── Total estimated duration ───────────────────────────────────────────────
  const totalSeconds  = computed(() => phases.value.reduce((s, p) => s + (p.seconds || 2), 0))
  const remaining     = computed(() => {
    if (!active.value) return 0
    const est = totalSeconds.value - elapsed.value
    return Math.max(0, Math.round(est))
  })
  const remainingLabel = computed(() => {
    const s = remaining.value
    if (s <= 0) return 'Finalisation…'
    if (s < 60) return `~${s}s restante${s > 1 ? 's' : ''}`
    return `~${Math.ceil(s / 60)} min restante${Math.ceil(s / 60) > 1 ? 's' : ''}`
  })

  // ── Start ──────────────────────────────────────────────────────────────────
  function start(presetName) {
    reset()
    phases.value    = (PRESETS[presetName] || []).map((p, i) => ({ ...p, index: i, done: false }))
    active.value    = true
    currentPhase.value = 0
    _targetPct      = phases.value[0]?.pct ?? 5
    _startedAt      = Date.now()

    // Elapsed counter
    _elapsedTimer = setInterval(() => { elapsed.value = Math.round((Date.now() - _startedAt) / 1000) }, 1000)

    // Smooth progress animation toward target
    _smoothTimer = setInterval(() => {
      if (pct.value < _targetPct) {
        pct.value = Math.min(_targetPct, pct.value + 0.5)
      }
    }, 80)

    // Auto-advance phases based on estimated durations
    _scheduleNextPhase()
  }

  function _scheduleNextPhase() {
    const idx = currentPhase.value
    if (idx < 0 || idx >= phases.value.length - 1) return
    const duration = (phases.value[idx]?.seconds ?? 2) * 1000
    _phaseTimer = setTimeout(() => {
      if (!active.value) return
      _advanceToPhase(idx + 1)
    }, duration)
  }

  function _advanceToPhase(idx) {
    if (idx < 0 || idx >= phases.value.length) return
    if (currentPhase.value >= 0) phases.value[currentPhase.value].done = true
    currentPhase.value = idx
    _targetPct = phases.value[idx]?.pct ?? pct.value
    _scheduleNextPhase()
  }

  // ── Public controls ────────────────────────────────────────────────────────
  function advance() {
    // Called by a real event (e.g. SSE context_ready) — skip timer
    clearTimeout(_phaseTimer)
    _advanceToPhase(currentPhase.value + 1)
  }

  function setPhase(idx) {
    // Jump to a specific phase index
    clearTimeout(_phaseTimer)
    while (currentPhase.value < idx) _advanceToPhase(currentPhase.value + 1)
  }

  function setProductProgress(done, total) {
    // Called per SSE product_result — update pct within phase 4
    if (!total) return
    const p4start = phases.value[2]?.pct ?? 40
    const p4end   = phases.value[3]?.pct ?? 88
    _targetPct = p4start + Math.round((done / total) * (p4end - p4start))
  }

  function finish() {
    clearTimeout(_phaseTimer)
    clearInterval(_elapsedTimer)
    phases.value.forEach(p => { p.done = true })
    currentPhase.value = phases.value.length
    _targetPct = 100
    setTimeout(() => {
      clearInterval(_smoothTimer)
      pct.value = 100
      active.value = false
    }, 800)
  }

  function reset() {
    clearTimeout(_phaseTimer)
    clearInterval(_elapsedTimer)
    clearInterval(_smoothTimer)
    phases.value    = []
    currentPhase.value = -1
    pct.value       = 0
    elapsed.value   = 0
    active.value    = false
    _targetPct      = 0
  }

  return {
    phases:        readonly(phases),
    currentPhase:  readonly(currentPhase),
    pct:           readonly(pct),
    elapsed:       readonly(elapsed),
    active:        readonly(active),
    remaining,
    remainingLabel,
    totalSeconds,
    start,
    advance,
    setPhase,
    setProductProgress,
    finish,
    reset,
  }
}
