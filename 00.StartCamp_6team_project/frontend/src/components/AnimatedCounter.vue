<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  value: { type: Number, default: 0 },
  duration: { type: Number, default: 1200 },
  delay: { type: Number, default: 0 },
  locale: { type: String, default: 'ko-KR' },
})

const root = ref(null)
const displayedValue = ref(0)
const hasEntered = ref(false)
let frameId = 0
let delayId = 0
let observer

const formatter = computed(() => new Intl.NumberFormat(props.locale, { maximumFractionDigits: 0 }))
const formattedValue = computed(() => formatter.value.format(Math.round(displayedValue.value)))
const formattedTarget = computed(() => formatter.value.format(Math.round(Number(props.value) || 0)))

function prefersReducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}

function animateTo(rawTarget) {
  const target = Number(rawTarget) || 0
  cancelAnimationFrame(frameId)
  clearTimeout(delayId)

  if (prefersReducedMotion()) {
    displayedValue.value = target
    return
  }

  const from = displayedValue.value
  const duration = Math.max(300, props.duration)

  delayId = window.setTimeout(() => {
    const startedAt = performance.now()
    const tick = (now) => {
      const progress = Math.min((now - startedAt) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 4)
      displayedValue.value = from + (target - from) * eased
      if (progress < 1) frameId = requestAnimationFrame(tick)
      else displayedValue.value = target
    }
    frameId = requestAnimationFrame(tick)
  }, props.delay)
}

function enter() {
  if (hasEntered.value) return
  hasEntered.value = true
  animateTo(props.value)
  observer?.disconnect()
}

watch(() => props.value, (value) => {
  if (hasEntered.value) animateTo(value)
})

onMounted(() => {
  if (!('IntersectionObserver' in window)) {
    enter()
    return
  }
  observer = new IntersectionObserver(([entry]) => {
    if (entry.isIntersecting) enter()
  }, { threshold: 0.35 })
  observer.observe(root.value)
})

onBeforeUnmount(() => {
  observer?.disconnect()
  cancelAnimationFrame(frameId)
  clearTimeout(delayId)
})
</script>

<template>
  <span ref="root" class="animated-counter" :aria-label="formattedTarget">
    <span aria-hidden="true">{{ formattedValue }}</span>
  </span>
</template>

<style scoped>
.animated-counter{display:inline-block;font-variant-numeric:tabular-nums;white-space:nowrap}
</style>
