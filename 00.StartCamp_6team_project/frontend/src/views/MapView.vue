<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { api } from '../api/client'
import AnimatedCounter from '../components/AnimatedCounter.vue'
import CategoryFilter from '../components/CategoryFilter.vue'
import KakaoMap from '../components/KakaoMap.vue'
import { loadDongFeatures } from '../composables/useSeoulGeo'

const category=ref(''), area=ref(''), keyword=ref(''), data=ref({total:0,excluded:0,items:[]}), loading=ref(false), error=ref('')
const selected=ref(null), clusterPlaces=ref([])
const panelPlaces=computed(()=>clusterPlaces.value.length?clusterPlaces.value:selected.value?[selected.value]:data.value.items.slice(0,24))
const panelTitle=computed(()=>clusterPlaces.value.length?`같은 영역의 ${clusterPlaces.value.length}개 장소`:selected.value?'선택한 장소':'전체 장소 미리보기')

const congestion=ref({configured:true,items:[],fetched_at:''}), congestionLoading=ref(false), congestionError=ref('')
const districtFeatures=ref([]), districtCongestion=ref({})
const dongFeatures=ref([]), dongError=ref('')
const showDongGrid=ref(false), showPlaces=ref(true)
const dongFeaturesForMap=computed(()=>showDongGrid.value?dongFeatures.value:[])
const placesForMap=computed(()=>showPlaces.value?data.value.items:[])
const congestionUpdatedAt=computed(()=>congestion.value.fetched_at?new Date(congestion.value.fetched_at).toLocaleTimeString('ko-KR',{hour:'2-digit',minute:'2-digit'}):'')
const LEGEND=[{tone:'calm',emoji:'🟢',label:'여유'},{tone:'normal',emoji:'🟡',label:'보통'},{tone:'busy',emoji:'🟠',label:'약간 붐빔'},{tone:'crowded',emoji:'🔴',label:'붐빔'}]

async function load(){
  loading.value=true;error.value='';selected.value=null;clusterPlaces.value=[]
  try{
    const params=new URLSearchParams()
    if(category.value)params.set('category',category.value)
    if(area.value.trim())params.set('area',area.value.trim())
    if(keyword.value.trim())params.set('keyword',keyword.value.trim())
    const path=`/contents/map?${params}`
    data.value=params.size
      ? await api.get(path)
      : await api.getCached(path,{ttl:30*60*1000,staleTtl:24*60*60*1000})
  }catch(e){error.value=e.message}
  finally{loading.value=false}
}
async function loadCongestion(force=false){
  congestionLoading.value=true;congestionError.value=''
  try{
    const [areas,districts]=await Promise.all([
      api.get(`/realtime/areas/congestion${force?'?refresh=true':''}`),
      api.get(`/geo/seoul-districts/congestion${force?'?refresh=true':''}`),
    ])
    congestion.value=areas
    districtCongestion.value=districts.districts||{}
  }catch(e){congestionError.value=e.message}
  finally{congestionLoading.value=false}
}
async function loadDistrictBoundaries(){try{const d=await api.get('/geo/seoul-districts');districtFeatures.value=d.features||[]}catch{/* boundaries are optional decoration */}}
async function loadDongGrid(){if(dongFeatures.value.length)return;try{dongFeatures.value=await loadDongFeatures()}catch(e){dongError.value=e.message}}
function selectPlace(place){selected.value=place;clusterPlaces.value=[]}
function selectCluster(places){clusterPlaces.value=places;selected.value=null}
function reset(){const categoryChanged=Boolean(category.value);category.value='';area.value='';keyword.value='';if(!categoryChanged)load()}
onMounted(()=>{load();loadCongestion();loadDistrictBoundaries()})
watch(category, load)
watch(showDongGrid, (value)=>{if(value)loadDongGrid()})
</script>

