<template>
  <section class="list-wrap">
    <header class="list-head">
      <h2>商品列表</h2>
    </header>

    <div class="card-grid">
      <article
        v-for="item in items"
        :key="item.id"
        class="card"
        @mouseenter="focusedId = item.id"
        @mouseleave="focusedId = null"
        @keydown.left.prevent="prev(item)"
        @keydown.right.prevent="next(item)"
        tabindex="0"
      >
        <!-- 圖片輪播 -->
        <div class="viewer">
          <template v-if="item.images && item.images.length">
            <img
              class="viewer-img"
              :src="item.images[item.currentIndex]"
              :alt="`${item.title}-${item.currentIndex+1}`"
              loading="lazy"
              referrerpolicy="no-referrer"
            />

            <!-- 只有多於 1 張時才顯示左右鍵 -->
            <button
              v-if="item.images.length > 1"
              class="nav nav--left"
              type="button"
              aria-label="上一張"
              @click="prev(item)"
            >‹</button>
            <button
              v-if="item.images.length > 1"
              class="nav nav--right"
              type="button"
              aria-label="下一張"
              @click="next(item)"
            >›</button>

            <!-- 只有多於 1 張時才顯示圓點 -->
            <div v-if="item.images.length > 1" class="dots" role="tablist">
              <button
                v-for="(img, idx) in item.images"
                :key="img + idx"
                class="dot"
                :class="{ 'is-active': idx === item.currentIndex }"
                @click="go(item, idx)"
                :aria-label="`第 ${idx+1} 張`"
              />
            </div>
          </template>

          <div v-else class="viewer-empty">
            <span class="emoji">🖼️</span>
            <span class="muted tiny">尚無圖片</span>
          </div>
        </div>

        <!-- 文字資訊 -->
        <div class="body">
          <h3 class="title" :title="item.title">{{ item.title }}</h3>
          <p class="desc">{{ item.description }}</p>

          <div class="meta">
            <div class="price">
              <span class="label">目前價格</span>
              <span class="value">${{ item.current_price ?? item.starting_price }}</span>
            </div>
            <div class="end">
              <span class="label">結束時間</span>
              <span class="value">{{ fmt(item.end_date) }}</span>
            </div>
          </div>
            <div class="flex justify-center items-center w-full">
              <router-link :to="`/sale_item/${item.id}`" class="btn btn--primary">我要出價</router-link>
            </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { ofetch } from 'ofetch'

type SaleItem = {
  id: string
  title: string
  description: string
  starting_price: number
  current_price?: number | null
  end_date: string
  images: string[]
  currentIndex: number
}

const items = ref<SaleItem[]>([])
const focusedId = ref<string | null>(null)

function fmt(iso: string) {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function next(item: SaleItem) {
  if (!item.images.length || item.images.length <= 1) return
  item.currentIndex = (item.currentIndex + 1) % item.images.length
}
function prev(item: SaleItem) {
  if (!item.images.length || item.images.length <= 1) return
  item.currentIndex = (item.currentIndex - 1 + item.images.length) % item.images.length
}
function go(item: SaleItem, idx: number) {
  if (!item.images.length || item.images.length <= 1) return
  item.currentIndex = idx
}

async function load() {
  // 1) 取商品清單
  const list = await ofetch('/api/sale_items') as any[]
  items.value = list.map((raw) => ({
    id: String(raw.id),
    title: raw.title,
    description: raw.description,
    starting_price: Number(raw.starting_price),
    current_price: raw.current_price ?? null,
    end_date: raw.end_date,
    images: [],
    currentIndex: 0,
  }))

  // 2) 取每個商品的多張圖片
  await Promise.all(items.value.map(async (item) => {
    try {
      const res = await ofetch(`/api/sale_item/images/${item.id}?num=10`) as { images: string[] }
      item.images = (res?.images ?? []).filter(Boolean)
      item.currentIndex = 0
    } catch {
      item.images = []
    }
  }))
}

onMounted(load)
</script>

<style scoped>
/* 版心與標題 */
.list-wrap{ width:min(1100px, 95vw); margin:26px auto 80px; }
.list-head h2{ margin:0 0 6px; font-size:24px; }
.muted{ color:#64748b; }
.tiny{ font-size:12px; }

/* 卡片網格 */
.card-grid{
  display:grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap:16px;
  margin-top:14px;
}

.card{
  background:#fff;
  border:1px solid #e6e8eb;
  border-radius:16px;
  overflow:hidden;
  box-shadow:0 6px 18px rgba(2,6,23,.06);
  transition: transform .18s cubic-bezier(.2,.8,.2,1), box-shadow .18s cubic-bezier(.2,.8,.2,1);
  outline:none;
}
.card:hover, .card:focus{
  transform: translateY(-4px);
  box-shadow:0 12px 28px rgba(2,6,23,.10);
}

/* 圖片檢視器 */
.viewer{ position:relative; height:200px; background:#f6f8fb; }
.viewer-img{
  position:absolute; inset:0; width:100%; height:100%;
  object-fit:contain; /* 不裁切，不變形 */
}
.viewer-empty{
  height:100%; display:flex; align-items:center; justify-content:center; gap:8px; flex-direction:column;
}
.viewer-empty .emoji{ font-size:26px; }

/* 導航按鈕（多於 1 張時才會渲染於 DOM，邏輯在 template） */
.nav{
  position:absolute; top:50%; transform:translateY(-50%);
  width:36px; height:36px; border-radius:50%;
  background:#ffffffcc; border:1px solid #e6e8eb;
  display:flex; align-items:center; justify-content:center;
  font-size:20px; font-weight:900; color:#0f172a; cursor:pointer;
  transition: filter .16s ease;
}
.nav:hover{ filter:brightness(.95); }
.nav--left{ left:8px; }
.nav--right{ right:8px; }

/* 圓點指示器（多於 1 張時才會渲染於 DOM） */
.dots{
  position:absolute; bottom:8px; left:0; right:0;
  display:flex; gap:6px; justify-content:center;
}
.dot{
  width:8px; height:8px; border-radius:50%;
  border:1px solid #b5c3e8; background:#fff; opacity:.7; cursor:pointer;
}
.dot.is-active{ background:#3b82f6; border-color:#3b82f6; opacity:1; }

/* 文字區 */
.body{ padding:12px 14px 14px; display:flex; flex-direction:column; gap:10px; }
.title{ margin:0; font-size:16px; line-height:1.3; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.desc{ margin:0; color:#475569; height:38px; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }

.meta{
  display:grid; grid-template-columns: 1fr auto; gap:8px; align-items:end;
}
.label{ display:block; font-size:12px; color:#64748b; }
.value{ font-weight:800; }

.btn{
  align-self:flex-start; margin-top:4px;
  display:inline-flex; align-items:center; gap:8px;
  padding:8px 12px; border-radius:12px;
  border:1px solid #e6e8eb;
  background: linear-gradient(180deg, #fff 70%, #fbfdff 30%);
  color:#0f172a; cursor:pointer;
  transition:transform .18s cubic-bezier(.2,.8,.2,1), box-shadow .18s cubic-bezier(.2,.8,.2,1), border-color .18s cubic-bezier(.2,.8,.2,1);
}
.btn:hover{ transform:translateY(-1px); box-shadow:0 4px 14px rgba(2,6,23,.06); border-color:#b6ccff; }
.btn--primary{
  background: linear-gradient(180deg, rgba(37,99,235,.12), rgba(6,182,212,.10));
  color:#0b1220; font-weight:700; border-color:#9db7ff;
}
</style>
