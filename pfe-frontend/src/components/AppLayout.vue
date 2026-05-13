<template>
  <div class="app-layout">

    <!-- ══════════════════════════════════════════
         GLOBAL FIXED BACKGROUND (same as Login)
    ══════════════════════════════════════════ -->
    <div class="bg-canvas" aria-hidden="true">
      <div class="bg-solid"></div>
      <div class="bg-noise"></div>
      <div class="blob blob-a"></div>
      <div class="blob blob-b"></div>
      <div class="blob blob-c"></div>
      <div class="blob blob-d"></div>
      <div class="global-waves">
        <svg class="gwave gw1" viewBox="0 0 1440 900" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0,450 C180,320 360,580 540,450 C720,320 900,580 1080,450 C1260,320 1380,500 1440,450 L1440,900 L0,900 Z"/>
        </svg>
        <svg class="gwave gw2" viewBox="0 0 1440 900" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0,600 C240,480 480,700 720,600 C960,500 1200,700 1440,600 L1440,900 L0,900 Z"/>
        </svg>
        <svg class="gwave gw3" viewBox="0 0 1440 900" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0,720 C200,650 400,790 600,720 C800,650 1000,790 1200,720 C1320,680 1400,750 1440,720 L1440,900 L0,900 Z"/>
        </svg>
        <svg class="gwave gw4" viewBox="0 0 1440 900" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0,300 C300,180 600,420 900,300 C1100,220 1280,380 1440,300 L1440,900 L0,900 Z"/>
        </svg>
      </div>
    </div>

    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-logo">
        <img :src="theme === 'light' ? '/sellynx-logo-light.svg' : '/sellynx-logo.svg'" alt="SELLYNX" />
      </div>

      <nav class="sidebar-nav">
        <RouterLink to="/search" class="nav-item" :class="{ active: $route.path === '/search' }">
          <span class="nav-icon">
            <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
              <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
              <circle cx="19.5" cy="19.5" r="2.5" stroke-width="1.5"/>
              <path d="M21.5 21.5l-1.5-1.5" stroke-width="1.8"/>
            </svg>
          </span>
          <span>Search Client</span>
        </RouterLink>

        <RouterLink to="/campaigns" class="nav-item" :class="{ active: $route.path === '/campaigns' }">
          <span class="nav-icon">
            <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
              <path d="M3 3h18v4H3z"/>
              <path d="M3 10h12v4H3z"/>
              <path d="M3 17h7v4H3z"/>
              <circle cx="19" cy="19" r="3"/>
              <path d="M21 21l-1.5-1.5"/>
            </svg>
          </span>
          <span>Campaigns</span>
        </RouterLink>

        <RouterLink to="/recommendations" class="nav-item" :class="{ active: $route.path === '/recommendations' }">
          <span class="nav-icon">
            <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
          </span>
          <span>Recommendations</span>
        </RouterLink>

        <RouterLink to="/reports" class="nav-item" :class="{ active: $route.path === '/reports' }">
          <span class="nav-icon">
            <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
          </span>
          <span>Reports</span>
        </RouterLink>

        <RouterLink to="/settings" class="nav-item" :class="{ active: $route.path === '/settings' }">
          <span class="nav-icon">
            <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>
            </svg>
          </span>
          <span>Settings</span>
        </RouterLink>

        <RouterLink v-if="hasRole('admin')" to="/admin" class="nav-item nav-item-admin" :class="{ active: $route.path.startsWith('/admin') }">
          <span class="nav-icon">
            <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </span>
          <span>Admin</span>
        </RouterLink>
      </nav>

      <div class="sidebar-bottom">
        <!-- Theme toggle -->
        <button class="theme-toggle" @click="toggleTheme" :title="theme === 'dark' ? 'Passer en mode clair' : 'Passer en mode sombre'">
          <span class="theme-toggle-track" :class="{ light: theme === 'light' }">
            <span class="theme-toggle-thumb">
              <!-- Sun icon (light) -->
              <svg v-if="theme === 'light'" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
              <!-- Moon icon (dark) -->
              <svg v-else width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>
              </svg>
            </span>
          </span>
          <span class="theme-toggle-label">{{ theme === 'dark' ? 'Mode sombre' : 'Mode clair' }}</span>
        </button>

        <button class="logout-btn" @click="logout">
          <span class="nav-icon">
            <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
          </span>
          <span>Logout</span>
        </button>
      </div>
    </aside>

    <!-- Main -->
    <div class="main-wrap">
      <!-- Topbar -->
      <header class="topbar">
        <div class="topbar-left">
          <h1 class="page-title">{{ title }}</h1>
          <p class="page-sub">{{ subtitle }}</p>
        </div>
        <div class="topbar-user">
          <div class="user-info">
            <span class="user-name">{{ user?.name || 'Loading…' }}</span>
            <span class="user-role">{{ user?.email || '' }}</span>
          </div>
          <div class="user-avatar" :title="user?.email">{{ user?.initials || '?' }}</div>
          <button class="logout-icon-btn" title="Sign out" @click="logout">
            <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="16 17 21 12 16 7" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="21" y1="12" x2="9" y2="12" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
      </header>

      <!-- Page content -->
      <main class="content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuth } from '../auth/useAuth'
