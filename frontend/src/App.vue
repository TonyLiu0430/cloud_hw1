<template>
  <el-menu
    :default-active="activeIndex"
    class="el-menu-demo"
    mode="horizontal"
    :ellipsis="false"
    @select="handleSelect"
  >
    <el-menu-item index="0">
      <!-- <img
        style="width: 100px"
        src="/images/element-plus-logo.svg"
        alt="Element logo"
      /> -->
    </el-menu-item>
    <el-menu-item 
      index="/sale_items">
      商品列表
    </el-menu-item>
    <el-menu-item
      v-if="userStore.isLoggedIn"
      index="/sale">
      我要拍賣
    </el-menu-item>
    <el-menu-item
      v-if="userStore.isLoggedIn"
      index="/my_trade">
      我的交易
    </el-menu-item>
    <el-menu-item
      v-if="!userStore.isLoggedIn"
      index="/login">
      登錄
    </el-menu-item>
    <el-menu-item
      v-if="userStore.isLoggedIn"
      index="/profile">
      個人資料
    </el-menu-item>
  </el-menu>
  <router-view />
</template>

<script lang="ts" setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from './stores/user'

const router = useRouter()
const activeIndex = ref('1')
const userStore = useUserStore()

onMounted(async () => {
  await userStore.refreshUser()
})


const handleSelect = (key: string, _keyPath: string[]) => {
  router.push(key)
}
</script>

<style scoped>
.el-menu--horizontal > .el-menu-item:nth-child(1) {
  margin-right: auto;
}
</style>
