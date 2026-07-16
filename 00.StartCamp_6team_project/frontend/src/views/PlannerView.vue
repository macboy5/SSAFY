<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AnimatedCounter from '../components/AnimatedCounter.vue'
import KakaoMap from '../components/KakaoMap.vue'
import PlacePicker from '../components/PlacePicker.vue'
import { usePlannerStore } from '../stores/planner'

const planner = usePlannerStore()
const route = useRoute()
const now = new Date()
const cursor = ref(new Date(now.getFullYear(), now.getMonth(), 1))
const selected = ref(toKey(now))
const editing = ref(null)
const draft = ref({ plan_date: '', visit_time: '', memo: '' })
const addingPlace = ref(false)
const placeFeedback = ref({ type: '', message: '' })
const placePickerKey = ref(0)
const weekdays = ['일', '월', '화', '수', '목', '금', '토']

function toKey(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function fromKey(key) {
  const [year, month, day] = key.split('-').map(Number)
  return new Date(year, month - 1, day)
}

const todayKey = toKey(now)
const title = computed(() => `${cursor.value.getFullYear()}년 ${cursor.value.getMonth() + 1}월`)
const itemsByDate = computed(() => {
  const result = new Map()
  for (const item of planner.items) {
    const items = result.get(item.plan_date) || []
    items.push(item)
    result.set(item.plan_date, items)
  }
  for (const items of result.values()) {
    items.sort((a, b) => {
      const timeOrder = (a.visit_time || '99:99').localeCompare(b.visit_time || '99:99')
      return timeOrder || a.sort_order - b.sort_order
    })
  }
  return result
})
const cells = computed(() => {
  const year = cursor.value.getFullYear()
  const month = cursor.value.getMonth()
  const first = new Date(year, month, 1 - new Date(year, month, 1).getDay())
  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(first)
    date.setDate(first.getDate() + index)
    const key = toKey(date)
    const items = itemsByDate.value.get(key) || []
    return {
      key,
      date,
      day: date.getDate(),
      current: date.getMonth() === month,
      items,
      recordable: key < todayKey && items.length >= 2,
    }
  })
})
const calendarRows = computed(() => Array.from({ length: 6 }, (_, index) => cells.value.slice(index * 7, index * 7 + 7)))
const selectedItems = computed(() => itemsByDate.value.get(selected.value) || [])
const mapPlaces = computed(() => selectedItems.value.map((item) => item.content))
const plannedDays = computed(() => new Set(planner.items.map((item) => item.plan_date)).size)
const isSelectedPast = computed(() => selected.value < todayKey)
const isSelectedToday = computed(() => selected.value === todayKey)
const canRecordCourse = computed(() => isSelectedPast.value && selectedItems.value.length >= 2)
const courseRecordRoute = computed(() => ({
  name: 'post-new',
  query: { type: 'course', date: selected.value, from: 'planner' },
}))
watch(selected, () => {
  placeFeedback.value = { type: '', message: '' }
  placePickerKey.value += 1
})
const selectedLabel = computed(() => new Intl.DateTimeFormat('ko-KR', { month: 'long', day: 'numeric', weekday: 'long' }).format(fromKey(selected.value)))
const selectedFullLabel = computed(() => new Intl.DateTimeFormat('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }).format(fromKey(selected.value)))
const monthPicker = computed({
  get: () => `${cursor.value.getFullYear()}-${String(cursor.value.getMonth() + 1).padStart(2, '0')}`,
  set: (value) => {
    if (!value) return
    const [year, month] = value.split('-').map(Number)
    const preferredDay = fromKey(selected.value).getDate()
    const lastDay = new Date(year, month, 0).getDate()
    cursor.value = new Date(year, month - 1, 1)
    selected.value = toKey(new Date(year, month - 1, Math.min(preferredDay, lastDay)))
    focusSelected()
  },
})
const datePicker = computed({
  get: () => selected.value,
  set: (value) => {
    if (!value) return
    const date = fromKey(value)
    selected.value = value
    cursor.value = new Date(date.getFullYear(), date.getMonth(), 1)
    focusSelected()
  },
})

function moveMonth(delta) {
  const target = new Date(cursor.value.getFullYear(), cursor.value.getMonth() + delta, 1)
  const preferredDay = fromKey(selected.value).getDate()
  const lastDay = new Date(target.getFullYear(), target.getMonth() + 1, 0).getDate()
  cursor.value = target
  selected.value = toKey(new Date(target.getFullYear(), target.getMonth(), Math.min(preferredDay, lastDay)))
}

function choose(cell) {
  selected.value = cell.key
  if (!cell.current) cursor.value = new Date(cell.date.getFullYear(), cell.date.getMonth(), 1)
}

function goToday() {
  cursor.value = new Date(now.getFullYear(), now.getMonth(), 1)
  selected.value = todayKey
  focusSelected()
}

async function focusSelected() {
  await nextTick()
  document.querySelector(`[data-date="${selected.value}"]`)?.focus()
}

function moveSelection(days) {
  const date = fromKey(selected.value)
  date.setDate(date.getDate() + days)
  selected.value = toKey(date)
  cursor.value = new Date(date.getFullYear(), date.getMonth(), 1)
  focusSelected()
}

function onDateKeydown(event, cell) {
  const actions = {
    ArrowLeft: () => moveSelection(-1),
    ArrowRight: () => moveSelection(1),
    ArrowUp: () => moveSelection(-7),
    ArrowDown: () => moveSelection(7),
    Home: () => moveSelection(-cell.date.getDay()),
    End: () => moveSelection(6 - cell.date.getDay()),
    PageUp: () => { moveMonth(-1); focusSelected() },
    PageDown: () => { moveMonth(1); focusSelected() },
  }
  if (!actions[event.key]) return
  event.preventDefault()
  actions[event.key]()
}

function dateAriaLabel(cell) {
  const date = new Intl.DateTimeFormat('ko-KR', { month: 'long', day: 'numeric', weekday: 'long' }).format(cell.date)
  return `${date}${cell.key === todayKey ? ', 오늘' : ''}, 일정 ${cell.items.length}개`
}

function categoryClass(category = '') {
  if (category.includes('축제') || category.includes('공연')) return 'coral'
  if (category.includes('음식') || category.includes('쇼핑')) return 'gold'
  if (category.includes('숙박')) return 'blue'
  return 'green'
}

function openEdit(item) {
  editing.value = item
  draft.value = { plan_date: item.plan_date, visit_time: item.visit_time, memo: item.memo }
}

function closeEdit() {
  editing.value = null
}

async function saveEdit() {
  const date = draft.value.plan_date
  await planner.updateItem(editing.value, { ...draft.value })
  selected.value = date
  cursor.value = new Date(fromKey(date).getFullYear(), fromKey(date).getMonth(), 1)
  closeEdit()
}

async function remove(item) {
  if (confirm(`‘${item.content.title}’ 일정을 삭제할까요?`)) await planner.removeItem(item)
}

async function addPlaceToSelectedDate(place) {
  if (!place || addingPlace.value) return
  if (selectedItems.value.some((item) => item.content.contentid === place.contentid)) {
    placeFeedback.value = { type: 'error', message: '이미 이 날짜에 담긴 장소예요.' }
    return
  }

  addingPlace.value = true
  placeFeedback.value = { type: '', message: '' }
  try {
    await planner.addItem(selected.value, place)
    placePickerKey.value += 1
    placeFeedback.value = { type: 'success', message: `‘${place.title}’을 이 날짜에 담았어요.` }
  } catch (error) {
    placeFeedback.value = { type: 'error', message: error.message }
  } finally {
    addingPlace.value = false
  }
}

onMounted(() => {
  if (!planner.ready) planner.load()
})
</script>

<template>
  <section class="planner-page">
    <header class="planner-hero">
      <div>
        <span class="eyebrow">MY SEOUL JOURNEY</span>
        <h1>서울의 하루를 <i>달력 위에.</i></h1>
        <p>마음에 든 장소를 날짜별로 모으고, 시간과 메모를 더해 오늘의 흐름을 완성하세요.</p>
      </div>
      <div class="summary-cards" aria-label="플래너 요약">
        <div><span>저장한 장소</span><strong><AnimatedCounter :value="planner.items.length" :duration="900" /></strong><small>PLACES</small></div>
        <div><span>일정이 있는 날</span><strong><AnimatedCounter :value="plannedDays" :duration="900" :delay="100" /></strong><small>DAYS</small></div>
      </div>
    </header>

    <section v-if="route.query.guide === 'course'" class="course-flow-guide" aria-label="하루 코스 만드는 방법">
      <div><span>HOW IT WORKS</span><strong>Planner에서 하루 코스를 준비해요.</strong></div>
      <ol>
        <li><b>01</b><span>여행할 날짜를 선택해요.</span></li>
        <li><b>02</b><span>방문할 장소를 순서대로 담아요.</span></li>
        <li><b>03</b><span>여행을 마치면 코스 기록 버튼이 열려요.</span></li>
      </ol>
    </section>

    <p v-if="planner.error" class="notice error" role="alert">{{ planner.error }}</p>
    <p v-else-if="planner.loading" class="notice" role="status">저장된 서울 일정을 불러오고 있어요…</p>

    <div class="planner-layout">
      <section v-reveal class="calendar-card" aria-labelledby="calendar-title">
        <div class="calendar-nav">
          <div class="month-stepper">
            <button type="button" aria-label="이전 달" @click="moveMonth(-1)">←</button>
            <div class="month-heading"><span>MONTHLY PLAN</span><h2 id="calendar-title">{{ title }}</h2></div>
            <button type="button" aria-label="다음 달" @click="moveMonth(1)">→</button>
          </div>
          <div class="calendar-jump" aria-label="날짜 바로가기">
            <label>
              <span>월 선택</span>
              <input v-model="monthPicker" type="month" aria-label="표시할 월 선택">
            </label>
            <label>
              <span>날짜 바로가기</span>
              <input v-model="datePicker" type="date" :aria-label="`이동할 날짜 선택, 현재 ${selectedFullLabel}`">
            </label>
          </div>
          <button type="button" class="today-button" @click="goToday">오늘로 이동</button>
        </div>
        <div class="weekdays" role="row">
          <span v-for="day in weekdays" :key="day" role="columnheader">{{ day }}</span>
        </div>
        <div class="calendar-grid" role="grid" :aria-label="`${title} 여행 일정`">
          <div v-for="(row, rowIndex) in calendarRows" :key="rowIndex" class="calendar-row" role="row">
            <button
              v-for="cell in row"
              :key="cell.key"
              class="date-cell"
              :class="{ dim: !cell.current, selected: selected === cell.key, today: cell.key === todayKey, planned: cell.items.length }"
              type="button"
              role="gridcell"
              :data-date="cell.key"
              :aria-label="dateAriaLabel(cell)"
              :aria-selected="selected === cell.key"
              :aria-current="cell.key === todayKey ? 'date' : undefined"
              :tabindex="selected === cell.key ? 0 : -1"
              @click="choose(cell)"
              @keydown="onDateKeydown($event, cell)"
            >
              <span class="day-number">{{ cell.day }}</span>
              <span v-for="item in cell.items.slice(0, 2)" :key="item.id" class="event-chip" :class="categoryClass(item.content.category)">
                <time>{{ item.visit_time || '여행' }}</time><b>{{ item.content.title }}</b>
              </span>
              <small v-if="cell.items.length > 2">+{{ cell.items.length - 2 }}개 더보기</small>
              <span v-if="cell.recordable" class="record-ready">기록 가능</span>
            </button>
          </div>
        </div>
        <div class="calendar-legend"><span><i class="green" /> 관광</span><span><i class="coral" /> 축제·공연</span><span><i class="gold" /> 음식·쇼핑</span><span><i class="blue" /> 숙박</span></div>
      </section>

      <aside v-reveal="1" class="agenda" aria-labelledby="agenda-title">
        <div class="agenda-title">
          <span>SELECTED DATE</span>
          <h2 id="agenda-title">{{ selectedLabel }}</h2>
          <p>{{ selectedItems.length ? `${selectedItems.length}곳을 만나는 날` : '아직 여백이 있는 하루' }}</p>
        </div>
        <Transition name="course-ready">
          <section
            v-if="selectedItems.length >= 2"
            class="course-record-card"
            :class="{ ready: canRecordCourse, locked: !canRecordCourse }"
            aria-live="polite"
          >
            <div>
              <span>{{ canRecordCourse ? 'TRIP COMPLETE' : 'UPCOMING COURSE' }}</span>
              <strong>{{ canRecordCourse ? '이 일정으로 여행 코스 후기를 작성해요.' : '여행을 다녀온 뒤 후기를 작성할 수 있어요.' }}</strong>
              <p>{{ canRecordCourse ? `아래 ${selectedItems.length}곳과 표시된 순서를 그대로 불러옵니다.` : isSelectedToday ? '오늘 일정은 하루가 지난 뒤 기록 버튼이 열려요.' : `${selectedLabel} 일정은 아직 여행 전이에요.` }}</p>
            </div>
            <RouterLink v-if="canRecordCourse" :to="courseRecordRoute">선택한 코스로 후기 작성하기 →</RouterLink>
            <div v-else class="course-record-lock"><i aria-hidden="true">◇</i><span>여행 완료 후 작성 가능</span></div>
          </section>
        </Transition>
        <div v-if="!selectedItems.length" class="empty-agenda">
          <i aria-hidden="true">＋</i><strong>이 날의 첫 장소를 골라볼까요?</strong>
          <p>장소를 검색해 이 날짜의 동선을 바로 만들어 보세요.</p>
          <div class="agenda-place-picker">
            <PlacePicker
              :key="placePickerKey"
              :model-value="null"
              :disabled="addingPlace"
              placeholder="이 날짜에 담을 장소 검색"
              helper="장소 이름을 두 글자 이상 입력해 주세요."
              @update:model-value="addPlaceToSelectedDate"
            />
          </div>
          <RouterLink class="browse-link" to="/">장소 목록에서 천천히 둘러보기 →</RouterLink>
        </div>
        <template v-else>
          <TransitionGroup tag="ol" name="agenda" class="agenda-list">
            <li
              v-for="(item, index) in selectedItems"
              :key="item.id"
              class="agenda-item"
            >
              <div class="timeline-mark"><time>{{ item.visit_time || '미정' }}</time><i /></div>
              <RouterLink
                class="agenda-place-link"
                :to="`/contents/${item.content.contentid}`"
                :aria-label="`${item.content.title} 상세 보기`"
              >
                <article>
                  <img v-if="item.content.firstimage" :src="item.content.firstimage" :alt="item.content.title">
                  <div v-else class="agenda-fallback">SEOUL</div>
                  <div class="agenda-copy"><span>{{ item.content.category }}</span><h3>{{ item.content.title }}</h3><p>{{ item.memo || '메모를 남겨두면 여행 날 더 편해요.' }}</p></div>
                  <b class="order">{{ String(index + 1).padStart(2, '0') }}</b>
                  <span class="open-hint" aria-hidden="true">↗</span>
                </article>
              </RouterLink>
              <div class="agenda-actions" @click.stop>
                <button type="button" :aria-label="`${item.content.title} 일정 수정`" @click.stop="openEdit(item)">수정</button>
                <button type="button" class="delete" :aria-label="`${item.content.title} 일정 삭제`" @click.stop="remove(item)">삭제</button>
              </div>
            </li>
          </TransitionGroup>

          <details class="agenda-add-place">
            <summary><span aria-hidden="true">＋</span> 이 날짜에 장소 더 담기</summary>
            <div class="agenda-place-picker">
              <PlacePicker
                :key="placePickerKey"
                :model-value="null"
                :disabled="addingPlace"
                placeholder="다음 장소 검색"
                helper="방문할 장소를 이어서 담아보세요."
                @update:model-value="addPlaceToSelectedDate"
              />
            </div>
          </details>

        </template>

        <p v-if="placeFeedback.message" class="place-feedback" :class="placeFeedback.type" role="status">
          {{ placeFeedback.message }}
        </p>
      </aside>
    </div>

    <section v-reveal class="map-section">
      <div><span class="eyebrow">ROUTE AT A GLANCE</span><h2>{{ selectedLabel }}의 장소를 지도에서</h2><p v-if="mapPlaces.length">{{ mapPlaces.length }}개 장소의 위치를 한눈에 확인하세요.</p></div>
      <KakaoMap :places="mapPlaces" height="430px" />
    </section>

    <div v-if="editing" class="modal-backdrop" @click.self="closeEdit" @keydown.esc="closeEdit">
      <form class="edit-modal" role="dialog" aria-modal="true" aria-labelledby="edit-title" @submit.prevent="saveEdit">
        <button type="button" class="modal-close" aria-label="편집 창 닫기" @click="closeEdit">×</button>
        <span class="eyebrow">EDIT SCHEDULE</span><h2 id="edit-title">{{ editing.content.title }}</h2>
        <label>날짜<input v-model="draft.plan_date" type="date" required></label>
        <label>방문 시간<input v-model="draft.visit_time" type="time"></label>
        <label>메모<textarea v-model="draft.memo" maxlength="500" placeholder="예약 정보나 하고 싶은 일을 적어두세요." /></label>
        <div class="modal-actions"><button type="button" class="btn btn-ghost" @click="closeEdit">취소</button><button class="btn">변경사항 저장</button></div>
      </form>
    </div>
  </section>
</template>

<style scoped>
.planner-page{padding-bottom:3rem}.eyebrow,.agenda-title>span,.calendar-nav>div>span{font-size:.66rem;font-weight:800;letter-spacing:.2em;color:var(--accent)}.planner-hero{display:grid;grid-template-columns:1fr auto;align-items:end;gap:3rem;padding:clamp(3rem,7vw,6rem) 0 2.5rem}.planner-hero h1{margin:.7rem 0 1rem;font:clamp(3.3rem,7vw,6.8rem)/.9 var(--display);letter-spacing:-.06em}.planner-hero h1 i{color:var(--primary);font-weight:600}.planner-hero p{max-width:580px;color:var(--muted)}.summary-cards{display:grid;grid-template-columns:repeat(2,150px);gap:.65rem}.summary-cards>div{position:relative;overflow:hidden;padding:1rem;border:1px solid var(--line);border-radius:22px;background:var(--surface);box-shadow:var(--shadow)}.summary-cards>div:after{content:'';position:absolute;right:-25px;bottom:-38px;width:85px;height:85px;border-radius:50%;background:color-mix(in srgb,var(--primary) 10%,transparent)}.summary-cards span{display:block;color:var(--muted);font-size:.68rem}.summary-cards strong{font:2.7rem var(--display)}.summary-cards small{margin-left:.35rem;color:var(--accent);font-size:.55rem;letter-spacing:.1em}.notice{margin-bottom:1rem;color:var(--muted)}.notice.error{color:var(--danger)}.planner-layout{display:grid;grid-template-columns:minmax(0,1.65fr) minmax(320px,.75fr);align-items:start;gap:1.2rem}.calendar-card,.agenda{border:1px solid var(--line);border-radius:28px;background:var(--surface);box-shadow:var(--shadow)}.calendar-card{padding:1.2rem}.calendar-nav{display:grid;grid-template-columns:auto 1fr auto auto;align-items:center;gap:.55rem;margin-bottom:1rem}.calendar-nav>div{text-align:center}.calendar-nav h2{font:1.75rem var(--display)}.calendar-nav>button{display:grid;place-items:center;width:40px;height:40px;border:1px solid var(--line);border-radius:50%;background:var(--soft);color:var(--text);font-weight:800;transition:.2s}.calendar-nav>button:hover{transform:translateY(-2px);border-color:var(--primary);color:var(--primary)}.calendar-nav .today-button{width:auto;padding:0 .8rem;border-radius:99px;font-size:.68rem}.weekdays,.calendar-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr))}.weekdays span{text-align:center;padding:.5rem;color:var(--muted);font-size:.66rem;font-weight:700}.weekdays span:first-child{color:var(--accent)}.calendar-row{display:contents}.date-cell{position:relative;min-width:0;min-height:116px;padding:.55rem;border:0;border-top:1px solid var(--line);border-right:1px solid var(--line);background:transparent;color:var(--text);text-align:left;overflow:hidden;transition:background .18s,box-shadow .18s}.date-cell:nth-child(7n){border-right:0}.date-cell:hover{background:color-mix(in srgb,var(--soft) 65%,transparent)}.date-cell.selected{z-index:1;background:color-mix(in srgb,var(--primary) 8%,var(--surface));box-shadow:inset 0 0 0 2px var(--primary)}.date-cell.dim{background:color-mix(in srgb,var(--soft) 40%,transparent);color:var(--muted)}.day-number{display:grid;place-items:center;width:25px;height:25px;margin-bottom:.28rem;border-radius:50%;font-size:.72rem;font-weight:800}.date-cell.today .day-number{background:var(--accent);color:white}.event-chip{display:flex;align-items:center;gap:.25rem;margin:.22rem 0;padding:.22rem .3rem;border-left:3px solid var(--primary);border-radius:4px;background:var(--soft);font-size:.57rem;line-height:1.35;overflow:hidden}.event-chip time{color:var(--muted)}.event-chip b{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.event-chip.green{border-color:#2c9670}.event-chip.coral{border-color:#e4664c}.event-chip.gold{border-color:#d1a42d}.event-chip.blue{border-color:#4c83b8}.date-cell>small{display:block;margin-top:.2rem;color:var(--primary);font-size:.55rem}.calendar-legend{display:flex;justify-content:flex-end;gap:.8rem;flex-wrap:wrap;padding-top:.8rem;color:var(--muted);font-size:.57rem}.calendar-legend span{display:flex;align-items:center;gap:.25rem}.calendar-legend i{width:6px;height:6px;border-radius:50%;background:#2c9670}.calendar-legend i.coral{background:#e4664c}.calendar-legend i.gold{background:#d1a42d}.calendar-legend i.blue{background:#4c83b8}.agenda{position:sticky;top:94px;min-height:560px;padding:1.25rem}.agenda-title{padding:.3rem .2rem 1rem;border-bottom:1px solid var(--line)}.agenda-title h2{margin:.2rem 0;font:2.1rem var(--display)}.agenda-title p{color:var(--muted);font-size:.72rem}.empty-agenda{display:flex;min-height:380px;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:2rem}.empty-agenda i{display:grid;place-items:center;width:48px;height:48px;margin-bottom:1rem;border:1px dashed var(--primary);border-radius:50%;color:var(--primary);font-style:normal;font-size:1.4rem}.empty-agenda strong{font:1.25rem var(--display)}.empty-agenda p{max-width:230px;margin:.45rem 0 1rem;color:var(--muted);font-size:.72rem}.empty-agenda a{color:var(--primary);font-size:.72rem;font-weight:800}.agenda-list{list-style:none;padding:0;margin:0}.agenda-item{display:grid;grid-template-columns:52px 1fr;padding-top:1rem}.timeline-mark{display:flex;flex-direction:column;align-items:center}.timeline-mark time{padding:.22rem .35rem;border-radius:99px;background:var(--ink);color:var(--bg);font-size:.56rem;font-weight:800}.timeline-mark i{flex:1;width:1px;margin-top:.35rem;background:var(--line)}.agenda-item article{position:relative;display:grid;grid-template-columns:62px 1fr;gap:.65rem;padding:.65rem;border:1px solid var(--line);border-radius:16px;background:var(--bg)}.agenda-item article img,.agenda-fallback{width:62px;height:68px;border-radius:11px;object-fit:cover}.agenda-fallback{display:grid;place-items:center;background:var(--soft);color:var(--muted);font-size:.5rem}.agenda-copy{min-width:0}.agenda-copy span{color:var(--accent);font-size:.55rem;font-weight:800}.agenda-copy h3{font-size:.87rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.agenda-copy p{margin-top:.2rem;color:var(--muted);font-size:.62rem;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.order{position:absolute;right:.55rem;top:.35rem;color:color-mix(in srgb,var(--ink) 13%,transparent);font:1.4rem var(--display)}.agenda-actions{grid-column:2;display:flex;justify-content:flex-end;gap:.35rem;padding:.35rem 0 .75rem}.agenda-actions a,.agenda-actions button{padding:.22rem .42rem;border:0;border-radius:6px;background:var(--soft);color:var(--text);font-size:.58rem;text-decoration:none}.agenda-actions .delete{color:var(--danger)}.agenda-enter-active,.agenda-leave-active{transition:.25s}.agenda-enter-from,.agenda-leave-to{opacity:0;transform:translateY(8px)}.map-section{margin-top:4rem}.map-section>div:first-child{margin-bottom:1rem}.map-section h2{margin:.3rem 0;font:clamp(2rem,4vw,3.2rem) var(--display)}.map-section p{color:var(--muted);font-size:.8rem}.modal-backdrop{position:fixed;inset:0;z-index:40;display:grid;place-items:center;padding:1rem;background:rgba(9,18,16,.72);backdrop-filter:blur(8px)}.edit-modal{position:relative;display:flex;width:min(460px,100%);flex-direction:column;gap:1rem;padding:2rem;border:1px solid var(--line);border-radius:25px;background:var(--surface);box-shadow:0 28px 90px rgba(0,0,0,.3)}.edit-modal h2{font:2rem var(--display)}.edit-modal label{display:flex;flex-direction:column;gap:.35rem;font-size:.72rem;font-weight:800}.edit-modal input,.edit-modal textarea{padding:.75rem;border:1px solid var(--line);border-radius:11px;background:var(--input);color:var(--text)}.edit-modal textarea{min-height:110px;resize:vertical}.modal-close{position:absolute;right:1rem;top:1rem;border:0;background:none;color:var(--muted);font-size:1.4rem}.modal-actions{display:flex;justify-content:flex-end;gap:.5rem}@media(max-width:1050px){.planner-layout{grid-template-columns:1fr}.agenda{position:static;min-height:0}.summary-cards{grid-template-columns:repeat(2,130px)}}@media(max-width:680px){.planner-hero{grid-template-columns:1fr;padding-top:2.5rem}.summary-cards{grid-template-columns:repeat(2,1fr)}.planner-hero h1{font-size:clamp(3.3rem,15vw,5.5rem)}.calendar-card{padding:.45rem;border-radius:18px}.calendar-nav{padding:.45rem}.calendar-nav h2{font-size:1.25rem}.calendar-nav>div>span,.calendar-legend{display:none}.date-cell{min-height:72px;padding:.3rem}.event-chip{height:5px;padding:0;border:0;border-radius:8px;font-size:0;background:var(--primary)}.event-chip.coral{background:#e4664c}.event-chip.gold{background:#d1a42d}.event-chip.blue{background:#4c83b8}.date-cell>small{font-size:.5rem}.day-number{width:23px;height:23px}.map-section{margin-top:3rem}}@media(max-width:430px){.calendar-nav{grid-template-columns:auto 1fr auto}.calendar-nav .today-button{display:none}.summary-cards>div{padding:.8rem}.summary-cards strong{font-size:2.2rem}}
</style>

<style scoped>
.planner-hero h1 {
  max-width: 680px;
  font-size: clamp(2.65rem, 5.1vw, 4.9rem);
  line-height: 1.1;
  letter-spacing: -.045em;
}

.course-flow-guide {
  display: grid;
  grid-template-columns: minmax(220px, .75fr) minmax(0, 1.4fr);
  align-items: center;
  gap: 1.5rem;
  margin: -1rem 0 1.5rem;
  padding: 1rem 1.15rem;
  border: 1px solid color-mix(in srgb, var(--accent) 25%, var(--line));
  border-radius: 12px 22px 12px 12px;
  background:
    radial-gradient(circle at 0 50%, color-mix(in srgb, var(--accent) 9%, transparent), transparent 34%),
    var(--surface);
  animation: course-guide-in .5s var(--ease-out) both;
}

.course-flow-guide > div {
  display: grid;
  gap: .2rem;
}

.course-flow-guide > div span {
  color: var(--accent);
  font-size: .58rem;
  font-weight: 850;
  letter-spacing: .14em;
}

.course-flow-guide > div strong {
  font-family: var(--display);
  font-size: 1.08rem;
}

.course-flow-guide ol {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: .45rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.course-flow-guide li {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: .45rem;
  color: var(--muted);
  font-size: .68rem;
}

.course-flow-guide li b {
  color: var(--accent);
  font-size: .56rem;
  font-variant-numeric: tabular-nums;
}

@keyframes course-guide-in {
  from { opacity: 0; transform: translate3d(0, -10px, 0); }
  to { opacity: 1; transform: translate3d(0, 0, 0); }
}

.eyebrow,
.agenda-title > span,
.month-heading > span {
  font-size: .75rem;
}

.calendar-nav {
  grid-template-columns: minmax(250px, 1fr) auto auto;
  gap: .8rem;
}

.month-stepper {
  display: grid;
  grid-template-columns: 40px minmax(140px, 1fr) 40px;
  align-items: center;
  gap: .55rem;
}

.month-heading {
  text-align: center;
}

.month-heading > span {
  color: var(--accent);
  font-weight: 800;
  letter-spacing: .2em;
}

.month-stepper > button {
  display: grid;
  width: 40px;
  height: 40px;
  place-items: center;
  border: 1px solid var(--line);
  border-radius: 50%;
  background: var(--soft);
  color: var(--text);
  font-weight: 800;
  transition: transform .22s ease, border-color .22s ease, color .22s ease, background .22s ease;
}

.month-stepper > button:hover {
  transform: translateY(-2px);
  border-color: var(--primary);
  background: color-mix(in srgb, var(--primary) 7%, var(--soft));
  color: var(--primary);
}

.month-stepper > button:active {
  transform: translateY(0) scale(.96);
}

.month-stepper > button:focus-visible,
.calendar-jump input:focus-visible,
.agenda-place-link:focus-visible,
.agenda-actions button:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--primary) 35%, transparent);
  outline-offset: 3px;
}

