<script setup>
defineProps({
  modelValue: { type: String, default: '' },
})
defineEmits(['update:modelValue'])

const CATEGORIES = ['관광지', '레포츠', '문화시설', '쇼핑', '숙박', '여행코스', '축제공연행사']
</script>

<template>
  <div class="filter-row" role="group" aria-label="관광 콘텐츠 카테고리">
    <button
      type="button"
      :class="{ active: modelValue === '' }"
      :aria-pressed="modelValue === ''"
      @click="$emit('update:modelValue', '')"
    >
      전체
    </button>
    <button
      v-for="c in CATEGORIES"
      :key="c"
      type="button"
      :class="{ active: modelValue === c }"
      :aria-pressed="modelValue === c"
      @click="$emit('update:modelValue', c)"
    >
      {{ c }}
    </button>
  </div>
</template>

<style scoped>
.filter-row {
  display: flex;
  gap: 0.35rem;
  margin-bottom: 1.25rem;
  padding-bottom: 0.35rem;
  overflow-x: auto;
  scrollbar-width: thin;
}
button {
  flex: 0 0 auto;
  min-height: 44px;
  padding: 0.62rem 0.9rem;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--text);
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 700;
  transition: background var(--motion-fast), color var(--motion-fast), transform var(--motion-fast);
}
button:hover {
  background: var(--soft);
}
button.active {
  background: var(--ink);
  color: var(--bg);
}
</style>
