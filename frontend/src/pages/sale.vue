<template> 
  <section class="sale-wrap">
    <header class="sale-head">
      <h2>上架商品</h2>
      <p class="muted">請填寫商品資訊，並上傳多張產品圖片（拖拉或點選）。</p>
    </header>

    <form class="sale-form" @submit.prevent="submitForm">
      <div class="field">
        <label for="title">商品名稱</label>
        <input v-model="form.title" id="title" type="text" class="input" placeholder="例：藍牙耳機" required />
      </div>

      <div class="field">
        <label for="description">商品描述</label>
        <textarea v-model="form.description" id="description" class="input textarea" rows="4" placeholder="簡短描述特色…" required></textarea>
      </div>

      <div class="grid-2">
        <div class="field">
          <label for="starting_price">起標價</label>
          <div class="input-affix">
            <span class="prefix">$</span>
            <input v-model.number="form.starting_price" id="starting_price" type="number" min="0" step="1" class="input no-padding-left" required />
          </div>
        </div>

        <div class="field">
          <label for="end_date">結束時間</label>
          <!-- <input v-model="form.end_date" id="end_date" type="datetime-local" class="input" step="1800" required /> -->
          <VueDatePicker
            v-model="form.end_date"
            :enable-time-picker="true"
            :minutes-increment="30"
            format="yyyy-MM-dd HH:mm"
            :is-24="true"
            placeholder="選擇日期時間"
          />
        </div>
      </div>

      <!-- 多圖上傳區 -->
      <div class="field">
        <label>上傳圖片</label>

        <div
          class="uploader"
          @dragover.prevent="dragOver = true"
          @dragleave.prevent="dragOver = false"
          @drop.prevent="onDrop"
          :class="{ 'is-drag': dragOver }"
        >
          <!-- 真正的檔案輸入（隱藏） -->
          <input
            ref="fileInput"
            class="file-input"
            id="image"
            type="file"
            accept=".jpg,.jpeg,.png,image/jpeg,image/png"
            multiple
            @change="onFilesSelected"
          />

          <!-- 縮圖網格（相片一張張排好） -->
          <div class="thumbs-grid">
            <!-- 已選圖片 -->
            <div v-for="(p, idx) in previews" :key="p.id" class="tile">
              <img :src="p.url" :alt="p.file.name" />
              <button type="button" class="tile-x" aria-label="移除" @click="removeAt(idx)">×</button>
            </div>

            <!-- 最後一格：新增卡（相機圖示） -->
            <button type="button" class="tile add-tile" @click="fileInput?.click()" title="新增圖片">
              <div class="cam">📷</div>
              <div class="add-text">拖拉圖片到此處 或 <span class="btn-mini">選擇檔案</span></div>
              <div class="muted tiny">僅支援 JPG / PNG，建議 &lt; 5MB / 張</div>
            </button>
          </div>
        </div>
      </div>

      <div class="actions">
        <button type="submit" class="btn btn--primary">上架商品</button>
      </div>
    </form>
  </section>
</template>

<script lang="ts" setup>
import { ref, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ofetch } from 'ofetch'
import VueDatePicker from '@vuepic/vue-datepicker';
import '@vuepic/vue-datepicker/dist/main.css';

const router = useRouter()

const ceil30 = (date: Date) => {
  let hr = date.getHours();
  let mn = date.getMinutes();

  if (mn % 30 !== 0) {
    mn = mn + (30 - (mn % 30));
    if (mn >= 60) {
      hr += 1;
      mn -= 60;
    }
  }

  date.setHours(hr, mn, 0, 0);

  return date
};

const form = ref({
  title: '',
  description: '',
  starting_price: 0,
  end_date: ceil30(new Date()),
})