.calendar-jump {
  display: grid;
  grid-template-columns: repeat(2, minmax(122px, 1fr));
  gap: .45rem;
  text-align: left;
}

.calendar-jump label {
  display: grid;
  gap: .2rem;
}

.calendar-jump label > span {
  padding-left: .2rem;
  color: var(--muted);
  font-size: .62rem;
  font-weight: 700;
}

.calendar-jump input {
  width: 100%;
  min-width: 0;
  height: 40px;
  padding: 0 .55rem;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: color-mix(in srgb, var(--soft) 72%, var(--surface));
  color: var(--text);
  font: 700 .69rem var(--sans);
  font-variant-numeric: tabular-nums;
  transition: border-color .22s ease, background .22s ease, box-shadow .22s ease;
}

.calendar-jump input:hover {
  border-color: color-mix(in srgb, var(--primary) 55%, var(--line));
  background: var(--surface);
}

.calendar-nav .today-button {
  align-self: end;
  height: 40px;
  padding-inline: .9rem;
  font-size: .72rem;
  white-space: nowrap;
}

.weekdays span {
  font-size: .74rem;
}

.agenda-item {
  border-radius: 18px;
}

.agenda-place-link {
  min-width: 0;
  border-radius: 18px;
  color: inherit;
  text-decoration: none;
  cursor: pointer;
}

