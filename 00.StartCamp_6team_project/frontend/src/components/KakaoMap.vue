<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { loadKakaoSdk, resetKakaoSdk } from '../composables/useKakaoSdk'

const props = defineProps({
  places: { type: Array, default: () => [] },
  height: { type: String, default: '360px' },
  cluster: { type: Boolean, default: false },
  fitBounds: { type: Boolean, default: true },
  dongFeatures: { type: Array, default: () => [] },
  districtFeatures: { type: Array, default: () => [] },
  districtCongestion: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['select-place', 'select-cluster'])

const CONGESTION_COLOR = { calm: '#2f9b68', normal: '#d4a819', busy: '#df7b32', crowded: '#d64a42' }
const CONGESTION_TONE = { 여유: 'calm', 보통: 'normal', '약간 붐빔': 'busy', 붐빔: 'crowded' }
const CLUSTER_CALCULATOR = [10, 50, 200, 500]
const CLUSTER_STYLES = [
  { width: '40px', height: '40px', lineHeight: '40px', background: 'var(--cluster-low)', color: 'var(--cluster-low-text)', border: '1px solid var(--cluster-border)', borderRadius: '13px 13px 7px 13px', boxShadow: '0 8px 22px var(--cluster-shadow)' },
  { width: '48px', height: '48px', lineHeight: '48px', background: 'var(--cluster-mid)', color: 'var(--cluster-mid-text)', border: '1px solid var(--cluster-border)', borderRadius: '15px 15px 8px 15px', boxShadow: '0 10px 26px var(--cluster-shadow)' },
  { width: '58px', height: '58px', lineHeight: '58px', background: 'var(--cluster-high)', color: 'var(--cluster-on-strong)', border: '1px solid color-mix(in srgb, var(--cluster-high) 70%, white)', borderRadius: '18px 18px 9px 18px', boxShadow: '0 12px 30px var(--cluster-shadow)' },
  { width: '70px', height: '70px', lineHeight: '70px', background: 'var(--cluster-dense)', color: 'var(--cluster-on-strong)', border: '1px solid color-mix(in srgb, var(--cluster-dense) 72%, white)', borderRadius: '21px 21px 10px 21px', boxShadow: '0 14px 34px var(--cluster-shadow)' },
  { width: '82px', height: '82px', lineHeight: '82px', background: 'var(--cluster-max)', color: 'var(--cluster-max-text)', border: '1px solid color-mix(in srgb, var(--cluster-max) 76%, white)', borderRadius: '24px 24px 12px 24px', boxShadow: '0 16px 40px var(--cluster-shadow)' },
].map((style) => ({
  ...style,
  textAlign: 'center',
  fontFamily: "'DM Sans', sans-serif",
  fontSize: '12px',
  fontWeight: '800',
  fontVariantNumeric: 'tabular-nums',
  cursor: 'pointer',
  transition: 'scale 180ms cubic-bezier(.2,.75,.25,1), filter 180ms ease, box-shadow 180ms ease',
}))

const mapId = `kakao-map-${Math.random().toString(36).slice(2)}`
const apiKey = String(import.meta.env.VITE_KAKAO_MAP_KEY || '').trim()
const status = ref(apiKey ? 'loading' : 'missing')
const errorMessage = ref('')
const currentOrigin = window.location.origin
const validPlaces = computed(() =>
  props.places.filter((place) => {
    const longitude = Number(place.mapx), latitude = Number(place.mapy)
    return Number.isFinite(longitude) && Number.isFinite(latitude)
      && longitude >= 126.7 && longitude <= 127.3
      && latitude >= 37.4 && latitude <= 37.8
  }),
)
let map = null
let markers = []
let clusterer = null
let clusterListenerAdded = false
let infoWindow = null
let dongPolygons = []
let districtPolygons = []
let districtPopup = null

function escapeHtml(value = '') {
  return String(value).replace(/[&<>'"]/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;',
  })[char])
}

function clusterText(size) {
  if (size < 1000) return String(size)
  return `${(size / 1000).toFixed(size < 10000 ? 1 : 0)}k`
}

function setClusterHover(cluster, active) {
  const marker = cluster.getClusterMarker?.()
  const content = marker?.getContent?.()
  if (!(content instanceof HTMLElement)) return
  content.style.scale = active ? '1.08' : '1'
  content.style.filter = active ? 'brightness(1.06) saturate(1.04)' : 'none'
}

function geometryToPaths(geometry) {
  const toLatLngRing = (ring) => ring.map(([lon, lat]) => new window.kakao.maps.LatLng(lat, lon))
  if (geometry?.type === 'Polygon') return [geometry.coordinates.map(toLatLngRing)]
  if (geometry?.type === 'MultiPolygon') return geometry.coordinates.map((polygon) => polygon.map(toLatLngRing))
  return []
}

