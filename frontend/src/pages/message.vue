<template>
  <section class="chat-layout">
    <!-- 左側：會話清單 -->
    <aside class="sidebar">
      <div class="side-head">
        <div class="title">對話</div>
        <el-button size="small" link @click="refreshUserList">重新整理</el-button>
      </div>

      <div class="side-list" v-loading="loadingList">
        <div
          v-for="u in userList"
          :key="u.peerId"
          :class="['side-item', u.peerId === activePeer ? 'is-active' : '']"
          @click="switchPeer(u.peerId)"
        >
          <div class="avatar">{{ u.peerId.slice(0, 2).toUpperCase() }}</div>
          <div class="meta">
            <div class="row1">
              <span class="name">{{ u.peerId }}</span>
              <span class="time">{{ fmtListTime(u.lastTime) }}</span>
            </div>
            <div class="row2 muted">點擊查看聊天紀錄</div>
          </div>
        </div>

        <div v-if="!userList.length && !loadingList" class="side-empty muted">
          尚無聊天紀錄
        </div>
      </div>
    </aside>

    <!-- 右側：聊天室 -->
    <main class="chat-wrap">
      <header class="chat-header">
        <div class="brand">MyMarket</div>
        <div class="peer">{{ activePeer ? '聊天室：' + activePeer : '聊天室' }}</div>
      </header>

      <div v-if="!activePeer" class="chat-empty">
        <span class="emoji">💬</span>
        <p class="muted">從左側選一個對話開始聊天！</p>
      </div>

      <template v-else>
        <section ref="scrollEl" class="chat-body">
          <el-scrollbar height="600px" ref="scrollbarRef">
            <div
              v-for="(m, i) in messages"
              :key="i"
              :class="['row', m.sender_uuid === userId ? 'me' : 'other']"
            >
              <div class="bubble">
                <div class="text">{{ m.message }}</div>
                <div class="meta">{{ fmtTime(m.timestamp) }}</div>
              </div>
            </div>
          </el-scrollbar>

          <div v-if="!messages.length" class="empty">
            <span class="emoji">💬</span>
            <p class="muted">開始聊天吧！</p>
          </div>
        </section>

        <div class="chat-input">
          <el-input
            v-model="input"
            placeholder="輸入訊息…"
            @keydown.enter.native="e => !e.isComposing && send()"
            class="input"
          />
          <el-button type="primary" class="send" @click="send">送出</el-button>
        </div>
      </template>
    </main>
  </section>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ofetch } from 'ofetch'
import { useRoute, useRouter } from 'vue-router'
import type { ScrollbarInstance } from 'element-plus'

/** ===== 型別 ===== */
type MessageReq = { reciver_uuid: string; message: string }
type ChatMessage = {
  sender_uuid: string
  reciver_uuid: string
  message: string
  timestamp?: string
}
type UserListItemAPI = { _id: string; last_message_time: string } // 後端回傳
type UserListItem = { peerId: string; lastTime: string }          // 前端用

/** ===== 路由 ===== */
const route = useRoute()
const router = useRouter()

const scrollbarRef = ref<ScrollbarInstance>()

/** ===== 狀態 ===== */
const userId = ref('')
const userList = ref<UserListItem[]>([])
const loadingList = ref(false)

const activePeer = ref<string | null>(null) // 當前右側開啟的聊天室對象
const input = ref('')
const messages = ref<ChatMessage[]>([])
const scrollEl = ref<HTMLElement | null>(null)

let ws: WebSocket | null = null

/** ===== 小工具 ===== */
function scrollToBottom() {
  if (!scrollbarRef.value) return
  const scrollHeight = scrollbarRef.value?.wrapRef?.scrollHeight || 0
  scrollbarRef.value.scrollTo({ top: scrollHeight })
}
function fmtTime(ts?: string) {
  const d = ts ? new Date(ts) : new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}
function fmtListTime(ts?: string) {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const sameDay =
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  return sameDay ? fmtTime(ts) : `${d.getMonth() + 1}/${d.getDate()}`
}

/** ===== 會話清單 API：/api/message/user_list =====
 *  後端回：{ user_list: [{ _id: <peerId>, last_message_time: <ISO> }, ...] }
 *  作用：顯示你曾經聊過天的對象，依最後訊息時間 desc 排序（後端已排序）
 */
async function refreshUserList() {
  loadingList.value = true
  try {
    const res = await ofetch<{ user_list: UserListItemAPI[] }>(
      '/api/message/user_list',
      { credentials: 'include' }
    )
    userList.value = (res.user_list || []).map((x) => ({
      peerId: x._id,
      lastTime: x.last_message_time,
    }))
  } finally {
    loadingList.value = false
  }
}

