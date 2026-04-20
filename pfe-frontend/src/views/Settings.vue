<template>
  <AppLayout title="Settings" subtitle="Configure your scoring pipeline preferences">
    <div class="settings-grid">
      <div class="settings-card">
        <div class="card-title">API Configuration</div>
        <div class="field"><label>Backend URL</label><input v-model="apiUrl" /></div>
        <div class="field"><label>Default Product ID</label><input v-model="productId" /></div>
        <button class="save-btn">Save Changes</button>
      </div>
      <div class="settings-card">
        <div class="card-title">Account</div>
        <div class="field"><label>Name</label><input value="John Doe" /></div>
        <div class="field"><label>Email</label><input value="john@company.com" /></div>
        <div class="field"><label>Role</label><input value="Account Manager" disabled /></div>
        <button class="save-btn">Update Profile</button>
      </div>
    </div>
  </AppLayout>
</template>
<script setup>
import { ref } from 'vue'
import AppLayout from '../components/AppLayout.vue'
const apiUrl = ref('http://localhost:8000')
const productId = ref('P001')
</script>
<style scoped>
.settings-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; max-width: 800px; }
.settings-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 24px 28px; display: flex; flex-direction: column; gap: 18px; }
.card-title { font-size: 15px; font-weight: 700; color: #fff; margin-bottom: 4px; }
.field { display: flex; flex-direction: column; gap: 7px; }
.field label { font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.35); text-transform: uppercase; letter-spacing: 0.4px; }
.field input { padding: 11px 14px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: #fff; font-size: 14px; outline: none; }
.field input:focus { border-color: rgba(232,98,44,0.5); }
.field input:disabled { opacity: 0.4; cursor: not-allowed; }
.save-btn { padding: 11px; background: linear-gradient(135deg, #E8622C, #ff7a45); color: #fff; font-size: 14px; font-weight: 700; border: none; border-radius: 9px; cursor: pointer; margin-top: 4px; }
.save-btn:hover { opacity: 0.9; }
</style>
