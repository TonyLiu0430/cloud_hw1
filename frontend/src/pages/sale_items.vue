<template>
  <div class="flex h-[70dvh]">
    <el-row :gutter="20" class="w-full p-4">
      <el-col
      v-for="item in sale_items"
      :key="item.id"
      :xs="24"
      :sm="12"
      :md="8"
      >
      <el-card shadow="hover" class="mb-4">
        <template #header>
          <span class="font-bold text-lg">{{ item.title }}</span>
        </template>
        <div class="mb-2 flex justify-center">
          <img
            v-if="item.img_url"
            :src="item.img_url"
            alt="商品圖片"
            class="max-h-40 object-contain rounded"
          />
          <div v-else class="w-full h-40 flex items-center justify-center bg-gray-100 text-gray-400">
            無圖片
          </div>
        </div>
        <div class="text-gray-600 mb-2">{{ item.description }}</div>
        <div class="text-orange-500 font-semibold mb-2">起標價：${{ item.starting_price }}</div>
        <div class="text-green-600 font-semibold mb-2">目前價格：${{ item.current_price }}</div>
        <div class="text-xs text-gray-400 mb-2">結束時間：{{ item.end_date }}</div>
        <el-button
          type="warning"
          class="mt-2 w-full"
          @click="router.push(`/sale_item/${item.id}`)"
        >
          查看詳情
        </el-button>
      </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script lang="ts" setup>
import { useRouter } from 'vue-router'
import { onMounted, ref } from 'vue'
import { ofetch } from 'ofetch'


const router = useRouter()

interface SaleItem {
  id: string
  title: string
  description: string
  starting_price: number
  end_date: string
  seller_id: number
  current_price: number
  img_url: string
}

const sale_items = ref<SaleItem[]>([])

onMounted(async () => {
  sale_items.value = await ofetch('/api/sale_items')
})

</script>