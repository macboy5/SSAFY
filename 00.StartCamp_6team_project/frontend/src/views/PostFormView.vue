<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import PlacePicker from '../components/PlacePicker.vue'
import { useAuthStore } from '../stores/auth'
import { usePlannerStore } from '../stores/planner'

function today() {
  const now = new Date()
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
  return now.toISOString().slice(0, 10)
}

function latestRecordableDate() {
  const date = new Date()
  date.setDate(date.getDate() - 1)
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset())
  return date.toISOString().slice(0, 10)
}

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const planner = usePlannerStore()
const isEdit = computed(() => route.name === 'post-edit')
const postId = route.params.id
const postType = ref(route.query.type === 'review' || route.query.content_id ? 'review' : 'course')
const isCourse = computed(() => postType.value === 'course')
const fromPlanner = computed(() => !isEdit.value && route.query.from === 'planner')
const title = ref('')
const body = ref('')
const recordableUntil = latestRecordableDate()
const requestedTravelDate = /^\d{4}-\d{2}-\d{2}$/.test(route.query.date || '') ? route.query.date : ''
const travelDate = ref(requestedTravelDate && requestedTravelDate <= recordableUntil ? requestedTravelDate : recordableUntil)
const selectedPlace = ref(null)
const coursePlaces = ref([])
const error = ref('')
const submitting = ref(false)
const loading = ref(true)
const forbidden = ref(false)
const plannedPlaces = computed(() => planner.byDate(travelDate.value)
  .slice()
  .sort((a, b) => {
    const timeOrder = (a.visit_time || '99:99').localeCompare(b.visit_time || '99:99')
    return timeOrder || a.sort_order - b.sort_order
  })
  .map((item) => item.content))

onMounted(async () => {
  try {
    if (isEdit.value) {
      const post = await api.get(`/posts/${postId}`)
      if (post.author_id && Number(post.author_id) !== Number(auth.user?.id)) {
        forbidden.value = true
        error.value = '작성자만 이 이야기를 수정할 수 있습니다.'
        return
      }
      postType.value = post.post_type || 'review'
      title.value = post.title
      body.value = post.body
      selectedPlace.value = post.content
      travelDate.value = post.travel_date || today()
      coursePlaces.value = (post.course_items || []).map((item) => item.content)
    } else if (route.query.content_id) {
      const response = await api.get(`/contents/${route.query.content_id}`)
      selectedPlace.value = response.content
    }
  } catch (err) {
    error.value = err.message
  } finally {
    if (!fromPlanner.value) loading.value = false
  }
  if (!planner.ready && !planner.loading) {
    try { await planner.load() } catch { /* 직접 장소를 고르는 흐름은 계속 사용할 수 있습니다. */ }
  }
  if (fromPlanner.value) {
    if (plannedPlaces.value.length >= 2) importPlannerCourse()
    else error.value = '선택한 날짜의 Planner 코스를 찾을 수 없습니다. Planner에서 일정을 다시 확인해 주세요.'
    loading.value = false
  }
})

function selectType(type) {
  if (!isEdit.value) postType.value = type
}

function importPlannerCourse() {
  if (plannedPlaces.value.length < 2) {
    error.value = '선택한 날짜의 Planner에 장소를 두 곳 이상 담아 주세요.'
    return
  }
  coursePlaces.value = plannedPlaces.value.slice(0, 10)
  error.value = ''
}

