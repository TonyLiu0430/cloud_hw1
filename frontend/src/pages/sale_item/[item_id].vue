<template>
    <div>
        <div v-if="images && images.length" class="container">
            <button @click="prevImage" :disabled="currentIndex === 0" class="btn">⬅ 上一張</button>

            <img :src="images[currentIndex]" alt="商品圖片" class="img" />

            <button @click="nextImage" :disabled="currentIndex === images.length - 1" class="btn">下一張 ➡</button>

            <div class="counter">
                {{ currentIndex + 1 }} / {{ images.length }}
            </div>
        </div>
        <el-card v-if="item" class="box-card" style="max-width: 400px; margin: 24px auto;">
            <div slot="header" class="clearfix">
                <span>{{ item.title }}</span>
            </div>
            <div>
                <el-descriptions :column="1">
                    <el-descriptions-item label="起標價">{{ parseInt(item.starting_price) }}</el-descriptions-item>
                    <el-descriptions-item>{{ item.description }}</el-descriptions-item>
                    <el-descriptions-item label="賣家">{{ item.seller_id }}</el-descriptions-item>
                </el-descriptions>
            </div>
            <template #footer>
                <el-row :gutter="10">
                    <el-col :span="16">
                        <el-input v-model="bid_input" type="number" />
                    </el-col>
                    <el-col :span="8">
                        <el-button @click="place_bid" style="width: 100%;">出價</el-button>
                    </el-col>
                </el-row>
            </template>
        </el-card>
        <el-card v-if="bids && bids.length" class="box-card" style="max-width: 400px; margin: 24px auto;">
            <div slot="header" class="clearfix">
                <span>出價紀錄</span>
            </div>
            <el-table :data="bids" style="width: 100%">
                <el-table-column prop="user_id" label="用戶" />
                <el-table-column prop="price" label="出價" />
                <el-table-column prop="created_at" label="時間">
                    <template #default="scope">
                        {{ new Date(scope.row.created_at).toLocaleString() }}
                    </template>
                </el-table-column>
            </el-table>
        </el-card>
    </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { ofetch } from 'ofetch'
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

// b.id, b.user_id, b.price, b.created_at

interface Bid {
    id: number,
    user_id: string,
    price: number,
    created_at: Date
}

const route = useRoute()
const itemId = route.params.item_id
const item = ref<any>()
const bids = ref<Bid[]>()
const images = ref<string[]>()
const bid_input = ref('')

const refresh_item_status = async () => {
  const item_resp = await ofetch(`/api/sale_item/${itemId}`)
  item.value = item_resp.item;
  bids.value = item_resp.bids;
  const response = await ofetch(`/api/sale_item/images/${itemId}`)
  images.value = response.images
}

onMounted(async () => {
  refresh_item_status()
})

const place_bid = async () => {
    console.log(typeof bid_input.value)
    const bid = Number(bid_input.value);
    if(bid <= item.value.starting_price) {
        ElMessage({
            message: '出價失敗: 低於底價',
            type: 'error',
            plain: true,
        })
        return;
    }
    if(bids.value && bids.value[0] != null && bid <= bids.value[0].price) {
        ElMessage({
            message: '出價失敗: 低於目前最高價格',
            type: 'error',
            plain: true,
        })
        return;
    }
    ofetch(`/api/sale_item/${itemId}/bid`,{
        method: 'POST',
        body: {
            price: bid
        }
    }).then(() => {
        ElMessage({
            message: '出價成功',
            type: 'success',
            plain: true,
        })
        refresh_item_status()
    }).catch((e) => {
        ElMessage({
            message: '出價失敗 未知錯誤',
            type: 'error',
            plain: true,
        })
        refresh_item_status()
    })
}
let currentIndex =ref(0);
function prevImage(){
    if(currentIndex.value === 0){
        return;
    }
    else{
        currentIndex.value -=1;
    }
}
function nextImage(){
    if(currentIndex.value === images.length){
        return;
    }
    else{
        currentIndex.value+=1;
    }
}
</script>

<style scoped>
.clearfix{margin-bottom: 8px; text-decoration: underline; font-weight: bold;}
.container {
  display: flex;
  align-items: center;       /* 垂直置中 */
  justify-content: center;   /* 水平置中整個區塊 */
  gap: 16px;                 /* 按鈕與圖片間距 */
  flex-wrap: wrap;           /* 小螢幕自動換行 */
}

.img {
  max-width: 400px;
  display: block;
  border: 2px solid #ccc;
  border-radius: 8px;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  background-color: black;
  color: white;
  font-weight: bold;
  transition: all 0.3s;
}

.btn:hover {
  background-color: black;
  transform: scale(1.05);
}

.counter {
  width: 100%;
  text-align: center;
  margin-top: 8px;
}
</style>
