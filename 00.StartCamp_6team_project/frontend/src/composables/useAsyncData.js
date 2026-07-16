import { ref } from 'vue'

export function useAsyncData() {
  const data = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function run(promiseFactory) {
    loading.value = true
    error.value = null
    try {
      data.value = await promiseFactory()
    } catch (err) {
      error.value = err.message || '알 수 없는 오류가 발생했습니다.'
    } finally {
      loading.value = false
    }
    return data.value
  }

  return { data, loading, error, run }
}
