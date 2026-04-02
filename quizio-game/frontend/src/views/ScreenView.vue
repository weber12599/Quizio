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

            <div v-if="currentView === 'lobby'" class="lobby-state">
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

            <div v-else-if="currentView === 'question'" class="question-state">
                <div class="question-display-card card">
                    <div class="q-meta">
                        <span class="q-type">{{
                            displayedQuestion?.type
                        }}</span>
                    </div>
                    <h1 class="q-content-huge">
                        {{ displayedQuestion?.content }}
                    </h1>

                    <div class="stats-container">
                        <div v-if="isChoiceQuestion(displayedQuestion?.type)">
                            <div
                                v-for="(opt, idx) in getOptions(
                                    displayedQuestion
                                )"
                                :key="idx"
                                class="stat-bar-wrapper"
                            >
                                <div class="stat-label">{{ opt }}</div>
                                <div class="bar-bg">
                                    <div
                                        class="bar-fill"
                                        :style="{
                                            width: getBarPercentage(idx) + '%'
                                        }"
                                    ></div>
                                    <span
                                        class="bar-count"
                                        :class="{
                                            'text-white':
                                                getBarPercentage(idx) > 10
                                        }"
                                    >
                                        {{ answerStats[idx] || 0 }} ({{
                                            getBarPercentage(idx)
                                        }}%)
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div v-else class="text-stats-container">
                            <div class="big-number">{{ totalAnswers }}</div>
                            <div class="stats-label">Responses Received</div>
                        </div>
                    </div>
                </div>
            </div>

            <div
                v-else-if="currentView === 'leaderboard'"
                class="leaderboard-state"
            >
                <div class="leaderboard-card card">
                    <h1 class="lb-title">🏆 Top Scorers 🏆</h1>
                    <div class="podium">
                        <div
                            v-for="(player, idx) in leaderboard.slice(0, 5)"
                            :key="idx"
                            class="lb-row"
                            :class="'rank-' + (idx + 1)"
                        >
                            <span class="lb-rank">#{{ idx + 1 }}</span>
                            <span class="lb-name">{{ player.name }}</span>
                            <span class="lb-score">{{ player.score }} pts</span>
                        </div>
                        <div
                            v-if="leaderboard.length === 0"
                            class="empty-stats"
                        >
                            No scores available yet.
                        </div>
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

interface PlayerScore {
    name: string
    score: number
}

// --- State ---
const roomPin = ref('')
const isConnected = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')
const players = ref<string[]>([])

// View Management
const currentView = ref<'lobby' | 'question' | 'leaderboard'>('lobby')

// Question Data
const displayedQuestion = ref<Question | null>(null)

// Stats Data
// For single/multiple: key is index. For boolean: 0 (True), 1 (False)
const answerStats = ref<Record<string, number>>({})
const totalAnswers = ref(0)

// Leaderboard Data
const leaderboard = ref<PlayerScore[]>([])

// --- Helpers ---
const isChoiceQuestion = (type?: string) => {
    return type === 'single' || type === 'multiple' || type === 'boolean'
}

const getOptions = (q: Question | null): string[] => {
    if (!q) return []
    let optsRaw = q.options
    let parsedOpts: string[] = []

    if (Array.isArray(optsRaw)) {
        parsedOpts = optsRaw
    } else if (typeof optsRaw === 'string') {
        try {
            const parsed = JSON.parse(optsRaw)
            if (Array.isArray(parsed)) parsedOpts = parsed
            else
                parsedOpts = Object.entries(parsed).map(
                    ([k, v]) => `${k}: ${v}`
                )
        } catch {
            parsedOpts = []
        }
    }

    if (q.type === 'boolean' && parsedOpts.length === 0) {
        return ['是 (True)', '非 (False)']
    }
    return parsedOpts
}

const getBarPercentage = (idx: number | string): number => {
    if (totalAnswers.value === 0) return 0
    const count = answerStats.value[idx] || 0
    return Math.round((count / totalAnswers.value) * 100)
}

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
        socket.emit('join_room', {
            room_pin: roomPin.value,
            role: 'screen'
        })
    })
}

