<template>
    <div class="client-view">
        <ButtonFloatingAction />

        <div v-if="!isJoined" class="auth-container">
            <el-card
                class="auth-card"
                shadow="hover"
                :body-style="{ padding: '32px' }"
            >
                <template #header>
                    <h2 class="text-center m-0">{{ $t('client.title') }}</h2>
                </template>

                <el-radio-group
                    v-model="joinMode"
                    size="large"
                    class="w-full flex-row mb-4 custom-radio-group"
                >
                    <el-radio-button value="student" class="flex-1">{{
                        $t('client.radio_student_login')
                    }}</el-radio-button>
                    <el-radio-button value="guest" class="flex-1">{{
                        $t('client.radio_guest_login')
                    }}</el-radio-button>
                </el-radio-group>

                <el-form
                    label-position="top"
                    @submit.prevent
                    @keyup.enter="joinRoom"
                >
                    <el-form-item :label="$t('common.room_pin')">
                        <el-input
                            v-model="roomPin"
                            :placeholder="$t('placeholder.pin')"
                            size="large"
                        />
                    </el-form-item>

                    <template v-if="joinMode === 'student'">
                        <el-form-item :label="$t('common.student_id')">
                            <el-input
                                v-model="studentId"
                                :placeholder="$t('placeholder.student_id')"
                                size="large"
                            />
                        </el-form-item>
                        <el-form-item :label="$t('common.password')">
                            <el-input
                                v-model="password"
                                type="password"
                                show-password
                                :placeholder="$t('placeholder.password')"
                                size="large"
                            />
                        </el-form-item>
                    </template>

                    <template v-else>
                        <el-form-item :label="$t('common.guest_name')">
                            <el-input
                                v-model="guestName"
                                :placeholder="$t('placeholder.guest_name')"
                                size="large"
                            />
                        </el-form-item>
                    </template>

                    <el-button
                        type="primary"
                        class="w-full mt-4"
                        size="large"
                        plain
                        @click="joinRoom"
                        :loading="isLoading"
                    >
                        {{
                            isLoading
                                ? $t('common.connecting')
                                : $t('client.btn_join')
                        }}
                    </el-button>
                </el-form>

                <el-alert
                    v-if="errorMessage"
                    :title="errorMessage"
                    type="error"
                    show-icon
                    class="mt-4"
                    :closable="false"
                />
            </el-card>
        </div>

        <div v-else class="room-container">
            <el-card
                class="dashboard-card"
                shadow="never"
                :body-style="{ padding: '24px 32px' }"
            >
                <div class="flex-between w-full flex-wrap gap-3">
                    <h2
                        class="m-0 flex-align-center gap-2"
                        style="font-size: 1.5rem"
                    >
                        {{ $t('client.room') }}
                        <span class="text-primary">{{ roomPin }}</span>
                        <el-tag
                            :type="joinMode === 'guest' ? 'warning' : 'success'"
                            effect="plain"
                            round
                            size="small"
                            class="ml-2"
                        >
                            {{ joinMode === 'guest' ? 'Guest' : 'Student' }}
                        </el-tag>
                    </h2>
                    <div class="flex-align-center gap-3">
                        <el-tag
                            :type="isConnected ? 'success' : 'warning'"
                            effect="plain"
                            round
                            size="large"
                        >
                            <span class="flex-align-center gap-2">
                                <span
                                    class="pulse-dot mr-2"
                                    :style="
                                        isConnected
                                            ? ''
                                            : 'background-color: var(--el-color-warning);'
                                    "
                                ></span>
                                {{
                                    isConnected
                                        ? $t('client.connected')
                                        : $t('common.connecting')
                                }}
                            </span>
                        </el-tag>
                        <el-button type="danger" plain @click="leaveRoom">{{
                            $t('common.leave')
                        }}</el-button>
                    </div>
                </div>
            </el-card>

            <el-alert
                v-if="!isConnected"
                :title="$t('common.network_disconnected')"
                type="warning"
                show-icon
                center
                :closable="false"
                class="mt-4"
            />

            <div class="feed-container mt-4">
                <el-empty
                    v-if="questionsFeed.length === 0"
                    description=" "
                    :image-size="0"
                >
                    <template #default>
                        <div class="loader-spinner mx-auto mb-3"></div>
                        <p class="text-muted">
                            {{ $t('client.waiting_teacher') }}
                        </p>
                        <p class="text-muted">
                            {{ $t('client.questions_appear_auto') }}
                        </p>
                    </template>
                </el-empty>

                <div v-else class="question-list flex-col-gap">
                    <GameQuestionCard
                        v-for="q in questionsFeed"
                        :key="q.id"
                        :question="q"
                        role="client"
                        v-model="tempAnswers[q.id]"
                        :submittedAnswer="submittedAnswers[q.id]"
                        :gradingResult="gradingResults[q.id]"
                    >
                        <template #actions>
                            <div class="flex-between w-full">
                                <el-badge
                                    v-if="submittedAnswers[q.id] !== undefined"
                                    :value="interactionBadge(q.id)"
                                    :hidden="interactionBadge(q.id) === 0"
                                >
                                    <el-button
                                        size="large"
                                        plain
                                        @click="openInteractionDialog(q)"
                                    >
                                        <el-icon class="mr-1"><ChatDotRound /></el-icon>
                                        {{ $t('interaction.view_discussion') }}
                                    </el-button>
                                </el-badge>
                                <span v-else />
                                <el-button
                                    v-if="submittedAnswers[q.id] === undefined"
                                    type="primary"
                                    size="large"
                                    plain
                                    @click="submitAnswer(q.id, tempAnswers[q.id])"
                                    :disabled="!canSubmit(q.id, q.type)"
                                >
                                    {{ $t('client.submit_answer') }}
                                </el-button>
                            </div>
                        </template>
                    </GameQuestionCard>
                </div>
            </div>
        </div>
    </div>

    <InteractionDialog
        v-model:visible="interactionDialogVisible"
        :question="currentInteractionQuestion"
        :peer-answers="
            peerAnswers[currentInteractionQuestion?.id ?? 0] ?? []
        "
        :interactions="
            interactions[currentInteractionQuestion?.id ?? 0] ?? {}
        "
        :my-player-id="myPlayerId"
        :is-host="false"
        @like="handleLike"
        @unlike="handleUnlike"
        @comment="handleComment"
        @like-comment="handleLikeComment"
        @unlike-comment="handleUnlikeComment"
    />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { socket } from '../utils/socket'
