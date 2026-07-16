<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { api } from '../api/client'
import ContentCard from '../components/ContentCard.vue'
import { useAuthStore } from '../stores/auth'
import { usePlannerStore } from '../stores/planner'

const CHAT_STORAGE_KEY = 'seoulmate.chat.v2'

function localDate() {
  const date = new Date()
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset())
  return date.toISOString().slice(0, 10)
}

function initialMessages() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(CHAT_STORAGE_KEY) || 'null')
    if (Array.isArray(saved) && saved.length) return saved
  } catch {
    // 저장된 대화가 손상된 경우 새 대화로 시작합니다.
  }

  return [
    {
      role: 'assistant',
      content:
        '안녕하세요. 가고 싶은 동네와 관심 분야, 여행 시간을 알려주시면 취향에 어울리는 서울을 찾아드릴게요.',
      items: [],
    },
  ]
}

const messages = ref(initialMessages())
const input = ref('')
const sending = ref(false)
const error = ref('')
const messageArea = ref(null)
const composerInput = ref(null)
const planDate = ref(localDate())
const plannerNotice = ref('')
const status = ref({ configured: false, mode: 'search', model: '', verified: false })

const planner = usePlannerStore()
const auth = useAuthStore()

const suggestions = [
  { index: '01', label: '성수 반나절', prompt: '성수에서 반나절 코스' },
  { index: '02', label: '강남 아트 투어', prompt: '강남에서 미술관 3시간' },
  { index: '03', label: '마포 공원 산책', prompt: '마포에서 공원 산책' },
  { index: '04', label: '아이와 하루', prompt: '아이와 하루 동안 갈 곳' },
]

const messageCount = computed(() => Math.max(messages.value.length - 1, 0))
const inputCount = computed(() => input.value.length)

watch(
  messages,
  (value) => sessionStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(value)),
  { deep: true },
)

async function refreshStatus() {
  try {
    status.value = await api.get('/chat/status')
  } catch {
    status.value = { configured: false, mode: 'search', model: '', verified: false }
  }
}

function recentContextIds() {
  return messages.value
    .flatMap((message) => message.items || [])
    .map((item) => item.contentid)
    .filter(Boolean)
    .slice(-8)
}

function resizeComposer() {
  const element = composerInput.value
  if (!element) return
  element.style.height = 'auto'
  element.style.height = `${Math.min(element.scrollHeight, 120)}px`
}

function scrollToLatest() {
  const area = messageArea.value
  if (area) area.scrollTop = area.scrollHeight
}

function onComposerKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault()
    send()
  }
}

async function send(text = input.value) {
  text = text.trim()
  if (!text || sending.value) return

  messages.value.push({ role: 'user', content: text, items: [] })
  input.value = ''
  error.value = ''
  sending.value = true

  await nextTick()
  resizeComposer()
  scrollToLatest()

  try {
    const history = messages.value.slice(-20).map(({ role, content }) => ({ role, content }))
    const response = await api.post('/chat', {
      message: text,
      history,
      context_ids: recentContextIds(),
    })
    status.value = {
      configured: response.mode === 'openai',
      mode: response.mode,
      model: response.model || status.value.model,
      verified: response.verified,
    }
    messages.value.push({
      role: 'assistant',
      content: response.answer,
      items: response.items || [],
      mode: response.mode,
    })
  } catch (requestError) {
    error.value = requestError.message
  } finally {
    sending.value = false
    await nextTick()
    scrollToLatest()
  }
}

async function addToPlanner(content) {
  try {
    await planner.addItem(planDate.value, content)
    plannerNotice.value = `${planDate.value} 일정에 담았습니다.`
    window.setTimeout(() => {
      plannerNotice.value = ''
    }, 2200)
  } catch (requestError) {
    error.value = requestError.message
  }
}

async function clearChat() {
  sessionStorage.removeItem(CHAT_STORAGE_KEY)
  messages.value = initialMessages()
  error.value = ''
  plannerNotice.value = ''
  await nextTick()
  scrollToLatest()
}

