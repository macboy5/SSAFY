<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const mode = ref(route.query.mode === 'signup' ? 'signup' : 'login')
const error = ref('')
const showPassword = ref(false)
const form = reactive({ email: '', nickname: '', password: '', passwordConfirm: '' })

const isSignup = computed(() => mode.value === 'signup')
const heading = computed(() => (isSignup.value ? '서울을 나답게 만날 준비' : '다시, 서울을 이어가세요'))

watch(
  () => route.query.mode,
  (value) => {
    mode.value = value === 'signup' ? 'signup' : 'login'
    error.value = ''
  },
)

function setMode(next) {
  mode.value = next
  error.value = ''
  router.replace({ query: { ...route.query, mode: next } })
}

function safeRedirect() {
  const target = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
  return target.startsWith('/') && !target.startsWith('//') ? target : '/'
}

async function submit() {
  error.value = ''
  if (isSignup.value && form.password !== form.passwordConfirm) {
    error.value = '비밀번호가 서로 일치하지 않습니다.'
    return
  }

  try {
    if (isSignup.value) {
      await auth.signup({
        email: form.email.trim(),
        nickname: form.nickname.trim(),
        password: form.password,
      })
    } else {
      await auth.login({ email: form.email.trim(), password: form.password })
    }
    await router.replace(safeRedirect())
  } catch (err) {
    error.value = err.message
  }
}
</script>

<template>
  <section class="auth-page">
    <div class="auth-story" aria-hidden="true">
      <span class="eyebrow">YOUR SEOUL, YOUR RHYTHM</span>
      <h1>오늘의 서울이 <i>나의 이야기</i>가 되도록.</h1>
      <p>마음에 드는 장소를 저장하고, 여행 일정을 만들고, 같은 서울을 좋아하는 사람들과 이야기를 나눠보세요.</p>
      <div class="feature-stack">
        <span><b>01</b> 장소와 일정, 한 번에</span>
        <span><b>02</b> 진짜 여행자의 로컬 이야기</span>
        <span><b>03</b> 내 취향을 아는 Soul Chat</span>
      </div>
    </div>

    <div class="auth-panel">
      <div class="mode-tabs" role="tablist" aria-label="인증 방식 선택">
        <button :class="{ active: !isSignup }" type="button" role="tab" :aria-selected="!isSignup" @click="setMode('login')">로그인</button>
        <button :class="{ active: isSignup }" type="button" role="tab" :aria-selected="isSignup" @click="setMode('signup')">회원가입</button>
      </div>

      <div class="panel-heading">
        <span>{{ isSignup ? 'JOIN THE JOURNEY' : 'WELCOME BACK' }}</span>
        <h2>{{ heading }}</h2>
        <p>{{ isSignup ? '30초면 충분해요. 나만의 서울 여행을 시작해 보세요.' : '저장한 장소와 플래너가 그대로 기다리고 있어요.' }}</p>
      </div>

      <form @submit.prevent="submit">
        <label v-if="isSignup">
          <span>닉네임</span>
          <input v-model="form.nickname" type="text" maxlength="64" autocomplete="nickname" placeholder="커뮤니티에서 사용할 이름" required>
        </label>
        <label>
          <span>이메일</span>
          <input v-model="form.email" type="email" autocomplete="email" placeholder="seoul@example.com" required>
        </label>
        <label>
          <span>비밀번호</span>
          <div class="password-field">
            <input v-model="form.password" :type="showPassword ? 'text' : 'password'" :autocomplete="isSignup ? 'new-password' : 'current-password'" minlength="8" placeholder="8자 이상 입력해 주세요" required>
            <button type="button" :aria-label="showPassword ? '비밀번호 숨기기' : '비밀번호 보기'" @click="showPassword = !showPassword">{{ showPassword ? '숨김' : '보기' }}</button>
          </div>
        </label>
        <label v-if="isSignup">
          <span>비밀번호 확인</span>
          <input v-model="form.passwordConfirm" :type="showPassword ? 'text' : 'password'" autocomplete="new-password" minlength="8" placeholder="한 번 더 입력해 주세요" required>
        </label>

        <p v-if="error" class="form-error" role="alert">{{ error }}</p>
        <button class="submit-button" type="submit" :disabled="auth.loading">
          <span>{{ auth.loading ? '잠시만요…' : isSignup ? '나의 서울 시작하기' : '로그인하고 이어가기' }}</span>
          <b aria-hidden="true">→</b>
        </button>
      </form>

      <p class="switch-copy">
        {{ isSignup ? '이미 계정이 있으신가요?' : '아직 계정이 없으신가요?' }}
        <button type="button" @click="setMode(isSignup ? 'login' : 'signup')">{{ isSignup ? '로그인' : '회원가입' }}</button>
      </p>
    </div>
  </section>
</template>

