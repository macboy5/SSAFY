<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import CategoryFilter from '../components/CategoryFilter.vue'
import CommunityPostCard from '../components/CommunityPostCard.vue'
import StateDisplay from '../components/StateDisplay.vue'
import { useAsyncData } from '../composables/useAsyncData'

const route = useRoute()
const router = useRouter()
const page = ref(Number(route.query.page) || 1)
const category = ref(route.query.category || '')
const keyword = ref(route.query.keyword || '')
const contentId = ref(route.query.content_id || '')
const postType = ref(['review', 'course'].includes(route.query.post_type) ? route.query.post_type : '')
const SORT_OPTIONS = [
  { value: 'newest', label: '최신순' },
  { value: 'likes', label: '좋아요순' },
  { value: 'comments', label: '댓글순' },
]
const TYPE_OPTIONS = [
  { value: '', label: '모든 기록', description: '후기와 코스를 함께' },
  { value: 'course', label: '하루 코스', description: '여러 장소의 동선' },
  { value: 'review', label: '장소 후기', description: '한 장소의 경험' },
]
const sort = ref(SORT_OPTIONS.some((option) => option.value === route.query.sort) ? route.query.sort : 'newest')
const popular = ref([])
const PAGE_SIZE = 12
const { data, loading, error, run } = useAsyncData()
const selectedPlace = computed(() => popular.value.find((item) => item.content.contentid === contentId.value)?.content)
const totalPages = computed(() => Math.max(1, Math.ceil((data.value?.total || 0) / PAGE_SIZE)))
const pages = computed(() => {
  const length = Math.min(5, totalPages.value)
  const start = Math.max(1, Math.min(page.value - 2, totalPages.value - length + 1))
  return Array.from({ length }, (_, index) => start + index)
})

function queryString() {
  const params = new URLSearchParams({ page: String(page.value), page_size: String(PAGE_SIZE), sort: sort.value })
  if (category.value) params.set('category', category.value)
  if (keyword.value.trim()) params.set('keyword', keyword.value.trim())
  if (contentId.value) params.set('content_id', contentId.value)
  if (postType.value) params.set('post_type', postType.value)
  return params
}

function load() {
  const params = queryString()
  router.replace({ query: Object.fromEntries([...params].filter(([key]) => key !== 'page_size')) })
  run(() => api.get(`/posts?${params}`))
}
function resetAndLoad() { page.value = 1; load() }
function selectPlace(id) { contentId.value = contentId.value === id ? '' : id; resetAndLoad() }
function setType(value) { if (postType.value !== value) { postType.value = value; resetAndLoad() } }
function setSort(value) { if (sort.value !== value) { sort.value = value; resetAndLoad() } }
function setPage(value) { page.value = value; load(); window.scrollTo({ top: 0, behavior: 'smooth' }) }

watch(category, resetAndLoad)
onMounted(async () => {
  try { popular.value = await api.get('/community/places?limit=8') } catch { popular.value = [] }
  load()
})
</script>