import { useNotifications } from '../composables/useNotifications'
import { useTheme } from '../composables/useTheme'

defineProps({ title: String, subtitle: String })
const { user, logout, hasRole } = useAuth()
const { requestPermission } = useNotifications()
const { theme, toggle: toggleTheme } = useTheme()

// Ask notification permission once the user is logged in
onMounted(async () => {
  await requestPermission()
})
</script>

<style scoped>
/* ══════════════════════════════════════
   ROOT
══════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

.app-layout {
  display: flex; min-height: 100vh;
  font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
  color: var(--text-primary);
  background: var(--bg-app);
}

/* ══════════════════════════════════════
   GLOBAL FIXED BACKGROUND CANVAS
══════════════════════════════════════ */
.bg-canvas {
  position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden;
}
.bg-solid { position: absolute; inset: 0; background: var(--bg-app); }
[data-theme="light"] .bg-noise { opacity: 0.006; }

/* Blobs — couleurs claires pastel */
[data-theme="light"] .blob-a { background: radial-gradient(circle, rgba(219,234,254,0.8) 0%, transparent 70%); filter: blur(100px); opacity: 0.9; }
[data-theme="light"] .blob-b { background: radial-gradient(circle, rgba(237,233,254,0.7) 0%, transparent 70%); filter: blur(100px); opacity: 0.9; }
[data-theme="light"] .blob-c { background: radial-gradient(circle, rgba(255,237,230,0.8) 0%, transparent 70%); filter: blur(90px);  opacity: 0.9; }
[data-theme="light"] .blob-d { background: radial-gradient(circle, rgba(220,240,255,0.7) 0%, transparent 70%); filter: blur(110px); opacity: 0.9; }

/* Waves — dégradé blanc sur fond clair */
[data-theme="light"] .gw1 { fill: rgba(255,255,255,0.68); }
[data-theme="light"] .gw2 { fill: rgba(255,255,255,0.50); }
[data-theme="light"] .gw3 { fill: rgba(255,255,255,0.42); }
[data-theme="light"] .gw4 { fill: rgba(255,255,255,0.60); }
.bg-noise {
  position: absolute; inset: 0; opacity: 0.025;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-size: 200px;
}

