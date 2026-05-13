<template>
  <RouterView />
  <NotificationToast />
</template>

<script setup>
import { RouterView } from 'vue-router'
import NotificationToast from './components/NotificationToast.vue'
import { useTheme } from './composables/useTheme'
const { init } = useTheme()
init()
</script>

<style>
/* ══════════════════════════════════════════════════
   CSS Variables — Dark (default)
══════════════════════════════════════════════════ */
:root {
  --bg-app:         #060E1A;
  --bg-card:        rgba(255,255,255,0.03);
  --bg-card-hover:  rgba(255,255,255,0.05);
  --bg-input:       rgba(255,255,255,0.04);
  --bg-dropdown:    #0d1f38;
  --text-primary:   #ffffff;
  --text-secondary: rgba(255,255,255,0.5);
  --text-muted:     rgba(255,255,255,0.25);
  --border:         rgba(255,255,255,0.08);
  --border-light:   rgba(255,255,255,0.04);
  --shadow:         0 4px 24px rgba(0,0,0,0.4);
  --topbar-bg:      rgba(6,14,26,0.85);
  --accent:         #E8622C;
  --accent-soft:    rgba(232,98,44,0.12);
  color-scheme: dark;
}

/* ══════════════════════════════════════════════════
   CSS Variables — Light
══════════════════════════════════════════════════ */
[data-theme="light"] {
  --bg-app:         #F1F5FB;
  --bg-card:        #FFFFFF;
  --bg-card-hover:  #F8FAFF;
  --bg-input:       #F8FAFC;
  --bg-dropdown:    #FFFFFF;
  --text-primary:   #0D1B2E;
  --text-secondary: #3D5068;
  --text-muted:     #7C93AE;
  --border:         rgba(13,27,46,0.10);
  --border-light:   rgba(13,27,46,0.05);
  --shadow:         0 2px 16px rgba(13,27,46,0.09);
  --topbar-bg:      rgba(241,245,251,0.94);
  --accent:         #E8622C;
  --accent-soft:    rgba(232,98,44,0.10);
  color-scheme: light;
}

/* ══════════════════════════════════════════════════
   Global resets
══════════════════════════════════════════════════ */
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg-app);
  font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
  color: var(--text-primary);
}

#app {
  width: 100% !important; max-width: 100% !important; margin: 0 !important;
  text-align: left !important; border: none !important; min-height: 100vh !important;
  display: block !important; background: var(--bg-app);
}

/* Smooth theme transition — only on structural elements */
.main-wrap, .content, .topbar, .page,
[class*="-card"], [class*="-wrap"], [class*="-section"],
[class*="-row"], [class*="-grid"], [class*="-list"],
.dropdown, .modal, .table, table {
  transition: background-color 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
}

/* ══════════════════════════════════════════════════
   LIGHT MODE — Global overrides
   Fixes hardcoded white text & transparent backgrounds
══════════════════════════════════════════════════ */