// --- Lifecycle & Socket Events ---
onMounted(() => {
    // 1. Room state updates
    socket.on('room_state', (data: { room_pin: string; players: string[] }) => {
        if (String(data.room_pin) === String(roomPin.value)) {
            players.value = [...data.players]
            isConnected.value = true
            isLoading.value = false
        }
    })

    // 2. Display a question (Switch to Question View)
    socket.on('display_question', (data: { question: Question | null }) => {
        if (data.question) {
            displayedQuestion.value = data.question
            currentView.value = 'question'
            answerStats.value = {}
            totalAnswers.value = 0
        } else {
            displayedQuestion.value = null
            currentView.value = 'lobby'
        }
    })

    // 3. Update real-time statistics
    socket.on(
        'update_stats',
        (data: { stats: Record<string, number>; total: number }) => {
            answerStats.value = data.stats
            totalAnswers.value = data.total
        }
    )

    // 4. Show Leaderboard (Triggered by Host)
    socket.on('show_leaderboard', (data: { leaderboard: PlayerScore[] }) => {
        leaderboard.value = data.leaderboard
        currentView.value = 'leaderboard'
    })

    // 5. Handle errors
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
    socket.off('update_stats')
    socket.off('show_leaderboard')
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
   Question Display & Bar Charts
--------------------------------------- */
.question-state {
    display: flex;
    flex: 1;
}

.question-display-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 60px 80px;
    border: 4px solid var(--primary-light);
}

.q-meta {
    margin-bottom: 20px;
    text-align: center;
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
    font-size: 3.5rem;
    line-height: 1.4;
    color: var(--text-main);
    text-align: center;
    margin: 0 auto 50px;
    font-weight: 800;
}

.stats-container {
    width: 100%;
    margin-top: auto;
}

/* Bar Chart Layout */
.stat-bar-wrapper {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 24px;
}

.stat-label {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--text-main);
}

.bar-bg {
    background: var(--border-color);
    height: 60px;
    border-radius: 12px;
    position: relative;
    overflow: hidden;
}

.bar-fill {
    background: linear-gradient(
        90deg,
        var(--primary-color) 0%,
        var(--primary-light) 100%
    );
    height: 100%;
    width: 0%;
    border-radius: 12px;
    transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1); /* Bouncy animation */
}

.bar-count {
    position: absolute;
    right: 20px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--text-main);
    z-index: 2;
    transition: color 0.3s ease;
}

.text-white {
    color: white !important;
}

/* Text Answers Stats */
.text-stats-container {
    text-align: center;
    background: var(--highlight-bg);
    padding: 40px;
    border-radius: 20px;
    border: 2px dashed var(--primary-light);
}

.big-number {
    font-size: 6rem;
    font-weight: 900;
    color: var(--primary-color);
    line-height: 1;
}

.stats-label {
    font-size: 2rem;
    color: var(--text-muted);
    font-weight: 600;
    margin-top: 10px;
}

/* --------------------------------------
   Leaderboard State
--------------------------------------- */
.leaderboard-state {
    display: flex;
    flex: 1;
    justify-content: center;
    align-items: center;
}

.leaderboard-card {
    width: 100%;
    max-width: 1000px;
    padding: 60px 80px;
    text-align: center;
    border: 4px solid var(--primary-color);
    background: var(--bg-card);
}

.lb-title {
    font-size: 4rem;
    color: var(--text-main);
    margin-bottom: 40px;
    font-weight: 900;
}

.podium {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.lb-row {
    display: flex;
    align-items: center;
    padding: 24px 40px;
    background: var(--highlight-bg);
    border-radius: 16px;
    font-size: 2.2rem;
    font-weight: 800;
    color: var(--text-main);
    border: 2px solid var(--border-color);
    transition: transform 0.3s ease;
}

/* Podium Colors */
.lb-row.rank-1 {
    background: linear-gradient(135deg, #ffd700 0%, #d4af37 100%);
    color: #000;
    transform: scale(1.05);
    border: none;
    box-shadow: 0 10px 20px rgba(212, 175, 55, 0.4);
    z-index: 3;
}

.lb-row.rank-2 {
    background: linear-gradient(135deg, #e0e0e0 0%, #bdbdbd 100%);
    color: #000;
    transform: scale(1.02);
    border: none;
    box-shadow: 0 8px 15px rgba(189, 189, 189, 0.4);
    z-index: 2;
}

.lb-row.rank-3 {
    background: linear-gradient(135deg, #cd7f32 0%, #a0522d 100%);
    color: #fff;
    border: none;
    box-shadow: 0 6px 12px rgba(160, 82, 45, 0.4);
    z-index: 1;
}

.lb-rank {
    width: 100px;
    text-align: left;
}

.lb-name {
    flex: 1;
    text-align: left;
}

.lb-score {
    font-weight: 900;
}

.empty-stats {
    font-size: 1.8rem;
    color: var(--text-muted);
    font-style: italic;
    padding: 40px;
}

/* Responsive adjustments */
@media (max-width: 1024px) {
    .pin-number {
        font-size: 2.5rem;
    }
    .q-content-huge {
        font-size: 2.5rem;
    }
    .lb-row {
        font-size: 1.5rem;
        padding: 16px 24px;
    }
    .lb-title {
        font-size: 2.5rem;
    }
}
</style>
