<template>
  <div></div>
</template>

<script setup>
import { ofetch } from 'ofetch'
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
const router = useRouter()
const userStore = useUserStore()
onMounted(async () => {
  await ofetch('/api/logout', {
    method: 'POST'
  })
  userStore.refreshUser()
  router.replace('/')
})
</script>