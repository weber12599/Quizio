<template>
    <div class="host-view">
        <ButtonLangToggle />

        <h1>{{ $t('host.title') }}</h1>

        <div v-if="!isConnected && !isReconnecting" class="login-panel card">
            <h2>{{ $t('host.step_login') }}</h2>
            <div class="form-group">
                <label>{{ $t('host.teacher_username') }}</label>
                <input
                    v-model="username"
                    :placeholder="$t('host.placeholder_username')"
                />
            </div>
            <div class="form-group">
                <label>{{ $t('common.password') }}</label>
                <input
                    v-model="password"
                    type="password"
                    :placeholder="$t('host.placeholder_password')"
                    @keyup.enter="loginAndCreateRoom"
                />
            </div>
            <div class="form-group">
                <label>{{ $t('common.room_pin') }}</label>
                <input
                    v-model="roomPin"
                    :placeholder="$t('host.placeholder_pin')"
                    @keyup.enter="loginAndCreateRoom"
                />
            </div>

            <button
                @click="loginAndCreateRoom"
                class="btn-primary"
                :disabled="isLoading"
            >
                {{
                    isLoading
                        ? $t('common.connecting')
                        : $t('host.btn_login_create')
                }}
            </button>
            <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>
        </div>

        <div v-else class="game-panel">
            <div class="room-header card">
                <h2>{{ $t('common.room_pin') }} {{ roomPin }}</h2>
                <p v-if="players.length === 0" class="status-indicator">
                    {{ $t('host.waiting_players') }}
                </p>
                <div class="header-actions" style="display: flex; gap: 12px">
                    <button
                        @click="toggleLeaderboard"
                        class="btn-secondary small-btn"
                        :class="{ 'is-displaying': isLeaderboardDisplayed }"
                    >
                        🏆
                        {{
                            isLeaderboardDisplayed
                                ? $t('host.hide_leaderboard')
                                : $t('host.show_leaderboard')
                        }}
                    </button>
                    <button @click="leaveRoom" class="btn-danger small-btn">
                        {{ $t('common.end_game') }}
                    </button>
                </div>
            </div>

            <div v-if="isReconnecting" class="reconnect-banner">
                {{ $t('common.network_disconnected') }}
            </div>

            <div class="layout-grid">
                <div class="left-col">
                    <div class="exam-selection card">
                        <h3>{{ $t('host.select_exam') }}</h3>

                        <div
                            v-if="!selectedExam"
                            class="custom-select-container"
                        >
                            <input
                                v-model="examSearchQuery"
                                :placeholder="$t('host.search_exam_title')"
                                class="search-input"
                                @focus="isDropdownOpen = true"
                            />

                            <div v-if="isDropdownOpen" class="dropdown-list">
                                <div
                                    v-for="exam in filteredExams"
                                    :key="exam.id"
                                    class="dropdown-item"
                                    @click="selectExam(exam)"
                                >
                                    <div class="exam-title">
                                        {{ exam.title }}
                                    </div>
                                    <div class="exam-meta">
                                        {{ $t('host.exam_id') }}{{ exam.id }}
                                    </div>
                                </div>
                                <div
                                    v-if="filteredExams.length === 0"
                                    class="dropdown-item empty"
                                >
                                    {{ $t('host.no_exams_found') }}
                                </div>
                            </div>
                        </div>

                        <div v-else class="selected-exam-card">
                            <div class="exam-header-actions">
                                <h4>{{ selectedExam.title }}</h4>
                                <button
                                    v-if="!isQuestionsLoaded"
                                    @click="selectedExam = null"
                                    class="btn-secondary small-btn"
                                >
                                    {{ $t('common.change') }}
                                </button>
                            </div>

                            <p
                                v-if="selectedExam.description"
                                class="exam-desc"
                            >
                                {{ selectedExam.description }}
                            </p>

                            <button
                                v-if="!isQuestionsLoaded"
                                @click="loadQuestions"
                                class="btn-success"
                                :disabled="isLoading"
                            >
                                {{
                                    isLoading
                                        ? $t('common.loading')
                                        : $t('host.load_questions')
                                }}
                            </button>
                        </div>
                    </div>

                    <div v-if="isQuestionsLoaded" class="waiting-pool card">
                        <div class="pool-header">
                            <h3>
                                {{ $t('host.question_pool') }} ({{
                                    waitingPool.length
                                }})
                            </h3>
                            <button
                                @click="broadcastSelected"
                                class="btn-primary small-btn"
                                :disabled="selectedQuestionIds.length === 0"
                            >
                                {{ $t('host.broadcast_selected') }} ({{
                                    selectedQuestionIds.length
                                }})
                            </button>
                        </div>

                        <div class="question-list">
                            <div
                                v-for="eq in waitingPool"
                                :key="eq.question_id"
                                class="question-card"
                                :class="{
                                    'is-broadcasted': broadcastedIds.includes(
                                        eq.question_id
                                    )
                                }"
                            >
                                <div class="q-header">
                                    <label class="checkbox-label">
                                        <input
                                            type="checkbox"
                                            :value="eq.question_id"
                                            v-model="selectedQuestionIds"
                                            :disabled="
                                                broadcastedIds.includes(
                                                    eq.question_id
                                                )
                                            "
                                        />
                                        <span class="q-number"
                                            >Q{{ eq.sort_order + 1 }}</span
                                        >
                                    </label>
                                    <span class="q-type">{{
                                        formatQuestionType(eq.question.type)
                                    }}</span>
                                </div>

                                <div class="q-content">
                                    {{ eq.question.content }}
                                </div>

                                <div class="q-actions">
                                    <span
                                        v-if="
                                            broadcastedIds.includes(
                                                eq.question_id
                                            )
                                        "
                                        class="status-badge"
                                        >{{ $t('host.sent') }}</span
                                    >

                                    <button
                                        @click="displayOnScreen(eq)"
                                        class="btn-secondary small-btn"
                                        :class="{
                                            'is-displaying':
                                                currentDisplayedEq?.question_id ===
                                                eq.question_id
                                        }"
                                    >
                                        {{
                                            currentDisplayedEq?.question_id ===
                                            eq.question_id
                                                ? $t('host.stop_displaying')
                                                : $t('host.display_on_screen')
                                        }}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="right-col">
                    <div class="player-list card">
                        <h3>
                            {{ $t('host.joined_players') }} ({{
                                players.length
                            }})
                        </h3>
                        <ul v-if="players.length > 0">
                            <li
                                v-for="player in players"
                                :key="player"
                                class="player-chip"
                            >
                                {{ player }}
                            </li>
                        </ul>
                        <p v-else class="empty-text">
                            {{ $t('host.no_students_joined') }}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { socket } from '../utils/socket'
