<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import StateDisplay from '../components/StateDisplay.vue'
import { useAsyncData } from '../composables/useAsyncData'
import { useAuthStore } from '../stores/auth'

const props = defineProps({ id: { type: String, required: true } })
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { data: post, loading, error, run } = useAsyncData()
const commentBody = ref('')
const actionError = ref('')
const commenting = ref(false)
const liking = ref(false)

const ownsPost = computed(() => Boolean(auth.user && post.value && Number(post.value.author_id) === Number(auth.user.id)))
const isLiked = computed(() => Boolean(post.value?.liked_by_me ?? post.value?.liked))
const isCourse = computed(() => post.value?.post_type === 'course')

function load() { actionError.value = ''; run(() => api.get(`/posts/${props.id}`)) }
watch(() => props.id, load, { immediate: true })

function dateLabel(value, withTime = true) {
  const options = { year: 'numeric', month: 'long', day: 'numeric' }
  if (withTime) Object.assign(options, { hour: '2-digit', minute: '2-digit' })
  const date = typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)
    ? new Date(`${value}T00:00:00`)
    : new Date(value)
  return new Intl.DateTimeFormat('ko-KR', options).format(date)
}

function goToLogin() { router.push({ name: 'auth', query: { mode: 'login', redirect: route.fullPath } }) }

async function toggleLike() {
  if (!auth.isAuthenticated) { goToLogin(); return }
  if (liking.value) return
  liking.value = true
  actionError.value = ''
  const wasLiked = isLiked.value
  try {
    if (wasLiked) await api.delete(`/posts/${props.id}/like`)
    else await api.put(`/posts/${props.id}/like`)
    post.value.liked_by_me = !wasLiked
    post.value.like_count = Math.max(0, Number(post.value.like_count || 0) + (wasLiked ? -1 : 1))
  } catch (err) { actionError.value = err.message } finally { liking.value = false }
}

async function deletePost() {
  if (!ownsPost.value || !confirm('이 기록을 삭제할까요? 삭제한 글은 되돌릴 수 없습니다.')) return
  actionError.value = ''
  try { await api.delete(`/posts/${props.id}`); await router.push({ name: 'community' }) }
  catch (err) { actionError.value = err.message }
}

async function submitComment() {
  if (!auth.isAuthenticated) { goToLogin(); return }
  const body = commentBody.value.trim()
  if (!body || commenting.value) return
  commenting.value = true
  actionError.value = ''
  try {
    await api.post(`/posts/${props.id}/comments`, { body })
    commentBody.value = ''
    await run(() => api.get(`/posts/${props.id}`))
  } catch (err) { actionError.value = err.message } finally { commenting.value = false }
}

async function deleteComment(commentId) {
  if (!confirm('댓글을 삭제할까요?')) return
  actionError.value = ''
  try { await api.delete(`/comments/${commentId}`); await run(() => api.get(`/posts/${props.id}`)) }
  catch (err) { actionError.value = err.message }
}
</script>

