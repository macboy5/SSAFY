<script setup>
defineProps({
  content: { type: Object, required: true },
  showAdd: { type: Boolean, default: false },
})

defineEmits(['add-to-planner'])
</script>

<template>
  <article class="card interactive-card">
    <RouterLink :to="`/contents/${content.contentid}`" class="card-link">
      <div class="thumb">
        <img v-if="content.firstimage" :src="content.firstimage" :alt="content.title" loading="lazy" />
        <div v-else class="thumb-fallback"><span>SEOUL</span><small>이미지 준비 중</small></div>
        <span class="view-arrow" aria-hidden="true">↗</span>
      </div>
      <div class="body">
        <span class="category">{{ content.category }}</span>
        <h3 class="title">{{ content.title }}</h3>
        <p class="addr">{{ content.addr1 || '주소 정보 없음' }}</p>
      </div>
    </RouterLink>
    <div v-if="showAdd" class="card-actions">
      <button class="add-btn" type="button" @click="$emit('add-to-planner', content)">
        <span aria-hidden="true">＋</span> 플래너에 담기
      </button>
    </div>
  </article>
</template>

<style scoped>
.card{display:flex;flex-direction:column;overflow:hidden;border:1px solid var(--line);border-radius:22px;background:var(--surface);box-shadow:var(--shadow)}.card-link{display:flex;flex:1;flex-direction:column;color:inherit;text-decoration:none}.thumb{position:relative;overflow:hidden;aspect-ratio:4/3;background:var(--soft)}.thumb:after{content:'';position:absolute;inset:45% 0 0;background:linear-gradient(transparent,rgba(8,20,17,.28));opacity:0;transition:opacity .35s}.thumb img{display:block;width:100%;height:100%;object-fit:cover;transition:transform .55s var(--ease-out),filter .55s}.thumb-fallback{width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;background:radial-gradient(circle at 30% 25%,color-mix(in srgb,var(--primary) 18%,transparent),transparent 55%),var(--soft);color:var(--muted)}.thumb-fallback span{font:1.5rem var(--display);letter-spacing:.08em}.thumb-fallback small{font-size:.6rem}.view-arrow{position:absolute;right:.8rem;bottom:.8rem;z-index:1;display:grid;place-items:center;width:38px;height:38px;border-radius:50%;background:var(--overlay);color:var(--ink);backdrop-filter:blur(8px);opacity:0;transform:translateY(8px) rotate(-25deg);transition:.3s var(--ease-out)}.body{padding:1rem 1rem 1.1rem;flex:1}.category{font-size:.66rem;letter-spacing:.08em;color:var(--accent);font-weight:800}.title{margin:.32rem 0;font:1.35rem/1.15 var(--display);letter-spacing:-.025em}.addr{font-size:.72rem;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.card-actions{padding:0 .8rem .8rem}.add-btn{width:100%;padding:.55rem;border:1px solid var(--line);background:var(--soft);color:var(--primary);border-radius:10px;font-size:.72rem;font-weight:800;transition:.2s}.add-btn:hover{border-color:var(--primary);background:var(--primary);color:var(--bg)}@media(hover:hover) and (pointer:fine){.card:hover .thumb img,.card:focus-within .thumb img{transform:scale(1.065);filter:saturate(1.08)}.card:hover .thumb:after,.card:focus-within .thumb:after{opacity:1}.card:hover .view-arrow,.card:focus-within .view-arrow{opacity:1;transform:none}}@media(max-width:520px){.card{border-radius:17px}.body{padding:.8rem}.title{font-size:1.05rem}}
</style>

<style scoped>
.card{border:0;border-radius:24px 24px 14px 24px;box-shadow:inset 0 0 0 1px var(--line),var(--shadow)}
.body{padding:1.1rem 1.1rem 1.25rem}
.category{letter-spacing:.04em}
.title{margin:.38rem 0 .5rem;font-size:clamp(1.22rem,2vw,1.5rem);line-height:1.13}
.view-arrow{border-radius:11px}
.add-btn{min-height:40px;border:0;border-radius:9px}
@media(max-width:520px){.card{border-radius:18px 18px 10px 18px}.body{padding:.85rem}.title{font-size:1.08rem}}
</style>