import api from '../api'
import ButtonLangToggle from '../components/ButtonFloatingAction.vue'
import { formatQuestionType } from '../utils/locales'

// --- Types ---
interface Exam {
    id: number
    title: string
    description?: string
    is_locked: boolean
}

interface Question {
    id: number
    type: string
    content: string
    options?: any
    reference_answer: any
}

interface ExamQuestion {
    exam_id: number
    question_id: number
    sort_order: number
    question: Question
}

// Initialize i18n
const { t } = useI18n()

// --- State ---
const username = ref('')
const password = ref('')
const roomPin = ref('1234')
const errorMessage = ref('')
const isConnected = ref(false)
const isLoading = ref(false)
const isReconnecting = ref(false) // 🚀 新增：斷線重連狀態
const players = ref<string[]>([])
const authToken = ref('')
const isLeaderboardDisplayed = ref(false)
const recoveredDisplayedId = ref<number | null>(null)

// Exam State
const exams = ref<Exam[]>([])
const examSearchQuery = ref('')
const isDropdownOpen = ref(false)
const selectedExam = ref<Exam | null>(null)

// Question Pool State
const waitingPool = ref<ExamQuestion[]>([])
const isQuestionsLoaded = ref(false)
const selectedQuestionIds = ref<number[]>([])
const broadcastedIds = ref<number[]>([])
const currentDisplayedEq = ref<ExamQuestion | null>(null)

// --- Computed ---
const filteredExams = computed(() => {
    if (!examSearchQuery.value) return exams.value
    const query = examSearchQuery.value.toLowerCase()
    return exams.value.filter((exam) =>
        exam.title.toLowerCase().includes(query)
    )
})

// --- API Calls ---
const fetchMyExams = async () => {
    try {
        exams.value = await api.get('/exams/')
    } catch (error) {
        console.error('Error fetching exams:', error)
        errorMessage.value = 'Could not load exams.'
    }
}