onMounted(() => {
  refreshStatus()
  nextTick(resizeComposer)
})
</script>

<template>
  <section class="chat-page">
    <aside class="chat-intro">
      <div class="intro-heading">
        <span class="eyebrow">SEOUL SOUL CHAT</span>
        <h1>당신의 취향과<br /><em>서울</em> 사이.</h1>
        <p>
          가고 싶은 동네와 관심 분야, 여행 시간을 이야기해 주세요. 지금의 기분과 동선에 잘 맞는 서울을 골라드려요.
        </p>
      </div>

      <div class="intent-tags" aria-label="대화에 활용할 정보">
        <span>동네</span>
        <span>취향</span>
        <span>여행 시간</span>
      </div>

      <section class="mode-card" aria-label="Soul Chat 연결 상태">
        <span class="mode-number">LIVE</span>
        <i :class="{ active: status.configured }" aria-hidden="true"></i>
        <div>
          <strong>{{ status.configured ? 'SOUL CURATOR' : 'SEOUL GUIDE' }}</strong>
          <small>
            {{ status.configured ? '대화를 바탕으로 취향을 분석하고 있어요' : '여행 조건에 맞는 서울을 찾고 있어요' }}
          </small>
        </div>
        <button type="button" aria-label="연결 상태 새로고침" @click="refreshStatus">
          <span>상태 확인</span>
          ↻
        </button>
      </section>

      <section class="chat-tools">
        <div class="tool-heading">
          <span>PLAN DATE</span>
          <label for="chat-plan-date">추천 장소를 담을 날짜</label>
        </div>
        <div class="date-choice">
          <input id="chat-plan-date" v-model="planDate" type="date" />
          <small>마음에 드는 장소를 이 날짜에 바로 담아요.</small>
        </div>

        <div class="tool-heading quick-heading">
          <span>QUICK ASK</span>
          <strong>바로 물어보기</strong>
        </div>
        <div class="suggestions">
          <button
            v-for="item in suggestions"
            :key="item.prompt"
            type="button"
            :disabled="!auth.isAuthenticated || sending"
            @click="send(item.prompt)"
          >
            <small>{{ item.index }}</small>
            <span>{{ item.label }}</span>
            <b aria-hidden="true">↗</b>
          </button>
        </div>
        <p v-if="!auth.isAuthenticated" class="quick-note">로그인하면 빠른 질문과 장소 추천을 사용할 수 있어요.</p>
      </section>
    </aside>

    <section class="chat-panel" aria-label="Soul Chat 대화창">
      <header class="chat-header">
        <div class="assistant-avatar" aria-hidden="true">S</div>
        <div class="chat-identity">
          <strong>Seoul Mate</strong>
          <span><i aria-hidden="true"></i> 서울 취향 큐레이터</span>
        </div>
        <div class="session-meta">
          <small>{{ messageCount }}개의 대화</small>
          <button type="button" @click="clearChat">대화 지우기</button>
        </div>
      </header>

      <div
        ref="messageArea"
        class="messages"
        role="log"
        aria-live="polite"
        aria-relevant="additions"
      >
        <div
          v-for="(message, index) in messages"
          :key="`${message.role}-${index}`"
          class="message-row"
          :class="message.role"
        >
          <div v-if="message.role === 'assistant'" class="mini-avatar" aria-hidden="true">S</div>
          <div class="message-stack">
            <span class="message-author">{{ message.role === 'assistant' ? 'SEOUL MATE' : '나' }}</span>
            <div class="bubble">
              <p>{{ message.content }}</p>
              <small v-if="message.role === 'assistant'" class="answer-source">
                <i aria-hidden="true"></i>
                {{ message.mode === 'openai' ? '취향 분석 · 서울 장소 확인' : '서울 여행 정보 기반 추천' }}
              </small>

              <div v-if="message.items?.length" class="recommendation-block">
                <div class="recommendation-heading">
                  <span>RECOMMENDED FOR YOU</span>
                  <small>{{ message.items.length }}곳</small>
                </div>
                <div class="recommend-grid">
                  <ContentCard
                    v-for="content in message.items"
                    :key="content.contentid"
                    :content="content"
                    show-add
                    @add-to-planner="addToPlanner"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="sending" class="message-row assistant typing-row" aria-label="답변을 작성하고 있습니다">
          <div class="mini-avatar" aria-hidden="true">S</div>
          <div class="message-stack">
            <span class="message-author">SEOUL MATE</span>
            <div class="bubble typing" aria-hidden="true">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>

      <div class="notice-stack" aria-live="assertive">
        <p v-if="error" class="notice error">{{ error }}</p>
        <p v-if="plannerNotice" class="notice success">{{ plannerNotice }}</p>
      </div>

      <form v-if="auth.isAuthenticated" class="composer" @submit.prevent="send()">
        <div class="composer-shell">
          <textarea
            ref="composerInput"
            v-model="input"
            rows="1"
            maxlength="400"
            placeholder="가고 싶은 동네, 취향, 시간을 알려주세요"
            aria-label="Soul Chat 메시지"
            @input="resizeComposer"
            @keydown="onComposerKeydown"
          ></textarea>
          <button type="submit" :disabled="sending || !input.trim()" aria-label="메시지 보내기">↑</button>
        </div>
        <div class="composer-meta">
          <span>Enter 전송 · Shift + Enter 줄바꿈</span>
          <span>{{ inputCount }}/400</span>
        </div>
      </form>

      <RouterLink
        v-else
        class="auth-login"
        :to="{ name: 'auth', query: { mode: 'login', redirect: '/chat' } }"
      >
        <span>
          <small>SOUL CHAT START</small>
          로그인하고 취향에 맞는 서울 찾기
        </span>
        <b aria-hidden="true">→</b>
      </RouterLink>
    </section>
  </section>
