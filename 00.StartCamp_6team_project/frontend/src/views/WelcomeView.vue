<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const active = ref(0)
const scenes = ref([])
let observer

const steps = [
  { number: '01', eyebrow: 'A LITTLE QUESTION', title: '어디 갈지 모르시겠다구요?', body: '괜찮아요. 서울은 아는 만큼이 아니라, 발견하는 만큼 내 것이 되니까요.' },
  { number: '02', eyebrow: 'FEEL THE CITY', title: '지금의 서울부터 살펴볼까요?', body: '실시간 혼잡도와 따릉이, 지도 위의 수천 개 장소가 오늘의 선택을 가볍게 해줘요.' },
  { number: '03', eyebrow: 'MAKE IT YOURS', title: '마음이 가는 곳을 하루에 담고', body: '발견한 장소를 캘린더에 더하면 나만의 서울 하루가 한눈에 이어집니다.' },
  { number: '04', eyebrow: 'SHARE THE SOUL', title: '같은 서울을 걷는 사람과 이야기하고', body: '장소마다 다른 경험을 읽고, 편하게 당신의 이야기도 남겨보세요.' },
  { number: '05', eyebrow: 'YOUR SEOUL STARTS HERE', title: '이제, 당신의 서울을 시작해 보세요.', body: '회원이 되면 장소를 저장하고 이야기에 반응하며, 나만의 여정을 자연스럽게 이어갈 수 있어요.' },
]

function finish(target) {
  localStorage.setItem('smsm:onboarding:v1', 'seen')
  router.push(target)
}

function skip() {
  finish({ name: 'contents' })
}

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0]
      if (visible) active.value = Number(visible.target.dataset.step)
    },
    { threshold: [0.35, 0.6, 0.8] },
  )
  scenes.value.forEach((element) => observer.observe(element))
})

onBeforeUnmount(() => observer?.disconnect())
</script>

