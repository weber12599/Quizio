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
                    <p>Questions will appear here automatically.</p>
                </div>

                <div v-else class="question-list">
                    <div
                        v-for="q in questionsFeed"
                        :key="q.id"
                        class="question-card card"
                        :class="{
                            'is-answered': submittedAnswers[q.id] !== undefined
                        }"
                    >
                        <div class="q-meta">
                            <span class="q-type">{{
                                formatQuestionType(q.type)
                            }}</span>
                            <span
                                v-if="gradingResults[q.id]"
                                class="badge-success"
                                >Graded</span
                            >
                            <span
                                v-else-if="submittedAnswers[q.id] !== undefined"
                                class="badge-pending"
                                >Submitted</span
                            >
                        </div>

                        <div
                            v-if="gradingResults[q.id]"
                            class="grading-banner"
                            :class="getBannerClass(q.id, q.type)"
                        >
                            <span class="banner-icon">{{
                                getBannerIcon(q.id, q.type)
                            }}</span>
                            <span class="banner-text">{{
                                getBannerText(q.id, q.type)
                            }}</span>
                        </div>

                        <h3 class="q-content">{{ q.content }}</h3>

                        <div
                            v-if="submittedAnswers[q.id] === undefined"
                            class="options-container"
                        >
                            <div
                                v-if="
                                    q.type === 'single' || q.type === 'boolean'
                                "
                                class="mcq-grid"
                            >
                                <button
                                    v-for="(opt, idx) in getOptions(q)"
                                    :key="idx"
                                    @click="setSingleAnswer(q.id, q.type, idx)"
                                    class="btn-option"
                                    :class="{
                                        selected: isSelected(q.id, q.type, idx)
                                    }"
                                >
                                    <div class="radio-box">
                                        <div
                                            v-if="isSelected(q.id, q.type, idx)"
                                            class="radio-inner"
                                        ></div>
                                    </div>
                                    <span class="opt-text">{{ opt }}</span>
                                </button>
                                <button
                                    @click="
                                        submitAnswer(q.id, tempAnswers[q.id])
                                    "
                                    class="btn-primary mt-3"
                                    :disabled="!canSubmit(q.id, q.type)"
                                >
                                    Submit Answer
                                </button>
                            </div>

                            <div
                                v-else-if="q.type === 'multiple'"
                                class="mcq-grid multi-select"
                            >
                                <button
                                    v-for="(opt, idx) in getOptions(q)"
                                    :key="idx"
                                    @click="toggleMultiSelect(q.id, idx)"
                                    class="btn-option"
                                    :class="{
                                        selected: isSelected(q.id, q.type, idx)
                                    }"
                                >
                                    <div class="checkbox-box">
                                        <span
                                            v-if="isSelected(q.id, q.type, idx)"
                                            >✓</span
                                        >
                                    </div>
                                    <span class="opt-text">{{ opt }}</span>
                                </button>
                                <button
                                    @click="
                                        submitAnswer(q.id, tempAnswers[q.id])
                                    "
                                    class="btn-primary mt-3"
                                    :disabled="!canSubmit(q.id, q.type)"
                                >
                                    Submit Answer
                                </button>
                            </div>

                            <div
                                v-else-if="
                                    q.type === 'short' || q.type === 'essay'
                                "
                                class="text-answer-container"
                            >
                                <textarea
                                    v-if="q.type === 'essay'"
                                    v-model="tempAnswers[q.id]"
                                    placeholder="Write your essay answer here..."
                                    class="answer-input textarea"
                                    rows="5"
                                ></textarea>
                                <input
                                    v-else
                                    v-model="tempAnswers[q.id]"
                                    placeholder="Type your short answer here..."
                                    class="answer-input"
                                />

                                <button
                                    @click="
                                        submitAnswer(q.id, tempAnswers[q.id])
                                    "
                                    class="btn-primary mt-3"
                                    :disabled="!canSubmit(q.id, q.type)"
                                >
                                    Submit Answer
                                </button>
                            </div>
                        </div>

                        <div v-else class="graded-state">
                            <div
                                v-if="
                                    q.type === 'single' ||
                                    q.type === 'boolean' ||
                                    q.type === 'multiple'
                                "
                                class="mcq-grid readonly"
                            >
                                <div
                                    v-for="(opt, idx) in getOptions(q)"
                                    :key="idx"
                                    class="btn-option read-only-opt"
                                    :class="
                                        getOptionGradingClass(q.id, q.type, idx)
                                    "
                                >
                                    <span class="opt-icon">{{
                                        getOptionGradingIcon(q.id, q.type, idx)
                                    }}</span>
                                    <span class="opt-text">{{ opt }}</span>
                                </div>
                            </div>

                            <div
                                v-else-if="q.type === 'short'"
                                class="short-answer-graded"
                            >
                                <div
                                    class="student-text-box"
                                    :class="
                                        gradingResults[q.id]?.is_correct
                                            ? 'box-correct'
                                            : 'box-wrong'
                                    "
                                >
                                    <span class="indicator">{{
                                        gradingResults[q.id]?.is_correct
                                            ? '✅ Your Answer'
                                            : '❌ Your Answer'
                                    }}</span>
                                    <div class="val">
                                        {{ submittedAnswers[q.id] }}
                                    </div>
                                </div>
                                <div
                                    v-if="!gradingResults[q.id]?.is_correct"
                                    class="correct-text-box"
                                >
                                    <span class="indicator"
                                        >🎯 Correct Answer</span
                                    >
                                    <div class="val">
                                        {{
                                            formatSubmittedAnswer(
                                                gradingResults[q.id]
                                                    ?.correct_answer
                                            )
                                        }}
                                    </div>
                                </div>
                            </div>

                            <div
                                v-else-if="q.type === 'essay'"
                                class="essay-graded"
                            >
                                <div class="student-text-box box-neutral">
                                    <span class="indicator"
                                        >📝 Your Submission</span
                                    >
                                    <div class="val">
                                        {{ submittedAnswers[q.id] }}
                                    </div>
                                </div>
                                <div class="correct-text-box box-reference">
                                    <span class="indicator"
                                        >💡 Reference Answer</span
                                    >
                                    <div class="val">
                                        {{
                                            formatSubmittedAnswer(
                                                gradingResults[q.id]
                                                    ?.correct_answer
                                            )
                                        }}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { socket } from '../utils/socket'

