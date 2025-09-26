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
        <el-input
          v-model="password_verify"
          style="width: 240px"
          type="password"
          placeholder="請再次輸入密碼"
          show-password
          class="mt-4"
        />
      <el-text v-if="verify_failed" class="mx-1" type="danger"> 
        密碼不相符
      </el-text>
      </div>
      <template #footer>
        <div class="flex items-center justify-center">
          <span>
            <el-button @click="register">註冊</el-button>
          </span>
        </div>
      </template>
    </ElCard>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ref } from 'vue'
import { ofetch } from 'ofetch'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'


const router = useRouter()

const username = ref('')
const password = ref('')
const password_verify = ref('')
const verify_failed = ref(false)
const userStore = useUserStore()

const register = () => {
  if(password.value != password_verify.value) {
    verify_failed.value = true
    return
  }
  ofetch('/api/register', {
    method: 'POST',
    body: {
      username: username.value,
      password: password.value
    }
  }).then(async () => {
    ElMessage({
      message: '註冊成功',
      type: 'success',
      plain: true,
    })
    userStore.refreshUser()
    await router.push('/')
  }).catch((res) => {
    ElMessage({
      message: `註冊失敗 + ${res.message}`,
      type: 'error',
      plain: true,
    })
  })
}
</script>