<template>
  <section class="community-page">
    <header class="community-hero">
      <div class="hero-copy">
        <span class="kicker">SEOUL TRAVEL JOURNALS</span>
        <h1>한 장소의 인상부터<br><em>하루의 동선</em>까지.</h1>
        <p>한 장소의 후기는 바로 남기고, 하루 동선은 Planner에 먼저 담아두세요. 여행을 마치면 그 코스를 기록으로 남길 수 있어요.</p>
      </div>
      <div class="hero-actions">
        <RouterLink class="btn course-cta" :to="{ name: 'planner', query: { guide: 'course' } }"><span>하루 코스 기록하러 가기</span><b>→</b></RouterLink>
        <RouterLink class="review-cta" :to="{ name: 'post-new', query: { type: 'review' } }">장소 후기 남기기</RouterLink>
      </div>
      <div class="hero-route" aria-hidden="true"><span>01</span><i></i><span>02</span><i></i><span>03</span></div>
    </header>

    <section v-if="popular.length" class="popular-places">
      <div class="section-heading"><span>PLACES PEOPLE TALK ABOUT</span><h2>지금 이야기가 이어지는 장소</h2></div>
      <div class="place-strip">
        <button v-for="(item, index) in popular" :key="item.content.contentid" v-reveal="index % 4" class="interactive-card" :class="{ active: contentId === item.content.contentid }" @click="selectPlace(item.content.contentid)">
          <img v-if="item.content.firstimage" :src="item.content.firstimage" :alt="item.content.title">
          <span><b>{{ item.content.title }}</b><small>{{ item.post_count }}개의 이야기</small></span>
        </button>
      </div>
    </section>

    <section class="story-browser">
      <div class="type-tabs" role="group" aria-label="기록 종류">
        <button v-for="option in TYPE_OPTIONS" :key="option.value" :class="{ active: postType === option.value }" :aria-pressed="postType === option.value" @click="setType(option.value)">
          <b>{{ option.label }}</b><small>{{ option.description }}</small>
        </button>
      </div>

      <div class="filters">
        <CategoryFilter v-model="category" />
        <div class="filter-row">
          <form @submit.prevent="resetAndLoad"><label class="sr-only" for="community-search">커뮤니티 검색</label><input id="community-search" v-model="keyword" placeholder="장소명이나 여행 이야기 검색"><button class="btn">검색</button></form>
          <fieldset class="sort-control">
            <legend>게시글 정렬</legend>
            <button v-for="option in SORT_OPTIONS" :key="option.value" type="button" :class="{ active: sort === option.value }" :aria-pressed="sort === option.value" @click="setSort(option.value)">{{ option.label }}</button>
          </fieldset>
        </div>
        <button v-if="contentId" class="clear-place" @click="contentId = ''; resetAndLoad()">{{ selectedPlace?.title || '선택 장소' }} 필터 해제 ×</button>
      </div>

      <div class="results-heading">
        <div><span>TRAVEL NOTES</span><h2>{{ data?.total ?? 0 }}개의 서울 기록</h2></div>
        <p v-if="postType === 'course'">여행자가 직접 걸어본 하루 코스만 모았어요.</p>
        <p v-else-if="postType === 'review'">한 장소를 깊게 경험한 후기를 모았어요.</p>
        <p v-else>서로 다른 방식으로 경험한 서울을 둘러보세요.</p>
      </div>

      <StateDisplay :loading="loading" :error="error" :empty="!loading && !error && data?.items?.length === 0" empty-text="이 조건에 맞는 기록이 아직 없습니다. 첫 이야기를 남겨보세요.">
        <div class="story-grid"><CommunityPostCard v-for="(post, index) in data?.items ?? []" :key="post.id" v-reveal="index % 6" :post="post" /></div>
        <nav v-if="totalPages > 1" class="pagination" aria-label="커뮤니티 페이지">
          <button :disabled="page <= 1" aria-label="이전 페이지" @click="setPage(page - 1)">←</button>
          <button v-for="number in pages" :key="number" :class="{ active: number === page }" :aria-current="number === page ? 'page' : undefined" @click="setPage(number)">{{ number }}</button>
          <button :disabled="page >= totalPages" aria-label="다음 페이지" @click="setPage(page + 1)">→</button>
        </nav>
      </StateDisplay>
    </section>
  </section>
</template>

