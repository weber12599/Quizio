<template>
    <div class="screen-view">
        <div v-if="!isConnected" class="login-panel card">
            <h2>Screen / Projector Setup</h2>
            <p class="subtitle">
                Enter the active Room PIN to connect this display.
            </p>

            <div class="form-group">
                <label>Room PIN:</label>
                <input
                    v-model="roomPin"
                    placeholder="Enter Room PIN (e.g. 1234)"
                    @keyup.enter="joinAsScreen"
                />
            </div>

            <button
                @click="joinAsScreen"
                class="btn-primary"
                :disabled="isLoading"
            >
                {{ isLoading ? 'Connecting...' : 'Connect to Room' }}
            </button>
            <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>
        </div>

        <div v-else class="display-wrapper">
            <div class="screen-header card">
                <div class="header-left">
                    <span class="join-instruction"
                        >Join at <strong>quizio.com</strong></span
                    >
                </div>
                <div class="header-center">
                    <span class="pin-label">PIN:</span>
                    <span class="pin-number">{{ roomPin }}</span>
                </div>
                <div class="header-right">
                    <span class="player-count"
                        >Players: {{ players.length }}</span
                    >
                </div>
            </div>

            <div v-if="!displayedQuestion" class="lobby-state">
                <div class="idle-card card">
                    <div class="pulse-ring"></div>
                    <h2>Waiting for the host...</h2>
                    <p>The teacher will display questions here shortly.</p>
                </div>

                <div class="players-grid card">
                    <div v-if="players.length === 0" class="empty-players">
                        Waiting for students to join...
                    </div>
                    <div v-else class="chips-container">
                        <div
                            v-for="player in players"
                            :key="player"
                            class="player-chip massive-chip"
                        >
                            {{ player }}
                        </div>
                    </div>
                </div>
            </div>

            <div v-else class="question-state">
                <div class="question-display-card card">
                    <div class="q-meta">
                        <span class="q-type">{{ displayedQuestion.type }}</span>
                    </div>
                    <h1 class="q-content-huge">
                        {{ displayedQuestion.content }}
                    </h1>

                    <div class="stats-placeholder">
                        <p class="stats-hint">
                            Student answers and statistics will appear here.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { socket } from '../utils/socket'

// --- Types ---
interface Question {
    id: number
    type: string
    content: string
    options?: any
    reference_answer: any
}

// --- State ---
const roomPin = ref('')
const isConnected = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')
const players = ref<string[]>([])
const displayedQuestion = ref<Question | null>(null)

// --- Methods ---
const joinAsScreen = () => {
    errorMessage.value = ''
    if (!roomPin.value.trim()) {
        errorMessage.value = 'Please enter a valid Room PIN.'
        return
    }

    isLoading.value = true
    socket.connect()

    socket.once('connect', () => {
        // Screen only needs room_pin and role to join
        socket.emit('join_room', {
            room_pin: roomPin.value,
            role: 'screen'
        })
    })
}

// --- Lifecycle & Socket Events ---
onMounted(() => {
    // 1. Listen for room state updates (player joins/leaves)
    socket.on('room_state', (data: { room_pin: string; players: string[] }) => {
        if (String(data.room_pin) === String(roomPin.value)) {
            players.value = [...data.players]
            isConnected.value = true
            isLoading.value = false
        }
    })

    // 2. Listen for the host displaying a question
    socket.on('display_question', (data: { question: Question | null }) => {
        console.log('🖥️ Screen received display event:', data)
        displayedQuestion.value = data.question
    })

    // 3. Handle errors (e.g., room does not exist)
    socket.on('error', (data: { message: string }) => {
        errorMessage.value = data.message
        isLoading.value = false
        socket.disconnect()
        isConnected.value = false
    })
})

onUnmounted(() => {
    socket.disconnect()
    socket.off('room_state')
    socket.off('display_question')
    socket.off('error')
})
</script>

<style scoped>
/* --------------------------------------
   Layout Structure
--------------------------------------- */
.screen-view {
    padding: 20px;
    max-width: 1400px;
    margin: 0 auto;
    min-height: calc(100vh - 80px);
    display: flex;
    flex-direction: column;
}