/* ===== 多圖上傳狀態 ===== */
type Preview = { id: number; url: string; file: File }
const fileInput = ref<HTMLInputElement | null>(null)
const dragOver = ref(false)
const files = ref<File[]>([])          // 送往後端的檔案（按加入順序）
const previews = ref<Preview[]>([])    // UI 預覽
let idSeed = 1
const MAX_SIZE = 10 * 1024 * 1024       // 5MB
const ALLOW = ['image/jpeg', 'image/png']
const ALLOW_EXT = ['.jpg', '.jpeg', '.png']

function isAllowed(f: File) {
  const ext = '.' + (f.name.split('.').pop() || '').toLowerCase()
  return ALLOW.includes(f.type) || ALLOW_EXT.includes(ext)
}

function addFiles(list: FileList | File[]) {
  const skipped: string[] = []
  const arr = Array.from(list)
  for (const f of arr) {
    if (!isAllowed(f) || f.size > MAX_SIZE) { skipped.push(f.name); continue }
    files.value.push(f)                                    // 依加入順序穩穩排列
    const url = URL.createObjectURL(f)
    previews.value.push({ id: idSeed++, url, file: f })
  }
  if (skipped.length) {
    alert(`有 ${skipped.length} 張不被接受（僅支援 JPG/PNG 且 < 5MB）：\n- ` + skipped.join('\n- '))
  }
}
function onFilesSelected(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length) addFiles(input.files)
  input.value = '' // 允許重選同一批
}
function onDrop(e: DragEvent) {
  dragOver.value = false
  if (e.dataTransfer?.files?.length) addFiles(e.dataTransfer.files)
}
function removeAt(idx: number) {
  const p = previews.value[idx]
  URL.revokeObjectURL(p.url)
  previews.value.splice(idx, 1)
  files.value.splice(idx, 1)
}
onBeforeUnmount(() => previews.value.forEach(p => URL.revokeObjectURL(p.url)))

/* ===== 送出流程（沿用你的 API：先建 → 逐張 /api/img/upload/:id，欄位名固定 image）===== */
const submitForm = async () => {
  try {
    // 1) 先建商品
    const saleItemResponse = await ofetch('/api/sale_item', {
      method: 'POST',
      body: form.value,
    })
    const saleItemId = (saleItemResponse as any).item_uuid

    // 2) 多張圖片依序上傳（單請求單檔：image）
    const okList:string[] = []
    const failList:string[] = []
    for (const f of files.value) {
      const fd = new FormData()
      fd.append('image', f) // 後端只認 "image"
      try {
        await ofetch(`/api/img/upload/${saleItemId}`, { method: 'POST', body: fd })
        okList.push(f.name)
      } catch (e:any) {
        failList.push(f.name)
        // 若是 400 多半是不支援的副檔名或其他驗證；我們繼續傳下一張
        continue
      }
    }

    // 成功提示（即使部分失敗也能上架完成）
    if (failList.length === 0) {
      alert(`商品上架成功！共上傳 ${okList.length} 張圖片。`)
    } else {
      alert(`商品已上架。\n成功 ${okList.length} 張，失敗 ${failList.length} 張：\n- ` + failList.join('\n- '))
    }
    router.push(`/sale_item/${saleItemId}`)
  } catch (error) {
    console.error(error)
    alert('上架商品失敗，請稍後再試。')
  }
}


</script>