const loadQuestions = async () => {
    if (!selectedExam.value) return

    try {
        isLoading.value = true
        const examDetails: any = await api.get(
            `/exams/${selectedExam.value.id}`
        )

        waitingPool.value = examDetails.exam_questions.sort(
            (a: ExamQuestion, b: ExamQuestion) => a.sort_order - b.sort_order
        )
        isQuestionsLoaded.value = true

        // 題目載入後，如果有之前未關閉的投放題目，把它高亮起來
        if (recoveredDisplayedId.value) {
            currentDisplayedEq.value =
                waitingPool.value.find(
                    (q) => q.question_id === recoveredDisplayedId.value
                ) || null
        }
    } catch (error) {
        console.error('Error loading questions:', error)
        alert('Failed to load questions.')
    } finally {
        isLoading.value = false
    }
}

// --- UI Actions ---
const selectExam = (exam: Exam) => {
    selectedExam.value = exam
    examSearchQuery.value = ''
    isDropdownOpen.value = false
    isQuestionsLoaded.value = false
    waitingPool.value = []
}

const broadcastSelected = () => {
    if (selectedQuestionIds.value.length === 0) return

    const questionsToBroadcast = waitingPool.value
        .filter((eq) => selectedQuestionIds.value.includes(eq.question_id))
        .map((eq) => eq.question)

    socket.emit('host_broadcast_questions', {
        room_pin: roomPin.value,
        questions: questionsToBroadcast
    })

    broadcastedIds.value.push(...selectedQuestionIds.value)
    selectedQuestionIds.value = []
}

const displayOnScreen = (eq: ExamQuestion) => {
    if (currentDisplayedEq.value?.question_id === eq.question_id) {
        currentDisplayedEq.value = null
        socket.emit('host_display_question', {
            room_pin: roomPin.value,
            question: null
        })
    } else {
        currentDisplayedEq.value = eq
        isLeaderboardDisplayed.value = false
        socket.emit('host_display_question', {
            room_pin: roomPin.value,
            question: eq.question
        })
    }
}

const toggleLeaderboard = () => {
    if (isLeaderboardDisplayed.value) {
        isLeaderboardDisplayed.value = false
        socket.emit('host_display_question', {
            room_pin: roomPin.value,
            question: null
        })
    } else {
        isLeaderboardDisplayed.value = true
        currentDisplayedEq.value = null
        socket.emit('host_show_leaderboard', {
            room_pin: roomPin.value
        })
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    const target = e.target as HTMLElement
    if (!target.closest('.custom-select-container')) {
        isDropdownOpen.value = false
    }
})

// --- Core Auth & Socket ---

