<template>
  <div class="flex flex-col justify-center items-center max-w-7xl mx-auto gap-6 pt-6">
    <el-card class="justify-center w-full mx-auto">
      <template #header>
        我的拍賣
      </template>
      <el-table
          :data="saleData"
          :border="true"
          style="width: 100%"
          :row-class-name="saletableRowClassName"
      >
        <el-table-column label="商品圖" width="120" align="center">
          <template #default="{ row }">
            <el-image style="width: 90px; height: 90px" :src="row.img_url" fit="fill" />
          </template>
        </el-table-column>
        <el-table-column prop="title" label="商品名" width="180" headerAlign="center"/>
        <el-table-column prop="highest_bid" label="最高價" width="180" headerAlign="center"/>
        <el-table-column prop="end_date" label="結束時間" headerAlign="center"/>
        <el-table-column label="剩餘時間" headerAlign="center">
          <template #default="{ row }">
            {{ show_last_time(row.end_date) }}
          </template>
        </el-table-column>
        <el-table-column label="拍賣頁面" width="130" align="center">
          <template #default="{ row }">
            <el-button plain @click="to_sale_page(row.sale_item_id)">至拍賣頁面</el-button>
          </template>
        </el-table-column>
        <el-table-column label="聯絡買家" width="130" align="center">
          <el-button plain>聯絡買家</el-button>
        </el-table-column>
      </el-table>
    </el-card>
    <!---->
    <el-card class="justify-center w-full mx-auto">
      <template #header>
        我的出價
      </template>
      <el-table
          :data="bidData"
          :border="true"
          style="width: 100%"
          :row-class-name="bidtableRowClassName"
      >
        <el-table-column label="商品圖" width="120" align="center">
          <template #default="{ row }">
            <el-image style="width: 90px; height: 90px" :src="row.img_url" fit="fill" />
          </template>
        </el-table-column>
        <el-table-column prop="title" label="商品名" width="180" headerAlign="center"/>
        <el-table-column prop="highest_bid" label="最高價" width="130" headerAlign="center"/>
        <el-table-column prop="my_bid" label="我的出價" width="130" headerAlign="center"/>
        <el-table-column prop="end_date" label="結束時間" headerAlign="center"/>
        <el-table-column label="剩餘時間" headerAlign="center">
          <template #default="{ row }">
            {{ show_last_time(row.end_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="狀態" headerAlign="center"/>
        <el-table-column label="拍賣頁面" width="130" align="center">
          <template #default="{ row }">
            <el-button plain @click="to_sale_page(row.sale_item_id)">至拍賣頁面</el-button>
          </template>
        </el-table-column>
        <el-table-column label="聯絡賣家" width="130" align="center">
          <el-button plain>聯絡賣家</el-button>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script lang="ts" setup>
import { ofetch } from 'ofetch'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'


interface Sale {
    description: string
    end_date: Date
    highest_bid: number | string
    highest_bidder: string
    sale_item_id: string
    starting_price: number
    title: string
    img_url: string | undefined
}

interface Bid {
  title: string,
  highest_bid: number,
  my_bid: number,
  status: string,
  sale_item_id: string,
  end_date: Date
  img_url: string | undefined
}

interface BidResult {
  bid_id: number
  price: number
  sale_item: {
    description: string
    end_date: string
    highest_price: number
    id: string
    seller_id: string
    starting_price: number
    title: string
  }
  sale_item_id: string
}

const saleData = ref<Sale[]>()
const bidData = ref<Bid[]>([])
const router = useRouter()

const get_img_url = async (sale_item_id : string) => {
  const { images } = await ofetch(`/api/sale_item/images/${sale_item_id}`,{
    query: {
      num: 1
    }
  })
  return images[0] ? images[0] as string : '/default.jpg'
}

const fetchSaleData = async () => {
  saleData.value = (await ofetch('/api/my_sale')).sales
  if (saleData.value) {
    for (const s of saleData.value) {
      s.end_date = new Date(s.end_date)
      if (s.highest_bid == null) {
        s.highest_bid = '還沒有人出價喔🥲'
      }
      get_img_url(s.sale_item_id).then((res) => {
        s.img_url = res
      })
    }
  }
}

const fetchBidData = async () => {
  const { bids } = await ofetch('/api/my_bids')
  if (bids) {
    for(const bid of bids as BidResult[]) {
      bidData.value.push({
        title: bid.sale_item.title,
        highest_bid: bid.sale_item.highest_price,
        my_bid: bid.price,
        status: get_status(bid.price, bid.sale_item.highest_price, new Date(bid.sale_item.end_date)),
        sale_item_id: bid.sale_item_id,
        end_date: new Date(bid.sale_item.end_date),
        img_url: undefined
      })
      const cur = bidData.value[bidData.value.length - 1]
      get_img_url(bid.sale_item_id).then((res) => {
        if(cur) {
          cur.img_url = res;
        }
      })
    }
  }
}

onMounted(async () => {
    await Promise.all([
      fetchSaleData(),
      fetchBidData()
    ])
})

const saletableRowClassName = ({
  row,
  rowIndex,
}: {
  row: Sale
  rowIndex: number
}) => {
  const currentDate = new Date()
  if(currentDate <= row.end_date) {
    return 'in-progress-row'
  }
  else {
    return 'ended-row'
  }
  return ''
}

const bidtableRowClassName = ({
  row,
  rowIndex,
}: {
  row: Bid
  rowIndex: number
}) => {
  const currentDate = new Date()
  if(currentDate <= row.end_date) {
    return 'in-progress-row'
  }
  else if(row.my_bid == row.highest_bid){
    return 'win-row'
  }
  return 'ended-row'
}

const get_status = (my_bid : number, h_bid : number, date : Date) => {
  if (new Date() <= date) {
    if(my_bid == h_bid) {
      return '進行中 目前最高標🤗'
    }
    else {
      return '進行中 最高標不是你🥲'
    }
  }
  if (my_bid === h_bid) {
    return '得標'
  }
  return '未得標'
}


const to_sale_page = async (id: string) => {
  await router.push(`/sale_item/${id}`)
}

const show_last_time = (end_date : Date) => {
  const now = new Date()
  const diffMs = end_date.getTime() - now.getTime()
  if (diffMs <= 0) {
    const diffSec = Math.floor((now.getTime() - end_date.getTime()) / 1000)
    const days = Math.floor(diffSec / (3600 * 24))
    const hours = Math.floor((diffSec % (3600 * 24)) / 3600)
    const minutes = Math.floor((diffSec % 3600) / 60)
    if (days > 0) return `已結束 ${days}天${hours}小時前`
    if (hours > 0) return `已結束 ${hours}小時${minutes}分鐘前`
    return `已結束 ${minutes}分鐘前`
  }
  const diffSec = Math.floor(diffMs / 1000)
  const days = Math.floor(diffSec / (3600 * 24))
  const hours = Math.floor((diffSec % (3600 * 24)) / 3600)
  const minutes = Math.floor((diffSec % 3600) / 60)
  if (days > 0) return `${days}天${hours}小時`
  if (hours > 0) return `${hours}小時${minutes}分鐘`
  return `${minutes}分鐘`
}

// 定時刷新 bidData 以觸發顯示更新
import { onUnmounted } from 'vue'
let timer: number | undefined
onMounted(() => {
  timer = window.setInterval(() => {
    // 只要 bidData 重新賦值即可觸發渲染
    bidData.value = [...bidData.value]
  }, 1000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})

</script>

<style>
.el-table .in-progress-row {
  --el-table-tr-bg-color: var(--el-color-success-light-9);
}
.el-table .ended-row {
  --el-table-tr-bg-color: #f0f0f0;
}
.el-table .in-progress-row .el-table__cell {
  --el-table-row-hover-bg-color: var(--el-color-success-light-9);
}
.el-table .ended-row .el-table__cell {
  --el-table-row-hover-bg-color: #f0f0f0;
}
.el-table .win-row {
  --el-table-tr-bg-color: #fff9c4;
}
.el-table .win-row .el-table__cell {
  --el-table-row-hover-bg-color: #fff9c4;
}
</style>