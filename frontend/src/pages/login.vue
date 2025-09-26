<template>
  <div class="flex h-[70dvh]">
    <ElCard class="m-auto w-full sm:w-5/6 md:w-3/4 lg:w-1/2 xl:w-1/3">
      <template #header>
        <ElPageHeader
          title="回首頁"
          content="登入"
          class="font-bold"
          @back="router.push('/')"
        />
      </template>
      <div class="flex w-full flex-col items-center justify-center">
        <el-input
          v-model="username"
          style="width: 240px"
          placeholder="使用者名稱"
        />
        <el-input
          v-model="password"
          style="width: 240px"
          type="password"
          placeholder="密碼"
          show-password
          class="mt-4"
        />
        <el-text v-if="login_failed" class="mx-1" type="danger"> 
          帳號或密碼錯誤
        </el-text>
      </div>
      <template #footer>
        <div class="flex items-center justify-center">
          <span>
            <el-button @click="register">註冊</el-button>
            <el-button @click="login">登入</el-button>
          </span>
        </div>
      </template>
    </ElCard>
  </div>
</template>

<script lang="ts" setup>
import { useRouter } from 'vue-router'
import { ref } from 'vue'
import { ofetch } from 'ofetch'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'


const router = useRouter()

const username = ref('')
const password = ref('')
const login_failed = ref(false)
const userStore = useUserStore()

const login = () => {
  ofetch('/api/login',{
    method: 'POST',
    body : {
      username: username.value,
      password: password.value
    }
  }).then(async () => {
    ElMessage({
      message: '登入成功',
      type: 'success',
      plain: true,
    })
    userStore.refreshUser()
    await router.push('/')
  }).catch(() => {
    login_failed.value = true
  })
}

const register = async () => {
  await router.push('/register')
}
</script>