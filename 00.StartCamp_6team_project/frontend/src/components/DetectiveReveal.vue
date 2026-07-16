<script setup>
defineProps({ visible: { type: Boolean, default: false } })
defineEmits(['close'])
</script>

<template>
  <Teleport to="body">
    <Transition name="detective-reveal">
      <div v-if="visible" class="detective-overlay" role="status" aria-live="assertive" @click.self="$emit('close')">
        <div class="case-rays" aria-hidden="true"></div>
        <div class="case-flash" aria-hidden="true"></div>
        <section class="detective-stage" aria-label="명탐정 코난 등장">
          <div class="detective-figure">
            <span class="figure-shadow" aria-hidden="true"></span>
            <div class="evidence-photo">
              <img src="/images/conana.webp" alt="손가락으로 앞을 가리키는 명탐정 코난" />
              <span class="case-number" aria-hidden="true">CASE FILE · 003 SEC</span>
            </div>
          </div>

          <div class="detective-copy">
            <span>3초간의 관찰 끝에</span>
            <h2>명탐정 코난<br><i>등장.</i></h2>
            <p>진실은 언제나 하나.</p>
          </div>
        </section>
        <button class="detective-close" type="button" aria-label="코난 등장 화면 닫기" @click="$emit('close')">×</button>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.detective-overlay{position:fixed;inset:0;z-index:110;display:grid;place-items:center;overflow:hidden;padding:clamp(1rem,4vw,3rem);background:rgba(5,12,20,.9);color:#fff;backdrop-filter:blur(8px)}
.case-rays{position:absolute;width:145vmax;height:145vmax;background:repeating-conic-gradient(from 10deg,rgba(255,255,255,.08) 0 3deg,transparent 3deg 10deg);animation:case-rays 18s linear infinite}
.case-flash{position:absolute;inset:0;background:radial-gradient(circle at 35% 48%,rgba(255,255,255,.82),rgba(106,167,212,.18) 18%,transparent 44%);animation:case-flash 1.1s ease-out both}
.detective-stage{position:relative;z-index:1;display:grid;width:min(920px,100%);grid-template-columns:minmax(270px,.85fr) minmax(280px,1.15fr);align-items:center;gap:clamp(1rem,5vw,5rem)}
.detective-figure{position:relative;filter:drop-shadow(0 30px 46px rgba(0,0,0,.42));animation:detective-arrive .9s cubic-bezier(.16,1.1,.3,1) both}
.figure-shadow{position:absolute;left:11%;right:11%;bottom:0;height:14%;border-radius:50%;background:rgba(0,0,0,.42);filter:blur(18px)}
.evidence-photo{position:relative;width:min(390px,100%);margin:auto;padding:.7rem .7rem 2.25rem;overflow:hidden;border-radius:16px 16px 6px 16px;background:#f7f2e8;box-shadow:inset 0 0 0 1px rgba(27,38,48,.14),0 28px 70px rgba(0,0,0,.38);transform:rotate(-2.5deg)}
.evidence-photo:before{content:'';position:absolute;left:50%;top:-.55rem;z-index:2;width:5.5rem;height:1.4rem;background:rgba(218,190,118,.74);box-shadow:0 2px 5px rgba(0,0,0,.12);transform:translateX(-50%) rotate(1deg)}
.evidence-photo:after{content:'';position:absolute;inset:-45% -80%;background:linear-gradient(105deg,transparent 42%,rgba(255,255,255,.66) 49%,transparent 56%);transform:translateX(-55%) rotate(8deg);animation:photo-glint 2.4s .7s ease-out both;pointer-events:none}
.evidence-photo img{display:block;width:100%;aspect-ratio:1;object-fit:cover;border-radius:8px}
.case-number{position:absolute;left:1rem;bottom:.65rem;color:#26394b;font:800 .6rem var(--sans);letter-spacing:.13em}
.detective-copy{animation:detective-copy-in .75s .35s var(--ease-out) both}
.detective-copy>span{display:inline-block;padding-bottom:.45rem;border-bottom:2px solid #d94a42;color:#d7e5f0;font-size:.74rem;font-weight:800;letter-spacing:.15em}
.detective-copy h2{margin:1rem 0 .7rem;font:clamp(3.5rem,8vw,7.5rem)/.82 var(--display);letter-spacing:-.07em;text-shadow:0 12px 36px rgba(0,0,0,.3)}
.detective-copy h2 i{color:#e44940;font-style:normal}
.detective-copy p{color:#d7e5f0;font-size:clamp(.9rem,1.6vw,1.15rem);font-weight:700;letter-spacing:.08em}
.detective-close{position:absolute;right:clamp(1rem,3vw,2rem);top:clamp(1rem,3vw,2rem);z-index:2;display:grid;width:44px;height:44px;place-items:center;border:1px solid rgba(255,255,255,.25);border-radius:12px;background:rgba(255,255,255,.08);color:#fff;font-size:1.6rem;transition:background var(--motion-fast),transform var(--motion-fast)}
.detective-close:hover{background:rgba(255,255,255,.18);transform:rotate(5deg) scale(1.04)}
.detective-reveal-enter-active,.detective-reveal-leave-active{transition:opacity .35s ease}.detective-reveal-enter-from,.detective-reveal-leave-to{opacity:0}
@keyframes detective-arrive{0%{opacity:0;transform:translate3d(-4rem,5rem,0) rotate(-7deg) scale(.65)}70%{opacity:1;transform:translate3d(.7rem,-.5rem,0) rotate(1.5deg) scale(1.04)}100%{transform:none}}
@keyframes detective-copy-in{from{opacity:0;transform:translate3d(3rem,0,0)}to{opacity:1;transform:none}}
@keyframes case-flash{0%{opacity:0;transform:scale(.25)}30%{opacity:1}100%{opacity:.5;transform:scale(1.4)}}
@keyframes case-rays{to{transform:rotate(360deg)}}
@keyframes photo-glint{0%{transform:translateX(-55%) rotate(8deg)}100%{transform:translateX(55%) rotate(8deg)}}
@media(max-width:700px){.detective-stage{grid-template-columns:1fr;text-align:center}.evidence-photo{width:min(245px,66vw);padding:.5rem .5rem 1.75rem}.case-number{left:.75rem;bottom:.48rem;font-size:.48rem}.detective-copy{margin-top:-1rem}.detective-copy h2{font-size:clamp(3.25rem,16vw,5.5rem)}}
</style>