// 🚀 新增：獨立處理 Socket 連線與監聽邏輯
const initSocketConnection = () => {
    socket.off('connect')
    socket.on('connect', () => {
        socket.emit('join_room', {
            room_pin: roomPin.value,
            role: 'host',
            student_id: 'Host_Teacher',
            password: '',
            token: authToken.value
        })
        isConnected.value = true
        isLoading.value = false
        isReconnecting.value = false // 連線成功，解除重連狀態
    })

    // 🚀 監聽異常斷線，觸發重連 Banner，但不退回首頁
    socket.off('disconnect')
    socket.on('disconnect', (reason) => {
        console.warn('Host disconnected:', reason)
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

    socket.connect()
}

const loginAndCreateRoom = async () => {
    errorMessage.value = ''
    isLoading.value = true
    if (!username.value || !password.value) {
        errorMessage.value = 'Please enter both username and password.'
        isLoading.value = false
        return
    }

    try {
        const formData = new URLSearchParams()
        formData.append('username', username.value)
        formData.append('password', password.value)

        const data: any = await api.post('/auth/login', formData.toString(), {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })

        authToken.value = data.access_token

        // 🚀 儲存登入憑證與房號供 F5 恢復使用
        localStorage.setItem('host_token', data.access_token)
        localStorage.setItem('quizio_host_pin', roomPin.value)

        await fetchMyExams()
        initSocketConnection()
    } catch (error: any) {
        errorMessage.value = error.response?.data?.detail || 'Login failed.'
        isLoading.value = false
    }
}

const leaveRoom = () => {
    if (isConnected.value) {
        socket.emit('end_game', { room_pin: roomPin.value })
    }

    // 🚀 徹底清除房號記憶
    localStorage.removeItem('quizio_host_pin')
    localStorage.removeItem('host_token')

    isConnected.value = false
    isReconnecting.value = false
    players.value = []
    authToken.value = ''
    selectedExam.value = null
    exams.value = []
    waitingPool.value = []
    isQuestionsLoaded.value = false

    broadcastedIds.value = []
    selectedQuestionIds.value = []
    currentDisplayedEq.value = null
    isLeaderboardDisplayed.value = false
    examSearchQuery.value = ''

    setTimeout(() => {
        socket.disconnect() // 這裡會觸發 reason: 'io client disconnect'
    }, 100)
}

onMounted(() => {
    // 🚀 F5 重新整理自動恢復機制
    const savedPin = localStorage.getItem('quizio_host_pin')
    const savedToken = localStorage.getItem('host_token')

    if (savedPin && savedToken && !isConnected.value) {
        roomPin.value = savedPin
        authToken.value = savedToken

        // 背景載入考卷清單並自動發起 Socket 連線
        fetchMyExams()
        initSocketConnection()
    }

    // --- Socket Events ---
    socket.on(
        'room_state',
        async (data: { room_pin: string; players: string[] }) => {
            if (String(data.room_pin) === String(roomPin.value)) {
                players.value = [...data.players]
                await nextTick()
            }
        }
    )

    socket.on(
        'host_recovered_state',
        (data: {
            broadcasted_ids: number[]
            displayed_question_id: number | null
            is_leaderboard_displayed: boolean
        }) => {
            broadcastedIds.value = data.broadcasted_ids
            isLeaderboardDisplayed.value = data.is_leaderboard_displayed
            recoveredDisplayedId.value = data.displayed_question_id

            if (recoveredDisplayedId.value && waitingPool.value.length > 0) {
                currentDisplayedEq.value =
                    waitingPool.value.find(
                        (q) => q.question_id === recoveredDisplayedId.value
                    ) || null
            } else {
                currentDisplayedEq.value = null
            }
        }
    )
})

onUnmounted(() => {
    socket.disconnect()
    socket.off('room_state')
    socket.off('host_recovered_state')
    socket.off('connect')
    socket.off('disconnect')
})
</script>

<style scoped>
/* --------------------------------------
   Layout & Panel Structure
--------------------------------------- */
.host-view {
    padding: 20px 15px;
    max-width: 1000px;
    margin: 0 auto;
}

h1 {
    font-size: 2rem;
    color: var(--text-main);
    margin-bottom: 24px;
    text-align: center;
    font-weight: 800;
    letter-spacing: -0.025em;
}

h2,
h3 {
    margin-top: 0;
    color: var(--text-main);
    font-weight: 700;
}

h3 {
    font-size: 1.25rem;
    margin-bottom: 16px;
}

/* Login Panel */
.login-panel {
    max-width: 480px;
    margin: 40px auto;
}

/* Game Panel Main Container */
.game-panel {
    display: flex;
    flex-direction: column;
    gap: 24px;
}

/* 🚀 Reconnect Banner Styles */
.reconnect-banner {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 1.1rem;
    text-align: center;
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
    animation: alert-pulse 2s infinite;
}

@keyframes alert-pulse {
    0% {
        opacity: 1;
    }
    50% {
        opacity: 0.8;
    }
    100% {
        opacity: 1;
    }
}

/* Layout Grid */
.layout-grid {
    display: flex;
    gap: 24px;
    flex-wrap: wrap;
    align-items: flex-start;
}

/* Left Column */
.left-col {
    flex: 2;
    min-width: 320px;
    display: flex;
    flex-direction: column;
    gap: 24px;
}

/* Right Column */
.right-col {
    flex: 1;
    min-width: 280px;
}

/* --------------------------------------
   Room Header & Indicators
--------------------------------------- */
.room-header {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    background: var(--bg-card);
    border-left: 4px solid var(--primary-light);
    padding: 16px 24px;
    gap: 16px;
}

.room-header h2 {
    margin: 0;
    font-size: 1.5rem;
    color: var(--text-main);
    grid-column: 1;
    justify-self: start;
}

.status-indicator {
    color: var(--success-color);
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
    grid-column: 2;
    justify-self: center;
    margin: 0;
}

.header-actions {
    grid-column: 3;
    justify-self: end;
    display: flex;
    gap: 12px;
}

.header-actions button {
    min-width: 180px; /* Prevent layout shift when toggling Show/Hide Leaderboard */
    display: inline-flex;
    justify-content: center;
}

/* --------------------------------------
   Custom Select Dropdown
--------------------------------------- */
.custom-select-container {
    position: relative;
    width: 100%;
}

.dropdown-list {
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    right: 0;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    max-height: 280px;
    overflow-y: auto;
    z-index: 20;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
}

.dropdown-item {
    padding: 16px;
    border-bottom: 1px solid var(--border-color);
    cursor: pointer;
    transition: background-color 0.15s ease;
}

.dropdown-item:last-child {
    border-bottom: none;
}

.dropdown-item:active,
.dropdown-item:hover {
    background: var(--hover-bg);
}

.exam-title {
    font-weight: 600;
    font-size: 1rem;
    color: var(--text-main);
}

.exam-meta {
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-top: 6px;
}

.empty {
    text-align: center;
    color: var(--text-muted);
    padding: 24px;
}

/* --------------------------------------
   Selected Exam Card
--------------------------------------- */
.selected-exam-card {
    border: 2px solid var(--border-color);
    border-radius: 12px;
    padding: 20px;
    background: var(--highlight-bg);
    position: relative;
    overflow: hidden;
}

.selected-exam-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--primary-light), #8b5cf6);
}