<style scoped>
/* 版心卡片 */
.sale-wrap{
  width:min(920px, 92vw);
  margin: 28px auto 80px;
  background:#fff;
  border:1px solid #e6e8eb;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(2,6,23,.06);
  padding: 22px 24px 28px;
}
.sale-head h2{ margin:0 0 6px; font-size:22px; letter-spacing:.3px; }
.muted{ color:#64748b; }
.tiny{ font-size:12px; }

/* 表單樣式 */
.sale-form{ display:flex; flex-direction:column; gap:16px; }
.field label{ display:block; font-weight:700; margin-bottom:6px; }
.input{
  width:100%; padding: 10px 12px; border-radius: 12px;
  border:1px solid #e6e8eb; background:#fff; color:#0f172a;
  transition: border-color .18s cubic-bezier(.2,.8,.2,1), box-shadow .18s cubic-bezier(.2,.8,.2,1);
}
.input:focus{ outline:none; border-color:#9db7ff; box-shadow:0 0 0 4px rgba(37,99,235,.14); }
.textarea{ resize:vertical; }

.grid-2{ display:grid; grid-template-columns: repeat(2,1fr); gap:14px; }
@media (max-width: 720px){ .grid-2{ grid-template-columns:1fr; } }

.input-affix{ position:relative; }
.input-affix .prefix{ position:absolute; left:10px; top:50%; transform:translateY(-50%); color:#64748b; }
.no-padding-left{ padding-left:26px; }

/* 上傳區（藍色虛線） */
.uploader{
  position:relative;
  border:2px dashed #b6ccff;
  border-radius:16px;
  background: linear-gradient(180deg, #fff, #fbfdff);
  padding:16px;
  transition: box-shadow .18s ease, border-color .18s ease;
}
.uploader.is-drag{
  border-color:#8fb1ff;
  box-shadow:0 0 0 6px rgba(37,99,235,.12);
}
.file-input{ position:absolute; inset:0; opacity:0; cursor:pointer; }

/* 縮圖網格：相片穩穩排序＋最後一格是新增卡 */
.thumbs-grid{
  display:grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap:12px;
  align-items:stretch;
}
.tile{
  position:relative;
  border:1px solid #e6e8eb;
  border-radius:14px;
  background:#f6f8fb;
  overflow:hidden;
  box-shadow:0 4px 14px rgba(2,6,23,.06);
  aspect-ratio:1/1;
}
.tile img{ width:100%; height:100%; object-fit:contain; }

/* 右上角小叉叉 */
.tile-x{
  position:absolute; top:6px; right:6px;
  width:26px; height:26px; border-radius:50%;
  border:1px solid #e6e8eb; background:#ffffffcc;
  color:#0f172a; font-weight:900; line-height:24px;
  display:flex; align-items:center; justify-content:center;
  cursor:pointer;
}
.tile-x:hover{ filter:brightness(0.95); }

/* 新增卡（相機圖示；永遠最後一格） */
.add-tile{
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  border:1px dashed #b6ccff;
  border-radius:14px;
  background:#f3f7ff;
  color:#0f172a; text-align:center; padding:12px;
  cursor:pointer;
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
  aspect-ratio:1/1;
}
.add-tile:hover{ transform:translateY(-1px); box-shadow:0 4px 14px rgba(2,6,23,.06); border-color:#9db7ff; }
.cam{ font-size:28px; margin-bottom:6px; }
.add-text{ font-weight:800; line-height:1.3; }
.btn-mini{
  display:inline-block; padding:2px 8px; border-radius:999px;
  border:1px solid #b6ccff; background:#fff; font-weight:800;
}

/* 動作列 */
.actions{ margin-top:8px; }
.btn{
  display:inline-flex; align-items:center; gap:8px;
  padding:10px 14px; border-radius:12px;
  border:1px solid #e6e8eb;
  background: linear-gradient(180deg, #fff 70%, #fbfdff 30%);
  color:#0f172a; cursor:pointer;
  transition:transform .18s cubic-bezier(.2,.8,.2,1), box-shadow .18s cubic-bezier(.2,.8,.2,1), border-color .18s cubic-bezier(.2,.8,.2,1);
}
.btn:hover{ transform:translateY(-1px); box-shadow:0 4px 14px rgba(2,6,23,.06); border-color:#b6ccff; }
.btn--primary{
  background: linear-gradient(180deg, rgba(37,99,235,.12), rgba(6,182,212,.10));
  color:#0b1220; font-weight:800; border-color:#9db7ff;
}
.hint{ color:#64748b; font-weight:400; margin-left:6px; }
.picker {
  width: 250px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
