<template>
    <div v-for="(message, index) in messages" :key="index">
        <div v-if="message.sender_uuid == userId">
          <div style="text-align: right;">
            {{ message.message }}
          </div>
        </div>
        <div v-else>
          <div style="text-align: left;">
            {{ message.message }}
          </div>
        </div>
    </div>
  <el-input v-model="input" style="width: 240px" placeholder="Please input" />
  <el-button @click="send"></el-button>
</template>

<script setup lang="ts">
import { ofetch } from 'ofetch'
import { onMounted, ref, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const query = route.query
const peer = query.peer as string
const input = ref('')
const userId = ref('')

/*
type MessageJson struct {
	Sender_uuid string `json:"sender_uuid"`
	Message     string `json:"message"`
}
*/
interface MessageReq {
  reciver_uuid: string,
  message: string
}

interface ChatMessage {
  sender_uuid: string
  reciver_uuid: string
  message: string
  timestamp?: string
}


const messages = ref<ChatMessage[]>([])

let ws: WebSocket | null = null

const send = () => {
  const req = {
    reciver_uuid: peer,
    message: input.value
  } as MessageReq
  ws?.send(JSON.stringify(req))
  input.value = ''
}


onMounted(async () => {
  userId.value = await ofetch('/api/user_id')
  
  ws = new WebSocket(`/api/message/message`)
  
  ws.onopen = () => {
    ws?.send(peer)
  }
  let isHistory = 1;
  ws.onmessage = (eventOri) => {
    const event = JSON.parse(eventOri.data)
    console.log(event)
    if (isHistory) {
      messages.value = event as ChatMessage[]
      isHistory = 0
      return
    }
    console.log(messages)
    messages.value.push(event)
  }

  ws.onclose = () => {
    console.log('WebSocket closed')
  }
})

onUnmounted(() => {
  if (ws) ws.close()
})

</script>