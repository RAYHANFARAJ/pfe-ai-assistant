<template>
  <div class="admin-shell">

    <!-- Background canvas -->
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
        <button
          v-for="tab in tabs" :key="tab.key"
          class="nav-item" :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <span class="nav-icon" v-html="tab.svg"></span>
          <span class="nav-label">{{ tab.label }}</span>
          <span v-if="activeTab === tab.key" class="nav-active-bar"></span>
        </button>
      </nav>

      <div class="sidebar-footer">
        <router-link to="/search" class="back-link">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/></svg>
          Back to app
        </router-link>
      </div>
    </aside>

    <!-- Main -->
    <main class="admin-main">
      <header class="admin-topbar">
        <div>
          <h1 class="topbar-title">{{ currentTab.label }}</h1>
          <p class="topbar-sub">{{ currentTab.desc }}</p>
        </div>
      </header>
      <div class="admin-content">
        <ProductsTab  v-if="activeTab === 'products'" />
        <CampaignsTab v-if="activeTab === 'campaigns'" />
        <SourcesTab   v-if="activeTab === 'sources'" />
        <RolesTab     v-if="activeTab === 'roles'" />
      </div>
    </main>

    <!-- Toast notifications -->
    <teleport to="body">
      <div class="toast-stack">
        <transition-group name="toast">
          <div
            v-for="n in notifications"
            :key="n.id"
            class="toast"
            :class="n.type"
          >
            <svg v-if="n.type === 'success'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M20 6L9 17l-5-5"/>
            </svg>
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>
            </svg>
            {{ n.message }}
          </div>
        </transition-group>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, provide } from 'vue'
import { useRoute } from 'vue-router'
import ProductsTab  from './tabs/ProductsTab.vue'
import CampaignsTab from './tabs/CampaignsTab.vue'
import SourcesTab   from './tabs/SourcesTab.vue'
import RolesTab     from './tabs/RolesTab.vue'
import { useNotify } from './composables/useNotify.js'

const { notifications, success, error } = useNotify()
provide('notify', { success, error })

const route     = useRoute()
const activeTab = ref(route.query.tab || 'products')

watch(() => route.query.tab, (tab) => { if (tab) activeTab.value = tab })

const tabs = [
  {
    key: 'products', label: 'Products & Criteria', desc: 'Manage qualification products and their scoring criteria',
    svg: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/></svg>`,
  },
  {
    key: 'campaigns', label: 'Campaigns', desc: 'View and manage Leyton campaigns linked to products',
    svg: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`,
  },
  {
    key: 'sources', label: 'Data Sources', desc: 'Configure data sources used in the scoring pipeline',
    svg: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>`,
  },
  {
    key: 'roles', label: 'Users & Roles', desc: 'Manage who has admin access to this backoffice',
    svg: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>`,
  },
]

const currentTab = computed(() => tabs.find(t => t.key === activeTab.value) || tabs[0])
</script>

<style scoped>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.admin-shell {
  display: flex;
  height: 100vh;
  font-family: 'Inter', 'Segoe UI', sans-serif;
  color: #fff;
  background: #060E1A;
  overflow: hidden;
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
  width: 240px;
  flex-shrink: 0;
  background: rgba(6,14,26,.8);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid rgba(255,255,255,.07);
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 10;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 24px 20px 20px;
  border-bottom: 1px solid rgba(255,255,255,.06);
}

