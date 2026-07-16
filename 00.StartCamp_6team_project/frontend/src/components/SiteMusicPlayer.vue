<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const audio = ref(null)
const expanded = ref(false)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(0.65)
const error = ref('')
let panelCloseTimer = null

const progressMax = computed(() => duration.value || 0)

function formatTime(value) {
  if (!Number.isFinite(value) || value < 0) return '0:00'
  const minutes = Math.floor(value / 60)
  const seconds = Math.floor(value % 60).toString().padStart(2, '0')
  return `${minutes}:${seconds}`
}

async function togglePlayback() {
  if (!audio.value) return
  error.value = ''

  if (isPlaying.value) {
    audio.value.pause()
    return
  }

  openPanel()
  try {
    await audio.value.play()
  } catch {
    error.value = '음원을 재생하지 못했습니다.'
    isPlaying.value = false
  }
}

function openPanel() {
  if (panelCloseTimer) window.clearTimeout(panelCloseTimer)
  panelCloseTimer = null
  expanded.value = true
}

function schedulePanelClose() {
  if (panelCloseTimer) window.clearTimeout(panelCloseTimer)
  panelCloseTimer = window.setTimeout(() => {
    expanded.value = false
    panelCloseTimer = null
  }, 180)
}

function closePanel() {
  if (panelCloseTimer) window.clearTimeout(panelCloseTimer)
  panelCloseTimer = null
  expanded.value = false
}

function handleFocusOut(event) {
  if (!event.currentTarget.contains(event.relatedTarget)) schedulePanelClose()
}

function syncMetadata() {
  duration.value = Number.isFinite(audio.value?.duration) ? audio.value.duration : 0
}

function syncTime() {
  currentTime.value = audio.value?.currentTime || 0
}

function seek(event) {
  if (!audio.value) return
  audio.value.currentTime = Number(event.target.value)
  syncTime()
}

function updateVolume(event) {
  volume.value = Number(event.target.value)
  if (audio.value) audio.value.volume = volume.value
  localStorage.setItem('seoul-sound-volume', String(volume.value))
}

function handleAudioError() {
  error.value = '음원 파일을 불러오지 못했습니다.'
  isPlaying.value = false
}

onMounted(() => {
  const savedVolume = Number(localStorage.getItem('seoul-sound-volume'))
  if (Number.isFinite(savedVolume) && savedVolume >= 0 && savedVolume <= 1) volume.value = savedVolume
  if (audio.value) audio.value.volume = volume.value
})

onBeforeUnmount(() => {
  if (panelCloseTimer) window.clearTimeout(panelCloseTimer)
  audio.value?.pause()
})
</script>

<template>
  <aside
    class="music-dock"
    :class="{ playing: isPlaying }"
    aria-label="사이트 음악 플레이어"
    @mouseenter="openPanel"
    @mouseleave="schedulePanelClose"
    @focusin="openPanel"
    @focusout="handleFocusOut"
  >
    <audio
      ref="audio"
      src="/audio/soulmate.mp3"
      preload="metadata"
      loop
      @loadedmetadata="syncMetadata"
      @durationchange="syncMetadata"
      @timeupdate="syncTime"
      @play="isPlaying = true"
      @pause="isPlaying = false"
      @error="handleAudioError"
    ></audio>

    <Transition name="music-panel">
      <section id="site-music-panel" v-show="expanded" class="music-panel" aria-label="로컬 음악 재생 제어">
        <div class="music-head">
          <div><small>SEOUL SOUND · 01</small><strong>MySoulMate Radio</strong></div>
          <button type="button" aria-label="플레이어 팝업 닫기" @click.stop="closePanel">×</button>
        </div>

        <div class="track-row">
          <div class="album-art" aria-hidden="true"><span></span><b>SM</b></div>
          <div class="track-copy">
            <small>LOCAL SOUNDTRACK</small>
            <strong>SoulMate</strong>
            <span>ZICO</span>
            <em><i aria-hidden="true"></i>{{ isPlaying ? '재생 중' : '일시 정지' }}</em>
          </div>
        </div>

        <label class="seek-control">
          <span class="sr-label">재생 위치</span>
          <input :value="currentTime" type="range" min="0" :max="progressMax" step="0.1" @input="seek" />
          <span class="time-row"><time>{{ formatTime(currentTime) }}</time><time>{{ formatTime(duration) }}</time></span>
        </label>

        <div class="player-controls">
          <button type="button" class="panel-play" :aria-label="isPlaying ? '음악 일시정지' : '음악 계속 재생'" @click="togglePlayback">{{ isPlaying ? 'Ⅱ' : '▶' }}</button>
          <div class="control-copy"><small>REPEAT ON</small><strong>{{ isPlaying ? 'Playing now' : 'Paused' }}</strong></div>
          <label class="volume-control"><span aria-hidden="true">VOL</span><input :value="volume" type="range" min="0" max="1" step="0.05" aria-label="음악 볼륨" @input="updateVolume" /></label>
        </div>
        <p v-if="error" class="music-error" role="alert">{{ error }}</p>
      </section>
    </Transition>

    <button
      class="music-toggle"
      type="button"
      :aria-label="isPlaying ? '사이트 음악 끄기' : '사이트 음악 켜기'"
      :aria-pressed="isPlaying"
      :aria-expanded="expanded"
      aria-controls="site-music-panel"
      @click="togglePlayback"
    >
      <span class="music-disc" aria-hidden="true">♪</span>
      <span class="music-label"><small>SEOUL SOUND</small><strong>{{ isPlaying ? '끄기' : '재생' }}</strong></span>
      <span class="sound-bars" aria-hidden="true"><i></i><i></i><i></i></span>
    </button>
  </aside>
