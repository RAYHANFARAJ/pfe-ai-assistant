<template>
  <RouterView />
</template>
<script setup>
import { RouterView } from 'vue-router'
</script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #060E1A; font-family: 'Inter', 'Segoe UI', Arial, sans-serif; }
#app { width: 100% !important; max-width: 100% !important; margin: 0 !important;
  text-align: left !important; border: none !important; min-height: 100vh !important;
  display: block !important; background: #060E1A; }
</style>
