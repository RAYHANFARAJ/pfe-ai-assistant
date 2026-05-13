<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="toast"
          :class="`toast-${t.type}`"
          @click="removeToast(t.id)"
        >
          <!-- Icon -->
          <div class="toast-icon">
            <svg v-if="t.type === 'success'" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            <svg v-else-if="t.type === 'info'" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <svg v-else-if="t.type === 'error'" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            <svg v-else width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/>
            </svg>
          </div>

          <!-- Content -->
          <div class="toast-content">
            <div class="toast-title">{{ t.title }}</div>
            <div v-if="t.body" class="toast-body">{{ t.body }}</div>
          </div>

          <!-- Close -->
          <button class="toast-close" @click.stop="removeToast(t.id)">✕</button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useNotifications } from '../composables/useNotifications'
const { toasts, removeToast } = useNotifications()
</script>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 14px;
  backdrop-filter: blur(16px);
  border: 1px solid;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  min-width: 280px;
  max-width: 380px;
  cursor: pointer;
  pointer-events: all;
  transition: all 0.2s;
}
.toast:hover { transform: translateY(-2px); box-shadow: 0 12px 40px rgba(0,0,0,0.5); }

.toast-success { background: rgba(10,30,20,0.92); border-color: rgba(34,197,94,0.35); }
.toast-info    { background: rgba(10,20,40,0.92); border-color: rgba(99,179,237,0.35); }
.toast-error   { background: rgba(30,10,10,0.92); border-color: rgba(239,68,68,0.35); }
.toast-warning { background: rgba(30,20,5,0.92);  border-color: rgba(245,158,11,0.35); }

.toast-icon {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.toast-success .toast-icon { background: rgba(34,197,94,0.15);  color: #22c55e; }
.toast-info    .toast-icon { background: rgba(99,179,237,0.15); color: #63b3ed; }
.toast-error   .toast-icon { background: rgba(239,68,68,0.15);  color: #f87171; }
.toast-warning .toast-icon { background: rgba(245,158,11,0.15); color: #f59e0b; }

.toast-content { flex: 1; min-width: 0; }
.toast-title   { font-size: 13px; font-weight: 700; color: #fff; margin-bottom: 2px; }
.toast-body    { font-size: 12px; color: rgba(255,255,255,0.55); line-height: 1.5; }

.toast-close {
  background: none;
  border: none;
  color: rgba(255,255,255,0.3);
  font-size: 13px;
  cursor: pointer;
  padding: 0;
  flex-shrink: 0;
  line-height: 1;
}
.toast-close:hover { color: rgba(255,255,255,0.7); }

/* Transitions */
.toast-enter-active { transition: all 0.3s cubic-bezier(0.34,1.56,0.64,1); }
.toast-leave-active { transition: all 0.25s ease; }
.toast-enter-from   { opacity: 0; transform: translateX(60px) scale(0.9); }
.toast-leave-to     { opacity: 0; transform: translateX(60px); }
</style>