/** ===== WebSocket 連線，依 activePeer 切房 ===== */
function wsUrl() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${location.host}/api/message/message`
}
function connectWS(peerId: string) {
  // 關掉舊連線
  if (ws && ws.readyState === WebSocket.OPEN) ws.close()
  ws = new WebSocket(wsUrl())

  ws.onopen = () => {
    // 後端協議：連上後第一個訊息要傳 peerId，後端就會回傳該房的歷史
    ws?.send(peerId)
  }

  let isHistory = true
  ws.onmessage = (evt) => {
    if(evt.data == null) return;
    const payload = JSON.parse(evt.data)
    if (isHistory) {
      messages.value = payload as ChatMessage[]
      isHistory = false
      nextTick(scrollToBottom)
      return
    }
    const msg = payload as ChatMessage
    if (msg.reciver_uuid == activePeer.value || msg.sender_uuid == activePeer.value) {
      // message from current peer
      messages.value.push(payload as ChatMessage)
      nextTick(scrollToBottom)
    }
    else {
      // TODO
      // 更新左側userList
    }
  }

  ws.onclose = () => {
    // 這裡先不自動重連，切房會自行呼叫 connectWS
    // console.log('WS closed')
  }
}

/** 切換聊天室（左側點擊） */
async function switchPeer(peerId: string) {
  if (activePeer.value === peerId) return
  activePeer.value = peerId
  messages.value = []
  // 更新網址 query，方便分享/刷新仍在同一房
  router.replace({ query: { ...route.query, peer: peerId } })
  connectWS(peerId)
}

/** 送訊息到當前房 */
function send() {
  const text = input.value.trim()
  if (!text || !activePeer.value || !ws || ws.readyState !== WebSocket.OPEN) return

  const req: MessageReq = { reciver_uuid: activePeer.value, message: text }
  ws.send(JSON.stringify(req))

  // 不准樂觀
  input.value = ''
  nextTick(scrollToBottom)
}

/** ===== 初始化 ===== */
onMounted(async () => {
  // 取得自己 userId（用於判斷左右與權限）
  userId.value = await ofetch('/api/user_id', { credentials: 'include' })

  // 先抓會話清單
  await refreshUserList()

  // 若網址帶有 ?peer=... 就直接打開該房；否則開清單第一個
  const qPeer = route.query.peer as string | undefined
  const initialPeer = qPeer || userList.value[0]?.peerId || null
  if (initialPeer) switchPeer(initialPeer)
})

onUnmounted(() => {
  if (ws && ws.readyState === WebSocket.OPEN) ws.close()
})
</script>

<style scoped>
/* 兩欄布局 */
.chat-layout{
  display:grid;
  grid-template-columns: 280px 1fr;
  gap:16px;
  width:min(1120px, 96vw);
  margin: 24px auto 64px;
}

/* 左側 */
.sidebar{
  border:1px solid #e6e8eb; border-radius:14px; background:#fff;
  box-shadow:0 8px 24px rgba(2,6,23,.06);
  overflow:hidden;
  display:flex; flex-direction:column; min-height:560px;
}
.side-head{
  display:flex; justify-content:space-between; align-items:center;
  padding:12px 12px; border-bottom:1px solid #e6e8eb;
  background:linear-gradient(180deg,#f8fbff,#f3f7ff);
}
.title{ font-weight:800; letter-spacing:.2px; }
.side-list{ padding:8px 8px; overflow:auto; }
.side-item{
  display:flex; gap:10px; align-items:center; padding:10px;
  border-radius:12px; cursor:pointer;
}
.side-item:hover{ background:#f5f7fb; }
.side-item.is-active{ background:#eef4ff; }
.avatar{
  width:36px; height:36px; border-radius:50%; background:#e0e7ff;
  display:flex; align-items:center; justify-content:center; font-weight:900; color:#334155;
}
.meta{ flex:1; min-width:0; }
.row1{ display:flex; justify-content:space-between; gap:8px; }
.name{ font-weight:700; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.time{ color:#64748b; font-size:12px; }
.row2{ font-size:12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.side-empty{ text-align:center; padding:24px 0; }

/* 右側 */
.chat-wrap{
  background:#fff; border:1px solid #e6e8eb; border-radius:16px;
  box-shadow:0 8px 24px rgba(2,6,23,.06);
  display:grid; grid-template-rows:64px 1fr auto; min-height:560px;
}
.chat-header{
  display:flex; align-items:center; justify-content:space-between;
  padding:0 16px; border-bottom:1px solid #e6e8eb;
  background:linear-gradient(180deg,#f8fbff,#f3f7ff);
}
.brand{ font-weight:900; color:#2563eb; letter-spacing:.3px; }
.peer{ color:#475569; }

.chat-empty{
  grid-row: 2 / span 2;
  display:flex; align-items:center; justify-content:center; flex-direction:column;
}
.emoji{ font-size:28px; }
.muted{ color:#64748b; }

.chat-body{
  overflow:auto; padding:14px 14px 0;
  background:linear-gradient(180deg,#fbfdff 0%, #ffffff 40%, #f8fafc 100%);
}
.row{ display:flex; margin:8px 0; }
.row.me{ justify-content:flex-end; }
.row.other{ justify-content:flex-start; }
.bubble{
  max-width:68%; border-radius:16px; padding:10px 12px;
  box-shadow:0 6px 18px rgba(2,6,23,.06); position:relative; word-break:break-word;
}
.me .bubble{
  color:#0b1220; background:linear-gradient(180deg,#e0f2fe,#bfdbfe);
  border-top-right-radius:4px;
}
.other .bubble{
  background:#fff; border:1px solid #e6e8eb; border-top-left-radius:4px;
}
.text{ white-space:pre-wrap; }
.meta{ font-size:12px; color:#64748b; margin-top:4px; text-align:right; }

.chat-input{
  display:grid; grid-template-columns:1fr auto; gap:10px; padding:10px 12px;
  border-top:1px solid #e6e8eb; background:#fff;
}
.input :deep(.el-input__wrapper){ border-radius:12px; }
.send{ border-radius:12px; padding:0 18px; }
</style>
