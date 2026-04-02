<template>
    <div class="host-view">
        <h1>Host Control Panel</h1>

        <div v-if="!isConnected" class="login-panel card">
            <h2>Step 1: Login</h2>
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

            <button
                @click="loginAndCreateRoom"
                class="btn-primary"
                :disabled="isLoading"
            >
                {{ isLoading ? 'Connecting...' : 'Login & Create Room' }}
            </button>
            <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>
        </div>

        <div v-else class="game-panel">
            <div class="room-header card">
                <h2>Room PIN: {{ roomPin }}</h2>
                <p class="status-indicator">● Waiting for players...</p>
                <button @click="leaveRoom" class="btn-danger small-btn">
                    End Game
                </button>
            </div>

            <div class="layout-grid">
                <div class="left-col">
                    <div class="exam-selection card">
                        <h3>Select an Exam</h3>

                        <div
                            v-if="!selectedExam"
                            class="custom-select-container"
                        >
                            <input
                                v-model="examSearchQuery"
                                placeholder="Search exam title..."
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
                                        ID: {{ exam.id }}
                                    </div>
                                </div>
                                <div
                                    v-if="filteredExams.length === 0"
                                    class="dropdown-item empty"
                                >
                                    No exams found.
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
                                    Change
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
                                    isLoading ? 'Loading...' : 'Load Questions'
                                }}
                            </button>
                        </div>
                    </div>

                    <div v-if="isQuestionsLoaded" class="waiting-pool card">
                        <div class="pool-header">
                            <h3>Question Pool ({{ waitingPool.length }})</h3>
                            <button
                                @click="broadcastSelected"
                                class="btn-primary small-btn"
                                :disabled="selectedQuestionIds.length === 0"
                            >
                                Broadcast Selected ({{
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
                                            >Q{{ eq.sort_order }}</span
                                        >
                                    </label>
                                    <span class="q-type">{{
                                        eq.question.type
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
                                        >已派發</span
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
                                                ? 'Stop Displaying'
                                                : 'Display on Screen'
                                        }}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="right-col">
                    <div class="player-list card">
                        <h3>Joined Players ({{ players.length }})</h3>
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
                            No students have joined yet.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { socket } from '../utils/socket'
import api from '../api'

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

// --- State ---
const username = ref('')
const password = ref('')
const roomPin = ref('1234')
const errorMessage = ref('')
const isConnected = ref(false)
const isLoading = ref(false)
const players = ref<string[]>([])
const authToken = ref('')

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

        // 將題目根據 sort_order 排序後存入 waitingPool
        waitingPool.value = examDetails.exam_questions.sort(
            (a: ExamQuestion, b: ExamQuestion) => a.sort_order - b.sort_order
        )
        isQuestionsLoaded.value = true
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

const broadcastQuestion = (eq: ExamQuestion) => {
    // Placeholder for Stage 3
    console.log('Broadcasting question:', eq.question)
    alert(
        `Broadcasting Q${eq.sort_order}: ${eq.question.content}\n\n(Socket emission will be implemented in Stage 3)`
    )
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
        socket.emit('host_display_question', {
            room_pin: roomPin.value,
            question: eq.question
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
        localStorage.setItem('host_token', data.access_token)

        await fetchMyExams()

        socket.connect()
        socket.once('connect', () => {
            socket.emit('join_room', {
                room_pin: roomPin.value,
                role: 'host',
                student_id: 'Host_Teacher',
                password: '',
                token: authToken.value
            })
            isConnected.value = true
            isLoading.value = false
        })
    } catch (error: any) {
        errorMessage.value = error.response?.data?.detail || 'Login failed.'
        isLoading.value = false
    }
}

const leaveRoom = () => {
    socket.disconnect()
    isConnected.value = false
    players.value = []
    authToken.value = ''
    selectedExam.value = null
    exams.value = []
    waitingPool.value = []
    isQuestionsLoaded.value = false
    localStorage.removeItem('host_token')
}

onMounted(() => {
    socket.on(
        'room_state',
        async (data: { room_pin: string; players: string[] }) => {
            if (String(data.room_pin) === String(roomPin.value)) {
                players.value = [...data.players]
                await nextTick()
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
/* --------------------------------------
   Layout & Panel Structure
--------------------------------------- */
/* Base View & Typography */
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

/* 登入區塊置中處理 */
.login-panel {
    max-width: 480px;
    margin: 40px auto;
}

/* 遊戲控制台主容器 */
.game-panel {
    display: flex;
    flex-direction: column;
    gap: 24px;
}

/* 左右欄網格排版 */
.layout-grid {
    display: flex;
    gap: 24px;
    flex-wrap: wrap;
    align-items: flex-start;
}

/* 左欄 (考卷與題目區) */
.left-col {
    flex: 2;
    min-width: 320px;
    display: flex;
    flex-direction: column;
    gap: 24px;
}

/* 右欄 (玩家名單區) */
.right-col {
    flex: 1;
    min-width: 280px;
}

/* --------------------------------------
   Room Header & Indicators
--------------------------------------- */
.room-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    background: var(--bg-card);
    border-left: 4px solid var(--primary-light);
    padding: 16px 24px;
}

.room-header h2 {
    margin: 0;
    font-size: 1.5rem;
    color: var(--text-main);
}

.status-indicator {
    color: var(--success-color);
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
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
    justify-content: space-between;
    align-items: center;
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px dashed var(--border-color);
}

.status-badge {
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