async function submit() {
  error.value = ''
  if (forbidden.value) return
  if (!title.value.trim() || !body.value.trim()) {
    error.value = '제목과 여행 이야기를 모두 작성해 주세요.'
    return
  }
  if (isCourse.value && coursePlaces.value.length < 2) {
    error.value = '여행 코스에는 장소를 두 곳 이상 담아 주세요.'
    return
  }
  if (isCourse.value && !travelDate.value) {
    error.value = '여행한 날짜를 선택해 주세요.'
    return
  }
  if (isCourse.value && travelDate.value > recordableUntil) {
    error.value = '여행을 마친 다음 날부터 하루 코스를 기록할 수 있어요.'
    return
  }
  if (!isCourse.value && !selectedPlace.value) {
    error.value = '후기를 남길 장소를 먼저 선택해 주세요.'
    return
  }

  submitting.value = true
  const base = { title: title.value.trim(), body: body.value.trim() }
  try {
    if (isEdit.value) {
      await api.put(`/posts/${postId}`, {
        ...base,
        ...(isCourse.value
          ? {
              travel_date: travelDate.value,
              course_content_ids: coursePlaces.value.map((place) => place.contentid),
            }
          : {}),
      })
      await router.push({ name: 'post-detail', params: { id: postId } })
    } else {
      const post = await api.post('/posts', {
        ...base,
        post_type: postType.value,
        content_id: isCourse.value ? undefined : selectedPlace.value.contentid,
        travel_date: isCourse.value ? travelDate.value : undefined,
        course_content_ids: isCourse.value
          ? coursePlaces.value.map((place) => place.contentid)
          : [],
      })
      await router.push({ name: 'post-detail', params: { id: post.id } })
    }
  } catch (err) {
    error.value = err.message
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="form-page">
    <header>
      <span>{{ isCourse ? 'TRAVEL JOURNAL' : 'PLACE REVIEW' }}</span>
      <h1>{{ isEdit ? '서울의 하루를 다시 다듬어요.' : isCourse ? '걸었던 순서대로, 서울의 하루를 기록해요.' : '한 장소의 인상을 나눠 주세요.' }}</h1>
      <p>{{ isCourse ? '여러 장소를 방문한 순서대로 담고, 그날의 분위기와 이동 팁을 블로그처럼 길게 남길 수 있어요.' : '분위기와 방문 팁처럼 다음 여행자에게 도움이 될 경험을 들려주세요.' }}</p>
      <div v-if="auth.user" class="author-chip"><span>{{ auth.user.nickname?.slice(0, 1) }}</span><p><small>WRITING AS</small><b>{{ auth.user.nickname }}</b></p></div>
    </header>

    <div v-if="loading" class="loading-card">기록할 공간을 준비하고 있어요…</div>
    <form v-else @submit.prevent="submit">
      <fieldset class="type-selector" :disabled="isEdit || fromPlanner">
        <legend>기록 종류</legend>
        <button type="button" :class="{ active: isCourse }" @click="selectType('course')">
          <span>01</span><b>하루 코스</b><small>여러 장소와 동선을 기록해요</small>
        </button>
        <button type="button" :class="{ active: !isCourse }" @click="selectType('review')">
          <span>02</span><b>장소 후기</b><small>한 장소의 경험을 남겨요</small>
        </button>
      </fieldset>

      <div v-if="isCourse" class="course-builder">
        <div class="form-field date-field">
          <label for="travel-date">여행한 날짜 <b>필수</b></label>
          <input id="travel-date" v-model="travelDate" type="date" :max="recordableUntil" :disabled="fromPlanner" required>
          <small>{{ fromPlanner ? 'Selected Date의 여행 날짜를 그대로 사용해요.' : '여행을 마친 날짜의 동선을 기록할 수 있어요.' }}</small>
        </div>
        <div v-if="plannedPlaces.length" class="planner-import">
          <div><span>{{ fromPlanner ? 'SELECTED DATE · CONNECTED' : 'MY PLANNER' }}</span><b>{{ fromPlanner ? `Planner에 표시된 ${plannedPlaces.length}곳을 순서대로 불러왔어요.` : `이 날짜에 ${plannedPlaces.length}곳이 담겨 있어요.` }}</b></div>
          <span v-if="fromPlanner" class="planner-locked">일정 연결됨</span>
          <button v-else type="button" :disabled="plannedPlaces.length < 2" @click="importPlannerCourse">코스 불러오기 →</button>
        </div>
        <div class="form-field place-field">
          <div class="field-heading"><label>{{ fromPlanner ? 'Selected Date의 장소 코스' : '코스에 담을 장소' }} <b>2곳 이상</b></label><small>{{ fromPlanner ? 'Planner에 보이던 장소와 순서를 그대로 사용해요.' : '화살표로 방문 순서를 바꿀 수 있어요.' }}</small></div>
          <PlacePicker
            v-model="coursePlaces"
            multiple
            :max="10"
            :disabled="fromPlanner"
            placeholder="코스에 추가할 장소를 검색하세요"
            helper="첫 장소부터 방문한 순서대로 추가해 보세요."
          />
        </div>
      </div>

      <div v-else class="form-field place-field">
        <label>후기를 남길 장소 <b>필수</b></label>
        <PlacePicker v-model="selectedPlace" :disabled="isEdit" />
        <small v-if="isEdit">기존 후기의 장소는 그대로 유지됩니다.</small>
      </div>

      <div class="form-field">
        <label for="post-title">제목</label>
        <input id="post-title" v-model="title" required maxlength="255" :placeholder="isCourse ? '예: 성수에서 서울숲까지, 천천히 걸은 여름 하루' : '이 장소에서 무엇을 발견했나요?'">
        <small>{{ title.length }}/255</small>
      </div>
      <div class="form-field story-field">
        <div class="field-heading"><label for="post-body">여행 이야기</label><small>분위기 · 동선 · 머문 시간 · 나만의 팁</small></div>
        <textarea id="post-body" v-model="body" required maxlength="12000" :placeholder="isCourse ? '어디서 하루를 시작했는지, 장소 사이를 어떻게 이동했는지, 기억에 남은 순간은 무엇인지 자유롭게 적어주세요.\n\n문단을 나눠 쓰면 더 편하게 읽을 수 있어요.' : '분위기, 방문 팁, 기억에 남은 순간을 자유롭게 적어주세요.'"></textarea>
        <small>{{ body.length }}/12000</small>
      </div>
      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
      <div class="form-actions">
        <button class="cancel-button" type="button" @click="router.back()">취소</button>
        <button class="submit-button" type="submit" :disabled="submitting || forbidden">
          <span>{{ submitting ? '기록 저장 중…' : isEdit ? '수정 완료' : isCourse ? '코스 기록 발행' : '장소 후기 등록' }}</span><b aria-hidden="true">→</b>
        </button>
      </div>
    </form>
  </section>
</template>

<style scoped>
.form-page{display:grid;grid-template-columns:minmax(280px,.7fr) minmax(0,1.15fr);gap:clamp(2.5rem,7vw,7rem);max-width:1180px;margin:clamp(3rem,7vw,6rem) auto}.form-page>header{align-self:start;position:sticky;top:120px}.form-page header>span{font-size:.72rem;letter-spacing:.2em;color:var(--accent);font-weight:800}.form-page h1{margin:.85rem 0 1.1rem;font:clamp(2.45rem,4.7vw,4.35rem)/1.08 var(--display);letter-spacing:-.045em}.form-page header>p{max-width:480px;color:var(--muted)}.author-chip{display:inline-flex;align-items:center;gap:.65rem;margin-top:2rem;padding:.45rem .7rem .45rem .45rem;border:1px solid var(--line);border-radius:99px;background:var(--surface)}.author-chip>span{display:grid;place-items:center;width:34px;height:34px;border-radius:50%;background:var(--primary);color:var(--bg);font-weight:800}.author-chip p{display:flex;flex-direction:column;padding-right:.3rem}.author-chip small{font-size:.52rem;letter-spacing:.12em;color:var(--muted)}.author-chip b{font-size:.75rem}.form-page form,.loading-card{padding:clamp(1.2rem,3vw,2.2rem);border:1px solid var(--line);border-radius:28px;background:var(--surface);box-shadow:var(--shadow)}.loading-card{color:var(--muted)}.type-selector{display:grid;grid-template-columns:1fr 1fr;gap:.6rem;margin:0 0 2rem;padding:0 0 1.5rem;border:0;border-bottom:1px solid var(--line)}.type-selector legend{margin-bottom:.55rem;font-size:.78rem;font-weight:800}.type-selector button{display:grid;grid-template-columns:auto 1fr;column-gap:.6rem;align-items:center;padding:.8rem;border:1px solid var(--line);border-radius:16px;background:var(--soft);color:var(--text);text-align:left;transition:transform .2s,border-color .2s,background .2s}.type-selector button>span{grid-row:1/3;display:grid;place-items:center;width:34px;height:34px;border-radius:10px;background:var(--surface);color:var(--muted);font-size:.65rem;font-weight:800}.type-selector button b{font-size:.83rem}.type-selector button small{color:var(--muted);font-size:.65rem}.type-selector button.active{border-color:color-mix(in srgb,var(--primary) 58%,var(--line));background:color-mix(in srgb,var(--primary) 8%,var(--surface))}.type-selector button.active>span{background:var(--primary);color:var(--bg)}.type-selector:not(:disabled) button:hover{transform:translateY(-2px)}.type-selector:disabled button{cursor:default}.course-builder{margin-bottom:1.6rem;padding:1.1rem;border-radius:20px;background:color-mix(in srgb,var(--soft) 74%,transparent)}.form-field{position:relative;margin-bottom:1.45rem}.form-field label,.field-heading label{font-size:.8rem;font-weight:800}.form-field label b{font-size:.62rem;color:var(--accent);margin-left:.3rem}.form-field input,.form-field textarea{border-radius:14px;padding:.88rem 1rem;outline:0}.form-field input:focus,.form-field textarea:focus{border-color:var(--primary);box-shadow:0 0 0 3px color-mix(in srgb,var(--primary) 13%,transparent)}.form-field input:disabled{opacity:.72;cursor:not-allowed}.form-field textarea{min-height:360px;line-height:1.85}.form-field>small{align-self:flex-end;color:var(--muted);font-size:.65rem}.date-field{max-width:330px}.planner-import{display:flex;align-items:center;justify-content:space-between;gap:1rem;margin:-.35rem 0 1.35rem;padding:.75rem .85rem;border:1px solid color-mix(in srgb,var(--accent) 26%,var(--line));border-radius:14px;background:var(--surface)}.planner-import div{display:flex;flex-direction:column}.planner-import span{color:var(--accent);font-size:.58rem;font-weight:800;letter-spacing:.13em}.planner-import b{font-size:.75rem}.planner-import button{padding:.52rem .7rem;border:1px solid var(--primary);border-radius:9px;background:transparent;color:var(--primary);font-size:.69rem;font-weight:800}.planner-import button:disabled{opacity:.4}.planner-import .planner-locked{padding:.4rem .55rem;border-radius:8px;background:color-mix(in srgb,var(--accent) 10%,var(--soft));white-space:nowrap}.field-heading{display:flex;align-items:baseline;justify-content:space-between;gap:1rem}.field-heading small{color:var(--muted);font-size:.65rem}.place-field{padding-bottom:1.25rem;border-bottom:1px solid var(--line)}.course-builder .place-field{margin-bottom:0;padding-bottom:0;border-bottom:0}.story-field{margin-top:.3rem}.form-error{margin:1rem 0;padding:.8rem 1rem;border-radius:12px;background:color-mix(in srgb,var(--danger) 10%,transparent);color:var(--danger);font-size:.8rem}.form-actions{display:flex;justify-content:flex-end;gap:.6rem;margin-top:1.5rem}.cancel-button,.submit-button{min-height:45px;padding:.78rem 1.15rem;border-radius:12px;font-size:.8rem;font-weight:800}.cancel-button{border:1px solid var(--line);background:transparent;color:var(--muted)}.submit-button{display:flex;align-items:center;gap:1.8rem;border:1px solid var(--primary);background:var(--primary);color:var(--bg)}.submit-button b{font-size:1.1rem;transition:transform .2s}.submit-button:hover b{transform:translateX(3px)}.submit-button:disabled{opacity:.45;cursor:not-allowed}@media(max-width:820px){.form-page{grid-template-columns:1fr;margin:2.5rem auto}.form-page>header{position:static}.author-chip{margin-top:1rem}}@media(max-width:560px){.type-selector{grid-template-columns:1fr}.form-page h1{font-size:clamp(2.3rem,10vw,3.5rem)}.field-heading{align-items:flex-start;flex-direction:column;gap:.2rem}.course-builder{padding:.75rem}.planner-import{align-items:flex-start;flex-direction:column}.form-field textarea{min-height:290px}.form-actions{display:grid;grid-template-columns:1fr 1fr}.submit-button{justify-content:space-between}}
</style>