import { storage } from '../utils/storage'
import { SocketEvent } from '../types/socket'
import ButtonFloatingAction from '../components/ButtonFloatingAction.vue'
import GameQuestionCard from '../components/GameQuestionCard.vue'
import InteractionDialog from '../components/InteractionDialog.vue'
import { ChatDotRound } from '@element-plus/icons-vue'
import type { PeerAnswer, QuestionInteractions } from '../types/interaction'

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

const { t } = useI18n()
const route = useRoute()

const joinMode = ref<'student' | 'guest'>('student')

const roomPin = ref('')
const studentId = ref('')
const password = ref('')
const guestName = ref('')
const errorMessage = ref('')
const isConnected = ref(false)
const isJoined = ref(false)
const isLoading = ref(false)

const questionsFeed = ref<Question[]>([])
const tempAnswers = ref<Record<string, any>>({})
const submittedAnswers = ref<Record<string, any>>({})
const gradingResults = ref<Record<string, GradingResult>>({})

// ── Interaction state ─────────────────────────────────────────────────────
const interactionDialogVisible = ref(false)
const currentInteractionQuestion = ref<Question | null>(null)
const peerAnswers = ref<Record<number, PeerAnswer[]>>({})
const interactions = ref<Record<number, QuestionInteractions>>({})
const myPlayerId = ref<string>('')
const myDisplayName = ref<string>('')
const seenInteractionCount = ref<Record<number, number>>({})

const canSubmit = (qId: number, type: string): boolean => {
    const ans = tempAnswers.value[qId]
    if (ans === undefined || ans === null || ans === '') return false
    if (type === 'multiple') return Array.isArray(ans) && ans.length > 0
    if (type === 'short' || type === 'essay')
        return typeof ans === 'string' && ans.trim().length > 0
    return true
}

const interactionBadge = (qId: number): number => {
    if (interactionDialogVisible.value && currentInteractionQuestion.value?.id === qId) return 0
    const ia = interactions.value[qId] ?? {}
    const total = Object.values(ia).reduce(
        (sum, x) => sum + x.likes.length + x.comments.length,
        0
    )
    return Math.max(0, total - (seenInteractionCount.value[qId] ?? 0))
}

const openInteractionDialog = (question: Question) => {
    currentInteractionQuestion.value = question
    const ia = interactions.value[question.id] ?? {}
    seenInteractionCount.value[question.id] = Object.values(ia).reduce(
        (sum, x) => sum + x.likes.length + x.comments.length,
        0
    )
    interactionDialogVisible.value = true
}

const handleLike = (ownerId: string) => {
    const qId = currentInteractionQuestion.value?.id
    if (!qId) return
    if (!interactions.value[qId]) interactions.value[qId] = {}
    const ia = interactions.value[qId][ownerId] ?? { likes: [], comments: [] }
    ia.likes.push({ from_id: myPlayerId.value, name: myDisplayName.value })
    interactions.value[qId][ownerId] = ia
    socket.emit(SocketEvent.LIKE_ANSWER, { room_pin: roomPin.value, question_id: qId, answer_owner_id: ownerId })
}