// --- Types ---
interface Question {
    id: number
    type: string
    content: string
    options?: any
}

interface GradingResult {
    is_correct: boolean
    correct_answer: any
}

const route = useRoute()

// --- State ---
const roomPin = ref('')
const studentId = ref('')
const password = ref('')
const errorMessage = ref('')
const isConnected = ref(false)
const isLoading = ref(false)

const questionsFeed = ref<Question[]>([])
const tempAnswers = ref<Record<string, any>>({})
const submittedAnswers = ref<Record<string, any>>({})
const gradingResults = ref<Record<string, GradingResult>>({})

// --- Helpers ---
const formatQuestionType = (type: string): string => {
    const typeMap: Record<string, string> = {
        single: '單選題',
        boolean: '是非題',
        multiple: '多選題',
        short: '簡答題',
        essay: '申論題'
    }
    return typeMap[type] || type
}

const getOptions = (q: Question): string[] => {
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
    // Return default translations for boolean options
    if (q.type === 'boolean' && parsedOpts.length === 0) {
        return ['是 (True)', '非 (False)']
    }
    return parsedOpts
}

const formatSubmittedAnswer = (ans: any): string => {
    if (Array.isArray(ans)) return ans.join(', ')
    return String(ans || 'N/A')
}

// --- Answer Handling Logic ---

// Determines if the submit button should be enabled
const canSubmit = (qId: number, type: string): boolean => {
    const ans = tempAnswers.value[qId]
    if (ans === undefined || ans === null) return false
    if (type === 'multiple') return Array.isArray(ans) && ans.length > 0
    if (type === 'short' || type === 'essay')
        return typeof ans === 'string' && ans.trim().length > 0
    return true // Single and Boolean just need to be not undefined
}