<template>
  <section class="map-page">
    <header class="map-hero"><div><span>SEOUL IN ONE VIEW</span><h1>서울의 모든 장소를 지도 한 장에.</h1></div><p>관광지부터 숙박, 축제까지 좌표가 확인된 전체 데이터를 클러스터로 탐색하세요.</p></header>
    <div class="map-filters"><CategoryFilter v-model="category"/><form @submit.prevent="load"><input v-model="area" placeholder="지역/주소 (예: 마포)"><input v-model="keyword" placeholder="장소명"><button class="btn">지도 검색</button><button type="button" class="reset" @click="reset">초기화</button></form><div class="result-count"><strong><AnimatedCounter :value="data.total" :duration="1050" /></strong><span>PLACES ON MAP</span><small v-if="data.excluded">좌표 오류 {{data.excluded}}건 제외</small></div></div>
    <div class="congestion-bar">
      <label class="congestion-toggle"><input v-model="showPlaces" type="checkbox"> 전체 장소 표시</label>
      <label class="congestion-toggle"><input v-model="showDongGrid" type="checkbox"> 행정동 경계 표시</label>
      <ul class="congestion-legend">
        <li v-for="entry in LEGEND" :key="entry.tone" :class="entry.tone">{{entry.emoji}} {{entry.label}}</li>
      </ul>
      <div class="congestion-status">
        <span v-if="congestionError">{{congestionError}}</span>
        <span v-else-if="dongError">{{dongError}}</span>
        <span v-else-if="congestionLoading">혼잡도 불러오는 중…</span>
        <span v-else-if="congestionUpdatedAt">{{congestionUpdatedAt}} 기준 · {{congestion.items.length}}개 지역 · {{Object.keys(districtCongestion).length}}개 자치구</span>
        <button type="button" :disabled="congestionLoading" @click="loadCongestion(true)">새로고침</button>
      </div>
    </div>
    <p v-if="error" class="map-error">{{error}}</p>
    <div class="map-layout" :class="{loading}">
      <div class="map-stage">
        <KakaoMap
          :places="placesForMap"
          :district-features="districtFeatures"
          :district-congestion="districtCongestion"
          :dong-features="dongFeaturesForMap"
          height="680px"
          cluster
          @select-place="selectPlace"
          @select-cluster="selectCluster"
        />
        <div class="cluster-guide" aria-label="장소 클러스터 색상 안내">
          <span>장소 묶음</span>
          <i class="low" aria-hidden="true">8</i><i class="mid" aria-hidden="true">36</i><i class="high" aria-hidden="true">120</i><i class="dense" aria-hidden="true">500+</i>
          <small>숫자가 클수록 가까이 모인 장소가 많아요</small>
        </div>
      </div>
      <aside class="place-panel"><div class="panel-heading"><span>MAP RESULTS</span><h2>{{panelTitle}}</h2><p v-if="clusterPlaces.length>50">처음 50개만 표시합니다.</p></div><TransitionGroup name="map-place" tag="div" class="panel-list"><RouterLink v-for="place in panelPlaces.slice(0,50)" :key="place.contentid" :to="`/contents/${place.contentid}`" class="map-place"><img v-if="place.firstimage" :src="place.firstimage" :alt="place.title" loading="lazy"><div class="no-image" v-else>SEOUL</div><span><small>{{place.category}}</small><strong>{{place.title}}</strong><p>{{place.addr1||'주소 정보 없음'}}</p></span><b>↗</b></RouterLink></TransitionGroup></aside>
      <div v-if="loading" class="loading-cover"><i></i><strong>장소 데이터를 불러오는 중</strong></div>
    </div>
  </section>
</template>

