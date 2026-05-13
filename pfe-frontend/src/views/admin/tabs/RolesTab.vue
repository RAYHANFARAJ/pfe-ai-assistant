<template>
  <div class="roles-page">

    <!-- Role explanation -->
    <div class="info-banner">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2" style="flex-shrink:0;margin-top:1px">
        <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
      </svg>
      <div>
        Only users with the <strong>admin</strong> role can access this backoffice.
        Regular users only see the main SELLYNX app. You cannot remove your own admin role.
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div><span>Loading users from Keycloak…</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-banner">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>
      </svg>
      {{ error }}
    </div>

    <!-- User table -->
    <div v-else class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>User</th>
            <th>Email</th>
            <th>Status</th>
            <th>Role</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!users.length">
            <td colspan="5" class="empty-row">No users found in Keycloak.</td>
          </tr>
          <tr v-for="u in users" :key="u.id" class="data-row">
            <td class="cell-name">
              <div class="user-avatar">{{ initials(u) }}</div>
              <div>
                <div class="user-fullname">{{ u.firstName }} {{ u.lastName }}</div>
                <div class="user-username">@{{ u.username }}</div>
              </div>
            </td>
            <td class="cell-email">{{ u.email || '—' }}</td>
            <td>
              <span class="status-chip" :class="u.enabled ? 'active' : 'disabled'">
                {{ u.enabled ? 'Active' : 'Disabled' }}
              </span>
            </td>
            <td>
              <span v-if="u.is_admin" class="role-chip admin">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
                Admin
              </span>
              <span v-else class="role-chip user">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>
                </svg>
                User
              </span>
            </td>
            <td>
              <button
                v-if="!u.is_admin"
                class="action-btn grant"
                :disabled="processing === u.id"
                @click="grantAdmin(u)"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
                {{ processing === u.id ? 'Saving…' : 'Grant Admin' }}
              </button>
              <button
                v-else-if="u.id !== currentUserId"
                class="action-btn revoke"
                :disabled="processing === u.id"
                @click="confirmRevoke(u)"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
                {{ processing === u.id ? 'Saving…' : 'Revoke Admin' }}
              </button>
              <span v-else class="self-badge">You</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Confirm revoke modal -->
    <div v-if="revokeTarget" class="modal-overlay" @click.self="revokeTarget = null">
      <div class="modal">
        <div class="modal-header">
          <h2>Revoke admin access</h2>
          <button class="close-btn" @click="revokeTarget = null">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <p>Remove admin role from <strong>{{ revokeTarget.firstName }} {{ revokeTarget.lastName }}</strong>?</p>
          <p class="warn-text">They will no longer be able to access the backoffice.</p>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="revokeTarget = null">Cancel</button>
          <button class="btn-danger" :disabled="!!processing" @click="execRevoke">
            {{ processing ? 'Revoking…' : 'Revoke Admin' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import { useAuth } from '../../../auth/useAuth'
import api from '../../../services/api'

const notify       = inject('notify', { success: () => {}, error: () => {} })
const { user }     = useAuth()
const currentUserId= computed(() => user.value?.sub)

const users       = ref([])
const loading     = ref(false)
const error       = ref(null)
const processing  = ref(null)
const revokeTarget= ref(null)

function initials(u) {
  const f = (u.firstName?.[0] || '').toUpperCase()
  const l = (u.lastName?.[0]  || '').toUpperCase()
  return f + l || u.username?.[0]?.toUpperCase() || '?'
}

async function load() {
  loading.value = true
  error.value   = null
  try {
    const { data } = await api.admin.listUsers()
    users.value = data
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Failed to load users from Keycloak. Make sure Keycloak is running.'
  } finally {
    loading.value = false
  }
}

async function grantAdmin(u) {
  processing.value = u.id
  try {
    await api.admin.makeAdmin(u.id)
    notify.success(`Admin role granted to ${u.firstName} ${u.lastName}`)
    await load()
  } catch (err) {
    notify.error(err?.response?.data?.detail || 'Failed to grant admin role')
  } finally {
    processing.value = null
  }
}

function confirmRevoke(u) { revokeTarget.value = u }

async function execRevoke() {
  const u = revokeTarget.value
  processing.value = u.id
  revokeTarget.value = null
  try {
    await api.admin.removeAdmin(u.id)
    notify.success(`Admin role removed from ${u.firstName} ${u.lastName}`)
    await load()
  } catch (err) {
    notify.error(err?.response?.data?.detail || 'Failed to remove admin role')
  } finally {
    processing.value = null
  }
}

onMounted(load)
</script>

<style scoped>
*, *::before, *::after { box-sizing: border-box; }
.roles-page { font-family: Inter, sans-serif; color: #fff; }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
h1 { font-size: 1.5rem; font-weight: 700; color: #fff; margin: 0 0 4px; }
.page-sub { font-size: .85rem; color: rgba(255,255,255,.35); margin: 0; }

.info-banner {
  display: flex; gap: 12px;
  background: rgba(96,165,250,.08); border: 1px solid rgba(96,165,250,.2);
  border-radius: 10px; padding: 12px 16px; margin-bottom: 24px;
  font-size: .85rem; color: rgba(255,255,255,.65); line-height: 1.5;
}
.info-banner strong { color: #fff; }

.error-banner {
  display: flex; gap: 10px; align-items: center;
  background: rgba(239,68,68,.1); border: 1px solid rgba(239,68,68,.25);
  border-radius: 10px; padding: 14px 18px;
  color: #f87171; font-size: .875rem;
}

.table-wrap {
  background: rgba(255,255,255,.04);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 12px; overflow: hidden;
}
.table { width: 100%; border-collapse: collapse; font-size: .875rem; }
.table thead tr { background: rgba(255,255,255,.03); border-bottom: 1px solid rgba(255,255,255,.08); }
.table th { padding: 12px 18px; font-size: .72rem; font-weight: 700; color: rgba(255,255,255,.35); text-transform: uppercase; letter-spacing: .05em; text-align: left; }
.data-row { border-bottom: 1px solid rgba(255,255,255,.05); transition: background .12s; }
.data-row:last-child { border-bottom: none; }
.data-row:hover { background: rgba(255,255,255,.03); }
.table td { padding: 14px 18px; vertical-align: middle; }
.empty-row { text-align: center; color: rgba(255,255,255,.25); padding: 40px; }

/* User cell */
.cell-name { display: flex; align-items: center; gap: 12px; }
.user-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(135deg, #E8622C, #ff8c5a);
  display: flex; align-items: center; justify-content: center;
  font-size: .8rem; font-weight: 700; color: #fff; flex-shrink: 0;
}
.user-fullname { font-weight: 600; color: #fff; font-size: .9rem; }
.user-username { font-size: .78rem; color: rgba(255,255,255,.35); margin-top: 2px; }
.cell-email { color: rgba(255,255,255,.55); font-size: .85rem; }

/* Status chip */
.status-chip { border-radius: 20px; padding: 3px 10px; font-size: .72rem; font-weight: 700; }
.status-chip.active   { background: rgba(74,222,128,.12); color: #4ade80; border: 1px solid rgba(74,222,128,.2); }
.status-chip.disabled { background: rgba(255,255,255,.06); color: rgba(255,255,255,.35); }

/* Role chip */
.role-chip { display: inline-flex; align-items: center; gap: 6px; border-radius: 20px; padding: 4px 12px; font-size: .78rem; font-weight: 700; }
.role-chip.admin { background: rgba(232,98,44,.15); color: #E8622C; border: 1px solid rgba(232,98,44,.25); }
.role-chip.user  { background: rgba(255,255,255,.06); color: rgba(255,255,255,.4); border: 1px solid rgba(255,255,255,.1); }

/* Action buttons */
.action-btn {
  display: flex; align-items: center; gap: 6px;
  border: none; border-radius: 7px; padding: 6px 14px;
  font-size: .8rem; font-weight: 600; cursor: pointer; transition: all .15s;
}
.action-btn:disabled { opacity: .4; cursor: default; }
.action-btn.grant  { background: rgba(232,98,44,.15); color: #E8622C; border: 1px solid rgba(232,98,44,.25); }
.action-btn.grant:hover:not(:disabled) { background: rgba(232,98,44,.3); }
.action-btn.revoke { background: rgba(239,68,68,.12); color: #f87171; border: 1px solid rgba(239,68,68,.2); }
.action-btn.revoke:hover:not(:disabled) { background: rgba(239,68,68,.25); }
.self-badge { font-size: .78rem; color: rgba(255,255,255,.25); font-style: italic; }

/* Loading */
.loading-state { display: flex; align-items: center; justify-content: center; gap: 12px; padding: 60px; color: rgba(255,255,255,.35); }
.spinner { width: 20px; height: 20px; border: 2px solid rgba(255,255,255,.1); border-top-color: #E8622C; border-radius: 50%; animation: spin .7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.7); backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; z-index: 300; }
.modal { background: rgba(15,23,42,.97); border: 1px solid rgba(255,255,255,.1); border-radius: 16px; width: 420px; display: flex; flex-direction: column; box-shadow: 0 32px 80px rgba(0,0,0,.6); }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px 0; }
.modal-header h2 { font-size: 1.05rem; font-weight: 700; color: #fff; margin: 0; }
.close-btn { background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1); color: rgba(255,255,255,.5); cursor: pointer; width: 28px; height: 28px; border-radius: 7px; display: flex; align-items: center; justify-content: center; }
.close-btn:hover { background: rgba(255,255,255,.1); color: #fff; }
.modal-body { padding: 16px 24px; }
.modal-body p { color: rgba(255,255,255,.7); font-size: .9rem; margin-bottom: 8px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 14px 24px; border-top: 1px solid rgba(255,255,255,.07); }
.btn-ghost { background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1); color: rgba(255,255,255,.7); border-radius: 8px; padding: 8px 18px; cursor: pointer; font-size: .875rem; }
.btn-ghost:hover { background: rgba(255,255,255,.1); }
.btn-danger { background: rgba(239,68,68,.2); border: 1px solid rgba(239,68,68,.3); color: #f87171; border-radius: 8px; padding: 8px 18px; cursor: pointer; font-size: .875rem; font-weight: 600; }
.btn-danger:hover { background: rgba(239,68,68,.35); }
.btn-danger:disabled { opacity: .4; cursor: default; }
.warn-text { color: rgba(239,68,68,.8) !important; font-size: .82rem !important; }

/* ══ LIGHT MODE ══════════════════════════════ */
[data-theme="light"] .roles-page { color: #0D1B2E; }

/* Info banner */
[data-theme="light"] .info-banner {
  background: rgba(59,130,246,0.07);
  border-color: rgba(59,130,246,0.20);
  color: #3D5068;
}
[data-theme="light"] .info-banner strong { color: #0D1B2E; }

/* Table */
[data-theme="light"] .table-wrap {
  background: #FFFFFF;
  border-color: rgba(13,27,46,0.09);
  box-shadow: 0 2px 10px rgba(13,27,46,0.06);
}
[data-theme="light"] .table thead tr { background: rgba(13,27,46,0.03); border-bottom-color: rgba(13,27,46,0.08); }
[data-theme="light"] .table th      { color: #7C93AE; }
[data-theme="light"] .data-row      { border-bottom-color: rgba(13,27,46,0.06); }
[data-theme="light"] .data-row:hover { background: rgba(13,27,46,0.025); }
[data-theme="light"] .table td      { color: #0D1B2E; }
[data-theme="light"] .empty-row     { color: #7C93AE; }

/* User cell */
[data-theme="light"] .user-fullname { color: #0D1B2E; }
[data-theme="light"] .user-username { color: #7C93AE; }
[data-theme="light"] .cell-email    { color: #3D5068; }
[data-theme="light"] .self-badge    { color: #94A3B8; }

/* Status chip */
[data-theme="light"] .status-chip.active   { background: rgba(22,163,74,0.10); color: #16a34a; border-color: rgba(22,163,74,0.20); }
[data-theme="light"] .status-chip.disabled { background: rgba(13,27,46,0.06); color: #7C93AE; }

/* Role chip */
[data-theme="light"] .role-chip.user { background: rgba(13,27,46,0.06); color: #3D5068; border-color: rgba(13,27,46,0.12); }

/* Modal */
[data-theme="light"] .modal {
  background: #FFFFFF; border-color: rgba(13,27,46,0.12);
  box-shadow: 0 24px 64px rgba(13,27,46,0.15);
}
[data-theme="light"] .modal-header {
  background: #FFFFFF; border-radius: 14px 14px 0 0;
  padding-bottom: 16px; border-bottom: 1px solid rgba(13,27,46,0.08);
}
[data-theme="light"] .modal h2    { color: #0D1B2E; }
[data-theme="light"] .modal-body p { color: #3D5068; }
[data-theme="light"] .modal-footer { border-top-color: rgba(13,27,46,0.08); }
[data-theme="light"] .close-btn { background: transparent; border: none; color: #7C93AE; }
[data-theme="light"] .close-btn:hover { background: rgba(13,27,46,0.06); color: #0D1B2E; }
[data-theme="light"] .btn-ghost {
  background: rgba(13,27,46,0.05); border-color: rgba(13,27,46,0.12); color: #3D5068;
}
[data-theme="light"] .btn-ghost:hover { background: rgba(13,27,46,0.10); }
</style>