// Check if a specific option index is selected
const isSelected = (qId: number, type: string, idx: number): boolean => {
    const ans = tempAnswers.value[qId]
    if (ans === undefined || ans === null) return false

    if (type === 'boolean') {
        // True corresponds to idx 0, False to idx 1
        return ans === (idx === 0)
    }
    if (type === 'multiple') {
        return Array.isArray(ans) && ans.includes(idx)
    }
    // Single choice
    return ans === idx
}

// Set answer for single choice or boolean questions
const setSingleAnswer = (qId: number, type: string, idx: number) => {
    if (type === 'boolean') {
        tempAnswers.value[qId] = idx === 0 // Boolean True for index 0, False for index 1
    } else {
        tempAnswers.value[qId] = idx // Store index directly
    }
}

// Toggle multi-select index
const toggleMultiSelect = (qId: number, idx: number) => {
    if (!tempAnswers.value[qId] || !Array.isArray(tempAnswers.value[qId])) {
        tempAnswers.value[qId] = []
    }
    const pos = tempAnswers.value[qId].indexOf(idx)
    if (pos > -1) {
        tempAnswers.value[qId].splice(pos, 1)
    } else {
        tempAnswers.value[qId].push(idx)
    }
}

// --- Grading UI Logic ---

const getBannerClass = (qId: number, type: string): string => {
    const grade = gradingResults.value[qId]
    if (!grade) return ''
    if (type === 'essay') return 'banner-neutral'
    return grade.is_correct ? 'banner-correct' : 'banner-wrong'
}

const getBannerIcon = (qId: number, type: string): string => {
    const grade = gradingResults.value[qId]
    if (!grade) return ''
    if (type === 'essay') return '📝'
    return grade.is_correct ? '🎉' : '❌'
}

const getBannerText = (qId: number, type: string): string => {
    const grade = gradingResults.value[qId]
    if (!grade) return ''
    if (type === 'essay') return 'Submission Received (Pending Manual Review)'
    return grade.is_correct ? 'Correct!' : 'Incorrect'
}

// Determines the CSS class based on backend grading results (using index)
const getOptionGradingClass = (
    qId: number,
    type: string,
    idx: number
): string => {
    const grade = gradingResults.value[qId]
    const stuAns = submittedAnswers.value[qId]

    if (!grade) return 'opt-pending'

    // The value to compare depends on question type
    const valToCheck = type === 'boolean' ? idx === 0 : idx

    const isStuSelected = Array.isArray(stuAns)
        ? stuAns.includes(valToCheck)
        : stuAns === valToCheck

    const isCorrectAns = Array.isArray(grade.correct_answer)
        ? grade.correct_answer.includes(valToCheck)
        : grade.correct_answer === valToCheck

    if (isStuSelected && isCorrectAns) return 'opt-correct'
    if (isStuSelected && !isCorrectAns) return 'opt-wrong'
    if (!isStuSelected && isCorrectAns) return 'opt-missed'
    return 'opt-neutral'
}

const getOptionGradingIcon = (
    qId: number,
    type: string,
    idx: number
): string => {
    const cls = getOptionGradingClass(qId, type, idx)
    if (cls === 'opt-correct') return '✅'
    if (cls === 'opt-wrong') return '❌'
    if (cls === 'opt-missed') return '🎯'
    return '⬜'
}

// --- Methods ---
const performJoin = (
    pin: string,
    sid: string,
    pwd: string,
    isAuto: bool = false
) => {
    if (!isAuto) {
        errorMessage.value = ''
    }

    isLoading.value = true
    socket.connect()

    socket.once('connect', () => {
        socket.emit('join_room', {
            room_pin: pin,
            role: 'client',
            student_id: sid,
            password: pwd
        })

        localStorage.setItem(
            'quizio_student_creds',
            JSON.stringify({ pin, sid, pwd })
        )
    })
}