</template>

<style scoped>
.chat-page {
  display: grid;
  grid-template-columns: minmax(230px, 290px) minmax(0, 1fr);
  gap: clamp(1.5rem, 2.5vw, 2.8rem);
  width: 100%;
  min-height: calc(100vh - 90px);
  margin: 0 auto;
  padding: clamp(1.5rem, 2.8vw, 2.8rem) 0 3.75rem;
}

.chat-intro {
  position: sticky;
  top: 102px;
  align-self: start;
  animation: chat-rail-in 620ms var(--ease-out) both;
}

.intro-heading .eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 0.7rem;
  margin-bottom: 1.2rem;
  color: var(--accent);
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.2em;
}

.intro-heading .eyebrow::before {
  width: 28px;
  height: 1px;
  background: currentColor;
  content: '';
}

.intro-heading h1 {
  max-width: 320px;
  margin: 0;
  color: var(--ink);
  font-family: 'Fraunces', serif;
  font-size: clamp(2.55rem, 3.8vw, 3.85rem);
  font-weight: 500;
  line-height: 0.98;
  letter-spacing: -0.055em;
}

.intro-heading h1 em {
  color: var(--accent);
  font-weight: 500;
}

.intro-heading p {
  max-width: 310px;
  margin: 1.45rem 0 0;
  color: var(--muted);
  font-size: 0.9rem;
  line-height: 1.72;
}

.intent-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin-top: 1.3rem;
}

.intent-tags span {
  padding: 0.38rem 0.72rem;
  border: 1px solid color-mix(in srgb, var(--ink) 13%, transparent);
  border-radius: 7px;
  color: var(--ink-soft);
  font-size: 0.76rem;
  font-weight: 700;
}

.mode-card {
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.8rem;
  margin-top: 2rem;
  padding: 1rem 1.05rem;
  border-top: 1px solid color-mix(in srgb, var(--ink) 16%, transparent);
  border-bottom: 1px solid color-mix(in srgb, var(--ink) 16%, transparent);
  background: color-mix(in srgb, var(--surface) 72%, transparent);
}