/* Main content area — transparent so waves show through */
[data-theme="light"] .main-wrap  { color: #0D1B2E; background: transparent !important; }
[data-theme="light"] .content    { background: transparent !important; }
[data-theme="light"] .app-layout { background: transparent !important; }

/* Cards — white with shadow */
[data-theme="light"] [class*="-card"],
[data-theme="light"] [class*="-wrap"]:not(.autocomplete-wrap):not(.search-wrap):not(.pag-bar-wrap):not(.main-wrap):not(.app-layout),
[data-theme="light"] [class*="-section"],
[data-theme="light"] .batch-launch-card,
[data-theme="light"] .doc-upload-zone,
[data-theme="light"] .config-row,
[data-theme="light"] .mode-selector,
[data-theme="light"] .product-select-card,
[data-theme="light"] .targets-table-wrap,
[data-theme="light"] .kpi-row > *,
[data-theme="light"] .results-section > *:not(.results-title),
[data-theme="light"] .scoring-experience,
[data-theme="light"] .progress-op {
  background: #FFFFFF !important;
  border-color: rgba(15,23,42,0.09) !important;
  box-shadow: 0 1px 6px rgba(15,23,42,0.06) !important;
}

/* Text resets — fix hardcoded white */
[data-theme="light"] h1, [data-theme="light"] h2, [data-theme="light"] h3,
[data-theme="light"] .step-title, [data-theme="light"] .batch-launch-title,
[data-theme="light"] .client-bar-name, [data-theme="light"] .results-title,
[data-theme="light"] .kpi-val, [data-theme="light"] .sp-val,
[data-theme="light"] .opp-name, [data-theme="light"] .rc-name,
[data-theme="light"] .company-name, [data-theme="light"] .psc-title,
[data-theme="light"] .rc-score-val, [data-theme="light"] .bpc-name,
[data-theme="light"] .t-name, [data-theme="light"] .cl-name,
[data-theme="light"] .pc-name, [data-theme="light"] .po-title,
[data-theme="light"] .products-title, [data-theme="light"] .item-name,
[data-theme="light"] .product-name, [data-theme="light"] .se-count,
[data-theme="light"] .smeta-row strong, [data-theme="light"] .cr-label,
[data-theme="light"] .scoring-step.active { color: #0D1B2E !important; }

/* Batch stat numbers */
[data-theme="light"] .batch-stat-val { color: #0D1B2E !important; }
[data-theme="light"] .batch-stat.success .batch-stat-val { color: #16a34a !important; }
[data-theme="light"] .batch-stat.error   .batch-stat-val { color: #dc2626 !important; }

/* Section title in scoring results */
[data-theme="light"] .section-title { color: #3D5068 !important; }

/* Muted / secondary text */
[data-theme="light"] .step-desc, [data-theme="light"] .batch-launch-sub,
[data-theme="light"] .client-bar-id, [data-theme="light"] .client-bar-emp,
[data-theme="light"] .kpi-lbl, [data-theme="light"] .sp-lbl,
[data-theme="light"] .opp-sector, [data-theme="light"] .rc-date,
[data-theme="light"] .rc-user, [data-theme="light"] .rc-duration,
[data-theme="light"] .t-id, [data-theme="light"] .t-calls,
[data-theme="light"] .psc-selected-count, [data-theme="light"] .preview-label,
[data-theme="light"] .po-phase-label, [data-theme="light"] .po-remaining,
[data-theme="light"] .config-label, [data-theme="light"] .teb-item,
[data-theme="light"] .batch-stat-lbl, [data-theme="light"] .products-sub,
[data-theme="light"] .product-criteria, [data-theme="light"] .se-step-label,
[data-theme="light"] .se-time, [data-theme="light"] .summary-label,
[data-theme="light"] .summary-pts, [data-theme="light"] .cr-val,
[data-theme="light"] .cr-score, [data-theme="light"] .trace-line,
[data-theme="light"] .stream-progress, [data-theme="light"] .scoring-step,
[data-theme="light"] .scoring-step.done, [data-theme="light"] .demo-desc,
[data-theme="light"] .search-hint, [data-theme="light"] .search-hint.active {
  color: #3D5068 !important;
}
[data-theme="light"] .se-time b { color: #0D1B2E !important; }
[data-theme="light"] .stream-progress b { color: #0D1B2E !important; }
[data-theme="light"] .demo-desc strong { color: #0D1B2E !important; }
[data-theme="light"] .cr-val.dim { color: #7C93AE !important; }
[data-theme="light"] .se-mini-id { color: #7C93AE !important; font-family: monospace; }
[data-theme="light"] .search-hint-sep { color: #94A3B8 !important; }

/* Criteria rows inside scoring card / modal */
[data-theme="light"] .smeta-row { color: #3D5068 !important; border-bottom-color: rgba(13,27,46,0.07) !important; }
[data-theme="light"] .smeta-row strong { color: #0D1B2E !important; }
[data-theme="light"] .cr-label  { color: #0D1B2E !important; }
[data-theme="light"] .cr-val    { color: #3D5068 !important; }
[data-theme="light"] .cr-score  { color: #3D5068 !important; }
[data-theme="light"] .cr-type   { color: rgba(232,98,44,0.75) !important; }

/* Inputs & selects */
[data-theme="light"] input:not([type="checkbox"]),
[data-theme="light"] select,
[data-theme="light"] .search-input,
[data-theme="light"] .config-select,
[data-theme="light"] .pag-select {
  background: #FFFFFF !important;
  border-color: rgba(15,23,42,0.15) !important;
  color: #0F172A !important;
}
[data-theme="light"] input::placeholder,
[data-theme="light"] .search-input::placeholder { color: #94A3B8 !important; }

/* Dropdowns */
[data-theme="light"] .dropdown {
  background: #FFFFFF !important;
  border-color: rgba(15,23,42,0.12) !important;
  box-shadow: 0 8px 32px rgba(15,23,42,0.12) !important;
}
[data-theme="light"] .dropdown-item:hover,
[data-theme="light"] .dropdown-item.highlighted {
  background: rgba(232,98,44,0.06) !important;
}
[data-theme="light"] .item-name  { color: #0F172A !important; }
[data-theme="light"] .item-id    { color: #94A3B8 !important; }

/* Tables */
[data-theme="light"] .targets-table thead { background: rgba(15,23,42,0.05) !important; }
[data-theme="light"] .targets-table th    { color: #475569 !important; }
[data-theme="light"] .targets-table td    { border-color: rgba(15,23,42,0.05) !important; }
[data-theme="light"] .targets-table tr:hover td { background: rgba(15,23,42,0.02) !important; }
[data-theme="light"] .targets-table tr.selected td { background: rgba(232,98,44,0.05) !important; }

/* Batch result cards */
[data-theme="light"] .batch-product-card {
  background: #FFFFFF !important;
  border-color: rgba(15,23,42,0.09) !important;
}
[data-theme="light"] .batch-product-card:hover { background: #F8FAFC !important; }
[data-theme="light"] .bpc-id   { color: #94A3B8 !important; }
[data-theme="light"] .bpc-pts  { color: #475569 !important; }

/* Tabs & mode selector */
[data-theme="light"] .mode-tab { color: #475569 !important; }
[data-theme="light"] .mode-tab.active {
  background: rgba(232,98,44,0.10) !important;
  color: #0F172A !important;
  border-color: rgba(232,98,44,0.25) !important;
}
[data-theme="light"] .tab { color: #475569 !important; }
[data-theme="light"] .tab.active {
  background: rgba(232,98,44,0.10) !important;
  color: #0F172A !important;
}

/* Pagination */
[data-theme="light"] .pag-btn {
  border-color: rgba(15,23,42,0.12) !important;
  background: #FFFFFF !important;
  color: #475569 !important;
}
[data-theme="light"] .pag-btn:hover:not(:disabled) { color: #0F172A !important; }
[data-theme="light"] .pag-btn.active { background: #E8622C !important; color: #fff !important; }
[data-theme="light"] .pag-info { color: #94A3B8 !important; }

/* Product chips */
[data-theme="light"] .preview-chip { background: rgba(15,23,42,0.05) !important; border-color: rgba(15,23,42,0.1) !important; color: #0F172A !important; }
[data-theme="light"] .preview-chip-id { color: #E8622C !important; }
[data-theme="light"] .psc-item { background: rgba(255,255,255,0.9) !important; }
[data-theme="light"] .psc-item:hover { background: #F8FAFC !important; }
[data-theme="light"] .psc-id   { color: #E8622C !important; }
[data-theme="light"] .psc-name { color: #475569 !important; }

/* Client bar */
[data-theme="light"] .client-bar {
  background: #FFFFFF !important;
  border-color: rgba(15,23,42,0.09) !important;
}
[data-theme="light"] .change-btn {
  background: #F1F5F9 !important;
  border-color: rgba(15,23,42,0.12) !important;
  color: #475569 !important;
}
[data-theme="light"] .change-btn:hover { color: #0F172A !important; }

/* Search hints */
[data-theme="light"] .search-hint { color: #94A3B8 !important; }
[data-theme="light"] .search-hint.active { color: #475569 !important; }

/* Campaign cards */
[data-theme="light"] .campaign-card {
  background: #FFFFFF !important;
  border-color: rgba(15,23,42,0.09) !important;
}
[data-theme="light"] .campaign-card:hover {
  background: #FFF7F4 !important;
  border-color: rgba(232,98,44,0.25) !important;
}
[data-theme="light"] .cc-title  { color: #0F172A !important; }
[data-theme="light"] .cc-count  { color: #94A3B8 !important; }
[data-theme="light"] .cc-meta span { color: #64748B !important; }

/* Buttons */
[data-theme="light"] .refresh-btn,
[data-theme="light"] .psc-action-btn {
  background: #FFFFFF !important;
  border-color: rgba(15,23,42,0.12) !important;
  color: #475569 !important;
}

/* Empty states */
[data-theme="light"] .empty-title { color: #475569 !important; }
[data-theme="light"] .empty-sub   { color: #94A3B8 !important; }
[data-theme="light"] .empty-icon  { background: #F1F5F9 !important; border-color: rgba(15,23,42,0.08) !important; }

/* Loading */
[data-theme="light"] .loading-center { color: #94A3B8 !important; }

/* Progress phases */
[data-theme="light"] .po-phase-text  { color: #475569 !important; }
[data-theme="light"] .po-elapsed     { color: #0F172A !important; }
[data-theme="light"] .po-bar-track   { background: rgba(15,23,42,0.08) !important; }

/* Modals */
[data-theme="light"] .modal-confirm,
[data-theme="light"] .modal {
  background: #FFFFFF !important;
  border-color: rgba(15,23,42,0.12) !important;
  box-shadow: 0 24px 64px rgba(13,27,46,0.15) !important;
}

/* Modal header — garde le fond dark pour le contraste */
[data-theme="light"] .modal-header {
  background: #FFFFFF !important;
  padding-bottom: 16px !important;
  border-radius: 14px 14px 0 0 !important;
  border-bottom: 1px solid rgba(13,27,46,0.08) !important;
}
[data-theme="light"] .modal-title  { color: #0D1B2E !important; }
[data-theme="light"] .modal-close  { background: transparent !important; border: none !important; color: #7C93AE !important; }
[data-theme="light"] .modal-close:hover { background: rgba(13,27,46,0.06) !important; color: #0D1B2E !important; }

/* Modal body content */
[data-theme="light"] .modal-body { background: #FFFFFF !important; }
[data-theme="light"] .modal-row  { border-bottom-color: rgba(13,27,46,0.08) !important; }
[data-theme="light"] .modal-text { color: #3D5068 !important; }
[data-theme="light"] .modal-quote {
  background: rgba(232,98,44,0.05) !important;
  color: #475569 !important;
  border-left-color: #E8622C !important;
}
[data-theme="light"] .modal-section { color: #3D5068 !important; }

/* Modal row label (.ml) and value (.mv) */
[data-theme="light"] .ml { color: #7C93AE !important; }
[data-theme="light"] .mv { color: #0D1B2E !important; }

/* Confirm modal */
[data-theme="light"] .modal-confirm-title { color: #0D1B2E !important; }
[data-theme="light"] .modal-confirm-sub   { color: #3D5068 !important; }

[data-theme="light"] .btn-cancel {
  background: #F1F5F9 !important;
  border-color: rgba(13,27,46,0.12) !important;
  color: #3D5068 !important;
}

/* Reports page */
[data-theme="light"] .report-card {
  background: #FFFFFF !important;
  border-color: rgba(15,23,42,0.09) !important;
}
[data-theme="light"] .report-card:hover { background: #FAFCFF !important; }
[data-theme="light"] .stat-pill.total   { background: #F1F5F9 !important; border-color: rgba(15,23,42,0.1) !important; color: #475569 !important; }
[data-theme="light"] .rc-meta span      { color: #94A3B8 !important; }

/* Recommendations */
[data-theme="light"] .opp-card {
  background: #FFFFFF !important;
  border-color: rgba(15,23,42,0.08) !important;
}
[data-theme="light"] .kpi-card { box-shadow: 0 1px 4px rgba(15,23,42,0.07) !important; }
[data-theme="light"] .tabs {
  background: #FFFFFF !important;
  border-color: rgba(15,23,42,0.09) !important;
}
[data-theme="light"] .product-card { background: #FFFFFF !important; border-color: rgba(15,23,42,0.08) !important; }
[data-theme="light"] .client-card  { background: #FFFFFF !important; border-color: rgba(15,23,42,0.08) !important; }
[data-theme="light"] .opp-arrow    { color: #CBD5E1 !important; }
[data-theme="light"] .opp-rank     { background: #F1F5F9 !important; border-color: rgba(15,23,42,0.1) !important; color: #64748B !important; }

/* Error bars */
[data-theme="light"] .error-bar { background: rgba(239,68,68,0.08) !important; border-color: rgba(239,68,68,0.2) !important; }

/* ══════════════════════════════════════════════════
   LIGHT MODE — Sidebar
   Sidebar — fond bleu-ardoise professionnel
══════════════════════════════════════════════════ */
[data-theme="light"] .sidebar {
  background: #C8D9EE !important;
  border-right: 1px solid rgba(13,27,46,0.08) !important;
  backdrop-filter: none !important;
  box-shadow: 4px 0 20px rgba(13,27,46,0.10) !important;
}

[data-theme="light"] .sidebar-logo {
  border-bottom-color: rgba(255,255,255,0.08) !important;
}

[data-theme="light"] .nav-item {
  color: #3A5070 !important;
}
[data-theme="light"] .nav-item:hover {
  color: #0D1B2E !important;
  background: rgba(13,27,46,0.08) !important;
}
[data-theme="light"] .nav-item.active {
  color: #E8622C !important;
  background: rgba(232,98,44,0.14) !important;
  border-color: rgba(232,98,44,0.28) !important;
  box-shadow: 0 0 12px rgba(232,98,44,0.08) !important;
}
[data-theme="light"] .nav-item.active svg { stroke: #E8622C !important; }
[data-theme="light"] .nav-item:not(.active) svg { stroke: #5A7A9A !important; }
[data-theme="light"] .nav-item:hover svg { stroke: #0D1B2E !important; }

[data-theme="light"] .nav-item-admin {
  border-top-color: rgba(13,27,46,0.10) !important;
}

[data-theme="light"] .sidebar-bottom {
  border-top-color: rgba(13,27,46,0.10) !important;
}

[data-theme="light"] .logout-btn {
  color: #5A7A9A !important;
}
[data-theme="light"] .logout-btn:hover {
  color: #E8622C !important;
  background: rgba(232,98,44,0.10) !important;
}
[data-theme="light"] .logout-btn svg { stroke: currentColor !important; }

[data-theme="light"] .theme-toggle {
  border-color: rgba(13,27,46,0.12) !important;
  color: #3A5070 !important;
}
[data-theme="light"] .theme-toggle:hover {
  color: #0D1B2E !important;
  border-color: rgba(13,27,46,0.22) !important;
  background: rgba(13,27,46,0.06) !important;
}
[data-theme="light"] .theme-toggle-track {
  background: rgba(13,27,46,0.15) !important;
  border-color: rgba(13,27,46,0.18) !important;
}
[data-theme="light"] .theme-toggle-label { color: #5A7A9A !important; }
[data-theme="light"] .sidebar-logo { border-bottom-color: rgba(13,27,46,0.10) !important; }
</style>