.exam-header-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.exam-header-actions h4 {
    margin: 0;
    font-size: 1.25rem;
    color: var(--text-main);
}

.exam-desc {
    color: var(--text-muted);
    font-size: 0.95rem;
    margin-bottom: 20px;
    line-height: 1.5;
}

/* --------------------------------------
   Question Pool & Cards
--------------------------------------- */
.pool-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-color);
}

.question-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
    max-height: 60vh;
    overflow-y: auto;
    padding-right: 8px;
}

.question-list::-webkit-scrollbar {
    width: 6px;
}
.question-list::-webkit-scrollbar-track {
    background: var(--bg-color);
    border-radius: 4px;
}
.question-list::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 4px;
}

.question-card {
    border: 1px solid var(--border-color);
    padding: 20px;
    border-radius: 12px;
    background: var(--bg-card);
    display: flex;
    flex-direction: column;
    gap: 12px;
    transition: all 0.2s ease;
}

.question-card:hover {
    border-color: var(--text-muted);
}

.q-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.checkbox-label {
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    user-select: none;
}

.checkbox-label input[type='checkbox'] {
    width: 20px;
    height: 20px;
    cursor: pointer;
    accent-color: var(--primary-light);
    border-radius: 4px;
}

.q-number {
    background: var(--border-color);
    color: var(--text-main);
    padding: 4px 10px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.9rem;
}

.q-type {
    text-transform: uppercase;
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--text-muted);
    letter-spacing: 0.05em;
}

.q-content {
    font-size: 1.05rem;
    color: var(--text-main);
    line-height: 1.6;
}

.question-card.is-broadcasted {
    border-left: 4px solid var(--success-color);
    background-color: var(--highlight-bg);
}

.q-actions {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px dashed var(--border-color);
    min-height: 48px;
    gap: 12px;
}

.status-badge {
    margin-right: auto;
    background: rgba(16, 185, 129, 0.15);
    color: var(--success-color);
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.q-actions button {
    min-width: 180px;
    display: inline-flex;
    justify-content: center;
}

@media (max-width: 640px) {
    .room-header {
        display: flex;
        flex-direction: column;
        align-items: stretch;
    }
    .room-header h2,
    .status-indicator,
    .header-actions {
        grid-column: auto;
        justify-self: stretch;
        justify-content: center;
    }
    .header-actions button {
        width: 100%;
    }
}

.status-badge::before {
    content: '';
    display: inline-block;
    width: 6px;
    height: 6px;
    background-color: var(--success-color);
    border-radius: 50%;
}

/* Displaying Animation */
.btn-secondary.is-displaying {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white;
    border: none;
    box-shadow: 0 4px 6px -1px rgba(245, 158, 11, 0.2);
    animation: pulse-orange 2s infinite;
}

@keyframes pulse-orange {
    0% {
        box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.4);
    }
    70% {
        box-shadow: 0 0 0 6px rgba(245, 158, 11, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(245, 158, 11, 0);
    }
}

/* --------------------------------------
   Player List
--------------------------------------- */
.player-list ul {
    list-style: none;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.player-chip {
    background: var(--chip-bg);
    color: var(--primary-light);
    padding: 8px 14px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9rem;
    border: 1px solid var(--chip-border);
    display: flex;
    align-items: center;
}

.empty-text {
    color: var(--text-muted);
    font-style: italic;
    text-align: center;
    padding: 20px 0;
}

/* --------------------------------------
   Responsive Adjustments
--------------------------------------- */
@media (max-width: 640px) {
    .host-view {
        padding: 10px;
    }
    .card {
        padding: 16px;
    }
    .room-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
    }
    .room-header button {
        width: 100%;
    }
    .pool-header {
        flex-direction: column;
        align-items: stretch;
        gap: 12px;
    }
}
</style>
