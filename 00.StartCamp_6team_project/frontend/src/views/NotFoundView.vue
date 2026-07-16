<template>
  <section class="not-found" aria-labelledby="not-found-title">
    <div class="route-mark" aria-hidden="true"><span>4</span><i /><span>4</span></div>
    <div class="not-found-copy">
      <span>길을 잠깐 벗어났어요</span>
      <h1 id="not-found-title">이 주소에는<br>아직 장소가 없습니다.</h1>
      <p>입력한 주소를 다시 확인하거나 서울의 다른 장소를 둘러보세요.</p>
      <div class="not-found-actions">
        <RouterLink class="btn" to="/">장소 탐색으로 돌아가기</RouterLink>
        <RouterLink to="/map">지도에서 찾아보기 <b>↗</b></RouterLink>
      </div>
    </div>
  </section>
</template>

<style scoped>
.not-found{display:grid;min-height:calc(100dvh - 158px);grid-template-columns:minmax(280px,.8fr) minmax(0,1.2fr);align-items:center;gap:clamp(2rem,8vw,8rem);padding:clamp(3rem,8vw,7rem) 0}
.route-mark{position:relative;display:flex;align-items:center;justify-content:center;gap:.1em;color:color-mix(in srgb,var(--ink) 12%,transparent);font:clamp(8rem,20vw,18rem)/.8 var(--display);letter-spacing:-.09em;user-select:none}
.route-mark i{width:.12em;height:.12em;border-radius:3px;background:var(--accent);box-shadow:0 0 0 .05em color-mix(in srgb,var(--accent) 16%,transparent);transform:translateY(.12em)}
.not-found-copy>span{color:var(--accent);font-size:.68rem;font-weight:800;letter-spacing:.14em}
.not-found h1{margin:.8rem 0 1.2rem;font:clamp(2.8rem,5.5vw,5.8rem)/1 var(--display);letter-spacing:-.055em}
.not-found p{max-width:48ch;color:var(--muted)}
.not-found-actions{display:flex;align-items:center;gap:1rem;margin-top:2rem;flex-wrap:wrap}
.not-found-actions>a:last-child{display:inline-flex;gap:.45rem;color:var(--primary);font-size:.78rem;font-weight:800;text-decoration:none}
.not-found-actions b{transition:transform var(--motion-fast)}
.not-found-actions>a:last-child:hover b{transform:translate(2px,-2px)}
@media(max-width:720px){.not-found{grid-template-columns:1fr;gap:1rem;text-align:center}.route-mark{font-size:clamp(8rem,42vw,13rem)}.not-found p{margin:auto}.not-found-actions{justify-content:center}}
</style>