<style scoped>
.community-page{padding-bottom:5rem}.community-hero{position:relative;display:flex;align-items:flex-end;justify-content:space-between;gap:2rem;min-height:410px;padding:clamp(3rem,7vw,6rem) 0 3rem;border-bottom:1px solid var(--line);overflow:hidden}.hero-copy{position:relative;z-index:2}.kicker,.section-heading span,.results-heading span{font-size:.74rem;letter-spacing:.2em;color:var(--accent);font-weight:800}.community-hero h1{max-width:800px;margin:.8rem 0 1.1rem;font:clamp(3rem,6.5vw,6.4rem)/.96 var(--display);letter-spacing:-.055em}.community-hero h1 em{color:var(--accent);font-style:italic}.community-hero p{max-width:620px;color:var(--muted);font-size:1rem}.hero-actions{position:relative;z-index:2;display:flex;align-items:center;flex-direction:column;gap:.65rem;flex:0 0 auto}.course-cta{gap:2rem;min-width:210px;justify-content:space-between}.course-cta b{font-size:1.1rem;transition:transform .2s}.course-cta:hover b{transform:translateX(4px)}.review-cta{color:var(--muted);font-size:.78rem;font-weight:800;text-underline-offset:4px}.review-cta:hover{color:var(--primary)}.hero-route{position:absolute;right:2%;top:19%;display:flex;align-items:center;gap:.5rem;opacity:.17;transform:rotate(-8deg);pointer-events:none}.hero-route span{display:grid;place-items:center;width:52px;height:52px;border:1px solid var(--ink);border-radius:50%;font-size:.65rem;font-weight:800}.hero-route i{width:70px;height:1px;background:var(--ink)}.popular-places{margin:clamp(3rem,6vw,5rem) 0}.section-heading h2{margin:.3rem 0 1.2rem;font:2rem var(--display)}.place-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:.7rem}.place-strip button{display:flex;gap:.65rem;align-items:center;min-width:0;padding:.55rem;border:1px solid var(--line);border-radius:14px;background:var(--surface);color:var(--text);text-align:left}.place-strip button.active{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent)}.place-strip img{width:52px;height:52px;border-radius:10px;object-fit:cover}.place-strip span{display:flex;flex-direction:column;min-width:0}.place-strip b,.place-strip small{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.place-strip b{font-size:.86rem}.place-strip small{color:var(--muted);font-size:.72rem}.story-browser{scroll-margin-top:100px}.type-tabs{display:grid;grid-template-columns:repeat(3,1fr);gap:.6rem;margin-bottom:.8rem}.type-tabs button{display:flex;align-items:baseline;justify-content:space-between;gap:.6rem;padding:1rem 1.15rem;border:1px solid var(--line);border-radius:15px;background:var(--surface);color:var(--text);text-align:left;transition:transform .2s,border-color .2s,background .2s}.type-tabs button:hover{transform:translateY(-2px)}.type-tabs button small{color:var(--muted);font-size:.67rem}.type-tabs button.active{border-color:var(--primary);background:color-mix(in srgb,var(--primary) 8%,var(--surface));color:var(--primary)}.filters{margin-bottom:2.5rem;padding:1rem;border:1px solid var(--line);border-radius:20px;background:var(--surface)}.filter-row{display:flex;align-items:center;justify-content:space-between;gap:1rem}.filters form{display:flex;flex:1;gap:.5rem}.filters form input{flex:1;min-width:0;padding:.7rem 1rem;border:1px solid var(--line);border-radius:12px;background:var(--input);color:var(--text)}.sort-control{display:flex;align-items:center;gap:.18rem;margin:0;padding:.22rem;border:1px solid var(--line);border-radius:12px;background:var(--soft)}.sort-control legend,.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}.sort-control button{padding:.58rem .78rem;border:0;border-radius:9px;background:transparent;color:var(--muted);font-size:.8rem;font-weight:700;white-space:nowrap}.sort-control button.active{background:var(--surface);color:var(--primary);box-shadow:0 3px 12px rgba(0,0,0,.08)}.clear-place{margin-top:.7rem;padding:.4rem .7rem;border:0;border-radius:9px;background:var(--soft);color:var(--primary);font-size:.78rem}.results-heading{display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;margin-bottom:1.4rem}.results-heading h2{margin-top:.25rem;font:clamp(1.7rem,3vw,2.3rem) var(--display)}.results-heading p{color:var(--muted);font-size:.78rem}.story-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1.2rem}@media(max-width:1000px){.community-hero{align-items:flex-start;flex-direction:column}.hero-actions{align-items:flex-start}.place-strip{grid-template-columns:repeat(2,1fr)}.story-grid{grid-template-columns:repeat(2,1fr)}.filter-row{align-items:stretch;flex-direction:column}.sort-control{align-self:flex-end}}@media(max-width:680px){.community-hero{min-height:auto}.community-hero h1{font-size:clamp(3rem,15vw,4.8rem)}.hero-route{display:none}.type-tabs{display:flex;overflow:auto}.type-tabs button{flex:0 0 160px;align-items:flex-start;flex-direction:column}.place-strip{display:flex;overflow:auto}.place-strip button{min-width:210px}.story-grid{grid-template-columns:1fr}.filters form{flex-direction:column}.sort-control{align-self:stretch;justify-content:center}.sort-control button{flex:1;padding-inline:.4rem}.results-heading{align-items:flex-start;flex-direction:column}.results-heading p{display:none}}
</style>
