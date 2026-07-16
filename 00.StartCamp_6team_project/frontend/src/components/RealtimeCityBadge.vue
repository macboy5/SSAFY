<script setup>
import { computed, ref, watch } from 'vue'
import { api } from '../api/client'

const props = defineProps({ contentId: { type: String, required: true } })
const data = ref(null)
const loading = ref(false)
const error = ref('')

const tone = computed(() => {
  const level = data.value?.congestion?.level
  return { 여유: 'calm', 보통: 'normal', '약간 붐빔': 'busy', 붐빔: 'crowded' }[level] || 'unknown'
})
const population = computed(() => {
  const { population_min: min, population_max: max } = data.value?.congestion || {}
  return min && max ? `${min.toLocaleString()}~${max.toLocaleString()}명` : ''
})
async function load(force = false) {
  loading.value = true
  error.value = ''
  try {
    const query = force ? '?refresh=true' : ''
    data.value = await api.get(`/realtime/contents/${props.contentId}${query}`)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

watch(() => props.contentId, () => load(false), { immediate: true })
</script>

<template>
  <section class="live-card" :class="tone" aria-labelledby="live-seoul-title">
    <div class="live-heading">
      <div>
        <span class="live-kicker"><i /> LIVE SEOUL</span>
        <h2 id="live-seoul-title">지금 이 동네는</h2>
      </div>
      <button type="button" class="refresh" :disabled="loading" aria-label="실시간 정보 새로고침" @click="load(true)">
        <span :class="{ spinning: loading }" aria-hidden="true">↻</span> 새로고침
      </button>
    </div>

    <div v-if="loading && !data" class="live-skeleton" role="status">
      <i /><i /><span>서울의 지금을 확인하고 있어요.</span>
    </div>
    <p v-else-if="error" class="unavailable" role="alert">{{ error }}</p>
    <template v-else-if="data?.available">
      <p class="area-name">
        서울시 관측 지역 · {{ data.area_name }}
        <span v-if="data.area_code">{{ data.area_code }}</span>
      </p>
      <div class="live-metrics">
        <div class="congestion-metric">
          <span>지금 혼잡도</span>
          <strong>{{ data.congestion.level }} <b aria-hidden="true">{{ data.congestion.emoji }}</b></strong>
          <p>{{ data.congestion.message || '실시간 유동 인구를 기준으로 한 혼잡도예요.' }}</p>
          <small v-if="population">현재 추정 {{ population }}</small>
        </div>
        <div class="bike-metric">
          <span>근처 따릉이</span>
          <strong><b>{{ data.bike.available_count.toLocaleString() }}</b>대</strong>
          <p>{{ data.bike.station_count }}개 가까운 대여소의 대여 가능 자전거</p>
        </div>
      </div>
      <div v-if="data.commercial?.available" class="commercial-strip">
        <span>이 동네 상권</span>
        <strong>{{ data.commercial.level }} {{ data.commercial.emoji }}</strong>
        <p>{{ data.commercial.message || '최근 상권 활동을 평소 같은 시간대와 비교한 결과예요.' }}</p>
      </div>
      <ul v-if="data.bike.stations?.length" class="bike-stations" aria-label="대여 가능 수가 많은 따릉이 대여소">
        <li v-for="station in data.bike.stations" :key="station.name">
          <span>{{ station.name }}<small v-if="station.distance_m"> · {{ station.distance_m }}m</small></span><strong>{{ station.available_count }}대</strong>
        </li>
      </ul>
      <div class="live-foot">
        <span>출처: {{ data.source || '서울 열린데이터광장' }}</span>
        <span v-if="data.stale">마지막 수신값</span>
        <span v-else-if="data.fallback">{{ data.notice }}</span>
        <span v-else-if="data.cached">최근 4분 이내 수신값</span>
        <span v-else>방금 수신한 정보</span>
      </div>
    </template>
    <div v-else class="unavailable">
      <strong>{{ data?.mapped ? '실시간 연결을 기다리고 있어요.' : '실시간 관측 지역 밖이에요.' }}</strong>
      <p>{{ data?.reason || '잠시 후 다시 확인해 주세요.' }}</p>
      <small v-if="data?.mapped && data?.area_name">매칭 지역 · {{ data.area_name }}<template v-if="data.area_code"> ({{ data.area_code }})</template></small>
      <button v-if="data?.mapped && !loading" type="button" class="retry" @click="load(true)">다시 연결</button>
    </div>
  </section>
</template>

<style scoped>
.live-card{--live:#718079;position:relative;overflow:hidden;margin:1.5rem 0;padding:1.35rem;border:1px solid color-mix(in srgb,var(--live) 34%,var(--line));border-radius:24px;background:linear-gradient(135deg,color-mix(in srgb,var(--live) 10%,var(--surface)),var(--surface) 58%);box-shadow:var(--shadow)}.live-card:after{content:'';position:absolute;right:-60px;top:-80px;width:190px;height:190px;border-radius:50%;background:color-mix(in srgb,var(--live) 12%,transparent);pointer-events:none}.live-card.calm{--live:#2f9b68}.live-card.normal{--live:#d4a819}.live-card.busy{--live:#df7b32}.live-card.crowded{--live:#d64a42}.live-heading,.live-foot{display:flex;align-items:center;justify-content:space-between;gap:1rem}.live-kicker{display:flex;align-items:center;gap:.45rem;font-size:.62rem;font-weight:800;letter-spacing:.18em;color:var(--live)}.live-kicker i{width:7px;height:7px;border-radius:50%;background:var(--live);box-shadow:0 0 0 5px color-mix(in srgb,var(--live) 15%,transparent);animation:pulse 1.8s ease-out infinite}.live-heading h2{font:1.8rem var(--display);margin-top:.25rem}.refresh,.retry{position:relative;z-index:1;border:1px solid var(--line);border-radius:99px;padding:.45rem .7rem;background:var(--surface);color:var(--text);font-size:.7rem}.refresh:disabled{opacity:.55}.spinning{display:inline-block;animation:spin .75s linear infinite}.area-name{display:flex;align-items:center;gap:.45rem;margin:.85rem 0 .55rem;color:var(--muted);font-size:.7rem}.area-name span{padding:.15rem .4rem;border-radius:99px;background:var(--soft);font-size:.56rem;font-weight:800;letter-spacing:.05em}.live-metrics{display:grid;grid-template-columns:1.2fr .8fr;gap:.7rem}.live-metrics>div{padding:1rem;border:1px solid var(--line);border-radius:17px;background:color-mix(in srgb,var(--surface) 85%,transparent)}.live-metrics span,.commercial-strip span{font-size:.68rem;font-weight:700;color:var(--muted)}.live-metrics strong{display:block;margin:.25rem 0;font:1.7rem var(--display)}.congestion-metric strong{color:var(--live)}.congestion-metric strong b{font-family:var(--sans);font-size:1rem}.live-metrics p{font-size:.72rem;color:var(--muted)}.live-metrics small{display:block;margin-top:.45rem;font-size:.65rem;color:var(--text)}.bike-metric strong b{font-size:2.2rem}.commercial-strip{display:grid;grid-template-columns:auto auto 1fr;align-items:center;gap:.65rem;margin-top:.7rem;padding:.65rem .8rem;border:1px solid color-mix(in srgb,var(--live) 20%,var(--line));border-radius:13px;background:color-mix(in srgb,var(--live) 6%,var(--surface))}.commercial-strip strong{font-size:.75rem;color:var(--live);white-space:nowrap}.commercial-strip p{font-size:.67rem;color:var(--muted)}.bike-stations{display:grid;grid-template-columns:repeat(3,1fr);gap:.4rem;list-style:none;padding:0;margin:.7rem 0 0}.bike-stations li{display:flex;justify-content:space-between;gap:.5rem;padding:.5rem .65rem;border-radius:10px;background:var(--soft);font-size:.65rem}.bike-stations li span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bike-stations li strong{color:var(--primary);white-space:nowrap}.live-foot{margin-top:.85rem;color:var(--muted);font-size:.58rem}.unavailable{padding:1.2rem 0 .3rem;color:var(--muted)}.unavailable strong{color:var(--text)}.unavailable p{font-size:.8rem;margin-top:.25rem}.unavailable small{display:block;margin-top:.45rem;font-size:.65rem}.retry{margin-top:.75rem}.live-skeleton{display:grid;grid-template-columns:1fr .7fr;gap:.7rem;margin-top:1rem}.live-skeleton i{height:100px;border-radius:17px;background:linear-gradient(100deg,var(--soft),var(--surface),var(--soft));background-size:200% 100%;animation:shimmer 1.2s infinite}.live-skeleton span{grid-column:1/-1;color:var(--muted);font-size:.7rem}@keyframes pulse{70%,100%{box-shadow:0 0 0 12px transparent}}@keyframes spin{to{transform:rotate(360deg)}}@keyframes shimmer{to{background-position:-200% 0}}@media(max-width:620px){.live-card{padding:1rem;border-radius:19px}.live-metrics{grid-template-columns:1fr}.commercial-strip{grid-template-columns:1fr}.bike-stations{grid-template-columns:1fr}.live-foot{align-items:flex-start;flex-direction:column;gap:.15rem}.refresh{font-size:0}.refresh span{font-size:1rem}}
</style>
