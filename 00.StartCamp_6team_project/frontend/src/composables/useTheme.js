import { ref } from 'vue'

const STORAGE_KEY = 'seoulmate.theme'
const saved = localStorage.getItem(STORAGE_KEY)
const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
const theme = ref(saved === 'dark' || saved === 'light' ? saved : preferred)

function applyTheme() {
  document.documentElement.dataset.theme = theme.value
  document.documentElement.style.colorScheme = theme.value
}

applyTheme()

export function useTheme() {
  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    localStorage.setItem(STORAGE_KEY, theme.value)
    applyTheme()
  }
  return { theme, toggleTheme }
}
