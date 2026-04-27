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
        <img src="/sellynx-logo.svg" alt="SELLYNX" />
      </div>

      <nav class="sidebar-nav">
        <RouterLink to="/search" class="nav-item" :class="{ active: $route.path === '/search' }">
          <span class="nav-icon">🔍</span>
          <span>Search Company</span>
        </RouterLink>
        <RouterLink to="/recommendations" class="nav-item" :class="{ active: $route.path === '/recommendations' }">
          <span class="nav-icon">💡</span>
          <span>Recommendations</span>
        </RouterLink>
        <RouterLink to="/reports" class="nav-item" :class="{ active: $route.path === '/reports' }">
          <span class="nav-icon">📄</span>
          <span>Reports</span>
        </RouterLink>
        <RouterLink to="/settings" class="nav-item" :class="{ active: $route.path === '/settings' }">
          <span class="nav-icon">⚙️</span>
          <span>Settings</span>
        </RouterLink>
      </nav>

      <div class="sidebar-bottom">
        <button class="logout-btn" @click="logout">
          <span class="nav-icon">↪</span>
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
import { useAuth } from '../auth/useAuth'
defineProps({ title: String, subtitle: String })
const { user, logout } = useAuth()
</script>

<style scoped>
/* ══════════════════════════════════════
   ROOT
══════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

.app-layout {
  display: flex; min-height: 100vh;
  font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
  color: #fff;
  background: #060E1A;
}

/* ══════════════════════════════════════
   GLOBAL FIXED BACKGROUND CANVAS
══════════════════════════════════════ */
.bg-canvas {
  position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden;
}
.bg-solid { position: absolute; inset: 0; background: #060E1A; }
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
.sidebar-logo img { height: 34px; }

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

/* Topbar — glassmorphism strip */
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 36px;
  border-bottom: 1px solid rgba(255,255,255,0.07);
  background: rgba(6,14,26,0.65);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  position: sticky; top: 0; z-index: 40;
}
.page-title { font-size: 20px; font-weight: 700; color: #fff; }
.page-sub   { font-size: 13px; color: rgba(255,255,255,0.35); margin-top: 2px; }

.topbar-user { display: flex; align-items: center; gap: 12px; }
.user-info   { text-align: right; }
.user-name   { display: block; font-size: 13.5px; font-weight: 600; color: #fff; }
.user-role   { display: block; font-size: 12px; color: rgba(255,255,255,0.35); }

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
  background: none; border: 1px solid rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.35); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.18s; margin-left: 4px;
}
.logout-icon-btn:hover { color: #E8622C; border-color: rgba(232,98,44,0.3); background: rgba(232,98,44,0.08); }

/* Content area — transparent so bg-canvas shows through */
.content { flex: 1; padding: 32px 36px; }
</style>
