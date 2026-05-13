import { ref, watch, onMounted } from 'vue'

const STORAGE_KEY = 'sellynx_theme'
const _theme = ref('dark')

export function useTheme() {
  function apply(t) {
    document.documentElement.setAttribute('data-theme', t)
    _theme.value = t
    localStorage.setItem(STORAGE_KEY, t)
  }

  function toggle() {
    apply(_theme.value === 'dark' ? 'light' : 'dark')
  }

  function init() {
    const saved = localStorage.getItem(STORAGE_KEY)
    apply(saved || 'dark')
  }

  return { theme: _theme, toggle, init }
}