.agenda-item article {
  overflow: hidden;
  transition: transform .25s cubic-bezier(.2, .8, .2, 1), border-color .25s ease, box-shadow .25s ease, background .25s ease;
}

.agenda-place-link:hover article,
.agenda-place-link:focus-visible article {
  transform: translateY(-3px);
  border-color: color-mix(in srgb, var(--primary) 42%, var(--line));
  background: color-mix(in srgb, var(--primary) 3%, var(--bg));
  box-shadow: 0 12px 28px color-mix(in srgb, var(--primary) 12%, transparent);
}

.agenda-place-link:active article {
  transform: translateY(-1px) scale(.99);
}

.agenda-copy {
  padding-right: 1.35rem;
}

.open-hint {
  position: absolute;
  right: .65rem;
  bottom: .55rem;
  display: grid;
  width: 22px;
  height: 22px;
  place-items: center;
  border-radius: 7px;
  background: color-mix(in srgb, var(--primary) 10%, var(--soft));
  color: var(--primary);
  font-size: .7rem;
  transition: transform .25s ease, background .25s ease, color .25s ease;
}

.agenda-place-link:hover .open-hint,
.agenda-place-link:focus-visible .open-hint {
  transform: translate(2px, -2px);
  background: var(--primary);
  color: var(--surface);
}