.login-panel {
    max-width: 480px;
    margin: 10vh auto;
}

.subtitle {
    color: var(--text-muted);
    margin-bottom: 24px;
}

.display-wrapper {
    display: flex;
    flex-direction: column;
    gap: 24px;
    flex: 1;
}

/* --------------------------------------
   Top Header Bar
--------------------------------------- */
.screen-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 32px;
    background: var(--bg-card);
    border-bottom: 4px solid var(--primary-light);
}

.header-left,
.header-right {
    flex: 1;
}

.header-right {
    text-align: right;
}

.join-instruction {
    font-size: 1.5rem;
    color: var(--text-main);
}

.join-instruction strong {
    color: var(--primary-color);
}

.header-center {
    display: flex;
    align-items: baseline;
    gap: 12px;
}

.pin-label {
    font-size: 1.5rem;
    color: var(--text-muted);
    font-weight: bold;
}

.pin-number {
    font-size: 3.5rem;
    font-weight: 900;
    letter-spacing: 0.1em;
    background: linear-gradient(135deg, var(--primary-light) 0%, #8b5cf6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.player-count {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--text-main);
    background: var(--chip-bg);
    padding: 8px 16px;
    border-radius: 12px;
    border: 1px solid var(--chip-border);
}

/* --------------------------------------
   Lobby State (Idle)
--------------------------------------- */
.lobby-state {
    display: flex;
    flex-direction: column;
    gap: 24px;
    flex: 1;
}

.idle-card {
    text-align: center;
    padding: 60px 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: var(--highlight-bg);
    border-color: var(--chip-border);
}

.idle-card h2 {
    font-size: 2.5rem;
    color: var(--primary-color);
    margin-bottom: 10px;
    z-index: 2;
}

.idle-card p {
    font-size: 1.2rem;
    color: var(--text-muted);
    z-index: 2;
}

/* Simple pulse animation for waiting state */
.pulse-ring {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: var(--primary-light);
    margin-bottom: 20px;
    animation: pulse-ring-anim 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse-ring-anim {
    0% {
        transform: scale(0.8);
        opacity: 0.8;
    }
    50% {
        transform: scale(1.5);
        opacity: 0;
    }
    100% {
        transform: scale(0.8);
        opacity: 0;
    }
}

.players-grid {
    flex: 1;
    min-height: 200px;
}

.empty-players {
    text-align: center;
    color: var(--text-muted);
    font-size: 1.5rem;
    padding: 40px;
    font-style: italic;
}

.chips-container {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    justify-content: center;
}

.massive-chip {
    font-size: 1.5rem;
    padding: 12px 24px;
    border-radius: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

/* --------------------------------------
   Question Display State
--------------------------------------- */
.question-state {
    display: flex;
    flex: 1;
}

.question-display-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 60px 40px;
    border: 4px solid var(--primary-light);
}

.q-meta {
    margin-bottom: 30px;
}

.q-type {
    background: var(--chip-bg);
    color: var(--primary-color);
    padding: 8px 20px;
    border-radius: 20px;
    font-size: 1.2rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    border: 2px solid var(--chip-border);
}

.q-content-huge {
    font-size: 3.5rem; /* Massive text for projector */
    line-height: 1.4;
    color: var(--text-main);
    max-width: 90%;
    margin: 0 auto 40px;
    font-weight: 800;
}

/* Placeholder for future bar charts */
.stats-placeholder {
    width: 100%;
    max-width: 800px;
    height: 200px;
    background: var(--bg-color);
    border: 2px dashed var(--border-color);
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: auto; /* Pushes it to the bottom if space allows */
}

.stats-hint {
    color: var(--text-muted);
    font-size: 1.2rem;
}

/* Responsive adjustments for smaller screens (e.g., testing on laptop) */
@media (max-width: 1024px) {
    .pin-number {
        font-size: 2.5rem;
    }
    .q-content-huge {
        font-size: 2.5rem;
    }
}
</style>
