<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { api } from '../api/client'
import AnimatedCounter from '../components/AnimatedCounter.vue'
import CategoryFilter from '../components/CategoryFilter.vue'
import ContentCard from '../components/ContentCard.vue'
import DetectiveReveal from '../components/DetectiveReveal.vue'
import StateDisplay from '../components/StateDisplay.vue'
import { useAsyncData } from '../composables/useAsyncData'

const category = ref('')
const area = ref('')
const keyword = ref('')
const page = ref(1)
const carouselPaused = ref(false)
const conanVisible = ref(false)
const conanArmed = ref(false)
const PAGE_SIZE = 12
let conanTimer = 0
let conanHideTimer = 0
let conanResetTimer = 0
let conanTriggered = false

const { data, loading, error, run } = useAsyncData()

function buildQuery() {
  const params = new URLSearchParams({ page: String(page.value), page_size: String(PAGE_SIZE) })
  if (category.value) params.set('category', category.value)
  if (area.value) params.set('area', area.value)
  if (keyword.value) params.set('keyword', keyword.value)
  return params.toString()
}

function load() {
  run(() => api.get(`/contents?${buildQuery()}`))
}

function search() {
  page.value = 1
  load()
}

watch(category, () => {
  page.value = 1
  load()
})

const totalPages = computed(() => Math.max(1, Math.ceil((data.value?.total || 0) / PAGE_SIZE)))
const pageNumbers = computed(() => Array.from({ length: Math.min(5, totalPages.value) }, (_, i) => Math.max(1, Math.min(page.value - 2, totalPages.value - 4)) + i))
const hasFilters = computed(() => Boolean(category.value || area.value.trim() || keyword.value.trim()))
function setPage(value) { page.value = value; load(); window.scrollTo({ top: 0, behavior: 'smooth' }) }

function clearFilters() {
  const categoryChanged = Boolean(category.value)
  category.value = ''
  area.value = ''
  keyword.value = ''
  page.value = 1
  if (!categoryChanged) load()
}

function moveTitleLens(event) {
  const title = event.currentTarget
  const rect = title.getBoundingClientRect()
  const x = Math.min(Math.max(event.clientX - rect.left, 0), rect.width)
  const y = Math.min(Math.max(event.clientY - rect.top, 0), rect.height)
  title.style.setProperty('--lens-x', `${x}px`)
  title.style.setProperty('--lens-y', `${y}px`)
  title.style.setProperty('--title-width', `${rect.width}px`)
}

function armConan(event) {
  if (event.pointerType !== 'mouse' || conanTriggered || conanVisible.value) return
  clearTimeout(conanTimer)
  conanArmed.value = true
  conanTimer = window.setTimeout(() => {
    conanTriggered = true
    conanArmed.value = false
    conanVisible.value = true
    conanHideTimer = window.setTimeout(hideConan, 5200)
  }, 3000)
}

function disarmConan() {
  clearTimeout(conanTimer)
  conanArmed.value = false
}

function hideConan() {
  clearTimeout(conanHideTimer)
  conanVisible.value = false
  clearTimeout(conanResetTimer)
  conanResetTimer = window.setTimeout(() => { conanTriggered = false }, 500)
}

onBeforeUnmount(() => {
  clearTimeout(conanTimer)
  clearTimeout(conanHideTimer)
  clearTimeout(conanResetTimer)
})

load()
</script>