const handleUnlike = (ownerId: string) => {
    const qId = currentInteractionQuestion.value?.id
    if (!qId) return
    const ia = interactions.value[qId]?.[ownerId]
    if (ia) ia.likes = ia.likes.filter((l) => l.from_id !== myPlayerId.value)
    socket.emit(SocketEvent.UNLIKE_ANSWER, { room_pin: roomPin.value, question_id: qId, answer_owner_id: ownerId })
}

const handleComment = (ownerId: string, content: string) => {
    const qId = currentInteractionQuestion.value?.id
    if (!qId) return
    if (!interactions.value[qId]) interactions.value[qId] = {}
    const ia = interactions.value[qId][ownerId] ?? { likes: [], comments: [] }
    ia.comments.push({
        id: `local-${Date.now()}`,
        from_id: myPlayerId.value,
        name: myDisplayName.value,
        content,
        is_host: false,
        likes: [],
    })
    interactions.value[qId][ownerId] = ia
    socket.emit(SocketEvent.COMMENT_ANSWER, {
        room_pin: roomPin.value,
        question_id: qId,
        answer_owner_id: ownerId,
        content
    })
}

const handleLikeComment = (ownerId: string, commentId: string) => {
    const qId = currentInteractionQuestion.value?.id
    if (!qId) return
    const comment = interactions.value[qId]?.[ownerId]?.comments.find((c) => c.id === commentId)
    if (comment) {
        if (!comment.likes) comment.likes = []
        comment.likes.push({ from_id: myPlayerId.value, name: myDisplayName.value })
    }
    socket.emit(SocketEvent.LIKE_COMMENT, {
        room_pin: roomPin.value,
        question_id: qId,
        answer_owner_id: ownerId,
        comment_id: commentId,
    })
}

const handleUnlikeComment = (ownerId: string, commentId: string) => {
    const qId = currentInteractionQuestion.value?.id
    if (!qId) return
    const comment = interactions.value[qId]?.[ownerId]?.comments.find((c) => c.id === commentId)
    if (comment?.likes) {
        comment.likes = comment.likes.filter((l) => l.from_id !== myPlayerId.value)
    }
    socket.emit(SocketEvent.UNLIKE_COMMENT, {
        room_pin: roomPin.value,
        question_id: qId,
        answer_owner_id: ownerId,
        comment_id: commentId,
    })
}

const performJoin = (
    pin: string,
    sid: string,
    pwd: string,
    gname: string,
    isGuest: boolean,
    isAuto = false,
    savedPlayerId: string | null = null
) => {
    if (!isAuto) errorMessage.value = ''
    isLoading.value = true
    myPlayerId.value = isGuest ? '' : sid
    myDisplayName.value = isGuest ? gname : sid
    socket.off('connect')
    socket.connect()
    socket.on('connect', () => {
        socket.emit('client_join_room', {
            room_pin: pin,
            is_guest: isGuest,
            guest_name: isGuest ? gname : null,
            student_id: !isGuest ? sid : null,
            password: !isGuest ? pwd : null,
            player_id: isAuto && isGuest ? savedPlayerId : null
        })
        storage.studentCreds.set({ pin, sid, pwd, gname, isGuest })
    })
}

const joinRoom = () => {
    if (
        joinMode.value === 'student' &&
        (!roomPin.value || !studentId.value || !password.value)
    ) {
        errorMessage.value = t('client.error_fill_fields')
        return
    }
    if (joinMode.value === 'guest' && (!roomPin.value || !guestName.value)) {
        errorMessage.value = '請填寫房間 PIN 碼與訪客暱稱'
        return
    }

    storage.studentCreds.clear()
    storage.uploadToken.clear()
    performJoin(
        roomPin.value,
        studentId.value,
        password.value,
        guestName.value,
        joinMode.value === 'guest'
    )
}

const submitAnswer = (questionId: number, answer: any) => {
    if (answer === undefined || answer === null) return
    submittedAnswers.value[questionId] = answer
    socket.emit(
        'submit_answer',
        { room_pin: roomPin.value, question_id: questionId, answer: answer },
        (response: GradingResult) => {
            gradingResults.value[questionId] = response
        }
    )
}

const leaveRoom = () => {
    socket.disconnect()
    storage.studentCreds.clear()
    storage.uploadToken.clear()
    isJoined.value = false
    isConnected.value = false
    questionsFeed.value = []
    submittedAnswers.value = {}
    tempAnswers.value = {}
    gradingResults.value = {}
}