function drawDongGrid() {
  if (!map || !window.kakao?.maps) return
  dongPolygons.forEach((polygon) => polygon.setMap(null))
  dongPolygons = []

  props.dongFeatures.forEach((feature) => {
    geometryToPaths(feature.geometry).forEach((path) => {
      const polygon = new window.kakao.maps.Polygon({
        path, strokeWeight: 1, strokeColor: '#999', strokeOpacity: 0.45,
        fillOpacity: 0,
      })
      polygon.setMap(map)
      dongPolygons.push(polygon)
    })
  })
}

function drawDistricts() {
  if (!map || !window.kakao?.maps) return
  districtPolygons.forEach((polygon) => polygon.setMap(null))
  districtPolygons = []
  districtPopup?.setMap(null)

  props.districtFeatures.forEach((feature) => {
    const guName = feature.properties?.sggnm
    const info = props.districtCongestion[guName]
    const tone = CONGESTION_TONE[info?.level] || 'calm'
    const color = info ? CONGESTION_COLOR[tone] : '#b7bfc7'
    const baseFillOpacity = info ? 0.28 : 0.05
    const hoverFillOpacity = info ? 0.58 : 0.18
    geometryToPaths(feature.geometry).forEach((path) => {
      const polygon = new window.kakao.maps.Polygon({
        path, strokeWeight: 2, strokeColor: color, strokeOpacity: 0.85,
        fillColor: color, fillOpacity: baseFillOpacity,
      })
      polygon.setMap(map)
      window.kakao.maps.event.addListener(polygon, 'mouseover', (mouseEvent) => {
        polygon.setOptions({ fillOpacity: hoverFillOpacity, strokeWeight: 3 })
        districtPopup?.setMap(null)
        const content = document.createElement('div')
        content.className = 'congestion-popup'
        content.innerHTML = info
          ? `<b>${escapeHtml(guName)}</b><span style="color:${color}">${escapeHtml(info.level)}</span><p>${info.inherited ? `인접한 ${escapeHtml(info.source_gu)}의 혼잡도를 따랐어요` : `관측지역 ${info.area_count}곳 기준`}</p>`
          : `<b>${escapeHtml(guName)}</b><span>데이터 없음</span>`
        districtPopup = new window.kakao.maps.CustomOverlay({
          position: mouseEvent.latLng, content, yAnchor: 1.35, zIndex: 4,
        })
        districtPopup.setMap(map)
      })
      window.kakao.maps.event.addListener(polygon, 'mousemove', (mouseEvent) => {
        districtPopup?.setPosition(mouseEvent.latLng)
      })
      window.kakao.maps.event.addListener(polygon, 'mouseout', () => {
        polygon.setOptions({ fillOpacity: baseFillOpacity, strokeWeight: 2 })
        districtPopup?.setMap(null)
      })
      districtPolygons.push(polygon)
    })
  })
}

function draw() {
  const container = document.getElementById(mapId)
  if (!container || !window.kakao?.maps || status.value !== 'ready') return
  const center = validPlaces.value[0] || { mapx: 126.978, mapy: 37.5665 }
  if (!map) {
    map = new window.kakao.maps.Map(container, {
      center: new window.kakao.maps.LatLng(Number(center.mapy), Number(center.mapx)),
      level: 7,
    })
  }
  clusterer?.clear()
  markers.forEach((marker) => marker.setMap(null))
  markers = []
  infoWindow?.close()
  infoWindow = new window.kakao.maps.InfoWindow()
  const bounds = new window.kakao.maps.LatLngBounds()
  const useCluster = props.cluster && window.kakao.maps.MarkerClusterer
  validPlaces.value.forEach((place) => {
    const position = new window.kakao.maps.LatLng(Number(place.mapy), Number(place.mapx))
    const marker = new window.kakao.maps.Marker({ position, ...(useCluster ? {} : { map }) })
    marker.__place = place
    window.kakao.maps.event.addListener(marker, 'click', () => {
      infoWindow.setContent(`<div class="map-label"><b>${escapeHtml(place.title)}</b><small>${escapeHtml(place.category)}</small></div>`)
      infoWindow.open(map, marker)
      emit('select-place', place)
    })
    markers.push(marker)
    bounds.extend(position)
  })
  if (useCluster) {
    if (!clusterer) {
      clusterer = new window.kakao.maps.MarkerClusterer({
        map, averageCenter: true, minLevel: 1, minClusterSize: 2,
        gridSize: 60, disableClickZoom: true, hoverable: true,
        calculator: CLUSTER_CALCULATOR, styles: CLUSTER_STYLES, texts: clusterText,
      })
    }
    clusterer.addMarkers(markers)
    if (!clusterListenerAdded) {
      window.kakao.maps.event.addListener(clusterer, 'clusterclick', (cluster) => {
        setClusterHover(cluster, false)
        const places = cluster.getMarkers().map((marker) => marker.__place).filter(Boolean)
        emit('select-cluster', places)
        map.setLevel(Math.max(map.getLevel() - 2, 1), { anchor: cluster.getCenter() })
      })
      window.kakao.maps.event.addListener(clusterer, 'clusterover', (cluster) => setClusterHover(cluster, true))
      window.kakao.maps.event.addListener(clusterer, 'clusterout', (cluster) => setClusterHover(cluster, false))
      clusterListenerAdded = true
    }
  }
  if (validPlaces.value.length > 1 && props.fitBounds) map.setBounds(bounds)
  else map.setCenter(new window.kakao.maps.LatLng(Number(center.mapy), Number(center.mapx)))
  drawDistricts()
  drawDongGrid()
  window.setTimeout(() => map?.relayout(), 0)
}