.agenda-actions button {
  min-width: 46px;
  padding: .38rem .58rem;
  font-size: .64rem;
  font-weight: 700;
  cursor: pointer;
  transition: transform .2s ease, background .2s ease, color .2s ease;
}

.agenda-actions button:hover {
  transform: translateY(-1px);
  background: color-mix(in srgb, var(--primary) 10%, var(--soft));
  color: var(--primary);
}

.agenda-actions .delete:hover {
  background: color-mix(in srgb, var(--danger) 10%, var(--soft));
  color: var(--danger);
}

.agenda-actions button:active {
  transform: scale(.96);
}

.record-ready {
  position: absolute;
  right: .38rem;
  bottom: .38rem;
  padding: .18rem .34rem;
  border-radius: 6px;
  background: color-mix(in srgb, var(--accent) 13%, var(--surface));
  color: var(--accent);
  font-size: .5rem;
  font-weight: 850;
  letter-spacing: .02em;
}

.agenda-place-picker {
  position: relative;
  z-index: 4;
  width: 100%;
  text-align: left;
}

.empty-agenda .agenda-place-picker {
  max-width: 310px;
  margin-top: .35rem;
}

.empty-agenda .browse-link {
  margin-top: .8rem;
}

.agenda-place-picker :deep(.picker-message) {
  text-align: left;
}

