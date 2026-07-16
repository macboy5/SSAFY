let observer

function getObserver() {
  if (observer) return observer
  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue
        entry.target.classList.add('is-visible')
        observer.unobserve(entry.target)
      }
    },
    { threshold: 0.12, rootMargin: '0px 0px -5% 0px' },
  )
  return observer
}

export const reveal = {
  mounted(el, binding) {
    const order = Math.min(Math.max(Number(binding.value) || 0, 0), 5)
    el.style.setProperty('--reveal-order', order)
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      el.classList.add('is-visible')
      return
    }
    el.classList.add('reveal-ready')
    getObserver().observe(el)
  },
  unmounted(el) {
    observer?.unobserve(el)
  },
}