.mode-number {
  color: var(--accent);
  font-size: 0.66rem;
  font-weight: 900;
  letter-spacing: 0.14em;
}

.mode-card > i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e2a93c;
  box-shadow: 0 0 0 5px rgb(226 169 60 / 12%);
}

.mode-card > i.active {
  background: #5f9d75;
  box-shadow: 0 0 0 5px rgb(95 157 117 / 13%);
}

.mode-card div {
  display: grid;
  gap: 0.15rem;
}

.mode-card strong {
  color: var(--ink);
  font-size: 0.81rem;
  letter-spacing: 0.05em;
}

.mode-card small {
  overflow: hidden;
  color: var(--muted);
  font-size: 0.72rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mode-card button {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.45rem 0.6rem;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: var(--muted);
  font-size: 0.72rem;
  font-weight: 700;
  cursor: pointer;
  transition: color 180ms ease, background 180ms ease;
}

.mode-card button:hover {
  background: var(--soft);
  color: var(--ink);
}

.chat-tools {
  margin-top: 1.6rem;
}

.tool-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.65rem;
}

.tool-heading > span {
  color: var(--accent);
  font-size: 0.65rem;
  font-weight: 900;
  letter-spacing: 0.14em;
}

.tool-heading label,
.tool-heading strong {
  color: var(--ink);
  font-size: 0.82rem;
  font-weight: 750;
}

.date-choice {
  display: grid;
  grid-template-columns: 1fr;
  align-items: center;
  gap: 0.8rem;
}

.date-choice input {
  width: 100%;
  padding: 0.72rem 0.82rem;
  border: 1px solid color-mix(in srgb, var(--ink) 14%, transparent);
  border-radius: 8px;
  outline: none;
  background: color-mix(in srgb, var(--surface) 72%, transparent);
  color: var(--ink);
  font: inherit;
  font-size: 0.83rem;
}

.date-choice input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 12%, transparent);
}

.date-choice small {
  color: var(--muted);
  font-size: 0.72rem;
  line-height: 1.45;
}

.quick-heading {
  margin-top: 1.35rem;
}

.suggestions {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.45rem;
}

.suggestions button {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 0.6rem;
  min-height: 52px;
  padding: 0.7rem 0.78rem;
  border: 0;
  border-radius: 8px 14px 8px 8px;
  background: color-mix(in srgb, var(--soft) 85%, transparent);
  color: var(--ink);
  text-align: left;
  cursor: pointer;
  transition: transform 180ms ease, background 180ms ease, color 180ms ease;
}

.suggestions button:nth-child(2n) {
  border-radius: 14px 8px 8px 8px;
}

.suggestions button:hover:not(:disabled) {
  transform: translateY(-2px);
  background: var(--accent);
  color: white;
}

.suggestions button:disabled {
  cursor: not-allowed;
  opacity: 0.48;
}

.suggestions small {
  opacity: 0.58;
  font-size: 0.62rem;
  font-weight: 800;
}

.suggestions span {
  font-size: 0.78rem;
  font-weight: 750;
}

.suggestions b {
  font-size: 0.9rem;
  font-weight: 500;
  transition: transform 180ms ease;
}

.suggestions button:hover:not(:disabled) b {
  transform: translate(2px, -2px);
}

.quick-note {
  margin: 0.65rem 0 0;
  color: var(--muted);
  font-size: 0.7rem;
}

.chat-panel {
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: calc(100dvh - 112px);
  min-height: 700px;
  max-height: 940px;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--ink) 13%, transparent);
  border-radius: 30px 30px 12px 30px;
  background: color-mix(in srgb, var(--surface) 91%, transparent);
  box-shadow: 0 34px 90px rgb(44 39 34 / 13%);
  backdrop-filter: blur(18px);
  animation: chat-stage-in 720ms var(--ease-out) 80ms both;
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  min-height: 86px;
  padding: 1rem clamp(1.25rem, 2.2vw, 1.8rem);
  border-bottom: 1px solid color-mix(in srgb, var(--ink) 10%, transparent);
  background: color-mix(in srgb, var(--surface) 84%, transparent);
}