<template>
  <section>
    <div class="page-header discover-header">
      <div class="discover-copy">
        <span class="kicker">서울 취향 아카이브</span>
        <h1 class="magnify-title" :class="{ 'is-investigating': conanArmed }" @pointerenter="armConan" @pointerleave="disarmConan" @pointermove="moveTitleLens">
          <span class="title-base">도시의 취향을<br>발견하는 방법</span>
          <span class="title-lens" aria-hidden="true">
            <span class="lens-viewport"><span class="lens-copy">도시의 취향을<br>발견하는 방법</span></span>
          </span>
          <span class="clue-pop" aria-hidden="true">!</span>
        </h1>
        <RouterLink class="map-link" to="/map">지도 한 장으로 서울 둘러보기 <b>↗</b></RouterLink>
      </div>
      <aside class="archive-note" aria-label="관광 데이터 안내">
        <strong><span v-if="loading" class="counter-loading">···</span><AnimatedCounter v-else :value="data?.total ?? 0" :duration="1450" /></strong>
        <span class="metric-label"><i aria-hidden="true"></i>지금 둘러볼 수 있는 장소</span>
        <p>관광공사 데이터를 서울의 일곱 가지 취향으로 정리했습니다.</p>
      </aside>
    </div>

    <CategoryFilter v-model="category" />

    <form class="search-row" @submit.prevent="search">
      <label><span>동네 또는 주소</span><input v-model="area" type="search" autocomplete="off" placeholder="예: 강남, 성수, 종로" /></label>
      <label><span>찾고 싶은 취향</span><input v-model="keyword" type="search" autocomplete="off" placeholder="예: 공원, 미술관, 야경" /></label>
      <button type="submit" class="btn search-button"><small>SEARCH</small><strong>장소 찾기</strong></button>
      <button v-if="hasFilters" type="button" class="clear-button" @click="clearFilters">조건 지우기</button>
    </form>

    <header class="result-line" aria-live="polite">
      <div>
        <span>둘러보기 결과</span>
        <h2>{{ hasFilters ? '선택한 조건에 맞는 장소' : '서울의 장소를 골라봤어요' }}</h2>
      </div>
      <p><small>전체</small><strong><AnimatedCounter :value="data?.total ?? 0" :duration="800" /></strong><em>곳</em></p>
    </header>

    <StateDisplay
      :loading="loading"
      :error="error"
      :empty="!loading && !error && data?.items?.length === 0"
      empty-text="검색 조건에 맞는 콘텐츠가 없습니다."
    >
      <section v-if="!hasFilters" class="places-carousel" :class="{ paused: carouselPaused }" aria-label="전체 장소 자동 슬라이드">
        <div class="carousel-toolbar">
          <span><i aria-hidden="true"></i>서울 곳곳을 천천히 둘러보세요</span>
          <button type="button" :aria-pressed="carouselPaused" @click="carouselPaused = !carouselPaused">
            {{ carouselPaused ? '계속 보기' : '잠시 멈춤' }}
          </button>
        </div>
        <div class="carousel-viewport">
          <div class="carousel-track">
            <div
              v-for="copy in 2"
              :key="copy"
              class="carousel-sequence"
              :aria-hidden="copy === 2 ? 'true' : undefined"
              :inert="copy === 2"
            >
              <div v-for="item in data?.items ?? []" :key="`${copy}-${item.contentid}`" class="carousel-item">
                <ContentCard :content="item" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <div v-else class="card-grid explore-grid">
        <ContentCard v-for="(item, index) in data?.items ?? []" :key="item.contentid" v-reveal="index % 6" :content="item" />
      </div>

      <div class="pagination">
        <button type="button" aria-label="이전 페이지" :disabled="page <= 1" @click="setPage(page-1)">←</button>
        <button v-for="n in pageNumbers" :key="n" type="button" :aria-label="`${n}페이지`" :aria-current="n === page ? 'page' : undefined" :class="{active:n===page}" @click="setPage(n)">{{ n }}</button>
        <button type="button" aria-label="다음 페이지" :disabled="page >= totalPages" @click="setPage(page+1)">→</button>
      </div>
    </StateDisplay>
    <DetectiveReveal :visible="conanVisible" @close="hideConan" />
  </section>
</template>

