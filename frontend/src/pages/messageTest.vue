<template>
  <vue-advanced-chat
    :current-user-id="currentUserId"
    :rooms="rooms"
    :messages="messages"
    :room-actions="roomActions"
  />
</template>

<script lang="ts" setup>
  import { ofetch } from 'ofetch'
  import { onMounted, ref } from 'vue'
  import { register } from 'vue-advanced-chat'
  register()

  // Or if you used CDN import
  // window['vue-advanced-chat'].register()

  const currentUserId = ref('1234')
  const rooms = ref([])
  const messages = ref([])
  const roomActions = ref([
    { name: 'inviteUser', title: 'Invite User' },
    { name: 'removeUser', title: 'Remove User' },
    { name: 'deleteRoom', title: 'Delete Room' }
  ])

  onMounted(async () => {
    currentUserId.value = await ofetch('/api/user_id')
    const userList = (await ofetch('/api/message/api/message/user_list')).user_list

    let count = 0
    for(const userRoom of userList) {
        const cur: any = {}
        cur.roomId = count.toString()
        count += 1
        rooms.value = [...rooms.value, cur]
    }
  })
</script>
