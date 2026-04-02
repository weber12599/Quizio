<template>
    <div class="host-view">
        <h1>Host Control Panel</h1>

        <div v-if="!isConnected">
            <div class="form-group">
                <label>Teacher Username: </label>
                <input v-model="username" placeholder="Enter username" />
            </div>
            <div class="form-group">
                <label>Password: </label>
                <input
                    v-model="password"
                    type="password"
                    placeholder="Enter password"
                />
            </div>
            <div class="form-group">
                <label>Room PIN: </label>
                <input
                    v-model="roomPin"
                    placeholder="Enter custom PIN (e.g. 1234)"
                />
            </div>

            <button @click="loginAndCreateRoom" style="margin-top: 15px">
                Login & Create Room
            </button>
            <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>
        </div>

        <div v-else>
            <h2>Room PIN: {{ roomPin }}</h2>
            <p>Status: Waiting for players...</p>

            <h3>Joined Players ({{ players.length }}):</h3>
            <ul>
                <li v-for="player in players" :key="player">{{ player }}</li>
            </ul>

            <button @click="leaveRoom" style="margin-top: 20px; color: red">
                End & Leave
            </button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { socket } from '../utils/socket'

const username = ref('')
const password = ref('')
const roomPin = ref('1234')
const errorMessage = ref('')
const isConnected = ref(false)
const players = ref<string[]>([])

// Store the token for fetching exams later
const authToken = ref('')

// Authenticate with Data Backend, then create the Socket.io room
const loginAndCreateRoom = async () => {
    errorMessage.value = ''
    if (!username.value || !password.value) {
        errorMessage.value = 'Please enter both username and password.'
        return
    }

    try {
        // Prepare form data for FastAPI OAuth2PasswordRequestForm
        const formData = new URLSearchParams()
        formData.append('username', username.value)
        formData.append('password', password.value)

        // Call Data Backend API to get the token
        // Note: Vite proxy needs to route '/api' to the Data Backend
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData.toString()
        })

        if (!response.ok) {
            throw new Error('Login failed. Please check your credentials.')
        }

        const data = await response.json()
        authToken.value = data.access_token

        console.log('Successfully obtained token from Data Backend.')

        // Now that we have the token, connect to Game Backend
        socket.connect()

        // Wait for connection to establish before emitting join event
        socket.once('connect', () => {
            socket.emit('join_room', {
                room_pin: roomPin.value,
                role: 'host',
                student_id: 'Host_Teacher', // Identifier for host
                password: '', // Not needed for host role in socket event
                token: authToken.value
            })
            isConnected.value = true
        })
    } catch (error: any) {
        errorMessage.value = error.message || 'An error occurred during login.'
    }
}

const leaveRoom = () => {
    socket.disconnect()
    isConnected.value = false
    players.value = []
    authToken.value = ''
}

onMounted(() => {
    // socket.onAny((eventName, ...args) => {
    //     console.log(`🚨 [Socket 雷達] 收到事件: ${eventName}`, args)
    // })
    // Listen for broadcasted room state to update player list
    socket.on(
        'room_state',
        async (data: { room_pin: string; players: string[] }) => {
            console.log('👉 [Host] 收到後端廣播的 room_state:', data)

            if (String(data.room_pin) === String(roomPin.value)) {
                // 🔥 Vue 3 的陣列更新：如果是用 ref，直接覆蓋 value 是可以的
                // 但為了確保絕對觸發更新，我們可以使用解構賦值重新建立一個新陣列
                players.value = [...data.players]

                // 等待 DOM 更新完畢
                await nextTick()
                console.log(
                    '✅ 畫面應該已經更新了！目前名單數量:',
                    players.value.length
                )
            }
        }
    )
})

onUnmounted(() => {
    socket.disconnect()
    socket.off('room_state')
})
</script>

<style scoped>
.host-view {
    padding: 20px;
}
.form-group {
    margin-bottom: 10px;
}
.form-group label {
    display: inline-block;
    width: 150px;
    font-weight: bold;
}
.error-msg {
    color: red;
    margin-top: 10px;
}
</style>