<template>
  <section class="post-page">
    <StateDisplay :loading="loading" :error="error">
      <article v-if="post" class="post-article" :class="{ 'course-post': isCourse }">
        <RouterLink class="back-link" to="/community">← 모든 여행 기록</RouterLink>

        <header class="post-header">
          <div>
            <span class="kicker">{{ isCourse ? 'ONE DAY IN SEOUL' : 'PLACE REVIEW' }}</span>
            <h1>{{ post.title }}</h1>
            <div class="meta">
              <b>{{ post.nickname }}</b><span>·</span><span>{{ dateLabel(post.created_at) }}</span>
              <template v-if="isCourse"><span>·</span><strong>{{ dateLabel(post.travel_date, false) }} 여행</strong></template>
            </div>
          </div>
          <div v-if="ownsPost" class="owner-actions">
            <RouterLink class="text-button" :to="{ name: 'post-edit', params: { id: post.id } }">수정</RouterLink>
            <button class="text-button danger" type="button" @click="deletePost">삭제</button>
          </div>
        </header>

        <section v-if="isCourse" class="course-route" aria-labelledby="course-route-title">
          <div class="route-heading">
            <div><span>DAY ROUTE</span><h2 id="course-route-title">이날 걸었던 순서</h2></div>
            <p><b>{{ post.course_items?.length || 0 }}</b>곳을 따라가 보세요</p>
          </div>
          <ol>
            <li v-for="(item, index) in post.course_items" :key="item.content.contentid">
              <RouterLink :to="`/contents/${item.content.contentid}`">
                <span class="route-number">{{ String(index + 1).padStart(2, '0') }}</span>
                <div class="route-image"><img v-if="item.content.firstimage" :src="item.content.firstimage" :alt="item.content.title"><span v-else>SEOUL</span></div>
                <div class="route-copy"><small>{{ item.content.category }}</small><strong>{{ item.content.title }}</strong><p>{{ item.content.addr1 || '서울' }}</p></div>
                <b class="route-arrow" aria-hidden="true">↗</b>
              </RouterLink>
            </li>
          </ol>
        </section>

        <RouterLink v-else-if="post.content" class="linked-content" :to="`/contents/${post.content.contentid}`">
          <div class="place-image"><img v-if="post.content.firstimage" :src="post.content.firstimage" :alt="post.content.title"><span v-else aria-hidden="true">SEOUL</span></div>
          <div class="place-copy"><span>{{ post.content.category || 'PLACE' }}</span><strong>{{ post.content.title }}</strong><small>{{ post.content.addr1 }}</small></div>
          <b class="place-arrow" aria-hidden="true">↗</b>
        </RouterLink>

        <div class="story-intro"><span>{{ isCourse ? 'TRAVEL NOTE' : 'STORY' }}</span><i></i></div>
        <div class="post-body">{{ post.body }}</div>

        <div class="reaction-row">
          <button class="like-button" :class="{ liked: isLiked }" type="button" :disabled="liking" :aria-pressed="isLiked" @click="toggleLike">
            <span aria-hidden="true">{{ isLiked ? '♥' : '♡' }}</span><b>{{ isLiked ? '좋아요를 눌렀어요' : '이 기록이 좋아요' }}</b><em>{{ post.like_count || 0 }}</em>
          </button>
          <span>댓글 {{ post.comments?.length || 0 }}</span>
        </div>
        <p v-if="actionError" class="action-error" role="alert">{{ actionError }}</p>

        <section class="comments">
          <div class="comments-heading"><span>CONVERSATION</span><h2>이야기를 이어가요 <b>{{ post.comments?.length || 0 }}</b></h2></div>
          <ul v-if="post.comments?.length">
            <li v-for="comment in post.comments" :key="comment.id">
              <span class="comment-avatar" aria-hidden="true">{{ comment.nickname?.slice(0, 1) }}</span>
              <div class="comment-content"><div><strong>{{ comment.nickname }}</strong><time>{{ dateLabel(comment.created_at) }}</time></div><p>{{ comment.body }}</p></div>
              <button v-if="auth.user && Number(comment.author_id) === Number(auth.user.id)" class="comment-delete" type="button" @click="deleteComment(comment.id)">삭제</button>
            </li>
          </ul>
          <div v-else class="empty-comments">아직 댓글이 없어요. 첫 번째 이야기를 건네보세요.</div>

          <form v-if="auth.isAuthenticated" class="comment-form" @submit.prevent="submitComment">
            <span class="comment-avatar">{{ auth.user.nickname?.slice(0, 1) }}</span>
            <label><span class="sr-only">댓글</span><textarea v-model="commentBody" maxlength="1000" :placeholder="isCourse ? '이 코스에서 궁금한 점이나 함께 나누고 싶은 이야기를 적어주세요.' : '이 장소에 대한 생각을 나눠주세요.'" required @keydown.ctrl.enter="submitComment"></textarea><small>{{ commentBody.length }}/1000 · Ctrl + Enter로 등록</small></label>
            <button type="submit" :disabled="commenting || !commentBody.trim()">{{ commenting ? '등록 중…' : '댓글 등록' }}</button>
          </form>
          <div v-else class="login-prompt"><div><span>함께 이야기해 볼까요?</span><p>로그인하면 여행자들과 댓글로 이야기를 나눌 수 있어요.</p></div><button type="button" @click="goToLogin">로그인하고 댓글 쓰기 →</button></div>
        </section>
      </article>
    </StateDisplay>
  </section>
</template>