.brand-icon {
  width: 36px; height: 36px;
  background: linear-gradient(135deg, #E8622C, #ff8c5a);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  box-shadow: 0 0 20px rgba(232,98,44,.35);
}

.brand-name {
  font-size: 1rem;
  font-weight: 700;
  color: #fff;
  letter-spacing: .3px;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 11px 14px;
  background: none;
  border: none;
  border-radius: 10px;
  color: rgba(255,255,255,.4);
  font-size: .875rem;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  transition: all .18s;
}

.nav-item:hover {
  color: rgba(255,255,255,.85);
  background: rgba(255,255,255,.06);
}

.nav-item.active {
  color: #fff;
  background: rgba(232,98,44,.15);
  border: 1px solid rgba(232,98,44,.2);
}

.nav-icon { display: flex; align-items: center; flex-shrink: 0; }
.nav-label { flex: 1; }
.nav-active-bar {
  width: 4px; height: 4px;
  border-radius: 50%;
  background: #E8622C;
  box-shadow: 0 0 8px #E8622C;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255,255,255,.06);
}

.back-link {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(255,255,255,.3);
  font-size: .82rem;
  text-decoration: none;
  transition: color .18s;
}
.back-link:hover { color: rgba(255,255,255,.65); }

/* Main */
.admin-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.admin-topbar {
  padding: 24px 36px 20px;
  border-bottom: 1px solid rgba(255,255,255,.06);
  background: rgba(6,14,26,.5);
  backdrop-filter: blur(16px);
  flex-shrink: 0;
}

.topbar-title { font-size: 1.3rem; font-weight: 700; color: #fff; margin-bottom: 3px; }
.topbar-sub   { font-size: .82rem; color: rgba(255,255,255,.35); }

.admin-content {
  flex: 1;
  overflow-y: auto;
  padding: 28px 36px;
}

/* Toast notifications */
.toast-stack {
  position: fixed;
  bottom: 28px;
  right: 28px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px;
  border-radius: 10px;
  font-size: .875rem;
  font-weight: 600;
  font-family: Inter, sans-serif;
  box-shadow: 0 8px 32px rgba(0,0,0,.4);
  backdrop-filter: blur(12px);
  pointer-events: auto;
}

.toast.success {
  background: rgba(22,163,74,.2);
  border: 1px solid rgba(74,222,128,.3);
  color: #4ade80;
}

.toast.error {
  background: rgba(239,68,68,.2);
  border: 1px solid rgba(248,113,113,.3);
  color: #f87171;
}

.toast-enter-active { transition: all .25s ease; }
.toast-leave-active { transition: all .2s ease; }
.toast-enter-from   { opacity: 0; transform: translateY(12px); }
.toast-leave-to     { opacity: 0; transform: translateX(20px); }

/* ══ LIGHT MODE ══════════════════════════════ */
[data-theme="light"] .admin-shell { background: #F1F5FB; color: #0D1B2E; }
[data-theme="light"] .bg-solid    { background: #F1F5FB; }

/* Blobs adaptés */
[data-theme="light"] .blob-a { background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%); }
[data-theme="light"] .blob-b { background: radial-gradient(circle, rgba(232,98,44,0.12) 0%, transparent 70%); }
[data-theme="light"] .blob-c { background: radial-gradient(circle, rgba(139,92,246,0.12) 0%, transparent 70%); }

/* Sidebar */
[data-theme="light"] .sidebar {
  background: #1B2A4A;
  border-right-color: rgba(255,255,255,0.06);
}
[data-theme="light"] .sidebar-brand { border-bottom-color: rgba(255,255,255,0.08); }
[data-theme="light"] .brand-name    { color: #fff; }
[data-theme="light"] .nav-item      { color: rgba(255,255,255,0.50); }
[data-theme="light"] .nav-item:hover { color: rgba(255,255,255,0.85); background: rgba(255,255,255,0.07); }
[data-theme="light"] .nav-item.active { color: #fff; background: rgba(232,98,44,0.18); border-color: rgba(232,98,44,0.3); }
[data-theme="light"] .sidebar-footer  { border-top-color: rgba(255,255,255,0.08); }
[data-theme="light"] .back-link       { color: rgba(255,255,255,0.45); }
[data-theme="light"] .back-link:hover { color: rgba(255,255,255,0.80); }

/* Topbar */
[data-theme="light"] .admin-topbar {
  background: rgba(241,245,251,0.90);
  border-bottom-color: rgba(13,27,46,0.09);
  backdrop-filter: blur(16px);
}
[data-theme="light"] .topbar-title { color: #0D1B2E; }
[data-theme="light"] .topbar-sub   { color: #3D5068; }

/* Content area */
[data-theme="light"] .admin-content { background: transparent; }
</style>
