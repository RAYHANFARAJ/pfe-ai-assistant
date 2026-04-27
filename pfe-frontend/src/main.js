import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import { initAuth } from './auth/useAuth'

// Initialize Keycloak BEFORE mounting so the router guard has auth state
initAuth().then(() => {
  createApp(App).use(router).mount('#app')
})
