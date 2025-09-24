<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface User {
  id: number
  username: string
}

interface SaleItem {
  id: string
  title: string
  description: string
  starting_price: number
  current_price: number
  end_time: string
  seller_id: number
  bids: Bid[]
}

interface Bid {
  id: number
  amount: number
  bidder_id: number
  item_id: string
  created_at: string
}

const user = ref<User | null>(null)
const items = ref<SaleItem[]>([])
const loginForm = ref({ username: '', password: '' })
const registerForm = ref({ username: '', password: '' })
const itemForm = ref({ title: '', description: '', starting_price: 0, end_time: '' })
const bidForm = ref({ item_id: '', amount: 0 })
const message = ref('')

const api = (endpoint: string, options?: RequestInit) => {
  return fetch(`/api${endpoint}`, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    ...options
  })
}

const login = async () => {
  try {
    const res = await api('/login', {
      method: 'POST',
      body: JSON.stringify(loginForm.value)
    })
    if (res.ok) {
      const data = await res.json()
      user.value = data.username
      message.value = '登入成功'
      loadItems()
    } else {
      message.value = '登入失敗'
    }
  } catch (e) {
    message.value = '登入錯誤'
  }
}

const register = async () => {
  try {
    const res = await api('/register', {
      method: 'POST',
      body: JSON.stringify(registerForm.value)
    })
    if (res.ok) {
      message.value = '註冊成功，請登入'
    } else {
      message.value = '註冊失敗'
    }
  } catch (e) {
    message.value = '註冊錯誤'
  }
}

const logout = async () => {
  await api('/logout', { method: 'POST' })
  user.value = null
  items.value = []
  message.value = '已登出'
}

const createItem = async () => {
  try {
    const res = await api('/create_sale_item', {
      method: 'POST',
      body: JSON.stringify(itemForm.value)
    })
    if (res.ok) {
      message.value = '商品建立成功'
      loadItems()
      itemForm.value = { title: '', description: '', starting_price: 0, end_time: '' }
    } else {
      message.value = '商品建立失敗'
    }
  } catch (e) {
    message.value = '商品建立錯誤'
  }
}

const placeBid = async () => {
  const item_uuid: string = bidForm.value.item_id
  try {
    const res = await api(`/sale_item/${item_uuid}/bid`, {
      method: 'POST',
      body: JSON.stringify({ price : bidForm.value.amount})
    })
    if (res.ok) {
      message.value = '出價成功'
      loadItems()
      bidForm.value = { item_id: '', amount: 0 }
    } else {
      message.value = '出價失敗'
    }
  } catch (e) {
    message.value = '出價錯誤'
  }
}

const loadItems = async () => {
  try {
    const res = await api('/sale_items')
    if (res.ok) {
      items.value = await res.json()
    }
  } catch (e) {
    message.value = '載入商品失敗'
  }
}

onMounted(() => {
  loadItems()
})
</script>

<template>
  <div class="app">
    <header>
      <h1>競標系統測試</h1>
      <div v-if="user">
        歡迎, {{ user.username }}
        <button @click="logout">登出</button>
      </div>
    </header>

    <div v-if="!user" class="auth">
      <div class="form">
        <h2>登入</h2>
        <input v-model="loginForm.username" placeholder="用戶名" />
        <input v-model="loginForm.password" type="password" placeholder="密碼" />
        <button @click="login">登入</button>
      </div>
      <div class="form">
        <h2>註冊</h2>
        <input v-model="registerForm.username" placeholder="用戶名" />
        <input v-model="registerForm.password" type="password" placeholder="密碼" />
        <button @click="register">註冊</button>
      </div>
    </div>

    <div v-else class="main">
      <div class="form">
        <h2>建立商品</h2>
        <input v-model="itemForm.title" placeholder="標題" />
        <textarea v-model="itemForm.description" placeholder="描述"></textarea>
        <input v-model.number="itemForm.starting_price" type="number" placeholder="起標價" />
        <input v-model="itemForm.end_time" type="datetime-local" placeholder="結束時間" />
        <button @click="createItem">建立</button>
      </div>

      <div class="form">
        <h2>出價</h2>
        <select v-model="bidForm.item_id">
          <option value="">選擇商品</option>
          <option v-for="item in items" :key="item.id" :value="item.id">{{ item.title }}</option>
        </select>
        <input v-model.number="bidForm.amount" type="number" placeholder="出價金額" />
        <button @click="placeBid">出價</button>
      </div>

      <div class="items">
        <h2>商品列表</h2>
        <div v-for="item in items" :key="item.id" class="item">
          <h3>{{ item.title }}</h3>
          <p>{{ item.description }}</p>
          <p>起標價: {{ item.starting_price }}</p>
          <p>目前價: {{ item.current_price }}</p>
          <p>結束時間: {{ item.end_time }}</p>
          <div class="bids">
            <h4>出價記錄</h4>
            <div v-for="bid in item.bids" :key="bid.id" class="bid">
              金額: {{ bid.amount }}, 時間: {{ bid.created_at }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="message">{{ message }}</div>
  </div>
</template>

<style scoped>
.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #ccc;
  padding-bottom: 10px;
  margin-bottom: 20px;
}

.auth {
  display: flex;
  gap: 40px;
  margin-bottom: 40px;
}

.form {
  border: 1px solid #ddd;
  padding: 20px;
  border-radius: 8px;
  background: #f9f9f9;
}

.form h2 {
  margin-top: 0;
}

input, textarea, select {
  display: block;
  width: 100%;
  margin-bottom: 10px;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

button {
  background: #007bff;
  color: white;
  border: none;
  padding: 10px 15px;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background: #0056b3;
}

.main {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.items {
  grid-column: 1 / -1;
}

.item {
  border: 1px solid #ddd;
  padding: 15px;
  margin-bottom: 15px;
  border-radius: 8px;
  background: #f9f9f9;
}

.bids {
  margin-top: 10px;
}

.bid {
  background: #fff;
  padding: 5px;
  margin: 5px 0;
  border-radius: 4px;
}

.message {
  margin-top: 20px;
  padding: 10px;
  background: #e9ecef;
  border-radius: 4px;
  color: #495057;
}
</style>