onMounted(() => {
    if (route.query.pin) roomPin.value = route.query.pin as string
    const saved = storage.studentCreds.get()
    if (saved && !isConnected.value) {
        const { pin, sid, pwd, gname, isGuest, player_id: savedPlayerId } = saved
        roomPin.value = pin
        studentId.value = sid
        password.value = pwd
        guestName.value = gname
        joinMode.value = isGuest ? 'guest' : 'student'

        performJoin(pin, sid, pwd, gname, isGuest, true, savedPlayerId ?? null)
    }

    socket.on('room_state', (data) => {
        if (String(data.room_pin) === String(roomPin.value)) {
            isJoined.value = true
            isConnected.value = true
            isLoading.value = false
        }
    })
    socket.on('auth_success', (data) => {
        if (data.upload_token)
            storage.uploadToken.set(data.upload_token)
        if (data.player_id) {
            myPlayerId.value = data.player_id as string
            const creds = storage.studentCreds.get()
            if (creds) {
                creds.player_id = data.player_id
                storage.studentCreds.set(creds)
            }
        }
    })
    socket.on('error', (data) => {
        errorMessage.value = data.message
        isLoading.value = false
        socket.disconnect()
        isJoined.value = false
        isConnected.value = false
        storage.studentCreds.clear()
    })
    socket.on('new_questions', (data) => {
        data.questions.forEach((incomingQ: any) => {
            if (!questionsFeed.value.some((q) => q.id === incomingQ.id))
                questionsFeed.value.push(incomingQ)
        })
    })
    socket.on('recovered_answers', (data) => {
        submittedAnswers.value = { ...submittedAnswers.value, ...data.answers }
        if (data.gradings)
            gradingResults.value = { ...gradingResults.value, ...data.gradings }
    })
    socket.on(SocketEvent.PEER_ANSWERS, (data) => {
        peerAnswers.value[data.question_id] = data.answers
    })
    socket.on(SocketEvent.INTERACTION_UPDATE, (data) => {
        if (!interactions.value[data.question_id]) interactions.value[data.question_id] = {}
        interactions.value[data.question_id][data.answer_owner_id] = data.answer_interactions
    })
    socket.on('disconnect', (reason) => {
        isConnected.value = false
        if (
            reason === 'io server disconnect' ||
            reason === 'io client disconnect'
        ) {
            isJoined.value = false
        }
    })
})

onUnmounted(() => {
    socket.disconnect()
    socket.off('room_state')
    socket.off('error')
    socket.off('new_questions')
    socket.off('recovered_answers')
    socket.off('disconnect')
    socket.off(SocketEvent.PEER_ANSWERS)
    socket.off(SocketEvent.INTERACTION_UPDATE)
})
</script>

<style scoped>
.client-view {
    padding: 32px 24px;
    height: 100dvh;
    max-width: 800px;
    margin: 0 auto;
    color: var(--el-text-color-primary);
    overflow: hidden;
}
.auth-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 70vh;
}
.auth-card {
    width: 100%;
    max-width: 480px;
    border-radius: 12px;
    background-color: var(--el-bg-color-overlay);
}
.room-container {
    display: flex;
    flex-direction: column;
    height: 100%;
}

.feed-container {
    flex: 1;
    overflow-y: auto;
}

.dashboard-card {
    border-radius: 12px;
    background-color: var(--el-bg-color-overlay);
}

.flex-between {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.flex-align-center {
    display: flex;
    align-items: center;
}
.flex-wrap {
    display: flex;
    flex-wrap: wrap;
}
.flex-row {
    display: flex;
    flex-direction: row;
}
.flex-1 {
    flex: 1;
}
.gap-2 {
    gap: 8px;
}
.gap-3 {
    gap: 16px;
}
.w-full {
    width: 100%;
}
.text-center {
    text-align: center;
}
.text-right {
    text-align: right;
}
.text-muted {
    color: var(--el-text-color-secondary);
}
.text-primary {
    color: var(--el-color-primary);
    font-weight: bold;
}
.m-0 {
    margin: 0;
}
.ml-2 {
    margin-left: 8px;
}
.mt-2 {
    margin-top: 8px;
}
.mt-4 {
    margin-top: 24px;
}
.mb-0 {
    margin-bottom: 0;
}
.mb-3 {
    margin-bottom: 12px;
}
.mb-4 {
    margin-bottom: 24px;
}
.mx-auto {
    margin-left: auto;
    margin-right: auto;
}
.flex-col-gap {
    display: flex;
    flex-direction: column;
    gap: 24px;
}

/* 確保 Radio Buttons 等寬 */
.custom-radio-group :deep(.el-radio-button__inner) {
    width: 100%;
    font-size: 1.05rem;
    font-weight: bold;
}

.pulse-dot {
    width: 6px;
    height: 6px;
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
        box-shadow: 0 0 0 6px rgba(103, 194, 58, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(103, 194, 58, 0);
    }
}
.loader-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid var(--el-border-color);
    border-top-color: var(--el-color-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}
@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}
</style>
