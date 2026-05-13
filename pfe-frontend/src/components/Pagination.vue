<template>
  <div v-if="totalPages > 1" class="pagination">

    <!-- Info -->
    <span class="pag-info">
      {{ from }}–{{ to }} sur {{ total }}
    </span>

    <!-- Controls -->
    <div class="pag-controls">

      <!-- First -->
      <button class="pag-btn" :disabled="page === 1" @click="go(1)" title="Première page">
        <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <polyline points="11 17 6 12 11 7"/><polyline points="18 17 13 12 18 7"/>
        </svg>
      </button>

      <!-- Prev -->
      <button class="pag-btn" :disabled="page === 1" @click="go(page - 1)" title="Page précédente">
        <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </button>

      <!-- Page numbers -->
      <template v-for="p in visiblePages" :key="p">
        <span v-if="p === '...'" class="pag-dots">…</span>
        <button
          v-else
          class="pag-btn pag-num"
          :class="{ active: p === page }"
          @click="go(p)"
        >{{ p }}</button>
      </template>

      <!-- Next -->
      <button class="pag-btn" :disabled="page === totalPages" @click="go(page + 1)" title="Page suivante">
        <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </button>

      <!-- Last -->
      <button class="pag-btn" :disabled="page === totalPages" @click="go(totalPages)" title="Dernière page">
        <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <polyline points="13 17 18 12 13 7"/><polyline points="6 17 11 12 6 7"/>
        </svg>
      </button>
    </div>

    <!-- Per page -->
    <div class="pag-perpage">
      <span>Par page :</span>
      <select :value="perPage" @change="$emit('update:perPage', +$event.target.value)" class="pag-select">
        <option v-for="n in perPageOptions" :key="n" :value="n">{{ n }}</option>
      </select>
    </div>

  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  page:     { type: Number, required: true },
  perPage:  { type: Number, default: 12 },
  total:    { type: Number, required: true },
  perPageOptions: { type: Array, default: () => [10, 20, 50] },
})

const emit = defineEmits(['update:page', 'update:perPage'])

const totalPages = computed(() => Math.ceil(props.total / props.perPage))
const from = computed(() => Math.min((props.page - 1) * props.perPage + 1, props.total))
const to   = computed(() => Math.min(props.page * props.perPage, props.total))

const visiblePages = computed(() => {
  const total = totalPages.value
  const cur   = props.page
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)

  const pages = []
  if (cur <= 4) {
    pages.push(1, 2, 3, 4, 5, '...', total)
  } else if (cur >= total - 3) {
    pages.push(1, '...', total - 4, total - 3, total - 2, total - 1, total)
  } else {
    pages.push(1, '...', cur - 1, cur, cur + 1, '...', total)
  }
  return pages
})

function go(p) {
  if (p < 1 || p > totalPages.value) return
  emit('update:page', p)
}
</script>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 16px 0 4px;
  border-top: 1px solid rgba(255,255,255,0.06);
  margin-top: 20px;
}

.pag-info {
  font-size: 12px;
  color: rgba(255,255,255,0.35);
}

.pag-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pag-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.03);
  color: rgba(255,255,255,0.5);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.15s;
}
.pag-btn:hover:not(:disabled) {
  background: rgba(232,98,44,0.1);
  border-color: rgba(232,98,44,0.3);
  color: #fff;
}
.pag-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.pag-btn.active {
  background: #E8622C;
  border-color: #E8622C;
  color: #fff;
}

.pag-dots {
  width: 32px;
  text-align: center;
  color: rgba(255,255,255,0.25);
  font-size: 13px;
}

.pag-perpage {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: rgba(255,255,255,0.35);
}

.pag-select {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 7px;
  color: #fff;
  font-size: 12px;
  padding: 4px 8px;
  cursor: pointer;
  outline: none;
}
.pag-select:focus {
  border-color: rgba(232,98,44,0.4);
}
</style>
