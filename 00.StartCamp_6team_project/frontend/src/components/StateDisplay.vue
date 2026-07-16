<script setup>
defineProps({
  loading: { type: Boolean, default: false },
  error: { type: String, default: null },
  empty: { type: Boolean, default: false },
  emptyText: { type: String, default: '표시할 내용이 없습니다.' },
})
</script>

<template>
  <div v-if="loading" class="state state-loading" role="status" aria-live="polite">
    <div class="loading-preview" aria-hidden="true"><i /><i /><i /></div>
    <strong>정보를 정리하고 있어요</strong>
    <span>잠시만 기다려 주세요.</span>
  </div>
  <div v-else-if="error" class="state state-error" role="alert">
    <i aria-hidden="true">×</i>
    <strong>정보를 불러오지 못했습니다</strong>
    <span>{{ error }}</span>
  </div>
  <div v-else-if="empty" class="state state-empty">
    <i aria-hidden="true">○</i>
    <strong>아직 보여드릴 내용이 없습니다</strong>
    <span>{{ emptyText }}</span>
  </div>
  <slot v-else />
</template>

<style scoped>
.state {
  display: flex;
  min-height: 230px;
  padding: 2.5rem 1rem 3rem;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  text-align: center;
  border: 1px solid var(--line);
  border-radius: 22px;
  color: var(--muted);
  background: color-mix(in srgb, var(--surface) 78%, transparent);
}
.state > i {
  display: grid;
  width: 42px;
  height: 42px;
  margin-bottom: 0.55rem;
  place-items: center;
  border: 1px solid currentColor;
  border-radius: 12px;
  font: 1.25rem var(--display);
}
.state strong {
  color: var(--text);
  font-size: 0.9rem;
}
.state span {
  max-width: 48ch;
  font-size: 0.76rem;
}
.state-error {
  color: var(--danger);
  background: var(--map-error);
}
.state-empty {
  color: var(--muted);
  background: var(--soft);
}
.loading-preview {
  display: grid;
  width: min(320px, 78vw);
  grid-template-columns: 1.35fr 1fr 0.75fr;
  align-items: end;
  gap: 0.45rem;
  margin-bottom: 1rem;
}
.loading-preview i {
  height: 48px;
  border-radius: 10px;
  background: linear-gradient(100deg, var(--soft) 25%, var(--surface) 45%, var(--soft) 65%);
  background-size: 240% 100%;
  animation: shimmer 1.4s infinite;
}
.loading-preview i:nth-child(2) { height: 68px; animation-delay: 120ms; }
.loading-preview i:nth-child(3) { height: 38px; animation-delay: 240ms; }
@keyframes shimmer { to { background-position: -240% 0; } }
</style>