const joinRoom = () => {
    errorMessage.value = ''
    if (!roomPin.value || !studentId.value || !password.value) {
        errorMessage.value = 'Please fill in all fields.'
        return
    }
    performJoin(roomPin.value, studentId.value, password.value)
}

const submitAnswer = (questionId: number, answer: any) => {
    // Basic validation handled by canSubmit, but double check
    if (answer === undefined || answer === null) return

    // Optimistic UI Update
    submittedAnswers.value[questionId] = answer

    // Send to backend and WAIT for grading callback
    socket.emit(
        'submit_answer',
        {
            room_pin: roomPin.value,
            question_id: questionId,
            answer: answer
        },
        (response: GradingResult) => {
            console.log('✅ Grading received:', response)
            gradingResults.value[questionId] = response
        }
    )
}

const leaveRoom = () => {
    socket.disconnect()
    localStorage.removeItem('quizio_student_creds')
    isConnected.value = false
    questionsFeed.value = []
    submittedAnswers.value = {}
    tempAnswers.value = {}
    gradingResults.value = {}
    errorMessage.value = ''
    isLoading.value = false
}

// --- Lifecycle & Socket Events ---
onMounted(() => {
    if (route.query.pin) {
        roomPin.value = route.query.pin as string
    }

    const saved = localStorage.getItem('quizio_student_creds')
    if (saved && !isConnected.value) {
        const { pin, sid, pwd } = JSON.parse(saved)
        // 填充輸入框讓使用者看得到
        roomPin.value = pin
        studentId.value = sid
        password.value = pwd
        // 自動執行連線
        performJoin(pin, sid, pwd, true)
    }

    socket.on('room_state', (data: { room_pin: string; players: string[] }) => {
        if (String(data.room_pin) === String(roomPin.value)) {
            isConnected.value = true
            isLoading.value = false
        }
    })

    socket.on('error', (data: { message: string }) => {
        const hasCache = localStorage.getItem('quizio_student_creds') !== null

        if (hasCache) {
            localStorage.removeItem('quizio_student_creds')
            isLoading.value = false
        } else {
            errorMessage.value = data.message
            isLoading.value = false
        }
        socket.disconnect()
    })

    socket.on('new_questions', (data: { questions: Question[] }) => {
        data.questions.forEach((incomingQ) => {
            if (!questionsFeed.value.some((q) => q.id === incomingQ.id))
                questionsFeed.value.push(incomingQ)
        })
    })

    socket.on(
        'recovered_answers',
        (data: {
            answers: Record<string, any>
            gradings?: Record<string, GradingResult>
        }) => {
            submittedAnswers.value = {
                ...submittedAnswers.value,
                ...data.answers
            }
            if (data.gradings) {
                gradingResults.value = {
                    ...gradingResults.value,
                    ...data.gradings
                }
            }
        }
    )
})

onUnmounted(() => {
    socket.disconnect()
    socket.off('room_state')
    socket.off('error')
    socket.off('new_questions')
    socket.off('recovered_answers')
})
</script>

<style scoped>
/* Layout & Shared styles */
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

/* Header */
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

/* Feed & Cards */
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
    gap: 24px;
}
.question-card {
    transition: all 0.3s ease;
}
.question-card.is-answered {
    background-color: var(--bg-card);
    border-color: var(--border-color);
}

.q-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}
.q-type {
    background: var(--chip-bg);
    color: var(--primary-color);
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.05em;
}
.badge-success {
    background: var(--success-color);
    color: white;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 700;
}
.badge-pending {
    background: #f59e0b;
    color: white;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 700;
}

/* Grading Banner */
.grading-banner {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 20px;
    font-weight: 700;
    font-size: 1.05rem;
}
.banner-correct {
    background: rgba(16, 185, 129, 0.15);
    color: var(--success-color);
    border: 1px solid rgba(16, 185, 129, 0.3);
}
.banner-wrong {
    background: rgba(239, 68, 68, 0.15);
    color: var(--danger-color);
    border: 1px solid rgba(239, 68, 68, 0.3);
}
.banner-neutral {
    background: rgba(99, 102, 241, 0.15);
    color: var(--primary-color);
    border: 1px solid rgba(99, 102, 241, 0.3);
}