async function load() {
  if (!apiKey) {
    status.value = 'missing'
    return
  }
  status.value = 'loading'
  errorMessage.value = ''
  try {
    await loadKakaoSdk(apiKey)
    status.value = 'ready'
    await nextTick()
    draw()
  } catch (error) {
    status.value = 'error'
    errorMessage.value = error.message
  }
}

function retry() {
  resetKakaoSdk()
  load()
}

onMounted(load)
watch(validPlaces, () => nextTick(draw), { deep: true })
watch(() => props.dongFeatures, () => nextTick(drawDongGrid))
watch([() => props.districtFeatures, () => props.districtCongestion], () => nextTick(drawDistricts))
</script>

<template>
  <div class="map-shell" :style="{ height }" role="region" aria-label="서울 관광 장소 지도">
    <div v-if="status === 'missing'" class="map-state">
      <span>MAP SETUP</span>
      <strong>카카오 JavaScript 키가 필요합니다.</strong>
      <small><code>frontend/.env</code>에 <code>VITE_KAKAO_MAP_KEY</code>를 입력하고 개발 서버를 다시 시작해 주세요.</small>
    </div>
    <div v-else-if="status === 'loading'" class="map-state loading-state">
      <i></i><strong>서울 지도를 불러오는 중</strong>
    </div>
    <div v-else-if="status === 'error'" class="map-state error-state">
      <span>MAP AUTH ERROR</span>
      <strong>카카오맵 인증이 거부되었습니다.</strong>
      <small>{{ errorMessage }}</small>
      <ol>
        <li>카카오맵 제품의 <b>사용 설정</b>을 ON으로 변경</li>
        <li><b>JavaScript 키</b>의 SDK 도메인에 <code>{{ currentOrigin }}</code> 등록</li>
        <li>JavaScript 키 확인 후 Vite 개발 서버 재시작</li>
      </ol>
      <button type="button" @click="retry">다시 불러오기</button>
    </div>
    <div
      v-else-if="status === 'ready' && !validPlaces.length && !districtFeatures.length"
      class="map-state"
    >
      <strong>표시할 위치 정보가 없습니다.</strong>
    </div>
    <div :id="mapId" class="map-canvas"></div>
  </div>
</template>

<style scoped>
.map-shell{position:relative;overflow:hidden;border-radius:24px;background:var(--soft);min-height:240px}.map-canvas{width:100%;height:100%}.map-state{position:absolute;inset:0;display:flex;z-index:2;align-items:center;justify-content:center;flex-direction:column;gap:.45rem;padding:1.25rem;background:var(--map-state);color:var(--ink);text-align:center}.map-state>span{letter-spacing:.2em;color:var(--accent);font-size:.7rem;font-weight:800}.map-state small{color:var(--muted);max-width:620px}.map-state code{padding:.08rem .3rem;border-radius:4px;background:var(--overlay)}.map-state ol{margin:.35rem 0;text-align:left;font-size:.78rem;color:var(--muted)}.map-state button{border:0;border-radius:99px;padding:.55rem 1rem;background:var(--ink);color:var(--bg);font-weight:700}.loading-state i{width:28px;height:28px;border:3px solid var(--surface);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite}.error-state{background:var(--map-error)}@keyframes spin{to{transform:rotate(360deg)}}:global(.map-label){display:flex;flex-direction:column;padding:8px 11px;font-size:12px;white-space:nowrap;color:#18231f}:global(.map-label small){color:#68756e;font-size:10px}
:global(.congestion-popup){display:flex;flex-direction:column;gap:2px;padding:8px 11px;border-radius:10px;background:#fff;box-shadow:0 6px 18px rgba(0,0,0,.18);font-size:12px;white-space:nowrap;color:#18231f;pointer-events:none}
:global(.congestion-popup span){font-size:11px;font-weight:800}
:global(.congestion-popup p){margin:2px 0 0;font-size:10px;color:#68756e;white-space:normal;max-width:220px}
</style>