<style scoped>
.discover-header{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(240px,.65fr);align-items:end;gap:clamp(2rem,7vw,7rem);padding:clamp(3rem,8vw,7rem) 0 2.5rem;margin:0}
.discover-copy{min-width:0}
.kicker{font-size:.68rem;letter-spacing:.16em;color:var(--accent);font-weight:800}
.discover-header h1{margin:.8rem 0 1.25rem;font-size:clamp(2.95rem,6.2vw,5.9rem);line-height:.98;letter-spacing:-.055em}
.magnify-title{--lens-x:50%;--lens-y:50%;--title-width:100%;position:relative;width:fit-content;cursor:zoom-in}
.title-base{display:block}
.title-lens{position:absolute;left:0;top:0;z-index:4;width:7.25rem;height:7.25rem;opacity:0;pointer-events:none;transform:translate3d(var(--lens-x),var(--lens-y),0) translate(-50%,-50%);transition:opacity var(--motion-fast)}
.title-lens:before{content:'';position:absolute;z-index:0;inset:-.48rem;border-radius:50%;opacity:0;pointer-events:none;background:conic-gradient(from 205deg,transparent 0 58%,color-mix(in srgb,var(--accent) 18%,transparent) 68%,color-mix(in srgb,var(--accent) 86%,transparent) 83%,transparent 94%);filter:drop-shadow(0 0 5px color-mix(in srgb,var(--accent) 34%,transparent));-webkit-mask:radial-gradient(farthest-side,transparent calc(100% - 3px),#000 calc(100% - 2px));mask:radial-gradient(farthest-side,transparent calc(100% - 3px),#000 calc(100% - 2px));transform:rotate(-35deg)}
.title-lens:after{content:'';position:absolute;right:-1.1rem;bottom:.25rem;width:2rem;height:.55rem;border:1px solid color-mix(in srgb,var(--ink) 25%,transparent);border-radius:99px;background:var(--primary);box-shadow:0 6px 14px color-mix(in srgb,var(--ink) 14%,transparent);transform:rotate(45deg);transform-origin:left center}
.lens-viewport{position:absolute;inset:0;z-index:1;overflow:hidden;border:2px solid color-mix(in srgb,var(--ink) 38%,transparent);border-radius:50%;background:color-mix(in srgb,var(--surface) 92%,transparent);box-shadow:inset 0 0 0 3px color-mix(in srgb,white 42%,transparent),0 16px 38px color-mix(in srgb,var(--ink) 18%,transparent);backdrop-filter:blur(4px);transform:scale(.78);transition:transform var(--motion-fast) var(--ease-out)}
.lens-viewport:after{content:'';position:absolute;z-index:3;left:10%;right:10%;top:18%;height:2px;border-radius:99px;opacity:0;pointer-events:none;background:linear-gradient(90deg,transparent,color-mix(in srgb,var(--accent) 82%,white),transparent);box-shadow:0 0 12px color-mix(in srgb,var(--accent) 52%,transparent);transform:translate3d(0,-.45rem,0) rotate(-5deg)}
.lens-copy{position:absolute;left:calc(50% - var(--lens-x));top:calc(50% - var(--lens-y));display:block;width:var(--title-width);color:var(--primary);font:inherit;letter-spacing:inherit;line-height:inherit;white-space:nowrap;transform:scale(1.18);transform-origin:var(--lens-x) var(--lens-y)}
.clue-pop{position:absolute;left:0;top:0;z-index:6;display:grid;width:1.75rem;height:1.95rem;place-items:center;border:1px solid color-mix(in srgb,var(--accent) 68%,var(--ink));border-radius:10px;background:color-mix(in srgb,var(--surface) 92%,white);box-shadow:0 7px 18px color-mix(in srgb,var(--accent) 22%,transparent),inset 0 0 0 2px color-mix(in srgb,white 58%,transparent);color:var(--accent);font:900 1.16rem/1 var(--display);letter-spacing:0;opacity:0;pointer-events:none;transform:translate3d(var(--lens-x),var(--lens-y),0) translate(2.2rem,-3.6rem) rotate(-10deg) scale(.25);transform-origin:35% 100%}
.clue-pop:after{content:'';position:absolute;left:.25rem;bottom:-.26rem;width:.48rem;height:.48rem;border-right:1px solid color-mix(in srgb,var(--accent) 68%,var(--ink));border-bottom:1px solid color-mix(in srgb,var(--accent) 68%,var(--ink));background:inherit;transform:rotate(45deg)}
.magnify-title.is-investigating .title-lens:before{animation:clue-orbit 3s cubic-bezier(.22,.72,.24,1) both}
.magnify-title.is-investigating .lens-viewport{animation:lens-investigate 3s linear forwards}
.magnify-title.is-investigating .lens-viewport:after{animation:clue-scan 1.08s .24s ease-in-out 2 alternate both}
.magnify-title.is-investigating .clue-pop{animation:clue-pop-in 1.45s .5s cubic-bezier(.18,.85,.25,1) both}
@media(hover:hover) and (pointer:fine){.magnify-title:hover .title-lens{opacity:1}.magnify-title:hover .lens-viewport{transform:scale(1)}}
.map-link{display:inline-flex;align-items:center;gap:.65rem;color:var(--text);font-size:.8rem;font-weight:700;text-decoration:none}
.map-link b{position:relative;display:grid;width:30px;height:30px;place-items:center;border:1px solid var(--line);border-radius:9px;color:var(--primary);transition:transform var(--motion-fast),background var(--motion-fast)}
.map-link b:after{content:'';position:absolute;inset:-1px;border:1px solid var(--accent);border-radius:inherit;opacity:0;pointer-events:none}
.map-link:hover b{transform:translate(2px,-2px);background:var(--soft)}
.map-link:hover b:after{animation:icon-ripple .7s ease-out}
.archive-note{position:relative;isolation:isolate;overflow:hidden;padding:1.4rem 1.45rem;border-radius:24px;background:var(--line);box-shadow:0 16px 44px color-mix(in srgb,var(--ink) 7%,transparent)}
.archive-note:before{content:'';position:absolute;z-index:-2;inset:-85%;background:conic-gradient(from 0deg,transparent 0 78%,color-mix(in srgb,var(--accent) 75%,transparent) 88%,var(--primary) 93%,transparent 100%);animation:border-trail 7s linear infinite}
.archive-note:after{content:'';position:absolute;z-index:-1;inset:1px;border-radius:23px;background:color-mix(in srgb,var(--surface) 94%,transparent)}
.archive-note strong{display:block;min-height:.95em;font:clamp(2.6rem,5vw,4.6rem)/.95 var(--display);letter-spacing:-.05em}
.archive-note .counter-loading{font:inherit}
.archive-note .metric-label{display:flex;align-items:center;gap:.45rem;margin-top:.25rem;font-size:.7rem;font-weight:800}
.metric-label i{width:6px;height:6px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 4px color-mix(in srgb,var(--accent) 12%,transparent);animation:live-pulse 2.2s ease-out infinite}
.archive-note p{max-width:32ch;margin-top:.8rem;color:var(--muted);font-size:.72rem;line-height:1.65}
.search-row{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr) auto auto;align-items:end;gap:.55rem;margin:0 0 1rem;padding:1rem;border:1px solid var(--line);border-radius:18px;background:color-mix(in srgb,var(--surface) 84%,transparent);box-shadow:0 14px 36px color-mix(in srgb,var(--ink) 5%,transparent)}
.search-row label{display:grid;gap:.35rem;min-width:0}
.search-row label span{padding-left:.15rem;color:var(--muted);font-size:.74rem;font-weight:700}
.search-row input{width:100%;min-height:46px;padding:.72rem .85rem;border:1px solid transparent;border-radius:11px;background:var(--soft);color:var(--text);outline:0;transition:border-color var(--motion-fast),background var(--motion-fast),box-shadow var(--motion-fast)}
.search-row input:focus{border-color:var(--accent);background:var(--input);box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 12%,transparent)}
.search-button{display:grid;min-width:112px;grid-template-columns:1fr;gap:0;padding:.42rem 1rem;text-align:left}
.search-button small{font-size:.58rem;letter-spacing:.11em;opacity:.76}
.search-button strong{font-size:.88rem}
.clear-button{min-height:46px;padding:.65rem .7rem;border:0;background:transparent;color:var(--muted);font-size:.78rem;font-weight:700;white-space:nowrap}
.clear-button:hover{color:var(--primary)}
.result-line{display:flex;align-items:flex-end;justify-content:space-between;gap:1.5rem;margin:clamp(2rem,4vw,3.25rem) 0 1.15rem;padding-bottom:.9rem;border-bottom:1px solid var(--line)}
.result-line>div{display:grid;gap:.2rem}
.result-line span{color:var(--accent);font-size:.68rem;font-weight:800;letter-spacing:.12em}
.result-line h2{font:clamp(1.5rem,2.5vw,2rem)/1.15 var(--display);letter-spacing:-.025em}
.result-line p{display:flex;align-items:baseline;gap:.28rem;color:var(--muted);white-space:nowrap}
.result-line p small{font-size:.68rem;font-weight:700}
.result-line p strong{color:var(--text);font:clamp(1.7rem,3vw,2.45rem)/1 var(--display);letter-spacing:-.035em}
.result-line p em{font-size:.76rem;font-style:normal;font-weight:700}
.places-carousel{--loop-gap:1.15rem;--loop-half-gap:.575rem;position:relative;min-width:0}
.carousel-toolbar{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.25rem .15rem;color:var(--muted);font-size:.72rem}
.carousel-toolbar span{display:flex;align-items:center;gap:.45rem;font-weight:700}
.carousel-toolbar i{width:6px;height:6px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 4px color-mix(in srgb,var(--accent) 10%,transparent)}
.carousel-toolbar button{padding:.35rem .5rem;border:0;border-bottom:1px solid var(--line);background:transparent;color:var(--muted);font-size:.7rem;font-weight:800;transition:color var(--motion-fast),border-color var(--motion-fast)}
.carousel-toolbar button:hover{border-color:var(--accent);color:var(--primary)}
.carousel-viewport{overflow:hidden;padding:1rem .15rem 1.8rem;mask-image:linear-gradient(to right,transparent,black 3%,black 97%,transparent)}
.carousel-track{display:flex;width:max-content;gap:var(--loop-gap);animation:places-loop 42s linear infinite;will-change:transform}
.carousel-sequence{display:flex;gap:var(--loop-gap)}
.carousel-item{display:flex;flex:0 0 clamp(15rem,22vw,19rem);width:clamp(15rem,22vw,19rem)}
.carousel-item :deep(.card){width:100%;height:100%}
.places-carousel:hover .carousel-track,.places-carousel.paused .carousel-track,.carousel-track:focus-within{animation-play-state:paused}
.explore-grid{grid-template-columns:repeat(4,minmax(0,1fr));gap:clamp(.8rem,1.5vw,1.25rem)}
.explore-grid :deep(.card:nth-child(6n+1)),.explore-grid :deep(.card:nth-child(6n+6)){grid-column:span 2}
.explore-grid :deep(.card:nth-child(6n+1) .thumb),.explore-grid :deep(.card:nth-child(6n+6) .thumb){aspect-ratio:2/1}
@keyframes border-trail{to{transform:rotate(360deg)}}
@keyframes icon-ripple{0%{opacity:.65;transform:scale(1)}100%{opacity:0;transform:scale(1.65)}}
@keyframes live-pulse{0%,45%{box-shadow:0 0 0 0 color-mix(in srgb,var(--accent) 30%,transparent)}100%{box-shadow:0 0 0 8px transparent}}
@keyframes clue-orbit{0%{opacity:0;transform:rotate(-35deg)}8%{opacity:.54}76%{opacity:.88}94%{opacity:1}100%{opacity:0;transform:rotate(325deg)}}
@keyframes clue-scan{0%{opacity:0;transform:translate3d(0,-.45rem,0) rotate(-5deg)}18%{opacity:.36}68%{opacity:.7}100%{opacity:0;transform:translate3d(0,5rem,0) rotate(-5deg)}}
@keyframes clue-pop-in{0%{opacity:0;transform:translate3d(var(--lens-x),var(--lens-y),0) translate(2.2rem,-3.6rem) rotate(-10deg) scale(.25)}18%{opacity:1;transform:translate3d(var(--lens-x),var(--lens-y),0) translate(2.65rem,-4.25rem) rotate(9deg) scale(1.18)}30%{transform:translate3d(var(--lens-x),var(--lens-y),0) translate(2.55rem,-4.1rem) rotate(4deg) scale(.94)}42%,76%{opacity:1;transform:translate3d(var(--lens-x),var(--lens-y),0) translate(2.55rem,-4.1rem) rotate(5deg) scale(1)}100%{opacity:0;transform:translate3d(var(--lens-x),var(--lens-y),0) translate(2.65rem,-4.55rem) rotate(8deg) scale(.88)}}
@keyframes lens-investigate{0%{border-color:color-mix(in srgb,var(--ink) 38%,transparent)}42%{border-color:color-mix(in srgb,var(--accent) 66%,var(--ink));box-shadow:inset 0 0 0 3px color-mix(in srgb,white 44%,transparent),0 0 0 3px color-mix(in srgb,var(--accent) 12%,transparent),0 16px 38px color-mix(in srgb,var(--ink) 18%,transparent)}78%{border-color:var(--accent);box-shadow:inset 0 0 0 3px color-mix(in srgb,white 50%,transparent),0 0 0 6px color-mix(in srgb,var(--accent) 18%,transparent),0 18px 42px color-mix(in srgb,var(--accent) 20%,transparent)}100%{border-color:var(--accent);box-shadow:inset 0 0 0 3px color-mix(in srgb,white 55%,transparent),0 0 0 10px color-mix(in srgb,var(--accent) 24%,transparent),0 20px 48px color-mix(in srgb,var(--accent) 30%,transparent)}}
@keyframes places-loop{to{transform:translate3d(calc(-50% - var(--loop-half-gap)),0,0)}}
@media(prefers-reduced-motion:reduce){.archive-note:before,.metric-label i{animation:none}.map-link:hover b:after{animation:none}.magnify-title.is-investigating .title-lens:before,.magnify-title.is-investigating .lens-viewport,.magnify-title.is-investigating .lens-viewport:after,.magnify-title.is-investigating .clue-pop{animation:none}.magnify-title.is-investigating .title-lens:before{opacity:.65}.magnify-title.is-investigating .clue-pop{opacity:1;transform:translate3d(var(--lens-x),var(--lens-y),0) translate(2.55rem,-4.1rem) rotate(5deg)}.carousel-viewport{overflow-x:auto;mask-image:none}.carousel-track{animation:none;will-change:auto}.carousel-sequence[aria-hidden="true"]{display:none}}
@media(max-width:1000px){.explore-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.discover-header{grid-template-columns:minmax(0,1.2fr) minmax(220px,.6fr)}.search-row{grid-template-columns:1fr 1fr}.search-button,.clear-button{width:100%}}
@media(max-width:680px){.discover-header{grid-template-columns:1fr;gap:1.8rem;padding-top:3.2rem}.discover-header h1{font-size:clamp(2.8rem,13vw,4.6rem);line-height:1}.title-lens{width:6rem;height:6rem}.archive-note{max-width:360px}.search-row{grid-template-columns:1fr}.result-line{align-items:center}.explore-grid :deep(.card:nth-child(6n+1)),.explore-grid :deep(.card:nth-child(6n+6)){grid-column:span 2}}
@media(max-width:480px){.places-carousel{--loop-gap:.8rem;--loop-half-gap:.4rem}.carousel-item{flex-basis:14rem;width:14rem}.carousel-track{animation-duration:34s}.explore-grid{grid-template-columns:1fr}.explore-grid :deep(.card:nth-child(6n+1)),.explore-grid :deep(.card:nth-child(6n+6)){grid-column:span 1}.explore-grid :deep(.card:nth-child(6n+1) .thumb),.explore-grid :deep(.card:nth-child(6n+6) .thumb){aspect-ratio:4/3}.archive-note strong{font-size:3.4rem}}
</style>
