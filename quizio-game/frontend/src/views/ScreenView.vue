<template>
    <div class="screen-view">
        <ButtonFloatingAction v-if="!isConnected" />

        <div v-if="!isConnected" class="login-container">
            <el-card
                class="login-card"
                shadow="always"
                :body-style="{ padding: '48px 40px' }"
            >
                <div class="text-center mb-5">
                    <h1 class="login-title">{{ $t('screen.title') }}</h1>
                    <p class="login-subtitle text-muted mt-2">
                        {{ $t('screen.subtitle') }}
                    </p>
                </div>

                <el-form
                    label-position="top"
                    @submit.prevent
                    @keyup.enter="joinAsScreen"
                    size="large"
                >
                    <el-form-item :label="$t('common.room_pin')">
                        <el-input
                            v-model="roomPin"
                            :placeholder="$t('placeholder.pin')"
                            class="pin-input"
                        />
                    </el-form-item>

                    <el-button
                        type="primary"
                        class="w-full mt-4"
                        size="large"
                        plain
                        @click="joinAsScreen"
                        :loading="isLoading"
                    >
                        {{
                            isLoading
                                ? $t('common.connecting')
                                : $t('screen.btn_connect')
                        }}
                    </el-button>
                </el-form>

                <el-alert
                    v-if="errorMessage"
                    :title="errorMessage"
                    type="error"
                    show-icon
                    center
                    class="mt-4"
                    :closable="false"
                />
            </el-card>
        </div>

        <div v-else class="display-wrapper">
            <div class="screen-header flex-between">
                <el-button
                    type="danger"
                    plain
                    size="large"
                    @click="leaveRoom"
                    class="leave-btn"
                >
                    <el-icon class="mr-2"><Close /></el-icon>
                    {{ $t('common.leave') }}
                </el-button>

                <div class="player-count-badge flex-align-center">
                    <span class="pulse-dot mr-3"></span>
                    <span class="count-label mr-2">{{
                        $t('screen.students_joined')
                    }}</span>
                    <span class="count-number">{{
                        playerStats.total_count
                    }}</span>
                </div>
            </div>

            <el-alert
                v-if="isReconnecting"
                :title="$t('common.network_disconnected')"
                type="warning"
                show-icon
                center
                class="my-4"
                :closable="false"
            />

            <div
                class="main-content-area"
                :class="{ 'is-lobby': currentView === 'lobby' }"
            >
                <div
                    v-if="currentView === 'lobby'"
                    class="lobby-state text-center w-full max-w-5xl"
                >
                    <el-card
                        class="lobby-card"
                        shadow="always"
                        :body-style="{
                            flex: 1,
                            display: 'flex',
                            flexDirection: 'column',
                            justifyContent: 'center',
                            alignItems: 'center',
                            padding: '40px 60px'
                        }"
                    >
                        <div class="lobby-grid w-full">
                            <div class="lobby-col border-b">
                                <div class="pin-label text-muted mb-2">
                                    {{ $t('common.room_pin') }}
                                </div>
                                <div class="pin-value text-primary">
                                    {{ roomPin }}
                                </div>
                                <div class="url-display text-muted mt-3">
                                    👉 {{ joinUrl }}
                                </div>
                            </div>

                            <div class="lobby-col flex-center w-full gap-4">
                                <div
                                    class="qr-container bg-white rounded-xl shadow-sm"
                                >
                                    <vue-qrcode
                                        :value="joinUrl"
                                        :width="220"
                                        :margin="1"
                                        type="image/webp"
                                        :color="{
                                            dark: '#000000',
                                            light: '#ffffff'
                                        }"
                                    />
                                </div>

                                <div
                                    class="text-muted waiting-text flex-center"
                                >
                                    <el-icon class="is-loading mr-2" :size="28"
                                        ><Loading
                                    /></el-icon>
                                    <span>{{ $t('screen.waiting_host') }}</span>
                                </div>
                            </div>
                        </div>
                    </el-card>
                </div>

                <div
                    v-else-if="currentView === 'question' && displayedQuestion"
                    class="w-full max-w-5xl"
                >
                    <GameQuestionCard
                        :question="displayedQuestion"
                        role="screen"
                        :stats="{ counts: answerStats, total: totalAnswers }"
                    />
                </div>

                <div
                    v-else-if="currentView === 'leaderboard'"
                    class="w-full max-w-4xl"
                >
                    <el-card
                        class="leaderboard-card"
                        shadow="always"
                        :body-style="{ padding: '40px' }"
                    >
                        <div class="text-center mb-5">
                            <h1 class="lb-title">
                                {{ $t('screen.top_scorers') }}
                            </h1>
                        </div>

                        <el-empty
                            v-if="leaderboard.length === 0"
                            :description="$t('screen.no_data')"
                            :image-size="120"
                        />

                        <div v-else class="lb-list flex-col gap-4">
                            <div
                                v-for="(student, index) in leaderboard"
                                :key="index"
                                class="lb-row flex-between"
                                :class="{
                                    'top-1': index === 0,
                                    'top-2': index === 1,
                                    'top-3': index === 2
                                }"
                            >
                                <div
                                    class="lb-rank-name flex-align-center gap-4"
                                >
                                    <div class="lb-rank flex-center">
                                        <span v-if="index === 0">🥇</span>
                                        <span v-else-if="index === 1">🥈</span>
                                        <span v-else-if="index === 2">🥉</span>
                                        <span v-else>{{ index + 1 }}</span>
                                    </div>
                                    <div class="lb-name">
                                        {{ student.name }}
                                    </div>
                                </div>
                                <div class="lb-score font-bold">
                                    {{ student.score }}
                                    <span class="text-muted text-sm">{{
                                        $t('common.pts')
                                    }}</span>
                                </div>
                            </div>
                        </div>
                    </el-card>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { socket } from '../utils/socket'