<style scoped>
.auth-page{display:grid;grid-template-columns:minmax(0,1fr) minmax(360px,460px);align-items:center;gap:clamp(2.5rem,6vw,6rem);min-height:calc(100svh - 78px);padding:clamp(3.5rem,7vw,6.5rem) clamp(0rem,1vw,1rem)}.auth-story{position:relative;min-width:0;padding:clamp(.5rem,2.5vw,2.5rem)}.auth-story:before{content:'';position:absolute;inset:-12% 8% -12% -12%;z-index:-1;border-radius:48% 52% 40% 60%;background:radial-gradient(circle at 35% 40%,color-mix(in srgb,var(--primary) 24%,transparent),transparent 67%);filter:blur(3px)}.eyebrow,.panel-heading>span{display:block;font-size:.65rem;font-weight:800;letter-spacing:.2em;color:var(--accent)}.auth-story h1{max-width:650px;margin:1rem 0 1.45rem;font:clamp(2.8rem,5.4vw,5.45rem)/1.09 var(--display);letter-spacing:-.05em;text-wrap:balance;word-break:keep-all}.auth-story h1 i{color:var(--primary);font-weight:600}.auth-story>p{max-width:560px;color:var(--muted);font-size:clamp(.92rem,1.2vw,1.04rem);line-height:1.82;word-break:keep-all}.feature-stack{display:grid;gap:.7rem;margin-top:2.25rem}.feature-stack span{display:flex;align-items:baseline;gap:.8rem;font-size:.8rem;line-height:1.6}.feature-stack b{flex:0 0 auto;color:var(--accent);font-size:.6rem;letter-spacing:.1em}.auth-panel{width:100%;padding:clamp(1.35rem,3vw,2.15rem);border:1px solid var(--line);border-radius:28px;background:color-mix(in srgb,var(--surface) 92%,transparent);box-shadow:var(--shadow);backdrop-filter:blur(16px)}.mode-tabs{display:grid;grid-template-columns:1fr 1fr;padding:.3rem;border-radius:99px;background:var(--soft)}.mode-tabs button{padding:.65rem;border:0;border-radius:99px;background:transparent;color:var(--muted);font-weight:700}.mode-tabs button.active{background:var(--surface);color:var(--text);box-shadow:0 5px 18px rgba(20,35,31,.08)}.panel-heading{margin:1.8rem 0}.panel-heading h2{max-width:380px;margin:.55rem 0;font:clamp(1.75rem,3vw,2.45rem)/1.2 var(--display);letter-spacing:-.035em;text-wrap:balance;word-break:keep-all}.panel-heading p{color:var(--muted);font-size:.84rem;line-height:1.72;word-break:keep-all}.auth-panel form{display:grid;gap:1rem}.auth-panel label{display:grid;gap:.42rem}.auth-panel label>span{font-size:.73rem;font-weight:700}.auth-panel input{width:100%;min-height:46px;padding:.8rem .95rem;border:1px solid var(--line);border-radius:12px;background:var(--input);color:var(--text);outline:0}.auth-panel input:focus{border-color:var(--primary);box-shadow:0 0 0 3px color-mix(in srgb,var(--primary) 15%,transparent)}.password-field{position:relative}.password-field input{padding-right:4.2rem}.password-field button{position:absolute;right:.45rem;top:50%;transform:translateY(-50%);padding:.35rem .55rem;border:0;background:transparent;color:var(--primary);font-size:.7rem;font-weight:800}.form-error{padding:.7rem .85rem;border-radius:10px;background:color-mix(in srgb,var(--danger) 10%,transparent);color:var(--danger);font-size:.8rem;line-height:1.65;white-space:pre-line}.submit-button{display:flex;align-items:center;justify-content:space-between;margin-top:.4rem;padding:.9rem 1.1rem;border:1px solid var(--ink);border-radius:13px;background:var(--ink);color:var(--bg);font-weight:800}.submit-button b{font-size:1.25rem;transition:transform .2s}.submit-button:hover b{transform:translateX(4px)}.submit-button:disabled{opacity:.55;cursor:wait}.switch-copy{text-align:center;margin-top:1.2rem;color:var(--muted);font-size:.8rem;line-height:1.65}.switch-copy button{border:0;background:none;color:var(--primary);font-weight:800;text-decoration:underline;text-underline-offset:3px}@media(max-width:900px){.auth-page{grid-template-columns:1fr;gap:2rem;max-width:680px;margin:auto;padding:3.5rem 0}.auth-story{padding:0}.auth-story h1{max-width:620px;font-size:clamp(2.65rem,8vw,4.4rem)}.feature-stack{display:none}.auth-panel{max-width:600px;margin:auto}}@media(max-width:480px){.auth-page{gap:1.8rem;padding:2.5rem 0}.auth-story h1{font-size:clamp(2.35rem,11vw,3.25rem);line-height:1.13}.auth-story>p{font-size:.87rem;line-height:1.75}.auth-panel{padding:1.15rem;border-radius:21px}.panel-heading{margin:1.45rem 0}.panel-heading h2{font-size:1.75rem}}
</style>

<style scoped>
.eyebrow,.panel-heading>span{font-size:.74rem}.auth-story h1{font-size:clamp(2.7rem,4.9vw,4.9rem);line-height:1.11}.auth-panel label>span{font-size:.8rem}.password-field button{font-size:.78rem}
@media(max-width:900px){.auth-story h1{font-size:clamp(2.5rem,7.5vw,4rem)}}
@media(max-width:480px){.auth-story h1{font-size:clamp(2.25rem,10vw,3.1rem)}}
</style>
