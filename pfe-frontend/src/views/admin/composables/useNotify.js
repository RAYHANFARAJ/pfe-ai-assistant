import { ref } from 'vue'

const notifications = ref([])
let _id = 0

export function useNotify() {
  function notify(message, type = 'success') {
    const id = ++_id
    notifications.value.push({ id, message, type })
    setTimeout(() => {
      notifications.value = notifications.value.filter(n => n.id !== id)
    }, 4000)
  }

  function success(msg) { notify(msg, 'success') }
  function error(msg)   { notify(msg, 'error') }

  return { notifications, success, error }
}
