<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SeoulLandmarkBackdrop from './components/SeoulLandmarkBackdrop.vue'
import SiteMusicPlayer from './components/SiteMusicPlayer.vue'
import { useTheme } from './composables/useTheme'
import { useAuthStore } from './stores/auth'

const open = ref(false)
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { theme, toggleTheme } = useTheme()
const scrollProgress = ref(0)
const isImmersive = computed(() => route.meta.layout === 'immersive')

function updateScrollProgress() {
  const height = document.documentElement.scrollHeight - window.innerHeight
  scrollProgress.value = height > 0 ? Math.min((window.scrollY / height) * 100, 100) : 0
}

onMounted(() => {
  auth.bootstrap()
  updateScrollProgress()
  window.addEventListener('scroll', updateScrollProgress, { passive: true })
})
onBeforeUnmount(() => window.removeEventListener('scroll', updateScrollProgress))

async function logout() {
  await auth.logout()
  open.value = false
  await router.push('/')
}
</script>

<template>
  <div class="shell" :class="{ 'immersive-shell': isImmersive }">
    <a class="skip-link" href="#main-content">본문으로 건너뛰기</a>
    <SeoulLandmarkBackdrop />
    <div v-if="!isImmersive" class="scroll-progress" :style="{ width: `${scrollProgress}%` }" aria-hidden="true" />
    <header v-if="!isImmersive" class="nav">
      <div class="nav-brand-group">
        <RouterLink to="/" class="brand"><span>SEOUL</span>MySoulMate</RouterLink>
        <SiteMusicPlayer />
      </div>
      <nav class="links" :class="{ open }" aria-label="주요 메뉴" @click="open = false">
        <RouterLink to="/">Explore</RouterLink>
        <RouterLink to="/map">Map</RouterLink>
        <RouterLink to="/planner">Planner</RouterLink>
        <RouterLink to="/community">Community</RouterLink>
        <RouterLink to="/chat">Soul Chat</RouterLink>
        <RouterLink v-if="!auth.isAuthenticated" class="mobile-auth" :to="{ name: 'auth', query: { mode: 'login' } }">Login</RouterLink>
      </nav>
      <div class="nav-actions">
        <div v-if="auth.isAuthenticated" class="account-menu">
          <span class="avatar">{{ auth.user.nickname?.slice(0, 1) }}</span>
          <span class="account-name">{{ auth.user.nickname }}</span>
          <button type="button" @click="logout">로그아웃</button>
        </div>
        <RouterLink v-else class="login-link" :to="{ name: 'auth', query: { mode: 'login' } }">로그인</RouterLink>
        <button class="theme-toggle" :aria-label="theme === 'light' ? '다크 모드로 전환' : '라이트 모드로 전환'" :aria-pressed="theme === 'dark'" @click="toggleTheme">
          <span aria-hidden="true">◐</span>
        </button>
        <button class="menu" :aria-label="open ? '메뉴 닫기' : '메뉴 열기'" :aria-expanded="open" @click="open = !open">{{ open ? '×' : '☰' }}</button>
      </div>
    </header>
    <main id="main-content" class="content" :class="{ immersive: isImmersive }">
      <RouterView v-slot="{ Component, route: viewRoute }">
        <Transition name="page-shift" mode="out-in">
          <component :is="Component" :key="viewRoute.path" />
        </Transition>
      </RouterView>
    </main>
    <footer v-if="!isImmersive">
      <div class="footer-brand"><strong>SeoulMySoulMate</strong><span>서울에서 내 취향의 리듬을 찾아보세요.</span></div>
      <nav aria-label="하단 메뉴"><RouterLink to="/">장소 탐색</RouterLink><RouterLink to="/community">커뮤니티</RouterLink><RouterLink to="/planner">플래너</RouterLink></nav>
      <a class="data-source" href="https://www.data.go.kr/data/15101578/openapi.do" target="_blank" rel="noreferrer">Data by 한국관광공사 ↗</a>
    </footer>
  </div>
</template>