/* Blobs */
.blob { position: absolute; border-radius: 50%; pointer-events: none; filter: blur(120px); }
.blob-a {
  width: 700px; height: 700px;
  background: radial-gradient(circle, rgba(59,91,219,0.22) 0%, transparent 70%);
  bottom: 0%; left: -8%;
  animation: float1 13s ease-in-out infinite alternate;
}
.blob-b {
  width: 500px; height: 500px;
  background: radial-gradient(circle, rgba(124,58,237,0.16) 0%, transparent 70%);
  top: 25%; left: 30%;
  animation: float2 17s ease-in-out infinite alternate;
}
.blob-c {
  width: 380px; height: 380px;
  background: radial-gradient(circle, rgba(232,98,44,0.14) 0%, transparent 70%);
  top: 8%; right: 4%;
  animation: float3 11s ease-in-out infinite alternate;
}
.blob-d {
  width: 450px; height: 450px;
  background: radial-gradient(circle, rgba(59,130,246,0.11) 0%, transparent 70%);
  bottom: 18%; right: -4%;
  animation: float1 15s ease-in-out infinite alternate-reverse;
}
@keyframes float1 { to { transform: translate(50px,-40px) scale(1.07); } }
@keyframes float2 { to { transform: translate(-40px,35px) scale(0.93); } }
@keyframes float3 { to { transform: translate(35px,-55px) scale(1.15); } }

/* Waves */
.global-waves { position: absolute; inset: 0; }
.gwave { position: absolute; left: 0; width: 100%; height: 100%; }
.gw1 {
  fill: rgba(59,91,219,0.07);
  animation: waveFlow1 5s ease-in-out infinite alternate;
  transform-origin: center bottom;
}
.gw2 {
  fill: rgba(124,58,237,0.055);
  animation: waveFlow2 7s ease-in-out infinite alternate-reverse;
  transform-origin: center bottom;
}
.gw3 {
  fill: rgba(232,98,44,0.045);
  animation: waveFlow3 4s ease-in-out infinite alternate;
  transform-origin: center bottom;
}
.gw4 {
  fill: rgba(59,130,246,0.04);
  animation: waveFlow4 9s ease-in-out infinite alternate-reverse;
  transform-origin: center bottom;
}
@keyframes waveFlow1 {
  0%   { transform: translateX(0%)   scaleY(1)    scaleX(1); }
  25%  { transform: translateX(-5%)  scaleY(1.08) scaleX(1.04); }
  75%  { transform: translateX(4%)   scaleY(0.93) scaleX(0.97); }
  100% { transform: translateX(-7%)  scaleY(1.11) scaleX(1.05); }
}
@keyframes waveFlow2 {
  0%   { transform: translateX(0%)   scaleY(1)    scaleX(1); }
  30%  { transform: translateX(7%)   scaleY(1.09) scaleX(1.05); }
  65%  { transform: translateX(-4%)  scaleY(0.92) scaleX(0.96); }
  100% { transform: translateX(6%)   scaleY(1.12) scaleX(1.06); }
}
@keyframes waveFlow3 {
  0%   { transform: translateX(0%)   scaleY(1)    scaleX(1); }
  40%  { transform: translateX(-6%)  scaleY(1.13) scaleX(1.06); }
  100% { transform: translateX(5%)   scaleY(0.90) scaleX(0.95); }
}
@keyframes waveFlow4 {
  0%   { transform: translateX(0%)   scaleY(1)    scaleX(1); }
  20%  { transform: translateX(8%)   scaleY(1.07) scaleX(1.04); }
  55%  { transform: translateX(-5%)  scaleY(0.94) scaleX(1.03); }
  100% { transform: translateX(7%)   scaleY(1.10) scaleX(0.96); }
}

/* ══════════════════════════════════════
   SIDEBAR — glassmorphism panel
══════════════════════════════════════ */
.sidebar {
  width: 230px; flex-shrink: 0;
  background: rgba(6,14,26,0.75);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid rgba(255,255,255,0.07);
  display: flex; flex-direction: column;
  position: fixed; top: 0; left: 0; bottom: 0; z-index: 50;
}
.sidebar-logo { padding: 24px 20px 20px; border-bottom: 1px solid rgba(255,255,255,0.06); }
.sidebar-logo img { height: 56px; }

