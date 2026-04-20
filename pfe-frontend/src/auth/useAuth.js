import { reactive, computed } from 'vue'

const KEYCLOAK_URL   = import.meta.env.VITE_KEYCLOAK_URL       || 'http://localhost:8080'
const REALM          = import.meta.env.VITE_KEYCLOAK_REALM     || 'sellynx'
const CLIENT_ID      = import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'sellynx-frontend'
const TOKEN_ENDPOINT = `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token`
const STORAGE_KEY    = 'sellynx_auth'

// ── JWT helpers ──────────────────────────────────────────────────────────────

function parseJwt(token) {
  try {
    const b64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(b64))
  } catch {
    return null
  }
}

// ── Persistent storage ───────────────────────────────────────────────────────

function saveToStorage({ accessToken, refreshToken }) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ accessToken, refreshToken }))
}

function loadFromStorage() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null') } catch { return null }
}

function clearStorage() {
  localStorage.removeItem(STORAGE_KEY)
}

// ── Module-level reactive state ──────────────────────────────────────────────

const state = reactive({
  accessToken:     null,
  refreshToken:    null,
  tokenParsed:     null,
  isAuthenticated: false,
  isInitialized:   false,
})

let _refreshTimer = null

function _applyTokens(accessToken, refreshToken) {
  state.accessToken     = accessToken
  state.refreshToken    = refreshToken
  state.tokenParsed     = parseJwt(accessToken)
  state.isAuthenticated = true
}

function _clearAuth() {
  state.accessToken     = null
  state.refreshToken    = null
  state.tokenParsed     = null
  state.isAuthenticated = false
  clearStorage()
  if (_refreshTimer) { clearInterval(_refreshTimer); _refreshTimer = null }
}

async function _doRefresh() {
  if (!state.refreshToken) { _clearAuth(); return false }
  try {
    const res = await fetch(TOKEN_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        client_id:     CLIENT_ID,
        grant_type:    'refresh_token',
        refresh_token: state.refreshToken,
      }),
    })
    if (!res.ok) { _clearAuth(); return false }
    const data = await res.json()
    const newRefresh = data.refresh_token || state.refreshToken
    _applyTokens(data.access_token, newRefresh)
    saveToStorage({ accessToken: data.access_token, refreshToken: newRefresh })
    return true
  } catch {
    _clearAuth()
    return false
  }
}

function _startRefreshTimer() {
  if (_refreshTimer) clearInterval(_refreshTimer)
  _refreshTimer = setInterval(async () => {
    if (!state.isAuthenticated || !state.tokenParsed) return
    const msUntilExpiry = state.tokenParsed.exp * 1000 - Date.now()
    if (msUntilExpiry < 60_000) await _doRefresh()
  }, 30_000)
}

// ── Public: called once at app startup (main.js) ─────────────────────────────

export async function initAuth() {
  const stored = loadFromStorage()
  if (stored?.accessToken) {
    const parsed = parseJwt(stored.accessToken)
    if (parsed && parsed.exp * 1000 > Date.now() + 5_000) {
      _applyTokens(stored.accessToken, stored.refreshToken)
      _startRefreshTimer()
    } else if (stored.refreshToken) {
      state.refreshToken = stored.refreshToken
      await _doRefresh()
      if (state.isAuthenticated) _startRefreshTimer()
    }
  }
  state.isInitialized = true
}

// ── Composable ───────────────────────────────────────────────────────────────

export function useAuth() {
  const user = computed(() => {
    const p = state.tokenParsed
    if (!p) return null
    const firstName = p.given_name  || ''
    const lastName  = p.family_name || ''
    const fullName  = p.name
      || [firstName, lastName].filter(Boolean).join(' ')
      || p.preferred_username || p.email || 'User'
    const initials = firstName && lastName
      ? (firstName[0] + lastName[0]).toUpperCase()
      : fullName.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase() || '?'
    return {
      name:     fullName,
      firstName,
      lastName,
      email:    p.email || '',
      username: p.preferred_username || '',
      initials,
      sub:      p.sub,
      roles:    p.realm_access?.roles || [],
    }
  })

  // login(username, password) → throws on failure
  async function login(username, password) {
    const res = await fetch(TOKEN_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        client_id:  CLIENT_ID,
        grant_type: 'password',
        username,
        password,
      }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.error_description || 'Invalid credentials. Please try again.')
    }
    const data = await res.json()
    _applyTokens(data.access_token, data.refresh_token)
    saveToStorage({ accessToken: data.access_token, refreshToken: data.refresh_token })
    _startRefreshTimer()
  }

  function logout() {
    _clearAuth()
    window.location.href = '/login'
  }

  function getToken() {
    return state.accessToken || null
  }

  return {
    isAuthenticated: computed(() => state.isAuthenticated),
    isInitialized:   computed(() => state.isInitialized),
    user,
    login,
    logout,
    getToken,
  }
}