import ButtonFloatingAction from '../components/ButtonFloatingAction.vue'
import GameQuestionCard from '../components/GameQuestionCard.vue'
import VueQrcode from 'vue-qrcode'
import { Close, Loading } from '@element-plus/icons-vue'

const { t } = useI18n()

// --- State ---
const roomPin = ref('')
const isConnected = ref(false)
const isLoading = ref(false)
const isReconnecting = ref(false)
const errorMessage = ref('')

const currentView = ref<'lobby' | 'question' | 'leaderboard'>('lobby')
const displayedQuestion = ref<any>(null)
const answerStats = ref<Record<string, number>>({})
const totalAnswers = ref(0)
const leaderboard = ref<any[]>([])

const playerStats = ref({
    student_count: 0,
    guest_count: 0,
    total_count: 0
})

// --- URL & QR Code Computed ---
const joinUrl = computed(() => {
    const baseUrl = window.location.origin
    return `${baseUrl}/client?pin=${roomPin.value}`
})

// --- Methods ---
const joinAsScreen = () => {
    if (!roomPin.value) {
        errorMessage.value = t('student.error_fill_fields')
        return
    }

    isLoading.value = true
    errorMessage.value = ''

    const joinPayload = {
        room_pin: roomPin.value,
        role: 'screen',
        student_id: 'screen',
        password: ''
    }

    if (socket.connected) {
        socket.emit('join_room', joinPayload)
        localStorage.setItem('quizio_screen_pin', roomPin.value)
    } else {
        socket.once('connect', () => {
            socket.emit('join_room', joinPayload)
            localStorage.setItem('quizio_screen_pin', roomPin.value)
        })
        socket.connect()
    }
}

const leaveRoom = () => {
    socket.disconnect()
    localStorage.removeItem('quizio_screen_pin')

    isConnected.value = false
    isReconnecting.value = false
    currentView.value = 'lobby'
    displayedQuestion.value = null
    leaderboard.value = []
    answerStats.value = {}
    totalAnswers.value = 0
    playerStats.value = { student_count: 0, guest_count: 0, total_count: 0 }
    roomPin.value = ''
}

