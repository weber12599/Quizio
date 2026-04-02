<template>
    <div class="student-view">
        <div v-if="!isConnected" class="login-panel card">
            <h2>Join a Game</h2>
            <p class="subtitle">
                Enter the Room PIN and your student credentials.
            </p>

            <div class="form-group">
                <label>Room PIN: </label>
                <input
                    v-model="roomPin"
                    placeholder="e.g. 1234"
                    type="text"
                    inputmode="numeric"
                />
            </div>

            <div class="form-group">
                <label>Student ID: </label>
                <input
                    v-model="studentId"
                    placeholder="Enter your student ID"
                    type="text"
                />
            </div>

            <div class="form-group">
                <label>Password: </label>
                <input
                    v-model="password"
                    placeholder="Enter your password"
                    type="password"
                    @keyup.enter="joinRoom"
                />
            </div>

            <button @click="joinRoom" class="btn-primary" :disabled="isLoading">
                {{ isLoading ? 'Connecting...' : 'Join Room' }}
            </button>

            <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>
        </div>

        <div v-else class="game-panel">
            <div class="room-header card">
                <h2>Room: {{ roomPin }}</h2>
                <div class="status-indicator">
                    <span class="pulse-dot"></span>
                    Connected
                </div>
                <button @click="leaveRoom" class="btn-danger small-btn">
                    Leave
                </button>
            </div>

            <div class="feed-container">
                <div
                    v-if="questionsFeed.length === 0"
                    class="waiting-card card"
                >
                    <div class="loader-spinner"></div>
                    <h3>Waiting for Teacher...</h3>
                    <p>
                        Questions will appear here automatically when the
                        teacher broadcasts them.
                    </p>
                </div>

                <div v-else class="question-list">
                    <div v-for="q in questionsFeed" :key="q.id" class="card">
                        <div class="q-meta">
                            <span class="q-type">{{ q.type }}</span>
                        </div>
                        <h3 class="q-content">{{ q.content }}</h3>
                        <p class="text-muted">
                            Options will be rendered here...
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
}

// --- State ---
const roomPin = ref('')
const studentId = ref('')
const password = ref('')
const errorMessage = ref('')
const isConnected = ref(false)
const isLoading = ref(false)

// Store the broadcasted questions
const questionsFeed = ref<Question[]>([])

// --- Methods ---
const joinRoom = () => {
    errorMessage.value = ''

    // Basic validation
    if (!roomPin.value || !studentId.value || !password.value) {
        errorMessage.value = 'Please fill in all fields.'
        return
    }

    isLoading.value = true
    socket.connect()

    socket.once('connect', () => {
        // Emit join_room with role 'client'
        // The backend will verify credentials with the Data API automatically
        socket.emit('join_room', {
            room_pin: roomPin.value,
            role: 'client',
            student_id: studentId.value,
            password: password.value
        })
    })
}

const leaveRoom = () => {
    socket.disconnect()
    isConnected.value = false
    questionsFeed.value = []
    errorMessage.value = ''
    isLoading.value = false
}

// --- Lifecycle & Socket Events ---
onMounted(() => {
    // 1. Successful connection indicator
    // When the backend broadcasts room_state, it confirms we are in.
    socket.on('room_state', (data: { room_pin: string; players: string[] }) => {
        if (String(data.room_pin) === String(roomPin.value)) {
            isConnected.value = true
            isLoading.value = false
        }
    })

    // 2. Handle connection errors or bad credentials
    socket.on('error', (data: { message: string }) => {
        errorMessage.value = data.message
        isLoading.value = false
        socket.disconnect()
        isConnected.value = false
    })

    // 3. Listen for incoming questions from the teacher
    socket.on('new_questions', (data: { questions: Question[] }) => {
        console.log('📝 Received new questions:', data.questions)

        // Append new questions to the feed
        data.questions.forEach((incomingQ) => {
            // Prevent duplicates if teacher broadcasts the same question again
            if (!questionsFeed.value.some((q) => q.id === incomingQ.id)) {
                questionsFeed.value.push(incomingQ)
            }
        })
    })
})

onUnmounted(() => {
    socket.disconnect()
    socket.off('room_state')
    socket.off('error')
    socket.off('new_questions')
})
</script>

<style scoped>
/* --------------------------------------
   Layout Structure
--------------------------------------- */
.student-view {
    padding: 20px 15px;
    max-width: 800px;
    margin: 0 auto;
}

.login-panel {
    max-width: 400px;
    margin: 10vh auto;
    text-align: center;
}

.login-panel h2 {
    color: var(--primary-color);
    margin-bottom: 8px;
}

.subtitle {
    color: var(--text-muted);
    margin-bottom: 24px;
    font-size: 0.95rem;
}

.login-panel .form-group {
    text-align: left;
}

.game-panel {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

/* --------------------------------------
   Top Header Bar
--------------------------------------- */
.room-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-left: 4px solid var(--primary-color);
}

.room-header h2 {
    margin: 0;
    font-size: 1.25rem;
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--success-color);
    font-weight: 600;
    font-size: 0.9rem;
    background: var(--chip-bg);
    padding: 6px 12px;
    border-radius: 20px;
}

.pulse-dot {
    width: 8px;
    height: 8px;
    background-color: var(--success-color);
    border-radius: 50%;
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0% {
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4);
    }
    70% {
        box-shadow: 0 0 0 6px rgba(16, 185, 129, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
    }
}

/* --------------------------------------
   Feed Area & Cards
--------------------------------------- */
.feed-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.waiting-card {
    text-align: center;
    padding: 60px 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
    border: 2px dashed var(--border-color);
    background: transparent;
    box-shadow: none;
}

.waiting-card h3 {
    color: var(--text-main);
    margin: 0;
}

.waiting-card p {
    color: var(--text-muted);
    margin: 0;
}

.loader-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid var(--border-color);
    border-top-color: var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

.question-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.q-meta {
    margin-bottom: 12px;
}

.q-type {
    background: var(--chip-bg);
    color: var(--primary-color);
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
}

.q-content {
    font-size: 1.2rem;
    color: var(--text-main);
    line-height: 1.5;
    margin: 0 0 16px 0;
}

.text-muted {
    color: var(--text-muted);
    font-size: 0.9rem;
    font-style: italic;
}

@media (max-width: 480px) {
    .room-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
    }
    .room-header button {
        width: 100%;
    }
}
</style>