.sidebar-nav { flex: 1; padding: 16px 12px; display: flex; flex-direction: column; gap: 4px; }
.nav-item {
  display: flex; align-items: center; gap: 12px;
  padding: 11px 14px; border-radius: 10px;
  color: rgba(255,255,255,0.45); font-size: 14px; font-weight: 500;
  text-decoration: none; transition: all 0.18s;
}
.nav-item:hover { color: rgba(255,255,255,0.8); background: rgba(255,255,255,0.06); }
.nav-item.active {
  color: #fff;
  background: rgba(232,98,44,0.15);
  border: 1px solid rgba(232,98,44,0.22);
  box-shadow: 0 0 20px rgba(232,98,44,0.08);
}
.nav-icon { font-size: 15px; width: 20px; text-align: center; }

.nav-item-admin { margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 14px; }

.sidebar-bottom { padding: 16px 12px; border-top: 1px solid rgba(255,255,255,0.06); }
.logout-btn {
  display: flex; align-items: center; gap: 12px; width: 100%;
  padding: 11px 14px; border-radius: 10px;
  color: rgba(255,255,255,0.35); font-size: 14px; font-weight: 500;
  background: none; border: none; cursor: pointer; transition: all 0.18s;
}
.logout-btn:hover { color: #E8622C; background: rgba(232,98,44,0.08); }

/* ══════════════════════════════════════
   MAIN CONTENT AREA
══════════════════════════════════════ */
.main-wrap {
  flex: 1; margin-left: 230px;
  display: flex; flex-direction: column; min-height: 100vh;
  position: relative; z-index: 1;
}

/* Topbar */
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 36px;
  border-bottom: 1px solid var(--border);
  background: var(--topbar-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  position: sticky; top: 0; z-index: 40;
}
.page-title { font-size: 20px; font-weight: 700; color: var(--text-primary); }
.page-sub   { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }

.topbar-user { display: flex; align-items: center; gap: 12px; }
.user-info   { text-align: right; }
.user-name   { display: block; font-size: 13.5px; font-weight: 600; color: var(--text-primary); }
.user-role   { display: block; font-size: 12px; color: var(--text-muted); }

.user-avatar {
  width: 38px; height: 38px; border-radius: 50%;
  background: linear-gradient(135deg, #E8622C, #ff8c5a);
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; color: #fff;
  cursor: default; user-select: none;
  box-shadow: 0 0 16px rgba(232,98,44,0.3);
}

.logout-icon-btn {
  width: 34px; height: 34px; border-radius: 8px;
  background: none; border: 1px solid var(--border);
  color: var(--text-muted); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.18s; margin-left: 4px;
}
.logout-icon-btn:hover { color: #E8622C; border-color: rgba(232,98,44,0.3); background: rgba(232,98,44,0.08); }

/* Content area */
.content { flex: 1; padding: 32px 36px; }

/* ── Theme toggle ── */
.theme-toggle {
  display: flex; align-items: center; gap: 10px;
  width: 100%; padding: 10px 12px; margin-bottom: 8px;
  background: none; border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px; cursor: pointer; color: rgba(255,255,255,0.5);
  font-size: 12.5px; transition: all 0.18s;
}
.theme-toggle:hover { color: rgba(255,255,255,0.8); border-color: rgba(255,255,255,0.15); }

.theme-toggle-track {
  width: 36px; height: 20px; border-radius: 99px; flex-shrink: 0;
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.15);
  position: relative; transition: background 0.25s;
}
.theme-toggle-track.light {
  background: linear-gradient(135deg, #FCD34D, #F59E0B);
  border-color: #F59E0B;
}
.theme-toggle-thumb {
  position: absolute; top: 2px; left: 2px;
  width: 14px; height: 14px; border-radius: 50%;
  background: rgba(255,255,255,0.9);
  display: flex; align-items: center; justify-content: center;
  color: #1B2A4A;
  transition: transform 0.25s cubic-bezier(0.34,1.56,0.64,1);
}
.theme-toggle-track.light .theme-toggle-thumb {
  transform: translateX(16px);
  background: #fff;
}
.theme-toggle-label { font-size: 12px; color: rgba(255,255,255,0.45); }
</style>
