<template>
  <div class="app-shell">
    <!-- 路由進度條 -->
    <div class="route-progress" :class="{ 'is-active': progressActive }" :style="{ '--rpw': progressWidth + '%' }"></div>
    
    <header class="app-header">
      <el-menu
        :default-active="activeIndex"
        class="el-menu-demo"
        mode="horizontal"
        :ellipsis="false"
        @select="handleSelect"
      >
        <!-- 品牌：純文字 Logo（不參與選取），點擊回到 /sale_items -->
        <el-menu-item index="brand" class="brand-item" title="回到商品列表">
          <span class="brand-link">MyMarket</span>
        </el-menu-item>

        <el-menu-item index="/sale_items">商品列表</el-menu-item>
        <el-menu-item v-if="userStore.isLoggedIn" index="/sale">我要拍賣</el-menu-item>
        <el-menu-item v-if="userStore.isLoggedIn" index="/my_trade">我的交易</el-menu-item>
        <el-menu-item v-if="!userStore.isLoggedIn" index="/login">登錄</el-menu-item>
        <el-menu-item v-if="userStore.isLoggedIn" index="/logout">登出</el-menu-item>
      </el-menu>
    </header>


    <main ref="mainRef" class="app-main">
      <!-- 頁面轉場 -->
      <transition name="fade-slide" mode="out-in">
        <router-view :key="route.fullPath" />
      </transition>
    </main>

    <!-- 回到頂部 -->
    <button v-show="showTop" class="fab-top" @click="scrollTop" aria-label="回到頂部">↑</button>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onBeforeUnmount, ref, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from './stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeIndex = ref(route.path)
const mainRef = ref<HTMLElement | null>(null)

/* 路由進度條狀態 */
const progressActive = ref(false)
const progressWidth = ref(0)
let progressTimer: number | null = null

function startProgress(){
  progressActive.value = true
  progressWidth.value = 0
  // 先流到 80%
  progressTimer && cancelAnimationFrame(progressTimer)
  const tick = () => {
    if (progressWidth.value < 80) {
      progressWidth.value += 2
      progressTimer = requestAnimationFrame(tick) as unknown as number
    }
  }
  progressTimer = requestAnimationFrame(tick) as unknown as number
}
function finishProgress(){
  progressWidth.value = 100
  setTimeout(() => { progressActive.value = false; progressWidth.value = 0 }, 220)
}

/* 回到頂部 */
const showTop = ref(false)
function onScroll(){
  showTop.value = (window.scrollY || document.documentElement.scrollTop) > 240
}
function scrollTop(){
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(async () => {
  // 首次載入
  await userStore.refreshUser()
  await nextTick()
  enhanceCards()
  onScroll()
  window.addEventListener('scroll', onScroll, { passive: true })

  // 註冊一次性的路由進度條
  router.beforeEach((to, from, next) => { startProgress(); next() })
  router.afterEach(() => { finishProgress() })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
})

/* 路由切換：同步選單狀態 + 重新套互動效果 */
watch(() => route.path, async (p) => {
  activeIndex.value = p
  await nextTick()
  requestAnimationFrame(() => enhanceCards())
})

const handleSelect = (key: string) => {
  if (key === 'brand') { router.push('/sale_items'); return }
  router.push(key)
}

/** 為現有商品卡片加互動與圖片保護（不動其他檔案） */
function enhanceCards(){
  const root = mainRef.value
  if (!root) return

  const candidates = root.querySelectorAll<HTMLElement>([
    '.card', '.product', '.product-card',
    '.item', '.item-card', '.goods', '.goods-item',
    '.el-card'
  ].join(','))

  // 多張卡的父層 → 自動網格
  const parents = new Set<HTMLElement>()
  candidates.forEach(el => { if (el.parentElement) parents.add(el.parentElement) })
  parents.forEach(parent => {
    const items = Array.from(parent.children).filter(c =>
      (c as HTMLElement).matches('.card, .product, .product-card, .item, .item-card, .goods, .goods-item, .el-card')
    )
    if (items.length >= 2) parent.classList.add('x-grid')
  })

  // 卡片互動與圖片完整顯示
  candidates.forEach(card => {
    if (!card.classList.contains('x-card')) {
      card.classList.add('x-card')

      // 第一張圖 → 避免跑版
      const img = card.querySelector('img')
      if (img && !img.classList.contains('x-card-media')) {
        img.classList.add('x-card-media')   // 防跑版、完整顯示
      }

      // 滑鼠光暈跟隨
      const onMove = (e: MouseEvent) => {
        const rect = card.getBoundingClientRect()
        const mx = ((e.clientX - rect.left) / rect.width) * 100
        const my = ((e.clientY - rect.top) / rect.height) * 100
        card.style.setProperty('--mx', mx + '%')
        card.style.setProperty('--my', my + '%')
      }
      const onLeave = () => {
        card.style.removeProperty('--mx')
        card.style.removeProperty('--my')
      }
      card.addEventListener('mousemove', onMove)
      card.addEventListener('mouseleave', onLeave)
      ;(card as any)._xHandlers = { onMove, onLeave }
    }
  })
}
</script>

<style scoped>
/* 讓品牌靠左，其餘項目靠右 */
.el-menu--horizontal > .el-menu-item:nth-child(1) { margin-right: auto; }
</style>