</template>

<style scoped>
.music-dock{position:relative;z-index:5;display:block;flex:none}
.music-dock>audio{display:none}
.music-panel{position:absolute;left:0;right:auto;top:calc(100% + .85rem);z-index:10;width:min(340px,calc(100vw - 2rem));padding:.8rem;border:1px solid color-mix(in srgb,var(--line) 78%,transparent);border-radius:9px 22px 22px;background:color-mix(in srgb,var(--surface) 96%,transparent);box-shadow:0 28px 80px color-mix(in srgb,var(--ink) 25%,transparent),inset 0 1px 0 color-mix(in srgb,white 58%,transparent);backdrop-filter:blur(20px)}
.music-panel:before{content:'';position:absolute;left:18px;right:auto;top:-6px;width:12px;height:12px;border-left:1px solid var(--line);border-top:1px solid var(--line);background:var(--surface);transform:rotate(45deg)}
.music-panel:after{content:'';position:absolute;inset:0;z-index:-1;border-radius:inherit;background-image:radial-gradient(color-mix(in srgb,var(--ink) 13%,transparent) .45px,transparent .55px);background-size:5px 5px;opacity:.14;pointer-events:none}
.music-head{display:flex;align-items:center;justify-content:space-between;padding:.05rem .05rem .75rem .15rem}.music-head>div{display:flex;flex-direction:column}.music-head small{color:var(--accent);font-size:.56rem;font-weight:800;letter-spacing:.16em}.music-head strong{font:1rem var(--display);letter-spacing:-.02em}.music-head button{display:grid;width:31px;height:31px;place-items:center;border:0;border-radius:9px;background:var(--soft);color:var(--text);font-size:1.15rem;transition:transform var(--motion-fast),background var(--motion-fast)}.music-head button:hover{background:color-mix(in srgb,var(--accent) 12%,var(--soft));transform:rotate(6deg)}
.track-row{display:grid;grid-template-columns:96px 1fr;align-items:center;gap:1rem;padding:.9rem;border-radius:8px 17px 17px;background:radial-gradient(circle at 12% 8%,color-mix(in srgb,var(--accent) 42%,transparent),transparent 48%),var(--ink);color:var(--bg);box-shadow:0 14px 34px color-mix(in srgb,var(--ink) 18%,transparent)}
.album-art{position:relative;display:grid;width:96px;height:96px;place-items:center;border:1px solid color-mix(in srgb,var(--bg) 18%,transparent);border-radius:50%;background:repeating-radial-gradient(circle,#19231f 0 4px,#101714 5px 8px);box-shadow:0 12px 25px rgba(0,0,0,.28),inset 0 0 0 1px rgba(255,255,255,.08)}.album-art:before{content:'';position:absolute;width:40%;height:40%;border-radius:50%;background:var(--accent);box-shadow:inset 0 0 0 5px color-mix(in srgb,white 14%,transparent)}.album-art span{position:absolute;z-index:1;width:8px;height:8px;border:2px solid rgba(255,255,255,.62);border-radius:50%;background:var(--ink)}.album-art b{position:absolute;z-index:1;top:57%;color:#fff;font-size:.42rem;letter-spacing:.08em}.playing .album-art{animation:music-disc 7s linear infinite}
.track-copy{display:flex;min-width:0;flex-direction:column}.track-copy small{color:color-mix(in srgb,var(--accent) 80%,white);font-size:.52rem;font-weight:800;letter-spacing:.12em}.track-copy strong{margin:.15rem 0;font:2rem/1 var(--display);letter-spacing:-.05em}.track-copy>span{color:color-mix(in srgb,var(--bg) 70%,transparent);font-size:.72rem;font-weight:700}.track-copy em{display:flex;align-items:center;gap:.4rem;margin-top:.65rem;color:color-mix(in srgb,var(--bg) 70%,transparent);font-size:.6rem;font-style:normal;font-weight:700}.track-copy em i{width:5px;height:5px;border-radius:50%;background:var(--accent)}.playing .track-copy em i{box-shadow:0 0 0 5px color-mix(in srgb,var(--accent) 16%,transparent);animation:status-pulse 1.8s ease-out infinite}
.seek-control{display:block;margin-top:.85rem;padding:0 .15rem}.sr-label{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}.seek-control input,.volume-control input{width:100%;height:4px;margin:0;appearance:none;border-radius:99px;background:color-mix(in srgb,var(--ink) 15%,var(--soft));cursor:pointer}.seek-control input::-webkit-slider-thumb,.volume-control input::-webkit-slider-thumb{width:13px;height:13px;appearance:none;border:3px solid var(--surface);border-radius:50%;background:var(--accent);box-shadow:0 2px 7px color-mix(in srgb,var(--ink) 20%,transparent)}.seek-control input::-moz-range-thumb,.volume-control input::-moz-range-thumb{width:9px;height:9px;border:3px solid var(--surface);border-radius:50%;background:var(--accent)}.time-row{display:flex;justify-content:space-between;margin-top:.25rem;color:var(--muted);font-size:.58rem;font-variant-numeric:tabular-nums}
.player-controls{display:grid;grid-template-columns:auto 1fr minmax(90px,115px);align-items:center;gap:.7rem;margin-top:.55rem;padding:.7rem .15rem .1rem;border-top:1px solid var(--line)}.panel-play{display:grid;width:42px;height:42px;place-items:center;padding:0 0 0 1px;border:0;border-radius:12px 12px 5px 12px;background:var(--accent);color:#fff;font-size:.8rem;font-weight:900;box-shadow:0 8px 20px color-mix(in srgb,var(--accent) 28%,transparent);transition:transform var(--motion-fast),box-shadow var(--motion-fast)}.panel-play:hover{transform:translateY(-2px);box-shadow:0 11px 24px color-mix(in srgb,var(--accent) 36%,transparent)}.control-copy{display:flex;min-width:0;flex-direction:column;line-height:1.2}.control-copy small{color:var(--muted);font-size:.48rem;font-weight:800;letter-spacing:.1em}.control-copy strong{font-size:.67rem;white-space:nowrap}.volume-control{display:grid;grid-template-columns:auto 1fr;align-items:center;gap:.4rem;color:var(--muted);font-size:.48rem;font-weight:800;letter-spacing:.08em}.music-error{margin-top:.55rem;padding:.45rem .55rem;border-radius:7px;background:color-mix(in srgb,var(--danger) 9%,transparent);color:var(--danger);font-size:.65rem}
.music-toggle{display:grid;grid-template-columns:auto auto auto;align-items:center;gap:.5rem;height:40px;padding:.25rem .55rem .25rem .3rem;border:1px solid var(--line);border-radius:11px;background:color-mix(in srgb,var(--surface) 82%,transparent);color:var(--text);box-shadow:inset 0 1px 0 color-mix(in srgb,white 45%,transparent);backdrop-filter:blur(12px);transition:transform var(--motion-fast) var(--ease-out),border-color var(--motion-fast),background var(--motion-fast)}.music-toggle:hover{border-color:color-mix(in srgb,var(--accent) 45%,var(--line));background:var(--soft);transform:translateY(-2px)}
.music-disc{display:grid;width:28px;height:28px;place-items:center;border-radius:8px;background:var(--ink);color:var(--bg);font:.8rem var(--display)}.playing .music-disc{animation:music-disc 5s linear infinite;border-radius:50%}.music-label{display:flex;min-width:58px;flex-direction:column;align-items:flex-start;line-height:1.08}.music-label small{color:var(--muted);font-size:.43rem;font-weight:800;letter-spacing:.09em}.music-label strong{margin-top:.12rem;font-size:.67rem}.sound-bars{display:flex;height:15px;align-items:flex-end;gap:2px}.sound-bars i{display:block;width:2px;height:3px;border-radius:2px;background:var(--accent)}.playing .sound-bars i{animation:music-bar .72s ease-in-out infinite alternate}.playing .sound-bars i:nth-child(2){animation-delay:-.35s}.playing .sound-bars i:nth-child(3){animation-delay:-.58s}
.music-panel-enter-active,.music-panel-leave-active{transition:opacity .25s,transform .25s var(--ease-out)}.music-panel-enter-from,.music-panel-leave-to{opacity:0;transform:translate3d(0,-9px,0) scale(.97)}
@keyframes music-disc{to{transform:rotate(360deg)}}@keyframes music-bar{to{height:14px}}@keyframes status-pulse{to{box-shadow:0 0 0 9px transparent}}
@media(max-width:1150px){.music-label small{display:none}.music-label{min-width:auto}.music-toggle{gap:.4rem}}
@media(max-width:620px){.music-toggle{width:36px;height:36px;padding:3px}.music-disc{width:28px;height:28px}.music-label,.sound-bars{display:none}.music-panel{position:fixed;left:.75rem;right:.75rem;top:70px;width:auto}.music-panel:before{right:auto;left:43%}.track-row{grid-template-columns:82px 1fr}.album-art{width:82px;height:82px}}
</style>