.assistant-avatar,
.mini-avatar {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  background: var(--ink);
  color: white;
  font-family: 'Fraunces', serif;
  font-weight: 700;
}

.assistant-avatar {
  width: 48px;
  height: 48px;
  border-radius: 14px 14px 5px 14px;
  box-shadow: 5px 5px 0 color-mix(in srgb, var(--accent) 45%, transparent);
}

.chat-identity {
  display: grid;
  gap: 0.2rem;
}

.chat-identity strong {
  color: var(--ink);
  font-family: 'Fraunces', serif;
  font-size: 1.24rem;
}

.chat-identity span {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--muted);
  font-size: 0.75rem;
}

.chat-identity span i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #5f9d75;
  box-shadow: 0 0 0 3px rgb(95 157 117 / 12%);
}

.session-meta {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-left: auto;
}

.session-meta small {
  color: var(--muted);
  font-size: 0.7rem;
}

.session-meta button {
  padding: 0.5rem 0.7rem;
  border: 1px solid color-mix(in srgb, var(--ink) 12%, transparent);
  border-radius: 7px;
  background: transparent;
  color: var(--muted);
  font-size: 0.7rem;
  font-weight: 700;
  cursor: pointer;
  transition: border-color 180ms ease, color 180ms ease;
}

.session-meta button:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.messages {
  position: relative;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 1.8rem clamp(1.15rem, 2.8vw, 2.35rem) 2.5rem;
  scroll-behavior: smooth;
  scrollbar-color: color-mix(in srgb, var(--accent) 36%, transparent) transparent;
  scrollbar-width: thin;
}

.messages::before {
  position: absolute;
  inset: 0;
  z-index: -1;
  background:
    radial-gradient(circle at 12% 8%, color-mix(in srgb, var(--accent) 7%, transparent), transparent 28%),
    linear-gradient(120deg, transparent 0 49.7%, color-mix(in srgb, var(--ink) 3%, transparent) 50%, transparent 50.3%);
  background-size: auto, 42px 42px;
  content: '';
  pointer-events: none;
}

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
  margin-bottom: 1.55rem;
}

.message-row.user {
  justify-content: flex-end;
}

.mini-avatar {
  width: 30px;
  height: 30px;
  margin-top: 1.3rem;
  border-radius: 10px 10px 3px 10px;
  font-size: 0.76rem;
}

.message-stack {
  display: grid;
  max-width: min(91%, 920px);
}

.user .message-stack {
  justify-items: end;
  max-width: min(78%, 720px);
}

.message-author {
  margin: 0 0 0.35rem 0.2rem;
  color: var(--muted);
  font-size: 0.62rem;
  font-weight: 850;
  letter-spacing: 0.12em;
}

.user .message-author {
  margin-right: 0.2rem;
}

.bubble {
  min-width: 0;
  padding: 1.12rem 1.25rem;
  border: 1px solid color-mix(in srgb, var(--ink) 8%, transparent);
  border-radius: 6px 18px 18px 18px;
  background: color-mix(in srgb, var(--soft) 72%, var(--surface));
  color: var(--ink);
  box-shadow: 0 8px 25px rgb(44 39 34 / 4%);
}

.user .bubble {
  border-color: transparent;
  border-radius: 18px 6px 18px 18px;
  background: var(--ink);
  color: white;
  box-shadow: 0 10px 25px rgb(44 39 34 / 12%);
}

.bubble > p {
  margin: 0;
  font-size: 0.98rem;
  line-height: 1.78;
  white-space: pre-wrap;
}

.answer-source {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.7rem;
  color: var(--muted);
  font-size: 0.71rem;
}

