<script setup>
import { ref, onMounted } from 'vue'

const message = ref('Loading...')

onMounted(async () => {
  try {
    const response = await fetch('http://localhost:8000/')
    const data = await response.json()
    message.value = data.message
  } catch (error) {
    message.value = 'Erreur backend'
  }
})
</script>

<template>
  <div style="padding: 40px">
    <h1>PFE Project</h1>
    <p>{{ message }}</p>
  </div>
</template>