.q-content {
    font-size: 1.3rem;
    color: var(--text-main);
    line-height: 1.6;
    margin: 0 0 24px 0;
}

/* Input UI (Unanswered) */
.options-container {
    margin-top: 16px;
}
.mcq-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 12px;
}
.btn-option {
    background: var(--bg-card);
    color: var(--text-main);
    border: 2px solid var(--border-color);
    padding: 16px;
    border-radius: 12px;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: left;
    display: flex;
    align-items: center;
}
.btn-option:hover:not(.read-only-opt) {
    border-color: var(--primary-light);
    background: var(--highlight-bg);
    transform: translateY(-2px);
}
.btn-option.selected {
    border-color: var(--primary-color);
    background: var(--highlight-bg);
}

/* Radio & Checkbox */
.radio-box,
.checkbox-box {
    width: 24px;
    height: 24px;
    border: 2px solid var(--border-color);
    margin-right: 12px;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-shrink: 0;
    transition: all 0.2s ease;
}
.radio-box {
    border-radius: 50%;
}
.checkbox-box {
    border-radius: 6px;
    font-size: 14px;
    color: white;
}
.radio-inner {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background-color: var(--primary-color);
}
.btn-option.selected .radio-box,
.btn-option.selected .checkbox-box {
    border-color: var(--primary-color);
}
.btn-option.selected .checkbox-box {
    background-color: var(--primary-color);
}

.opt-text {
    flex: 1;
}
.mt-3 {
    margin-top: 16px;
}
.text-answer-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.answer-input {
    padding: 16px;
    border: 2px solid var(--border-color);
    border-radius: 10px;
    font-size: 1.1rem;
    background: var(--input-bg);
    color: var(--input-text);
    width: 100%;
}
.answer-input:focus {
    outline: none;
    border-color: var(--primary-light);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
}
.textarea {
    resize: vertical;
    min-height: 120px;
    font-family: inherit;
    line-height: 1.5;
}

/* Graded State UI */
.graded-state {
    margin-top: 16px;
}
.mcq-grid.readonly .btn-option {
    cursor: default;
    transform: none;
}
.read-only-opt {
    opacity: 0.8;
}
.opt-icon {
    margin-right: 12px;
    font-size: 1.2rem;
}

/* Grading Highlight Classes */
.opt-correct {
    border-color: var(--success-color);
    background: rgba(16, 185, 129, 0.1);
    opacity: 1;
}
.opt-wrong {
    border-color: var(--danger-color);
    background: rgba(239, 68, 68, 0.1);
    opacity: 1;
}
.opt-missed {
    border-color: var(--success-color);
    border-style: dashed;
    background: rgba(16, 185, 129, 0.05);
    opacity: 1;
}

/* Text Graded Boxes */
.student-text-box,
.correct-text-box {
    padding: 16px;
    border-radius: 12px;
    margin-bottom: 12px;
}
.indicator {
    font-size: 0.85rem;
    font-weight: 700;
    margin-bottom: 8px;
    display: block;
}
.val {
    font-size: 1.1rem;
    line-height: 1.5;
    white-space: pre-wrap;
    color: var(--text-main);
}

.box-correct {
    background: rgba(16, 185, 129, 0.1);
    border: 2px solid var(--success-color);
}
.box-wrong {
    background: rgba(239, 68, 68, 0.1);
    border: 2px solid var(--danger-color);
}
.correct-text-box {
    background: rgba(16, 185, 129, 0.05);
    border: 2px dashed var(--success-color);
}

.box-neutral {
    background: var(--bg-card);
    border: 2px solid var(--border-color);
}
.box-reference {
    background: var(--highlight-bg);
    border: 2px solid var(--primary-light);
}
</style>