// --- Lifecycle ---
onMounted(() => {
    const savedPin = localStorage.getItem('quizio_screen_pin')
    if (savedPin && !isConnected.value) {
        roomPin.value = savedPin
        joinAsScreen()
    }

    socket.on('room_state', async (data: any) => {
        if (String(data.room_pin) === String(roomPin.value)) {
            isConnected.value = true
            isLoading.value = false
            isReconnecting.value = false
            errorMessage.value = ''

            if (data.player_stats) {
                playerStats.value = data.player_stats
            }
            await nextTick()
        }
    })

    socket.on('display_question', (data: any) => {
        if (data.question) {
            displayedQuestion.value = data.question
            currentView.value = 'question'
        } else {
            displayedQuestion.value = null
            currentView.value = 'lobby'
        }
    })

    socket.on('update_stats', (data: any) => {
        answerStats.value = data.stats
        totalAnswers.value = data.total
    })

    socket.on('show_leaderboard', (data: any) => {
        leaderboard.value = data.leaderboard
        currentView.value = 'leaderboard'
    })

    socket.on('error', (data: any) => {
        errorMessage.value = data.message
        isLoading.value = false

        localStorage.removeItem('quizio_screen_pin')
        socket.disconnect()
        isConnected.value = false
    })

    socket.on('disconnect', (reason) => {
        if (
            reason === 'io server disconnect' ||
            reason === 'io client disconnect'
        ) {
            isConnected.value = false
            isReconnecting.value = false
        } else {
            isReconnecting.value = true
        }
    })
})

onUnmounted(() => {
    socket.disconnect()
    socket.off('room_state')
    socket.off('display_question')
    socket.off('update_stats')
    socket.off('show_leaderboard')
    socket.off('error')
    socket.off('disconnect')
})
</script>

<style scoped>
/* ==========================================
   Global Utilities
========================================== */
.flex-between {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.flex-align-center {
    display: flex;
    align-items: center;
}
.flex-center {
    display: flex;
    justify-content: center;
    align-items: center;
}
.flex-col {
    display: flex;
    flex-direction: column;
}
.text-center {
    text-align: center;
}
.text-muted {
    color: var(--el-text-color-secondary);
}
.text-primary {
    color: var(--el-color-primary);
    font-weight: bold;
}
.text-danger {
    color: var(--el-color-danger);
}
.text-success {
    color: var(--el-color-success);
}
.font-bold {
    font-weight: bold;
}

.m-0 {
    margin: 0;
}
.my-4 {
    margin-top: 24px;
    margin-bottom: 24px;
}
.mt-2 {
    margin-top: 8px;
}
.mt-3 {
    margin-top: 12px;
}
.mt-4 {
    margin-top: 24px;
}
.mt-5 {
    margin-top: 40px;
}
.pt-4 {
    padding-top: 24px;
}
.mb-2 {
    margin-bottom: 8px;
}
.mb-5 {
    margin-bottom: 40px;
}
.mr-2 {
    margin-right: 8px;
}
.mr-3 {
    margin-right: 12px;
}
.p-3 {
    padding: 12px;
}
.w-full {
    width: 100%;
}
.max-w-4xl {
    max-width: 800px;
}
.max-w-5xl {
    max-width: calc(100dvw - 40px);
    padding: 10px;
}
.gap-2 {
    gap: 8px;
}
.gap-3 {
    gap: 12px;
}
.gap-4 {
    gap: 16px;
}
.bg-white {
    background-color: #ffffff;
}
.rounded-xl {
    border-radius: 16px;
}
.shadow-sm {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.border-b {
    border-bottom: 2px dashed var(--el-border-color-lighter);
}

/* ==========================================
   Base Layout
========================================== */
.screen-view {
    height: 100dvh;
    overflow: hidden;
    background-color: var(--el-bg-color-page);
    color: var(--el-text-color-primary);
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}

.display-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 32px 48px;
    box-sizing: border-box;
    min-height: 0;
}

/* ==========================================
   Login Panel
========================================== */
.login-container {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 24px;
}
.login-card {
    width: 100%;
    max-width: 500px;
    border-radius: 16px;
    background-color: var(--el-bg-color-overlay);
}
.login-title {
    font-size: 2.5rem;
    font-weight: 800;
    letter-spacing: 1px;
}
.login-subtitle {
    font-size: 1.2rem;
}

/* ==========================================
   Header
========================================== */
.screen-header {
    margin-bottom: 24px;
}
.leave-btn {
    font-size: 1.1rem;
    padding: 12px 24px;
    border-radius: 8px;
}

.player-count-badge {
    background-color: var(--el-fill-color-light);
    padding: 12px 24px;
    border-radius: 50px;
    border: 1px solid var(--el-border-color-lighter);
}
.count-label {
    font-size: 1.2rem;
    font-weight: bold;
    color: var(--el-text-color-secondary);
}
.count-number {
    font-size: 1.8rem;
    font-weight: 900;
    color: var(--el-color-primary);
}

.pulse-dot {
    width: 12px;
    height: 12px;
    background-color: var(--el-color-success);
    border-radius: 50%;
    animation: pulse 1.5s infinite;
    display: inline-block;
}
@keyframes pulse {
    0% {
        box-shadow: 0 0 0 0 rgba(103, 194, 58, 0.4);
    }
    70% {
        box-shadow: 0 0 0 8px rgba(103, 194, 58, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(103, 194, 58, 0);
    }
}

/* ==========================================
   Main Content Area
========================================== */
.main-content-area {
    flex: 1;
    min-height: 0;
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: stretch;
    overflow: hidden;
}

.main-content-area > div {
    display: flex;
    flex-direction: column;
    height: 100%;
}

/* ==========================================
   Lobby State (Fluid & Responsive)
========================================== */
.lobby-state {
    display: flex;
    flex-direction: column;
    min-height: 0;
}
.lobby-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    border-radius: 24px;
    background-color: var(--el-bg-color-overlay);
    min-height: 0;
}

.lobby-card :deep(.el-card__body) {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 3vh 4vw;
    min-height: 0;
}

.lobby-grid {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 3vh;
    justify-content: space-evenly;
    align-items: center;
    background-color: var(--el-fill-color-darker);
    border-radius: 20px;
    padding: 3vh 40px;
    width: 100%;
    min-height: 0;
}

.lobby-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 0;
}
.border-b {
    border-bottom: 2px dashed var(--el-border-color-lighter);
    padding-bottom: 2vh;
    width: 80%;
}