.agenda-add-place {
  margin: .35rem 0 1rem 52px;
  border-top: 1px solid var(--line);
}

.agenda-add-place summary {
  display: flex;
  align-items: center;
  gap: .45rem;
  padding: .75rem .25rem;
  color: var(--muted);
  font-size: .72rem;
  font-weight: 750;
  cursor: pointer;
  list-style: none;
  transition: color .2s ease, transform .2s ease;
}

.agenda-add-place summary::-webkit-details-marker {
  display: none;
}

.agenda-add-place summary span {
  display: grid;
  width: 22px;
  height: 22px;
  place-items: center;
  border-radius: 7px;
  background: var(--soft);
  color: var(--primary);
}

.agenda-add-place summary:hover {
  transform: translateX(2px);
  color: var(--primary);
}

.agenda-add-place[open] summary {
  color: var(--primary);
}

.agenda-add-place .agenda-place-picker {
  padding: .25rem 0 1rem;
}

.course-record-card {
  display: grid;
  gap: .85rem;
  margin: .85rem 0 1rem;
  padding: 1rem;
  border-left: 3px solid var(--line);
  border-radius: 6px 16px 16px 6px;
  background: color-mix(in srgb, var(--soft) 72%, transparent);
}

.course-record-card.locked {
  border-left-color: color-mix(in srgb, var(--muted) 45%, var(--line));
  background: color-mix(in srgb, var(--soft) 50%, transparent);
}