<style scoped>
.scroll-progress{position:fixed;left:0;top:0;z-index:100;height:3px;background:linear-gradient(90deg,var(--accent),var(--primary));transition:width .08s linear;pointer-events:none}
.shell{min-height:100vh}.shell.immersive-shell{background:var(--bg)}.nav{height:78px;display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:2rem;padding:0 clamp(1rem,4vw,4rem);position:sticky;top:0;z-index:20;background:var(--nav-bg);backdrop-filter:blur(16px);border-bottom:1px solid var(--line)}.brand{text-decoration:none;font:1.4rem var(--display);letter-spacing:-.04em;white-space:nowrap}.brand span{display:inline-block;font:700 .6rem var(--sans);letter-spacing:.22em;color:var(--accent);margin-right:.45rem;vertical-align:middle}.links{display:flex;justify-content:flex-end;gap:clamp(.8rem,2vw,2rem)}.links a{text-decoration:none;text-transform:uppercase;font-size:.66rem;letter-spacing:.13em;font-weight:700;position:relative}.links a:after{content:'';position:absolute;left:0;right:100%;bottom:-8px;height:2px;background:var(--accent);transition:.25s}.links a.router-link-active:after{right:0}.mobile-auth{display:none}.nav-actions{display:flex;align-items:center;gap:.55rem}.theme-toggle{display:grid;place-items:center;width:38px;height:38px;border:1px solid var(--line);border-radius:50%;background:var(--surface);color:var(--text);font-size:1rem;transition:transform .25s,background .25s}.theme-toggle:hover{transform:rotate(12deg) translateY(-1px)}.menu{display:none;border:0;background:none;color:var(--text);font-size:1.4rem}.login-link{padding:.48rem .85rem;border:1px solid var(--line);border-radius:99px;text-decoration:none;font-size:.72rem;font-weight:800;transition:.2s}.login-link:hover{border-color:var(--primary);color:var(--primary);transform:translateY(-1px)}.account-menu{display:flex;align-items:center;gap:.42rem;padding:.25rem .3rem .25rem .25rem;border:1px solid var(--line);border-radius:99px;background:var(--surface)}.avatar{display:grid;place-items:center;width:29px;height:29px;border-radius:50%;background:var(--primary);color:var(--bg);font-size:.72rem;font-weight:800}.account-name{max-width:90px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:.7rem;font-weight:800}.account-menu button{padding:.28rem .5rem;border:0;border-left:1px solid var(--line);background:transparent;color:var(--muted);font-size:.65rem}.content{max-width:1440px;margin:auto;padding:0 clamp(1rem,4vw,4rem) 5rem}.content.immersive{max-width:none;margin:0;padding:0}footer{max-width:1440px;margin:auto;border-top:1px solid var(--line);padding:2rem clamp(1rem,4vw,4rem);display:flex;justify-content:space-between;color:var(--muted)}footer strong{color:var(--ink);font-family:var(--display)}@media(max-width:1050px){.account-name{display:none}}@media(max-width:850px){.menu{display:block}.links{display:none;position:absolute;top:78px;left:0;right:0;background:var(--surface);padding:1.5rem;flex-direction:column;border-bottom:1px solid var(--line);box-shadow:var(--shadow)}.links.open{display:flex}.links a{padding:.45rem 0}.links a:after{bottom:0}.mobile-auth{display:block}.login-link{display:none}}@media(max-width:540px){.account-menu{display:none}}@media(max-width:420px){.brand span{display:none}footer{flex-direction:column;gap:.35rem}}
</style>

<style scoped>
.skip-link{position:fixed;left:1rem;top:.75rem;z-index:120;padding:.65rem .9rem;border-radius:10px;background:var(--ink);color:var(--bg);font-size:.75rem;font-weight:800;text-decoration:none;transform:translateY(-160%);transition:transform var(--motion-fast)}
.skip-link:focus{transform:none}
.shell{position:relative;isolation:isolate;min-height:100dvh}
.content,footer{position:relative;z-index:1}
.nav{box-shadow:0 1px 0 color-mix(in srgb,var(--ink) 5%,transparent)}
.nav-brand-group{display:flex;align-items:center;gap:.7rem;min-width:0}
.links{gap:.2rem}
.links a{padding:.52rem .72rem;border-radius:9px;color:var(--muted);font-size:.84rem;letter-spacing:.005em;text-transform:none;transition:color var(--motion-fast),background var(--motion-fast),transform var(--motion-fast)}
.links a:after{display:none}
.links a:hover{color:var(--text);background:color-mix(in srgb,var(--soft) 72%,transparent)}
.links a.router-link-active{background:var(--soft);color:var(--primary)}
.theme-toggle{border-radius:11px}
.theme-toggle:hover{transform:translateY(-2px) rotate(10deg);border-color:var(--primary)}
.login-link{border-radius:10px;font-size:.82rem}
.account-menu{border-radius:12px}
.avatar{border-radius:8px}
.account-name{font-size:.8rem}.account-menu button{font-size:.75rem}
footer{display:grid;grid-template-columns:minmax(220px,1fr) auto minmax(220px,1fr);align-items:end;gap:2rem;padding-top:2.6rem;padding-bottom:2.8rem}
.footer-brand{display:flex;flex-direction:column;gap:.2rem}
.footer-brand strong{font-size:1.1rem}
.footer-brand span{font-size:.72rem}
footer nav{display:flex;gap:1rem}
footer nav a,.data-source{font-size:.78rem;font-weight:700;text-decoration:none}
footer nav a:hover,.data-source:hover{color:var(--primary)}
.data-source{justify-self:end;color:var(--muted)}
@media(max-width:850px){.links{gap:.3rem}.links a{padding:.7rem .75rem}.links a.router-link-active{background:var(--soft)}footer{grid-template-columns:1fr auto}.data-source{grid-column:1/-1;justify-self:start}}
@media(max-width:620px){.nav{gap:.75rem}.nav-brand-group{gap:.4rem}.brand{font-size:1.2rem}}
@media(max-width:540px){footer{grid-template-columns:1fr;gap:1.2rem}footer nav{flex-wrap:wrap}.data-source{grid-column:auto}.footer-brand span{display:block}}
.page-shift-enter-active,.page-shift-leave-active{transition:opacity 180ms ease,transform 220ms var(--ease-out)}
.page-shift-enter-from{opacity:0;transform:translate3d(0,12px,0)}
.page-shift-leave-to{opacity:0;transform:translate3d(0,-6px,0)}
@media(prefers-reduced-motion:reduce){.page-shift-enter-active,.page-shift-leave-active{transition:none}}
</style>