.pin-label {
    font-size: clamp(1rem, 2vh, 1.5rem);
    text-transform: uppercase;
    letter-spacing: 2px;
}
.pin-value {
    font-size: clamp(3rem, 12vh, 8rem);
    font-weight: 900;
    letter-spacing: 8px;
    line-height: 1;
}
.url-display {
    font-size: clamp(1rem, 2.5vh, 1.8rem);
    font-family: monospace;
    font-weight: bold;
}

.qr-container {
    border: 4px solid #fff;
    max-height: 25vh;
    aspect-ratio: 1 / 1;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 8px;
}

.qr-container :deep(canvas),
.qr-container :deep(img) {
    width: 100% !important;
    height: 100% !important;
    object-fit: contain;
}

.waiting-text {
    font-size: clamp(1.2rem, 3vh, 2rem);
    font-weight: normal;
}

/* ==========================================
   Leaderboard State
========================================== */
.leaderboard-card {
    border-radius: 20px;
    background-color: var(--el-bg-color-overlay);
}
.lb-title {
    font-size: 2.8rem;
    font-weight: 800;
    color: var(--el-color-warning);
}
.lb-row {
    padding: 20px 24px;
    background-color: var(--el-fill-color-light);
    border-radius: 12px;
    font-size: 1.5rem;
    transition: transform 0.2s;
}
.lb-row:hover {
    transform: scale(1.02);
}
.lb-rank {
    width: 48px;
    height: 48px;
    background-color: var(--el-fill-color-darker);
    border-radius: 50%;
    font-weight: bold;
    font-size: 1.3rem;
}

/* Top 3 Highlighting */
.top-1 {
    background-color: var(--el-color-warning-light-9);
    border: 2px solid var(--el-color-warning-light-5);
}
.top-1 .lb-rank {
    background-color: transparent;
    font-size: 2.2rem;
}
.top-1 .lb-name,
.top-1 .lb-score {
    color: var(--el-color-warning);
    font-size: 1.8rem;
    font-weight: bold;
}

.top-2 {
    background-color: var(--el-color-info-light-9);
}
.top-2 .lb-rank {
    background-color: transparent;
    font-size: 2rem;
}
.top-2 .lb-name {
    font-weight: bold;
    font-size: 1.6rem;
}

.top-3 {
    background-color: var(--el-color-danger-light-9);
}
.top-3 .lb-rank {
    background-color: transparent;
    font-size: 1.8rem;
}
.top-3 .lb-name {
    color: var(--el-color-danger);
    font-weight: bold;
    font-size: 1.5rem;
}
</style>