<style scoped>
.post-page{max-width:1040px;margin:0 auto;padding:3rem 0 6rem}.back-link{display:inline-flex;margin-bottom:2.4rem;color:var(--muted);font-size:.78rem;font-weight:800;text-decoration:none;transition:color .2s,transform .2s}.back-link:hover{color:var(--primary);transform:translateX(-3px)}.post-header{display:flex;justify-content:space-between;align-items:flex-start;gap:2rem;padding-bottom:2.2rem;border-bottom:1px solid var(--line)}.kicker,.comments-heading>span,.route-heading span,.story-intro span{font-size:.7rem;letter-spacing:.2em;color:var(--accent);font-weight:800}.post-header h1{max-width:850px;margin:.7rem 0 1rem;font:clamp(2.7rem,5.4vw,5rem)/1.06 var(--display);letter-spacing:-.045em}.meta{display:flex;align-items:center;flex-wrap:wrap;gap:.5rem;color:var(--muted);font-size:.8rem}.meta b{color:var(--text)}.meta strong{color:var(--accent);font-size:.75rem}.owner-actions{display:flex;gap:.4rem;flex:0 0 auto}.text-button{padding:.5rem .75rem;border:1px solid var(--line);border-radius:9px;background:transparent;color:var(--muted);font-size:.72rem;font-weight:700;text-decoration:none}.text-button:hover{color:var(--primary);border-color:var(--primary)}.text-button.danger:hover{color:var(--danger);border-color:var(--danger)}.course-route{margin:2.5rem 0 4rem}.route-heading{display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;margin-bottom:1rem}.route-heading h2{margin-top:.25rem;font:clamp(1.7rem,3vw,2.3rem) var(--display)}.route-heading>p{color:var(--muted);font-size:.76rem}.route-heading>p b{color:var(--accent);font-size:1.25rem}.course-route ol{display:grid;gap:.55rem;margin:0;padding:0;list-style:none}.course-route li{position:relative}.course-route li:not(:last-child):after{content:'';position:absolute;z-index:2;left:28px;top:100%;width:1px;height:.6rem;background:color-mix(in srgb,var(--accent) 55%,var(--line))}.course-route a{display:grid;grid-template-columns:44px 104px minmax(0,1fr) auto;align-items:center;gap:1rem;padding:.65rem;border:1px solid var(--line);border-radius:18px;background:var(--surface);color:var(--text);text-decoration:none;transition:transform .25s,border-color .25s,box-shadow .25s}.course-route a:hover{transform:translateX(6px);border-color:color-mix(in srgb,var(--primary) 45%,var(--line));box-shadow:0 14px 36px color-mix(in srgb,var(--ink) 9%,transparent)}.route-number{display:grid;place-items:center;width:42px;height:42px;border-radius:12px;background:var(--ink);color:var(--bg);font-size:.7rem;font-weight:800}.route-image{display:grid;place-items:center;width:104px;height:76px;overflow:hidden;border-radius:12px;background:var(--soft);color:var(--muted);font-size:.55rem;letter-spacing:.1em}.route-image img{width:100%;height:100%;object-fit:cover;transition:transform .45s}.course-route a:hover img{transform:scale(1.08)}.route-copy{display:flex;flex-direction:column;min-width:0}.route-copy small{color:var(--accent);font-size:.65rem;font-weight:800}.route-copy strong{font:1.32rem var(--display)}.route-copy p{color:var(--muted);font-size:.72rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.route-arrow,.place-arrow{display:grid;place-items:center;width:38px;height:38px;border-radius:11px;background:var(--soft);color:var(--primary);transition:transform .25s}.course-route a:hover .route-arrow,.linked-content:hover .place-arrow{transform:rotate(45deg)}.linked-content{display:grid;grid-template-columns:96px 1fr auto;gap:1rem;align-items:center;margin:2rem 0 3.5rem;padding:.75rem;border:1px solid var(--line);border-radius:20px;background:var(--surface);color:var(--text);text-decoration:none;overflow:hidden;transition:transform .28s,box-shadow .28s,border-color .28s}.linked-content:hover{transform:translateY(-4px);box-shadow:var(--shadow);border-color:color-mix(in srgb,var(--primary) 45%,var(--line))}.place-image{height:82px;border-radius:14px;overflow:hidden;background:var(--soft);display:grid;place-items:center;color:var(--primary);font-size:.6rem;letter-spacing:.15em}.place-image img{width:100%;height:100%;object-fit:cover;transition:transform .45s}.linked-content:hover img{transform:scale(1.07)}.place-copy{display:flex;flex-direction:column;min-width:0}.place-copy>span{font-size:.62rem;color:var(--accent);font-weight:800}.place-copy strong{font:1.35rem var(--display)}.place-copy small{color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.story-intro{display:flex;align-items:center;gap:1rem;margin-top:3.5rem}.story-intro i{flex:1;height:1px;background:var(--line)}.post-body{max-width:780px;min-height:200px;margin:0 auto;padding:2.2rem 0 4rem;white-space:pre-wrap;word-break:break-word;font-size:1.05rem;line-height:2}.reaction-row{display:flex;align-items:center;justify-content:space-between;padding:1.2rem 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);color:var(--muted);font-size:.78rem}.like-button{display:flex;align-items:center;gap:.55rem;padding:.68rem .9rem;border:1px solid var(--line);border-radius:11px;background:var(--surface);color:var(--text);transition:transform .22s,border-color .22s}.like-button>span{color:var(--accent);font-size:1.2rem;line-height:1}.like-button b{font-size:.75rem}.like-button em{min-width:24px;padding:.1rem .35rem;border-radius:7px;background:var(--soft);font-style:normal;font-size:.68rem}.like-button:hover{transform:translateY(-2px);border-color:var(--accent)}.like-button.liked{background:color-mix(in srgb,var(--accent) 10%,var(--surface));border-color:color-mix(in srgb,var(--accent) 55%,var(--line))}.action-error{margin:1rem 0;padding:.75rem 1rem;border-radius:12px;background:color-mix(in srgb,var(--danger) 10%,transparent);color:var(--danger);font-size:.8rem}.comments{padding-top:4rem}.comments-heading{display:flex;align-items:baseline;justify-content:space-between;gap:1rem;border-bottom:1px solid var(--line);margin-bottom:1.25rem}.comments-heading h2{display:flex;align-items:flex-start;gap:.35rem;margin:.3rem 0 1rem;font:clamp(1.3rem,2.6vw,1.75rem)/1.3 var(--display)}.comments-heading h2 b{display:grid;place-items:center;min-width:22px;height:22px;padding:0 .35rem;border-radius:7px;background:var(--soft);color:var(--accent);font:700 .65rem var(--sans)}.comments ul{display:grid;gap:.65rem;margin:0;padding:0;list-style:none}.comments li{display:grid;grid-template-columns:42px 1fr auto;gap:.8rem;padding:1rem;border:1px solid var(--line);border-radius:16px;background:var(--surface)}.comment-avatar{display:grid;place-items:center;width:42px;height:42px;border-radius:12px;background:var(--soft);color:var(--primary);font-weight:800}.comment-content{min-width:0}.comment-content>div{display:flex;align-items:center;gap:.55rem}.comment-content strong{font-size:.8rem}.comment-content time{color:var(--muted);font-size:.65rem}.comment-content p{margin-top:.35rem;white-space:pre-wrap;word-break:break-word;font-size:.88rem}.comment-delete{align-self:start;border:0;background:transparent;color:var(--muted);font-size:.67rem}.comment-delete:hover{color:var(--danger)}.empty-comments{padding:2rem;border:1px dashed var(--line);border-radius:16px;text-align:center;color:var(--muted);font-size:.82rem}.comment-form{display:grid;grid-template-columns:42px 1fr auto;align-items:start;gap:.8rem;margin-top:1.2rem;padding:1rem;border-radius:18px;background:var(--soft)}.comment-form label{display:grid;gap:.25rem}.comment-form textarea{width:100%;min-height:80px;padding:.75rem;border:1px solid var(--line);border-radius:12px;resize:vertical;background:var(--input);color:var(--text)}.comment-form small{color:var(--muted);font-size:.62rem}.comment-form>button{align-self:stretch;padding:0 .9rem;border:0;border-radius:12px;background:var(--primary);color:var(--bg);font-size:.75rem;font-weight:800}.comment-form>button:disabled{opacity:.45}.login-prompt{display:flex;align-items:center;justify-content:space-between;gap:1rem;margin-top:1.2rem;padding:1.2rem;border-radius:18px;background:var(--soft)}.login-prompt span{font-weight:800}.login-prompt p{margin-top:.2rem;color:var(--muted);font-size:.75rem}.login-prompt button{padding:.7rem 1rem;border:1px solid var(--primary);border-radius:11px;background:transparent;color:var(--primary);font-size:.72rem;font-weight:800}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}@media(max-width:680px){.post-page{padding-top:2rem}.post-header{display:block}.owner-actions{margin-top:1rem}.route-heading{align-items:flex-start;flex-direction:column}.course-route a{grid-template-columns:38px 72px minmax(0,1fr)}.route-number{width:36px;height:36px}.route-image{width:72px;height:64px}.route-arrow{display:none}.linked-content{grid-template-columns:72px 1fr}.place-image{height:68px}.place-arrow{display:none}.comments-heading{display:block}.comment-form{grid-template-columns:36px 1fr}.comment-form .comment-avatar{width:36px;height:36px}.comment-form>button{grid-column:2;padding:.65rem}.login-prompt{align-items:flex-start;flex-direction:column}.like-button b{display:none}}@media(max-width:440px){.course-route a{grid-template-columns:34px minmax(0,1fr)}.route-image{display:none}.post-header h1{font-size:2.6rem}}
</style>
