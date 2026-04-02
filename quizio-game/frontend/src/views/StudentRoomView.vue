<template>
    <div class="room-view">
        <div v-if="connectionError" class="error-screen">
            <h2>Connection Failed</h2>
            <p>{{ connectionError }}</p>
            <button @click="goBack">Go Back to Login</button>
        </div>

        <div v-else-if="!isConnected" class="loading-screen">
            <h2>Connecting to Game Room...</h2>
        </div>

        <div v-else class="game-screen">
            <div class="header">
                <span class="pin">PIN: {{ route.params.pin }}</span>
                <span class="status">Waiting for host to start...</span>
            </div>

            <h1>You're in!</h1>
            <p>See your nickname on the screen</p>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { socket } from '../utils/socket'

const route = useRoute()
const router = useRouter()

const isConnected = ref(false)
const connectionError = ref('')

// Extract parameters from the route URL
const pin = route.params.pin as string
const studentId = route.params.student_id as string
const password = route.params.pwd as string

const goBack = () => {
    router.push({ name: 'join' })
}

onMounted(() => {
    // Setup socket error listener sent by backend
    socket.on('error', (data: { message: string }) => {
        connectionError.value = data.message
        socket.disconnect()
    })

    // Connect to Socket.io server
    socket.connect()

    socket.once('connect', () => {
        // Send join_room request with credentials for backend verification
        socket.emit('join_room', {
            room_pin: pin,
            role: 'client',
            student_id: studentId,
            password: password
        })

        isConnected.value = true
    })

    socket.on('disconnect', () => {
        isConnected.value = false
        if (!connectionError.value) {
            connectionError.value = 'Disconnected from server.'
        }
    })
})

onUnmounted(() => {
    socket.disconnect()
    socket.off('error')
})
</script>

<style scoped>
.room-view {
    text-align: center;
    padding: 20px;
}
.header {
    display: flex;
    justify-content: space-between;
    background-color: #f1f1f1;
    padding: 10px 20px;
    border-radius: 4px;
    margin-bottom: 40px;
    font-weight: bold;
}
.error-screen {
    color: red;
    margin-top: 50px;
}
.game-screen h1 {
    font-size: 3rem;
    color: #4caf50;
}
</style>