.answer-source i {
  width: 13px;
  height: 1px;
  background: var(--accent);
}

.recommendation-block {
  width: min(820px, 100%);
  margin-top: 1.1rem;
  padding-top: 0.85rem;
  border-top: 1px solid color-mix(in srgb, var(--ink) 9%, transparent);
}

.recommendation-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.65rem;
}

.recommendation-heading span {
  color: var(--accent);
  font-size: 0.64rem;
  font-weight: 900;
  letter-spacing: 0.14em;
}

.recommendation-heading small {
  color: var(--muted);
  font-size: 0.66rem;
}

.recommend-grid {
  display: grid;
  grid-auto-columns: minmax(230px, 32%);
  grid-auto-flow: column;
  gap: 0.7rem;
  overflow-x: auto;
  padding: 0.1rem 0 0.65rem;
  scroll-snap-type: x proximity;
  scrollbar-color: color-mix(in srgb, var(--accent) 30%, transparent) transparent;
  scrollbar-width: thin;
}

.recommend-grid :deep(.card) {
  height: 100%;
  scroll-snap-align: start;
}

.typing-row {
  margin-bottom: 0;
}

.typing {
  display: flex;
  align-items: center;
  gap: 0.32rem;
  width: max-content;
  min-height: 42px;
  padding: 0 1rem;
}

.typing span {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--muted);
  animation: typing-bounce 1.1s infinite ease-in-out;
}

.typing span:nth-child(2) {
  animation-delay: 120ms;
}

.typing span:nth-child(3) {
  animation-delay: 240ms;
}

.notice-stack {
  display: grid;
  gap: 0.35rem;
  padding: 0 1.2rem;
}

.notice {
  margin: 0.5rem 0 0;
  padding: 0.7rem 0.85rem;
  border-left: 3px solid currentColor;
  border-radius: 4px 9px 9px 4px;
  font-size: 0.75rem;
}

.notice.error {
  background: #fff0ed;
  color: #b94838;
}

.notice.success {
  background: #edf7f0;
  color: #39744f;
}

.composer {
  padding: 1rem clamp(1.1rem, 2.2vw, 1.7rem) 1.15rem;
  border-top: 1px solid color-mix(in srgb, var(--ink) 9%, transparent);
  background: color-mix(in srgb, var(--surface) 93%, transparent);
}

.composer-shell {
  display: flex;
  align-items: flex-end;
  gap: 0.65rem;
  padding: 0.5rem 0.55rem 0.5rem 0.95rem;
  border: 1px solid color-mix(in srgb, var(--ink) 16%, transparent);
  border-radius: 14px 22px 14px 14px;
  background: var(--surface);
  transition: border-color 180ms ease, box-shadow 180ms ease;
}

.composer-shell:focus-within {
  border-color: color-mix(in srgb, var(--accent) 68%, transparent);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent) 9%, transparent);
}

.composer textarea {
  flex: 1;
  min-height: 35px;
  max-height: 120px;
  padding: 0.48rem 0;
  overflow-y: auto;
  resize: none;
  border: 0;
  outline: none;
  background: transparent;
  color: var(--ink);
  font: inherit;
  font-size: 0.96rem;
  line-height: 1.5;
}

.composer textarea::placeholder {
  color: color-mix(in srgb, var(--muted) 76%, transparent);
}

.composer button {
  display: grid;
  flex: 0 0 auto;
  width: 46px;
  height: 46px;
  place-items: center;
  border: 0;
  border-radius: 13px 18px 8px 13px;
  background: var(--accent);
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  transition: transform 180ms ease, background 180ms ease, opacity 180ms ease;
}

.composer button:hover:not(:disabled) {
  transform: translateY(-2px);
  background: var(--ink);
}

.composer button:disabled {
  cursor: not-allowed;
  opacity: 0.38;
}

.composer-meta {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.45rem 0.2rem 0;
  color: var(--muted);
  font-size: 0.63rem;
}