<template>
  <section class="welcome-page">
    <div class="welcome-top">
      <span class="welcome-brand"><b>SEOUL</b> MySoulMate</span>
      <button class="skip" type="button" @click="skip">먼저 둘러보기 <span>→</span></button>
    </div>

    <aside class="story-rail" aria-label="온보딩 진행률">
      <ol>
        <li v-for="(_, index) in steps" :key="index" :class="{ active: active === index }">
          <i /><span class="sr-only">{{ index + 1 }}번째 이야기</span>
        </li>
      </ol>
    </aside>

    <div class="story-scenes">
      <article
        v-for="(step, index) in steps"
        :key="step.number"
        :ref="(el) => { if (el) scenes[index] = el }"
        class="story-scene"
        :class="{ active: active === index }"
        :data-step="index"
      >
        <span class="scene-number" aria-hidden="true">{{ step.number }}</span>
        <div class="scene-copy">
          <span>{{ step.eyebrow }}</span>
          <h1 v-if="index === 0">{{ step.title }}</h1>
          <h2 v-else>{{ step.title }}</h2>
          <p>{{ step.body }}</p>
          <div v-if="index === steps.length - 1" class="welcome-actions">
            <button type="button" class="join" @click="finish({ name: 'auth', query: { mode: 'signup', redirect: '/' } })">
              <span>무료 회원가입</span><b>나의 서울 시작하기 <i aria-hidden="true">→</i></b>
            </button>
            <button type="button" class="browse" @click="skip">가입 없이 먼저 둘러보기</button>
          </div>
          <small v-else>SCROLL TO DISCOVER <b>↓</b></small>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.welcome-page{position:relative;overflow:clip;background:linear-gradient(180deg,color-mix(in srgb,var(--soft) 45%,var(--bg)),var(--bg) 20%,var(--bg) 80%,color-mix(in srgb,var(--primary) 7%,var(--bg)))}.welcome-top{position:fixed;top:0;left:0;right:0;z-index:12;display:flex;align-items:center;justify-content:space-between;padding:clamp(1.1rem,2.8vw,2rem) clamp(1.2rem,4vw,4rem);pointer-events:none}.welcome-brand{font:1.05rem var(--display);letter-spacing:-.025em;pointer-events:auto}.welcome-brand b{margin-right:.42rem;color:var(--accent);font:700 .55rem var(--sans);letter-spacing:.2em}.skip{padding:.58rem .88rem;border:1px solid var(--line);border-radius:99px;background:var(--overlay);backdrop-filter:blur(12px);color:var(--text);font-size:.7rem;font-weight:800;pointer-events:auto}.skip span{display:inline-block;margin-left:.4rem;transition:transform .2s}.skip:hover span{transform:translateX(3px)}.story-rail{position:fixed;right:clamp(.7rem,2vw,1.8rem);top:50%;z-index:9;transform:translateY(-50%)}.story-rail ol{display:grid;gap:.55rem;margin:0;padding:0;list-style:none}.story-rail li{display:grid;place-items:center;width:18px;height:18px}.story-rail li i{width:5px;height:5px;border-radius:99px;background:var(--line);transition:height .35s,background .35s}.story-rail li.active i{height:18px;background:var(--accent)}.story-scenes{width:100%}.story-scene{position:relative;isolation:isolate;display:grid;min-height:100svh;place-items:center;padding:clamp(7rem,12vh,10rem) clamp(1.5rem,9vw,10rem);text-align:center}.story-scene:after{content:'';position:absolute;left:50%;bottom:0;width:min(680px,70vw);height:1px;transform:translateX(-50%);background:linear-gradient(90deg,transparent,var(--line),transparent)}.story-scene:last-child:after{display:none}.scene-number{position:absolute;z-index:-1;left:50%;top:50%;transform:translate(-50%,-51%);color:color-mix(in srgb,var(--ink) 4%,transparent);font:clamp(12rem,32vw,32rem)/.8 var(--display);letter-spacing:-.09em;user-select:none}.scene-copy{display:flex;width:min(100%,980px);flex-direction:column;align-items:center;opacity:.2;transform:translateY(48px);transition:opacity .7s var(--ease-out),transform .8s var(--ease-out)}.story-scene.active .scene-copy{opacity:1;transform:none}.scene-copy>span{font-size:.63rem;font-weight:800;letter-spacing:.24em;color:var(--accent)}.scene-copy h1,.scene-copy h2{max-width:980px;margin:1rem 0 1.4rem;font:clamp(2.8rem,6.7vw,6.4rem)/1.08 var(--display);letter-spacing:-.052em;text-wrap:balance;word-break:keep-all}.scene-copy p{max-width:650px;color:var(--muted);font-size:clamp(.94rem,1.4vw,1.12rem);line-height:1.85;text-wrap:balance;word-break:keep-all}.scene-copy small{display:inline-flex;align-items:center;gap:.55rem;margin-top:3rem;color:var(--muted);font-size:.58rem;letter-spacing:.14em}.scene-copy small b{animation:bounce 1.4s infinite}.welcome-actions{display:flex;align-items:stretch;justify-content:center;gap:.75rem;margin-top:2.2rem;flex-wrap:wrap}.welcome-actions button{min-height:58px;border-radius:16px;font-weight:800}.join{display:flex;min-width:260px;align-items:center;justify-content:center;gap:.65rem;padding:.9rem 1.2rem;border:1px solid var(--ink);background:var(--ink);color:var(--bg)}.join span{font-size:.61rem;letter-spacing:.1em;opacity:.68}.join b{font-size:.88rem}.join i{display:inline-block;margin-left:.25rem;font-style:normal;transition:transform .2s}.join:hover i{transform:translateX(4px)}.browse{padding:.85rem 1.05rem;border:1px solid var(--line);background:var(--surface);color:var(--muted)}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}@keyframes bounce{50%{transform:translateY(4px)}}@media(max-width:640px){.welcome-top{padding:1rem}.welcome-brand{font-size:.95rem}.skip{font-size:.64rem}.story-rail{right:.3rem}.story-scene{padding:6.5rem 1.4rem 5rem}.scene-copy h1,.scene-copy h2{font-size:clamp(2.35rem,11vw,4rem);line-height:1.13;letter-spacing:-.045em}.scene-copy p{max-width:32rem;font-size:.9rem;line-height:1.8}.scene-copy small{margin-top:2.4rem}.welcome-actions{width:100%;max-width:340px;flex-direction:column}.welcome-actions button{width:100%}.join{min-width:0}}@media(prefers-reduced-motion:reduce){.scene-copy,.story-scene.active .scene-copy{opacity:1;transform:none}.scene-copy small b{animation:none}}
</style>

<style scoped>
.welcome-brand b{font-size:.65rem}.skip{font-size:.8rem}.scene-copy>span{font-size:.72rem}
.scene-copy h1,.scene-copy h2{font-size:clamp(2.7rem,6vw,5.7rem);line-height:1.1;letter-spacing:-.047em}
.scene-copy small{font-size:.68rem}
@media(max-width:640px){.skip{font-size:.74rem}.scene-copy h1,.scene-copy h2{font-size:clamp(2.25rem,10vw,3.75rem);line-height:1.15}}
</style>
