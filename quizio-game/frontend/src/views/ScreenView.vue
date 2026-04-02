<template>
    <div class="screen-view">
        <h1>Projector Screen</h1>

        <div v-if="!isConnected">
            <div>
                <label>Enter Room PIN: </label>
                <input v-model="roomPin" />
            </div>
            <button @click="joinAsScreen" style="margin-top: 10px">
                Connect Screen
            </button>
        </div>

        <div v-else>
            <h2>Join with PIN: {{ roomPin }}</h2>
            <div class="player-grid">
                <div
                    v-for="player in players"
                    :key="player"
                    class="player-card"
                >
                    {{ player }}
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { socket } from '../utils/socket'

const roomPin = ref('1234')
const isConnected = ref(false)
const players = ref<string[]>([])

// Join the room as Screen (Projector)
const joinAsScreen = () => {
    socket.connect()

    socket.once('connect', () => {
        socket.emit('join_room', {
            room_pin: roomPin.value,
            role: 'screen',
            student_id: 'Projector',
            password: ''
        })
        isConnected.value = true
    })
}

onMounted(() => {
    socket.on('room_state', (data: { room_pin: string; players: string[] }) => {
        if (data.room_pin === roomPin.value) {
            players.value = data.players
        }
    })
})

onUnmounted(() => {
    socket.disconnect()
    socket.off('room_state')
})
</script>

<style scoped>
.screen-view {
    padding: 20px;
    text-align: center;
}
.player-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
    margin-top: 20px;
}
.player-card {
    padding: 10px 20px;
    background-color: #4caf50;
    color: white;
    border-radius: 8px;
    font-weight: bold;
}
</style>