.course-record-card.ready {
  border-left-color: var(--accent);
  background:
    radial-gradient(circle at 100% 0, color-mix(in srgb, var(--accent) 11%, transparent), transparent 48%),
    color-mix(in srgb, var(--soft) 72%, transparent);
}

.course-record-card div {
  display: grid;
  gap: .22rem;
}

.course-record-card span {
  color: var(--accent);
  font-size: .56rem;
  font-weight: 850;
  letter-spacing: .14em;
}

.course-record-card strong {
  font-family: var(--display);
  font-size: 1.05rem;
  line-height: 1.3;
}

.course-record-card p {
  color: var(--muted);
  font-size: .67rem;
}

.course-record-card a {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: .7rem .8rem;
  border-radius: 10px 15px 7px 10px;
  background: var(--ink);
  color: var(--bg);
  font-size: .72rem;
  font-weight: 800;
  text-decoration: none;
  transition: transform .22s var(--ease-out), box-shadow .22s ease;
}

.course-record-card a:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 22px color-mix(in srgb, var(--ink) 16%, transparent);
}

.course-record-lock {
  display: flex !important;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: .5rem !important;
  padding-top: .65rem;
  border-top: 1px solid var(--line);
  color: var(--muted);
}

.course-record-lock i {
  display: grid;
  width: 24px;
  height: 24px;
  place-items: center;
  border-radius: 7px;
  background: var(--soft);
  color: var(--muted);
  font-style: normal;
}

