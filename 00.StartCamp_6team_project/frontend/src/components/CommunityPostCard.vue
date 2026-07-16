<script setup>
import { computed } from 'vue'

const props = defineProps({ post: { type: Object, required: true } })
const isCourse = computed(() => props.post.post_type === 'course')
const stops = computed(() => props.post.course_items || [])
const cover = computed(() => stops.value[0]?.content || props.post.content)

function excerpt(body = '') {
  const text = body.replace(/\s+/g, ' ').trim()
  return text.length > 120 ? `${text.slice(0, 120)}…` : text
}

function travelDate(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat('ko-KR', { month: 'long', day: 'numeric' }).format(
    new Date(`${value}T00:00:00`),
  )
}
</script>

<template>
  <article class="story-card interactive-card" :class="{ 'course-card': isCourse }">
    <RouterLink :to="{ name: 'post-detail', params: { id: post.id } }" class="visual">
      <img v-if="cover?.firstimage" :src="cover.firstimage" :alt="cover.title" loading="lazy">
      <div v-else class="visual-fallback"><span>SEOUL JOURNAL</span></div>
      <span class="category">{{ isCourse ? `${stops.length}곳 · 하루 코스` : cover?.category || '장소 후기' }}</span>
      <div v-if="isCourse" class="route-mark" aria-hidden="true"><i></i><i></i><i></i><b>→</b></div>
    </RouterLink>

    <div class="story-body">
      <div v-if="isCourse" class="course-summary">
        <span class="travel-date">{{ travelDate(post.travel_date) }}</span>
        <div class="stop-names" :aria-label="`${stops.length}개 장소로 구성된 코스`">
          <template v-for="(item, index) in stops.slice(0, 3)" :key="item.content.contentid">
            <span>{{ item.content.title }}</span><b v-if="index < Math.min(stops.length, 3) - 1">→</b>
          </template>
          <em v-if="stops.length > 3">+{{ stops.length - 3 }}</em>
        </div>
      </div>
      <RouterLink v-else-if="cover" class="place" :to="`/contents/${cover.contentid}`">
        <strong>{{ cover.title }}</strong><span>{{ cover.addr1 || '서울' }}</span>
      </RouterLink>
      <div v-else class="place"><strong>서울 이야기</strong><span>여행자의 자유로운 기록</span></div>

      <RouterLink :to="{ name: 'post-detail', params: { id: post.id } }" class="story-link">
        <h2>{{ post.title }}</h2><p>{{ excerpt(post.body) }}</p>
      </RouterLink>
      <footer>
        <span>by {{ post.nickname }}</span>
        <span class="social">
          <b :class="{ liked: post.liked_by_me }" :aria-label="`좋아요 ${post.like_count || 0}개`">{{ post.liked_by_me ? '♥' : '♡' }} {{ post.like_count || 0 }}</b>
          <span class="comment-count" :aria-label="`댓글 ${post.comment_count || 0}개`">댓글 {{ post.comment_count || 0 }}</span>
          <time>{{ new Date(post.created_at).toLocaleDateString('ko-KR') }}</time>
        </span>
      </footer>
    </div>
  </article>
</template>

<style scoped>
.story-card{overflow:hidden;border:1px solid var(--line);border-radius:22px;background:var(--surface);box-shadow:var(--shadow);transition:transform .25s var(--ease-out)}.story-card:focus-within{transform:translateY(-4px)}.story-card:focus-within .visual>img{transform:scale(1.04)}.visual{position:relative;display:block;aspect-ratio:16/10;overflow:hidden;background:var(--soft)}.visual>img{width:100%;height:100%;object-fit:cover;transition:transform .55s var(--ease-out)}.story-card:hover .visual>img{transform:scale(1.055)}.visual:after{content:'';position:absolute;inset:45% 0 0;background:linear-gradient(transparent,rgba(15,24,20,.48));pointer-events:none}.visual-fallback{width:100%;height:100%;display:grid;place-items:center;background:linear-gradient(135deg,var(--soft),var(--surface))}.visual-fallback span{font:.7rem var(--sans);letter-spacing:.18em;color:var(--muted)}.category{position:absolute;z-index:2;left:1rem;top:1rem;padding:.32rem .65rem;border-radius:9px;background:var(--overlay);color:var(--ink);backdrop-filter:blur(10px);font-size:.68rem;font-weight:800}.route-mark{position:absolute;z-index:2;right:1rem;bottom:1rem;display:flex;align-items:center;gap:.28rem;color:#fff}.route-mark i{width:7px;height:7px;border:2px solid #fff;border-radius:50%;box-shadow:0 2px 8px rgba(0,0,0,.25)}.route-mark b{margin-left:.15rem;font-size:.85rem;transition:transform .25s}.story-card:hover .route-mark b{transform:translateX(4px)}.story-body{padding:1.15rem}.place{display:flex;flex-direction:column;text-decoration:none;padding-bottom:.8rem;border-bottom:1px solid var(--line)}.place strong{font-size:.82rem;color:var(--primary)}.place span{font-size:.69rem;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.course-summary{min-height:51px;padding-bottom:.75rem;border-bottom:1px solid var(--line)}.travel-date{display:block;margin-bottom:.25rem;color:var(--accent);font-size:.66rem;font-weight:800;letter-spacing:.06em}.stop-names{display:flex;align-items:center;gap:.3rem;min-width:0;overflow:hidden}.stop-names span{max-width:92px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:.72rem;font-weight:700}.stop-names b{color:var(--muted);font-size:.6rem}.stop-names em{flex:0 0 auto;padding:.08rem .32rem;border-radius:6px;background:var(--soft);color:var(--muted);font-size:.62rem;font-style:normal}.story-link{text-decoration:none}.story-link h2{margin:1rem 0 .55rem;font:1.45rem/1.23 var(--display)}.story-link p{min-height:2.7rem;color:var(--muted);font-size:.84rem;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.story-body footer{display:flex;align-items:center;flex-wrap:wrap;gap:.65rem;justify-content:flex-start;margin-top:1.2rem;color:var(--muted);font-size:.68rem}.social{display:flex;align-items:center;gap:.6rem;margin-left:auto}.social b,.comment-count{color:var(--muted);white-space:nowrap}.social b.liked{color:var(--accent)}@media(max-width:420px){.social time{display:none}}
</style>
