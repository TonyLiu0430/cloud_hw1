<template>
  <div class="flex flex-col items-center">
    <h2 class="text-2xl font-bold mb-4">上架商品</h2>
    <form @submit.prevent="submitForm" class="w-full max-w-md">
      <div class="mb-4">
        <label for="title" class="block text-sm font-medium">商品名稱</label>
        <input v-model="form.title" id="title" type="text" class="input" required />
      </div>
      <div class="mb-4">
        <label for="description" class="block text-sm font-medium">商品描述</label>
        <textarea v-model="form.description" id="description" class="input" required></textarea>
      </div>
      <div class="mb-4">
        <label for="starting_price" class="block text-sm font-medium">起標價</label>
        <input v-model.number="form.starting_price" id="starting_price" type="number" class="input" required />
      </div>
      <div class="mb-4">
        <label for="end_date" class="block text-sm font-medium">結束時間</label>
        <input v-model="form.end_date" id="end_date" type="datetime-local" class="input" required />
      </div>
      <div class="mb-4">
        <label for="image" class="block text-sm font-medium">上傳圖片</label>
        <input @change="handleFileChange" id="image" type="file" class="input" accept="image/*" />
      </div>
      <button type="submit" class="btn btn-primary">上架商品</button>
    </form>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ofetch } from 'ofetch'

const router = useRouter()

const form = ref({
  title: '',
  description: '',
  starting_price: 0,
  end_date: '',
})

const selectedFile = ref<File | null>(null)

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0] ?? null
  }
}

const submitForm = async () => {
  try {
    // 上架商品
    const saleItemResponse = await ofetch('/api/sale_item', {
      method: 'POST',
      body: form.value,
    })

    const saleItemId = saleItemResponse.item_uuid

    // 上傳圖片
    if (selectedFile.value) {
      const formData = new FormData()
      formData.append('image', selectedFile.value)

      await ofetch(`/api/img/upload/${saleItemId}`, {
        method: 'POST',
        body: formData,
      })
    }

    alert('商品上架成功！')
    router.push('/')
  } catch (error) {
    console.error(error)
    alert('上架商品失敗，請稍後再試。')
  }
}
</script>

<style scoped>
.input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.btn {
  display: inline-block;
  padding: 0.5rem 1rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.btn-primary {
  background-color: #007bff;
}
</style>