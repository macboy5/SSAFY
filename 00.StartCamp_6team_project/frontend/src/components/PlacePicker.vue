<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { api } from '../api/client'

const props = defineProps({
  modelValue: { type: [Object, Array], default: null },
  disabled: { type: Boolean, default: false },
  multiple: { type: Boolean, default: false },
  max: { type: Number, default: 10 },
  placeholder: { type: String, default: '서울의 장소를 검색하세요 (2자 이상)' },
  helper: { type: String, default: '장소 이름을 두 글자 이상 입력해 주세요.' },
})

const emit = defineEmits(['update:modelValue'])
const query = ref('')
const results = ref([])
const loading = ref(false)
const error = ref('')
const queryInput = ref(null)
let timer

const selected = computed(() => {
  if (props.multiple) return Array.isArray(props.modelValue) ? props.modelValue : []
  return props.modelValue ? [props.modelValue] : []
})
const canSearch = computed(
  () => !props.disabled && (props.multiple ? selected.value.length < props.max : !props.modelValue),
)
const filteredResults = computed(() => {
  const selectedIds = new Set(selected.value.map((place) => place.contentid))
  return results.value.filter((place) => !selectedIds.has(place.contentid))
})

async function search() {
  const keyword = query.value.trim()
  if (keyword.length < 2 || !canSearch.value) {
    results.value = []
    return
  }
  loading.value = true
  error.value = ''
  try {
    const params = new URLSearchParams({ keyword, page_size: '8' })
    results.value = (await api.get(`/contents?${params}`)).items
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

watch(query, () => {
  clearTimeout(timer)
  timer = setTimeout(search, 260)
})
onBeforeUnmount(() => clearTimeout(timer))

function choose(place) {
  if (props.multiple) {
    if (selected.value.some((item) => item.contentid === place.contentid)) return
    emit('update:modelValue', [...selected.value, place])
  } else {
    emit('update:modelValue', place)
  }
  query.value = ''
  results.value = []
  nextTick(() => queryInput.value?.focus())
}

function remove(index) {
  if (props.multiple) {
    emit('update:modelValue', selected.value.filter((_, itemIndex) => itemIndex !== index))
  } else {
    emit('update:modelValue', null)
  }
}

function move(index, direction) {
  const target = index + direction
  if (!props.multiple || target < 0 || target >= selected.value.length) return
  const next = [...selected.value]
  ;[next[index], next[target]] = [next[target], next[index]]
  emit('update:modelValue', next)
}
</script>

<template>
  <div class="place-picker" :class="{ 'is-multiple': multiple }">
    <ol v-if="multiple && selected.length" class="route-list" aria-label="여행 코스 순서">
      <li v-for="(place, index) in selected" :key="place.contentid" class="selected-place route-stop">
        <span class="stop-number">{{ String(index + 1).padStart(2, '0') }}</span>
        <img v-if="place.firstimage" :src="place.firstimage" :alt="place.title">
        <div class="place-copy">
          <span>{{ place.category }}</span>
          <strong>{{ place.title }}</strong>
          <small>{{ place.addr1 || '서울' }}</small>
        </div>
        <div v-if="!disabled" class="stop-actions">
          <button type="button" :disabled="index === 0" :aria-label="`${place.title} 순서 앞으로`" @click="move(index, -1)">↑</button>
          <button type="button" :disabled="index === selected.length - 1" :aria-label="`${place.title} 순서 뒤로`" @click="move(index, 1)">↓</button>
          <button class="remove" type="button" :aria-label="`${place.title} 코스에서 빼기`" @click="remove(index)">×</button>
        </div>
      </li>
    </ol>

    <div v-else-if="!multiple && modelValue" class="selected-place">
      <img v-if="modelValue.firstimage" :src="modelValue.firstimage" :alt="modelValue.title">
      <div class="place-copy">
        <span>{{ modelValue.category }}</span>
        <strong>{{ modelValue.title }}</strong>
        <small>{{ modelValue.addr1 }}</small>
      </div>
      <button v-if="!disabled" class="change-button" type="button" @click="remove(0)">변경</button>
    </div>

    <div v-if="canSearch" class="search-area">
      <div class="picker-input">
        <span aria-hidden="true">⌕</span>
        <input ref="queryInput" v-model="query" :placeholder="placeholder" autocomplete="off">
        <b v-if="multiple">{{ selected.length }}/{{ max }}</b>
      </div>
      <p v-if="loading" class="picker-message">어울리는 장소를 찾고 있어요…</p>
      <p v-else-if="error" class="picker-message error" role="alert">{{ error }}</p>
      <ul v-else-if="filteredResults.length" class="search-results">
        <li v-for="place in filteredResults" :key="place.contentid">
          <button type="button" @click="choose(place)">
            <img v-if="place.firstimage" :src="place.firstimage" :alt="place.title">
            <span v-else class="result-fallback" aria-hidden="true">SEOUL</span>
            <span><b>{{ place.title }}</b><small>{{ place.category }} · {{ place.addr1 || '서울' }}</small></span>
            <em>{{ multiple ? '코스에 추가' : '선택' }}</em>
          </button>
        </li>
      </ul>
      <p v-else class="picker-message">{{ query.trim().length === 1 ? '한 글자만 더 입력해 주세요.' : helper }}</p>
    </div>

    <p v-if="multiple && selected.length >= max" class="picker-message limit-message">한 코스에는 장소를 최대 {{ max }}곳까지 담을 수 있어요.</p>
  </div>
</template>

<style scoped>
.place-picker{position:relative}.route-list{display:grid;gap:.55rem;margin:0 0 .8rem;padding:0;list-style:none}.selected-place{display:grid;grid-template-columns:72px minmax(0,1fr) auto;align-items:center;gap:.85rem;padding:.72rem;border:1px solid var(--line);border-radius:16px;background:var(--soft)}.selected-place img{width:72px;height:66px;object-fit:cover;border-radius:11px}.place-copy{display:flex;flex-direction:column;min-width:0}.place-copy>span{font-size:.66rem;color:var(--accent);font-weight:800;letter-spacing:.04em}.place-copy strong{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:.9rem}.place-copy small{color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:.7rem}.route-stop{position:relative;grid-template-columns:38px 64px minmax(0,1fr) auto;padding:.58rem;background:color-mix(in srgb,var(--soft) 70%,var(--surface))}.route-stop:not(:last-child):after{content:'';position:absolute;left:26px;top:100%;width:1px;height:.6rem;background:color-mix(in srgb,var(--accent) 45%,var(--line))}.route-stop img{width:64px;height:58px}.stop-number{display:grid;place-items:center;width:34px;height:34px;border-radius:11px;background:var(--ink);color:var(--bg);font-size:.67rem;font-weight:800;font-variant-numeric:tabular-nums}.stop-actions{display:flex;gap:.22rem}.stop-actions button,.change-button{display:grid;place-items:center;min-width:32px;height:32px;padding:0 .45rem;border:1px solid var(--line);border-radius:9px;background:var(--surface);color:var(--text);font-size:.75rem;transition:transform .18s,border-color .18s,color .18s}.stop-actions button:not(:disabled):hover,.change-button:hover{transform:translateY(-2px);border-color:var(--primary);color:var(--primary)}.stop-actions button:disabled{opacity:.28}.stop-actions .remove:hover{border-color:var(--danger);color:var(--danger)}.search-area{position:relative}.picker-input{display:flex;align-items:center;gap:.6rem;border:1px solid var(--line);border-radius:14px;padding:0 .9rem;background:var(--input);transition:border-color .2s,box-shadow .2s}.picker-input:focus-within{border-color:var(--primary);box-shadow:0 0 0 3px color-mix(in srgb,var(--primary) 12%,transparent)}.picker-input>span{font-size:1.2rem;color:var(--primary)}.picker-input input{width:100%;border:0;outline:0;padding:.88rem 0;background:transparent;color:var(--text)}.picker-input>b{color:var(--muted);font-size:.68rem;white-space:nowrap}.search-results{position:absolute;left:0;right:0;z-index:20;max-height:350px;overflow:auto;list-style:none;padding:.45rem;margin:.38rem 0;background:var(--surface);border:1px solid var(--line);border-radius:16px;box-shadow:0 22px 60px color-mix(in srgb,var(--ink) 18%,transparent)}.search-results li button{display:grid;grid-template-columns:52px minmax(0,1fr) auto;align-items:center;gap:.75rem;width:100%;border:0;background:transparent;color:var(--text);padding:.6rem;text-align:left;border-radius:11px}.search-results li button:hover{background:var(--soft)}.search-results img,.result-fallback{width:52px;height:52px;border-radius:9px;object-fit:cover}.result-fallback{display:grid;place-items:center;background:var(--soft);color:var(--muted);font-size:.52rem;letter-spacing:.1em}.search-results li button>span:nth-child(2){min-width:0;display:flex;flex-direction:column}.search-results li small{color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:.69rem}.search-results em{color:var(--primary);font-size:.68rem;font-style:normal;font-weight:800}.picker-message{margin-top:.45rem;color:var(--muted);font-size:.72rem}.picker-message.error{color:var(--danger)}.limit-message{margin-top:.2rem}.change-button{padding:0 .7rem}@media(max-width:620px){.route-stop{grid-template-columns:34px 52px minmax(0,1fr)}.route-stop img{width:52px;height:50px}.stop-actions{grid-column:2/4;justify-content:flex-end}.selected-place:not(.route-stop){grid-template-columns:58px minmax(0,1fr) auto}.selected-place:not(.route-stop) img{width:58px;height:54px}.search-results li button{grid-template-columns:46px minmax(0,1fr)}.search-results img,.result-fallback{width:46px;height:46px}.search-results em{display:none}}
</style>