.course-record-lock span {
  color: var(--muted);
  font-size: .65rem;
  letter-spacing: 0;
}

.place-feedback {
  margin: .75rem 0 0 52px;
  padding: .62rem .75rem;
  border-radius: 9px;
  font-size: .7rem;
}

.place-feedback.success {
  background: color-mix(in srgb, #5f9d75 12%, transparent);
  color: #39744f;
}

.place-feedback.error {
  background: color-mix(in srgb, var(--danger) 10%, transparent);
  color: var(--danger);
}

.course-ready-enter-active,
.course-ready-leave-active {
  transition: opacity .24s ease, transform .28s var(--ease-out);
}

.course-ready-enter-from,
.course-ready-leave-to {
  opacity: 0;
  transform: translate3d(0, 8px, 0);
}

@media (max-width: 1180px) and (min-width: 1051px) {
  .calendar-nav {
    grid-template-columns: 1fr auto;
  }

  .month-stepper {
    grid-column: 1 / -1;
  }
}

@media (max-width: 680px) {
  .planner-hero h1 {
    font-size: clamp(2.4rem, 10vw, 3.8rem);
    line-height: 1.14;
  }

  .course-flow-guide {
    grid-template-columns: 1fr;
    margin-top: -.5rem;
  }

  .course-flow-guide ol {
    grid-template-columns: 1fr;
  }

  .calendar-nav {
    grid-template-columns: 1fr auto;
    padding: .55rem .35rem .7rem;
  }

  .month-stepper {
    grid-column: 1 / -1;
  }

  .month-heading > span {
    display: block;
  }

  .calendar-jump {
    grid-column: 1;
  }

  .calendar-nav .today-button {
    grid-column: 2;
  }

  .record-ready {
    width: 7px;
    height: 7px;
    padding: 0;
    overflow: hidden;
    border-radius: 50%;
    color: transparent;
    background: var(--accent);
  }

  .agenda-add-place,
  .course-record-card,
  .place-feedback {
    margin-left: 0;
  }
}

@media (max-width: 430px) {
  .calendar-nav {
    grid-template-columns: 1fr;
  }

  .month-stepper,
  .calendar-jump,
  .calendar-nav .today-button {
    grid-column: 1;
  }

  .calendar-nav .today-button {
    display: grid;
    width: 100%;
    height: 36px;
  }

  .calendar-jump {
    width: 100%;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .calendar-jump input {
    padding-inline: .35rem;
    font-size: .62rem;
  }
}
</style>
