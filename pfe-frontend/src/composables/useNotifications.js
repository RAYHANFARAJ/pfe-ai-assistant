/**
 * useNotifications — Browser Push Notifications + in-app toasts.
 *
 * Browser Notifications work even when the user is on another tab (YouTube, etc.)
 * as long as the browser is open. The notification appears as an OS system alert.
 *
 * Usage:
 *   const { notify, requestPermission, hasPermission } = useNotifications()
 *   await requestPermission()          // ask user once
 *   notify('Scoring terminé', { body: '15 produits scorés' })
 */
import { ref, readonly } from 'vue'

const _permission = ref(
  typeof Notification !== 'undefined' ? Notification.permission : 'denied'
)
const _toasts = ref([])   // in-app toast queue
let   _toastId = 0

export function useNotifications() {

  // ── Permission ──────────────────────────────────────────────────────────────
  const hasPermission = readonly(
    ref(_permission.value === 'granted')
  )

  async function requestPermission() {
    if (typeof Notification === 'undefined') return false
    if (_permission.value === 'granted') return true

    const result = await Notification.requestPermission()
    _permission.value = result
    return result === 'granted'
  }

  // ── OS notification (works when user is on another tab) ────────────────────
  function notifyOS(title, { body = '', icon = '/sellynx-logo.svg', tag = '' } = {}) {
    if (typeof Notification === 'undefined') return
    if (_permission.value !== 'granted') return

    const n = new Notification(title, {
      body,
      icon,
      badge: '/sellynx-logo.svg',
      tag:   tag || title,
    })
    // Click brings the SELLYNX tab back into focus
    n.onclick = () => {
      window.focus()
      n.close()
    }
    // Auto-close after 8 seconds
    setTimeout(() => n.close(), 8000)
  }

  // ── In-app toast (shown when user IS on the page) ──────────────────────────
  function toast(title, { body = '', type = 'success', duration = 5000 } = {}) {
    const id = ++_toastId
    _toasts.value.push({ id, title, body, type })
    setTimeout(() => {
      _toasts.value = _toasts.value.filter(t => t.id !== id)
    }, duration)
  }

  function removeToast(id) {
    _toasts.value = _toasts.value.filter(t => t.id !== id)
  }

  // ── Combined notify — OS + in-app ──────────────────────────────────────────
  function notify(title, options = {}) {
    notifyOS(title, options)
    toast(title, options)
  }

  return {
    permission:       readonly(_permission),
    hasPermission:    _permission.value === 'granted',
    toasts:           readonly(_toasts),
    requestPermission,
    notify,
    notifyOS,
    toast,
    removeToast,
  }
}