<style scoped>
.map-page{padding:3.5rem 0}.map-hero{display:flex;align-items:flex-end;justify-content:space-between;gap:2rem;margin-bottom:2rem}.map-hero span,.panel-heading span{font-size:.68rem;letter-spacing:.2em;color:var(--accent);font-weight:800}.map-hero h1{font:clamp(3rem,6vw,5.4rem)/.95 var(--display);letter-spacing:-.05em;margin-top:.8rem}.map-hero>p{max-width:370px;color:var(--muted);padding-bottom:.5rem}.map-filters{position:relative;padding:1rem 180px 1rem 1rem;border:1px solid var(--line);border-radius:20px;background:var(--surface);margin-bottom:1rem}.map-filters form{display:flex;gap:.5rem}.map-filters input{min-width:0;flex:1;border:1px solid var(--line);border-radius:99px;padding:.65rem 1rem;background:var(--input);color:var(--text)}.reset{border:0;background:none;color:var(--muted)}.result-count{position:absolute;right:1.2rem;top:50%;transform:translateY(-50%);display:grid;grid-template-columns:auto 1fr;align-items:center;column-gap:.5rem}.result-count strong{grid-row:1/3;font:2.2rem var(--display)}.result-count span{font-size:.55rem;letter-spacing:.12em}.result-count small{font-size:.58rem;color:var(--muted)}.map-layout{position:relative;display:grid;grid-template-columns:minmax(0,1fr) 350px;gap:1rem}.place-panel{height:680px;border:1px solid var(--line);border-radius:24px;background:var(--surface);overflow:hidden;display:flex;flex-direction:column}.panel-heading{padding:1.2rem;border-bottom:1px solid var(--line)}.panel-heading h2{font:1.6rem var(--display)}.panel-heading p{font-size:.65rem;color:var(--muted)}.panel-list{overflow:auto;padding:.5rem}.map-place{display:grid;grid-template-columns:58px 1fr auto;align-items:center;gap:.65rem;padding:.6rem;text-decoration:none;border-bottom:1px solid var(--line)}.map-place:hover{background:var(--soft)}.map-place img,.no-image{width:58px;height:58px;border-radius:9px;object-fit:cover}.no-image{display:grid;place-items:center;background:var(--soft);font-size:.52rem;letter-spacing:.1em;color:var(--muted)}.map-place>span{display:flex;flex-direction:column;min-width:0}.map-place small{font-size:.58rem;color:var(--accent)}.map-place strong,.map-place p{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.map-place strong{font-size:.8rem}.map-place p{font-size:.62rem;color:var(--muted)}.map-place>b{color:var(--accent)}.loading-cover{position:absolute;inset:0;z-index:8;border-radius:24px;background:var(--overlay);backdrop-filter:blur(8px);display:flex;gap:.7rem;align-items:center;justify-content:center}.loading-cover i{width:24px;height:24px;border:3px solid var(--line);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite}.map-error{color:var(--danger);margin-bottom:1rem}@keyframes spin{to{transform:rotate(360deg)}}@media(max-width:950px){.map-hero{display:block}.map-hero>p{margin-top:1rem}.map-layout{grid-template-columns:1fr}.place-panel{height:400px}.map-filters{padding-right:1rem}.result-count{position:static;transform:none;margin-top:1rem}}@media(max-width:620px){.map-page{padding:2rem 0}.map-filters form{flex-direction:column}.map-hero h1{font-size:3.2rem}}
.congestion-bar{display:flex;flex-wrap:wrap;align-items:center;gap:.9rem;padding:.7rem 1rem;border:1px solid var(--line);border-radius:16px;background:var(--surface);margin-bottom:1rem;font-size:.75rem}.congestion-toggle{display:flex;align-items:center;gap:.4rem;font-weight:700;cursor:pointer}.congestion-legend{display:flex;flex-wrap:wrap;gap:.6rem;list-style:none;padding:0;margin:0;color:var(--muted)}.congestion-status{display:flex;align-items:center;gap:.6rem;margin-left:auto;color:var(--muted)}.congestion-status button{border:1px solid var(--line);border-radius:99px;padding:.3rem .7rem;background:none;color:var(--text);font-size:.72rem}.congestion-status button:disabled{opacity:.5}@media(max-width:620px){.congestion-bar{flex-direction:column;align-items:flex-start}.congestion-status{margin-left:0}}
</style>

<style scoped>
.map-hero>div{min-width:0}.map-hero h1{max-width:760px;font-size:clamp(2.45rem,4.8vw,4.25rem);line-height:1.12;letter-spacing:-.04em}@media(max-width:620px){.map-hero h1{font-size:clamp(2.25rem,9vw,3rem);line-height:1.16}}
.map-stage{position:relative;min-width:0}
.cluster-guide{position:absolute;left:14px;bottom:14px;z-index:7;display:flex;align-items:center;gap:.35rem;padding:.45rem .55rem;border:1px solid color-mix(in srgb,var(--line) 75%,transparent);border-radius:14px;background:var(--overlay);box-shadow:0 10px 28px color-mix(in srgb,var(--ink) 12%,transparent);backdrop-filter:blur(12px);color:var(--muted);pointer-events:none}
.cluster-guide>span{margin-right:.15rem;color:var(--text);font-size:.72rem;font-weight:800}
.cluster-guide i{display:grid;min-width:26px;height:26px;padding:0 .25rem;place-items:center;border:1px solid var(--cluster-border);border-radius:8px 8px 4px 8px;font-style:normal;font-size:.6rem;font-weight:800;font-variant-numeric:tabular-nums}
.cluster-guide .low{background:var(--cluster-low);color:var(--cluster-low-text)}
.cluster-guide .mid{background:var(--cluster-mid);color:var(--cluster-mid-text)}
.cluster-guide .high{background:var(--cluster-high);color:var(--cluster-on-strong)}
.cluster-guide .dense{background:var(--cluster-dense);color:var(--cluster-on-strong)}
.cluster-guide small{margin-left:.15rem;font-size:.66rem}
.congestion-bar{font-size:.84rem}.congestion-status button{font-size:.8rem}.result-count span{font-size:.68rem}.result-count small{font-size:.68rem}.panel-heading span{font-size:.76rem}.panel-heading p{font-size:.74rem}.map-place small{font-size:.68rem}.map-place strong{font-size:.9rem}.map-place p{font-size:.72rem}
.map-place{transition:transform var(--motion-fast) var(--ease-out),background var(--motion-fast),opacity var(--motion-fast)}
.map-place:active{transform:translate3d(2px,0,0) scale(.99)}
.map-place-enter-active,.map-place-leave-active,.map-place-move{transition:transform var(--motion-base) var(--ease-out),opacity var(--motion-fast)}
.map-place-enter-from,.map-place-leave-to{opacity:0;transform:translate3d(12px,0,0)}
@media(hover:hover) and (pointer:fine){.map-place:hover{transform:translate3d(4px,0,0)}}
@media(max-width:720px){.cluster-guide small{display:none}}
@media(max-width:420px){.cluster-guide>span{display:none}.cluster-guide{left:9px;bottom:9px}}
</style>
