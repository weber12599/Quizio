<template>
    <div class="screen-view">
        <ButtonLangToggle />

        <div v-if="!isConnected" class="login-panel card">
            <h2>{{ $t('screen.title') }}</h2>
            <p class="subtitle">
                {{ $t('screen.subtitle') }}
            </p>

            <div class="form-group">
                <label>{{ $t('common.room_pin') }}</label>
                <input
                    v-model="roomPin"
                    :placeholder="$t('screen.placeholder_pin')"
                    @keyup.enter="joinAsScreen"
                />
            </div>

            <button
                @click="joinAsScreen"
                class="btn-primary"
                :disabled="isLoading"
            >
                {{
                    isLoading
                        ? $t('common.connecting')
                        : $t('screen.btn_connect')
                }}
            </button>
            <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>
        </div>

        <div v-else class="display-wrapper">
            <div class="screen-header-minimal">
                <div class="header-right">
                    <span class="player-count">
                        {{ $t('screen.students_joined') }}
                        <strong>{{ players.length }}</strong>
                    </span>
                </div>
            </div>

            <div v-if="currentView === 'lobby'" class="lobby-state-split">
                <div class="join-hero-card card">
                    <div class="qr-col">
                        <QrcodeVue
                            :value="joinUrl"
                            :size="220"
                            level="H"
                            class="hero-qr"
                        />
                    </div>
                    <div class="text-col">
                        <div class="step-text">
                            {{ $t('screen.join_at')
                            }}<strong>{{ joinUrl }}</strong>
                        </div>
                        <div class="step-subtext">
                            {{ $t('common.room_pin') }}
                        </div>
                        <div class="hero-pin">{{ roomPin }}</div>
                    </div>
                </div>

                <div class="waiting-hero-card card">
                    <div class="waiting-header">
                        <div class="pulse-ring"></div>
                        <h2>{{ $t('screen.waiting_host') }}</h2>
                    </div>

                    <div class="players-container">
                        <div v-if="players.length === 0" class="empty-players">
                            {{ $t('screen.scan_to_join_desc') }}
                        </div>
                        <div v-else class="chips-grid">
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
            </div>

            <div v-else class="game-active-state">
                <div
                    v-if="currentView === 'question'"
                    class="question-display-card card"
                >
                    <div class="q-meta">
                        <span class="q-type">{{
                            formatQuestionType(displayedQuestion?.type || '')
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
                            <div class="stats-label">
                                {{ $t('screen.responses_received') }}
                            </div>
                        </div>
                    </div>
                </div>

                <div
                    v-else-if="currentView === 'leaderboard'"
                    class="leaderboard-state"
                >
                    <div class="leaderboard-card card">
                        <h1 class="lb-title">{{ $t('screen.top_scorers') }}</h1>
                        <div class="podium">
                            <div
                                v-for="(player, idx) in leaderboard.slice(0, 5)"
                                :key="idx"
                                class="lb-row"
                                :class="'rank-' + (idx + 1)"
                            >
                                <span class="lb-rank">#{{ idx + 1 }}</span>
                                <span class="lb-name">{{ player.name }}</span>
                                <span class="lb-score"
                                    >{{ player.score }}
                                    {{ $t('common.pts') }}</span
                                >
                            </div>
                            <div
                                v-if="leaderboard.length === 0"
                                class="empty-stats"
                            >
                                {{ $t('screen.no_scores') }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { socket } from '../utils/socket'
import QrcodeVue from 'qrcode.vue'
import { formatQuestionType } from '../utils/locales'
import ButtonLangToggle from '../components/ButtonLangToggle.vue'

// Initialize i18n
const { t } = useI18n()

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
const answerStats = ref<Record<string, number>>({})
const totalAnswers = ref(0)

// Leaderboard Data
const leaderboard = ref<PlayerScore[]>([])

// --- Computed ---

// Raw URL string for the QR Code component
const joinUrl = computed(() => {
    if (!roomPin.value) return ''
    const baseUrl = window.location.origin
    return `${baseUrl}/join?pin=${roomPin.value}`
})

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
        // localized fallback for boolean options
        return [t('common.true_option'), t('common.false_option')]
    }
    return parsedOpts
}

const getBarPercentage = (idx: number | string): number => {
    if (totalAnswers.value === 0) return 0
    const count = answerStats.value[idx] || 0
    return Math.round((count / totalAnswers.value) * 100)
}

// --- Methods ---

// Reusable join logic for both manual and auto-reconnect
const performJoin = (pin: string) => {
    isLoading.value = true
    socket.connect()

    socket.once('connect', () => {
        socket.emit('join_room', {
            room_pin: pin,
            role: 'screen'
        })

        // Save the PIN to local storage for auto-reconnect on refresh
        localStorage.setItem('quizio_screen_pin', pin)
    })
}

const joinAsScreen = () => {
    errorMessage.value = ''
    if (!roomPin.value.trim()) {
        errorMessage.value = t('screen.error_invalid_pin')
        return
    }
    performJoin(roomPin.value)
}

// --- Lifecycle & Socket Events ---
onMounted(() => {
    // Check local storage for auto-reconnect
    const savedPin = localStorage.getItem('quizio_screen_pin')
    if (savedPin && !isConnected.value) {
        roomPin.value = savedPin
        performJoin(savedPin)
    }

    // 1. Room state updates
    socket.on('room_state', (data: { room_pin: string; players: string[] }) => {
        if (String(data.room_pin) === String(roomPin.value)) {
            players.value = [...data.players]
            isConnected.value = true
            isLoading.value = false
        }
    })

    // 2. Display a question
    socket.on('display_question', (data: { question: Question | null }) => {
        if (data.question) {
            displayedQuestion.value = data.question
            currentView.value = 'question'
            answerStats.value = {}
            totalAnswers.value = 0
        } else {
            displayedQuestion.value = null
            if (currentView.value !== 'leaderboard') {
                currentView.value = 'lobby'
            }
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

    // 4. Show Leaderboard
    socket.on('show_leaderboard', (data: { leaderboard: PlayerScore[] }) => {
        leaderboard.value = data.leaderboard
        currentView.value = 'leaderboard'
    })

    // 5. Handle errors
    socket.on('error', (data: { message: string }) => {
        // If the error message from backend has dynamic translation needs,
        // you may handle it here, otherwise we display as is.
        errorMessage.value = data.message
        isLoading.value = false
        socket.disconnect()
        isConnected.value = false

        // Clear local storage if the room doesn't exist or host ended the game
        localStorage.removeItem('quizio_screen_pin')
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
    min-height: calc(100vh - 40px);
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
    gap: 20px;
    flex: 1;
}

/* --------------------------------------
   Minimal Header
--------------------------------------- */
.screen-header-minimal {
    display: flex;
    justify-content: flex-end;
    align-items: center;
}

.player-count {
    font-size: 1.5rem;
    color: var(--text-main);
    background: var(--chip-bg);
    padding: 10px 24px;
    border-radius: 12px;
    border: 2px solid var(--chip-border);
}
.player-count strong {
    color: var(--primary-color);
    font-size: 1.8rem;
    margin-left: 8px;
}

/* --------------------------------------
   Split Lobby State (Robust & Beautiful)
--------------------------------------- */
.lobby-state-split {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 24px;
}

/* Top Card: Join Info */
.join-hero-card {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 60px;
    padding: 50px;
    border: 4px solid var(--primary-light);
    background: var(--bg-card);
}

.hero-qr {
    border-radius: 16px;
    padding: 12px;
    background: white;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.text-col {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
}

.step-text {
    font-size: 2.5rem;
    color: var(--text-main);
}
.step-text strong {
    color: var(--primary-color);
    font-weight: 900;
}

.step-subtext {
    font-size: 1.8rem;
    color: var(--text-muted);
    margin-top: 15px;
    font-weight: 700;
}

.hero-pin {
    font-size: 6.5rem;
    font-weight: 900;
    letter-spacing: 0.1em;
    color: var(--text-main);
    line-height: 1;
    margin-top: 5px;
    text-shadow: 2px 2px 0px rgba(99, 102, 241, 0.2);
}

/* Bottom Card: Waiting State */
.waiting-hero-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 40px;
    background: rgba(99, 102, 241, 0.03);
    border: 2px dashed var(--border-color);
}

.waiting-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 20px;
    margin-bottom: 40px;
}

.waiting-header h2 {
    font-size: 2.2rem;
    color: var(--text-muted);
    font-weight: 700;
    margin: 0;
}

/* Pulse Ring Animation */
.pulse-ring {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: var(--primary-color);
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

/* Players Grid */
.players-container {
    width: 100%;
}

.empty-players {
    text-align: center;
    font-size: 1.8rem;
    color: var(--text-muted);
    font-style: italic;
    opacity: 0.7;
}

.chips-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    justify-content: center;
}

.massive-chip {
    font-size: 1.8rem;
    padding: 12px 30px;
    border-radius: 20px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    background: var(--bg-card);
    border: 2px solid var(--border-color);
    color: var(--text-main);
    font-weight: 700;
    animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes popIn {
    0% {
        transform: scale(0.5);
        opacity: 0;
    }
    100% {
        transform: scale(1);
        opacity: 1;
    }
}

/* --------------------------------------
   Active Game State Layout
--------------------------------------- */
.game-active-state {
    display: flex;
    flex: 1;
    position: relative;
}

/* --------------------------------------
   Question Display & Bar Charts
--------------------------------------- */
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
    transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
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
    .join-hero-card {
        flex-direction: column;
        gap: 30px;
        text-align: center;
    }
    .text-col {
        align-items: center;
    }
    .hero-pin {
        font-size: 5rem;
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
