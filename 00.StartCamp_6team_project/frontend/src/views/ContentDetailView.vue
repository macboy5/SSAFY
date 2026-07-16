<script setup>
import { ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api/client'
import StateDisplay from '../components/StateDisplay.vue'
import { useAsyncData } from '../composables/useAsyncData'
import { usePlannerStore } from '../stores/planner'
import KakaoMap from '../components/KakaoMap.vue'
import RealtimeCityBadge from '../components/RealtimeCityBadge.vue'

const props = defineProps({
  id: { type: String, required: true },
})

const { data, loading, error, run } = useAsyncData()
const planner = usePlannerStore()
const planDate = ref(new Date().toLocaleDateString('sv-SE'))
const added = ref(false)

function load() {
  run(() => api.get(`/contents/${props.id}`))
}

watch(() => props.id, load, { immediate: true })

async function addToPlanner() {
  await planner.addItem(planDate.value, data.value.content)
  added.value = true
  setTimeout(() => added.value = false, 2200)
}

function storyExcerpt(body = '') {
  const text = body.replace(/\s+/g, ' ').trim()
  return text.length > 105 ? `${text.slice(0, 105).trim()}…` : text
}

function storyDate(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(new Date(value))
}
</script>

<template>
  <section>
    <StateDisplay :loading="loading" :error="error">
      <template v-if="data">
        <div class="detail">
          <img
            v-if="data.content.firstimage"
            :src="data.content.firstimage"
            :alt="data.content.title"
            class="hero-image"
          />
          <span class="category">{{ data.content.category }}</span>
          <h1>{{ data.content.title }}</h1>
          <p class="addr">{{ data.content.addr1 }} {{ data.content.addr2 }}</p>
          <p v-if="data.content.tel">전화: {{ data.content.tel }}</p>

          <div class="add-row"><label>여행 날짜 <input v-model="planDate" type="date"></label><button class="btn" @click="addToPlanner">캘린더에 추가</button><RouterLink class="planner-link" to="/planner">플래너 보기 →</RouterLink></div>
          <p v-if="added" class="success">✓ 선택한 날짜의 일정에 저장했어요.</p>
          <RealtimeCityBadge v-reveal :content-id="data.content.contentid" />
          <KakaoMap v-reveal="1" :places="[data.content]" height="320px" />
        </div>

        <section v-reveal class="related-stories" aria-labelledby="related-stories-title">
          <header class="stories-header">
            <div class="stories-copy">
              <p class="stories-kicker">
                <span>COMMUNITY</span>
                <span aria-hidden="true">·</span>
                <span>{{ data.posts.length }} STORIES</span>
              </p>
              <h2 id="related-stories-title">
                <em>{{ data.content.title }}</em>에서 이어진 이야기
              </h2>
              <p>먼저 다녀온 사람들의 시선으로 이 장소를 조금 더 깊게 만나보세요.</p>
            </div>
            <RouterLink
              class="new-story-action"
              :to="{ name: 'post-new', query: { content_id: id } }"
              :aria-label="`${data.content.title}에 관한 새 글 쓰기`"
            >
              <span>이 장소에 대한</span>
              <strong>나의 이야기 쓰기</strong>
              <b aria-hidden="true">↗</b>
            </RouterLink>
          </header>

          <div v-if="data.posts.length" class="story-grid" role="list">
            <article v-for="(post, index) in data.posts" :key="post.id" role="listitem">
              <RouterLink
                class="story-card"
                :to="{ name: 'post-detail', params: { id: post.id } }"
                :aria-label="`${post.title}, ${post.nickname} 작성`"
              >
                <div class="story-card-top">
                  <span class="story-number">STORY {{ String(index + 1).padStart(2, '0') }}</span>
                  <span v-if="post.like_count" class="story-like" :aria-label="`좋아요 ${post.like_count}개`">
                    <span aria-hidden="true">♥</span> {{ post.like_count }}
                  </span>
                </div>
                <div class="story-card-copy">
                  <h3>{{ post.title }}</h3>
                  <p>{{ storyExcerpt(post.body) || '이 장소에서 만난 특별한 순간을 확인해 보세요.' }}</p>
                </div>
                <footer class="story-meta">
                  <span class="story-avatar" aria-hidden="true">{{ post.nickname?.slice(0, 1) || 'S' }}</span>
                  <span class="story-author">
                    <strong>{{ post.nickname }}</strong>
                    <time :datetime="post.created_at">{{ storyDate(post.created_at) }}</time>
                  </span>
                  <span class="story-read">읽어보기 <b aria-hidden="true">↗</b></span>
                </footer>
              </RouterLink>
            </article>
          </div>

          <div v-else class="empty-stories">
            <div class="empty-mark" aria-hidden="true">
              <span>SEOUL</span>
              <i></i><i></i><i></i>
            </div>
            <div>
              <span>BE THE FIRST STORYTELLER</span>
              <h3>이 장소의 첫 이야기를 남겨보세요.</h3>
              <p>좋았던 풍경, 나만의 동선, 작은 팁까지. 다음 여행자에게 오래 남을 이야기가 됩니다.</p>
            </div>
            <RouterLink class="empty-story-action" :to="{ name: 'post-new', query: { content_id: id } }">
              첫 이야기 쓰기 <span aria-hidden="true">→</span>
            </RouterLink>
          </div>
        </section>
      </template>
    </StateDisplay>
  </section>
</template>

<style scoped>
.detail {
  margin-bottom: 2rem;
}
.detail h1{font:clamp(2.5rem,5vw,4.5rem)/1.05 var(--display);margin:.5rem 0}.detail>.map-shell{margin-top:2rem}.add-row label{font-size:.75rem;font-weight:700;display:flex;flex-direction:column;gap:.2rem}.add-row input{border:1px solid var(--line);border-radius:8px;padding:.55rem}.planner-link{color:var(--primary);font-weight:700;font-size:.8rem}.success{color:var(--primary);font-size:.85rem;margin-top:.5rem}
.hero-image {
  width: 100%;
  max-height: 320px;
  object-fit: cover;
  border-radius: 12px;
  margin-bottom: 1rem;
  transition:transform .65s var(--ease-out),filter .65s;
}
.detail:hover .hero-image{transform:scale(.995);filter:saturate(1.04)}
.category {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--primary);
}
.addr {
  color: var(--muted);
}
.add-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1rem;
  flex-wrap: wrap;
}
.related-stories{margin-top:clamp(4rem,9vw,8rem);padding:clamp(1.25rem,3vw,2.2rem);border:1px solid var(--line);border-radius:30px;background:color-mix(in srgb,var(--surface) 94%,transparent);box-shadow:var(--shadow);overflow:hidden}.stories-header{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:end;gap:2rem;padding:clamp(.4rem,2vw,1.2rem) clamp(.2rem,1vw,.7rem) clamp(2rem,5vw,3.5rem)}.stories-kicker{display:flex;align-items:center;gap:.5rem;margin:0;color:var(--accent);font-size:.62rem;font-weight:800;letter-spacing:.18em}.stories-copy h2{margin:.7rem 0 1rem;font:clamp(2.15rem,4.7vw,4.3rem)/1.03 var(--display);letter-spacing:-.045em}.stories-copy h2 em{color:var(--primary);font-style:normal}.stories-copy>p:last-child{max-width:560px;margin:0;color:var(--muted);font-size:.86rem;line-height:1.75}.new-story-action{position:relative;display:grid;min-width:210px;grid-template-columns:1fr auto;gap:.15rem 1rem;align-items:center;padding:1rem 1.1rem;border:1px solid var(--line);border-radius:18px;background:var(--soft);color:var(--text);text-decoration:none;transition:transform .25s,border-color .25s,background .25s}.new-story-action span{font-size:.59rem;color:var(--muted);letter-spacing:.06em}.new-story-action strong{font-size:.8rem}.new-story-action b{grid-column:2;grid-row:1/3;display:grid;place-items:center;width:36px;height:36px;border-radius:50%;background:var(--ink);color:var(--bg);transition:transform .25s}.new-story-action:hover,.new-story-action:focus-visible{transform:translateY(-3px);border-color:color-mix(in srgb,var(--primary) 50%,var(--line));background:color-mix(in srgb,var(--primary) 8%,var(--soft))}.new-story-action:hover b,.new-story-action:focus-visible b{transform:rotate(45deg)}.story-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.85rem}.story-grid article{min-width:0}.story-card{position:relative;display:flex;min-height:260px;height:100%;flex-direction:column;padding:clamp(1.1rem,2.5vw,1.5rem);border:1px solid var(--line);border-radius:22px;background:var(--surface);color:var(--text);text-decoration:none;overflow:hidden;transition:transform .3s var(--ease-out),box-shadow .3s,border-color .3s}.story-card:before{content:'';position:absolute;right:-85px;top:-95px;width:190px;height:190px;border-radius:50%;background:color-mix(in srgb,var(--primary) 7%,transparent);transition:transform .55s var(--ease-out),background .3s}.story-card:hover,.story-card:focus-visible{z-index:1;transform:translateY(-6px);border-color:color-mix(in srgb,var(--primary) 42%,var(--line));box-shadow:0 20px 48px color-mix(in srgb,var(--ink) 11%,transparent)}.story-card:hover:before,.story-card:focus-visible:before{transform:scale(1.3);background:color-mix(in srgb,var(--accent) 11%,transparent)}.story-card-top{position:relative;display:flex;align-items:center;justify-content:space-between;gap:1rem}.story-number{font-size:.58rem;font-weight:800;letter-spacing:.14em;color:var(--accent)}.story-like{font-size:.66rem;font-weight:700;color:var(--muted)}.story-like>span{color:var(--accent)}.story-card-copy{position:relative;flex:1;padding:clamp(1.3rem,3vw,2rem) 0}.story-card-copy h3{margin:0 0 .7rem;font:clamp(1.35rem,2.2vw,1.85rem)/1.22 var(--display);letter-spacing:-.025em;overflow-wrap:anywhere}.story-card-copy p{display:-webkit-box;margin:0;color:var(--muted);font-size:.78rem;line-height:1.75;-webkit-box-orient:vertical;-webkit-line-clamp:3;overflow:hidden}.story-meta{position:relative;display:grid;grid-template-columns:34px 1fr auto;align-items:center;gap:.65rem;padding:1rem 0 0;border-top:1px solid var(--line)}.story-avatar{display:grid;place-items:center;width:34px;height:34px;border-radius:50%;background:var(--soft);color:var(--primary);font-size:.72rem;font-weight:800}.story-author{display:flex;min-width:0;flex-direction:column}.story-author strong{font-size:.7rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.story-author time{color:var(--muted);font-size:.58rem}.story-read{display:flex;align-items:center;gap:.35rem;color:var(--primary);font-size:.65rem;font-weight:800}.story-read b{font-size:.85rem;transition:transform .25s}.story-card:hover .story-read b,.story-card:focus-visible .story-read b{transform:translate(2px,-2px)}.empty-stories{position:relative;display:grid;grid-template-columns:150px minmax(0,1fr) auto;align-items:center;gap:clamp(1rem,3vw,2rem);min-height:230px;padding:clamp(1.3rem,4vw,2.6rem);border:1px dashed color-mix(in srgb,var(--primary) 42%,var(--line));border-radius:22px;background:linear-gradient(135deg,color-mix(in srgb,var(--primary) 8%,var(--surface)),var(--surface));overflow:hidden}.empty-mark{position:relative;display:grid;place-items:center;width:135px;aspect-ratio:1;border:1px solid color-mix(in srgb,var(--primary) 25%,var(--line));border-radius:50%;color:color-mix(in srgb,var(--primary) 62%,transparent);font:1rem var(--display);letter-spacing:.12em}.empty-mark:before,.empty-mark:after{content:'';position:absolute;border:1px solid color-mix(in srgb,var(--accent) 28%,transparent);border-radius:50%}.empty-mark:before{inset:16%;transform:rotate(18deg)}.empty-mark:after{inset:31%;transform:rotate(-12deg)}.empty-mark i{position:absolute;width:6px;height:6px;border-radius:50%;background:var(--accent)}.empty-mark i:nth-of-type(1){left:14%;top:38%}.empty-mark i:nth-of-type(2){right:17%;top:23%}.empty-mark i:nth-of-type(3){right:27%;bottom:12%}.empty-stories>div:nth-child(2)>span{color:var(--accent);font-size:.56rem;font-weight:800;letter-spacing:.16em}.empty-stories h3{margin:.45rem 0 .55rem;font:clamp(1.5rem,2.8vw,2.15rem)/1.2 var(--display)}.empty-stories p{max-width:570px;margin:0;color:var(--muted);font-size:.76rem;line-height:1.7}.empty-story-action{display:flex;align-items:center;gap:.7rem;padding:.8rem 1rem;border-radius:99px;background:var(--ink);color:var(--bg);font-size:.7rem;font-weight:800;text-decoration:none;white-space:nowrap;transition:transform .25s}.empty-story-action:hover,.empty-story-action:focus-visible{transform:translateY(-3px)}.empty-story-action span{font-size:1rem}@media(max-width:800px){.stories-header{grid-template-columns:1fr;align-items:start}.new-story-action{width:min(100%,280px)}.empty-stories{grid-template-columns:105px 1fr}.empty-mark{width:100px}.empty-story-action{grid-column:2;justify-self:start}}@media(max-width:620px){.related-stories{margin-top:4rem;padding:1rem;border-radius:22px}.stories-header{padding:.6rem .3rem 2rem}.stories-copy h2 br{display:none}.story-grid{grid-template-columns:1fr}.story-card{min-height:230px}.empty-stories{grid-template-columns:1fr;text-align:center}.empty-mark{margin:auto}.empty-story-action{grid-column:1;justify-self:center}.story-meta{grid-template-columns:34px 1fr}.story-read{display:none}}@media(prefers-reduced-motion:reduce){.story-card,.story-card:before,.new-story-action,.new-story-action b,.empty-story-action{transition:none}.story-card:hover,.story-card:focus-visible,.new-story-action:hover,.new-story-action:focus-visible,.empty-story-action:hover,.empty-story-action:focus-visible{transform:none}}
.detail h1{max-width:900px;font-size:clamp(2.3rem,4.7vw,4rem);line-height:1.12;letter-spacing:-.035em;text-wrap:balance}.stories-copy h2{max-width:760px;font-size:clamp(2rem,4.3vw,3.65rem);line-height:1.12;letter-spacing:-.035em;text-wrap:balance}
</style>