.auth-login {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin: 0.85rem 1.2rem 1.2rem;
  padding: 0.9rem 1rem;
  border-radius: 12px 20px 12px 12px;
  background: var(--ink);
  color: white;
  text-decoration: none;
  transition: transform 180ms ease, box-shadow 180ms ease;
}

.auth-login:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgb(44 39 34 / 16%);
}

.auth-login span {
  display: grid;
  gap: 0.2rem;
  font-size: 0.83rem;
  font-weight: 750;
}

.auth-login small {
  color: color-mix(in srgb, var(--accent) 78%, white);
  font-size: 0.58rem;
  letter-spacing: 0.14em;
}

.auth-login b {
  color: var(--accent);
  font-size: 1.3rem;
}

@keyframes typing-bounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.45; }
  30% { transform: translateY(-4px); opacity: 1; }
}

@keyframes chat-rail-in {
  from { opacity: 0; transform: translate3d(-18px, 0, 0); }
  to { opacity: 1; transform: translate3d(0, 0, 0); }
}

@keyframes chat-stage-in {
  from { opacity: 0; transform: translate3d(0, 20px, 0) scale(0.985); }
  to { opacity: 1; transform: translate3d(0, 0, 0) scale(1); }
}

@media (max-width: 1050px) {
  .chat-page {
    grid-template-columns: 1fr;
  }

  .chat-intro {
    position: static;
  }

  .intro-heading p {
    max-width: 680px;
  }

  .intro-heading h1 {
    max-width: 620px;
  }

  .chat-tools {
    display: grid;
    grid-template-columns: minmax(240px, 0.7fr) minmax(0, 1.3fr);
    column-gap: 1.5rem;
  }

  .chat-tools .tool-heading:first-child,
  .chat-tools .date-choice {
    grid-column: 1;
  }

  .quick-heading,
  .suggestions,
  .quick-note {
    grid-column: 2;
  }

  .quick-heading {
    grid-row: 1;
    margin-top: 0;
  }

  .suggestions {
    grid-row: 2 / span 2;
  }

  .chat-panel {
    height: min(840px, calc(100dvh - 1.5rem));
  }
}

@media (max-width: 640px) {
  .chat-page {
    gap: 2rem;
    padding-inline: 0;
  }

  .intro-heading h1 {
    font-size: clamp(2.6rem, 14vw, 3.5rem);
  }

  .mode-card {
    grid-template-columns: auto auto minmax(0, 1fr) auto;
    padding-inline: 0.75rem;
  }

  .mode-card button span,
  .mode-card small {
    display: none;
  }

  .chat-tools {
    display: block;
  }

  .quick-heading {
    margin-top: 1.35rem;
  }

  .date-choice {
    grid-template-columns: 1fr;
  }

  .suggestions {
    grid-template-columns: 1fr;
  }

  .chat-panel {
    min-height: 620px;
    border-radius: 22px 22px 8px 22px;
  }

  .chat-header {
    min-height: 68px;
    padding-inline: 0.9rem;
  }

  .assistant-avatar {
    width: 38px;
    height: 38px;
  }

  .session-meta small {
    display: none;
  }

  .session-meta button {
    padding-inline: 0.5rem;
  }

  .messages {
    padding-inline: 0.85rem;
  }

  .message-stack,
  .user .message-stack {
    max-width: calc(100% - 38px);
  }

  .bubble {
    padding: 0.85rem 0.9rem;
  }

  .recommendation-block {
    width: 100%;
  }

  .recommend-grid {
    grid-auto-columns: 86%;
  }

  .composer {
    padding-inline: 0.85rem;
  }

  .composer-meta span:first-child {
    display: none;
  }

  .composer-meta {
    justify-content: flex-end;
  }
}

@media (prefers-reduced-motion: reduce) {
  .chat-intro,
  .chat-panel {
    animation: none;
  }

  .typing span {
    animation: none;
  }

  .messages {
    scroll-behavior: auto;
  }
}
</style>
