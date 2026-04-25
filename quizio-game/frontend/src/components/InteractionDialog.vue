<template>
    <el-dialog
        :model-value="visible"
        :title="$t('interaction.dialog_title')"
        width="620px"
        @update:model-value="emit('update:visible', $event)"
        @closed="cleanupHearts"
    >
        <!-- Text mode: empty state -->
        <el-empty
            v-if="isTextType && peerAnswers.length === 0"
            :description="$t('interaction.no_peer_answers')"
            :image-size="80"
        />

        <!-- Text mode: per-answer feed -->
        <div v-else-if="isTextType" class="feed">
            <div
                v-for="peer in peerAnswers"
                :key="peer.player_id"
                class="answer-card"
            >
                <div class="card-head">
                    <el-tag
                        :type="peer.is_guest ? 'warning' : 'primary'"
                        size="small"
                        effect="plain"
                    >
                        {{ peer.name }}
                    </el-tag>
                    <div class="head-stats">
                        <span class="stat-chip"
                            >❤️ {{ getLikeCount(peer.player_id) }}</span
                        >
                        <span class="stat-chip"
                            >💬 {{ getCommentCount(peer.player_id) }}</span
                        >
                    </div>
                </div>

                <div
                    class="answer-content markdown-body"
                    v-html="renderMarkdown(String(peer.answer ?? ''))"
                />

                <div class="actions-row">
                    <div class="like-wrapper">
                        <el-button
                            :type="
                                hasLiked(peer.player_id) ? 'danger' : 'default'
                            "
                            size="small"
                            plain
                            :disabled="peer.player_id === myPlayerId"
                            @click="onLike(peer.player_id)"
                        >
                            ❤️
                        </el-button>
                        <span class="hearts-container" aria-hidden="true">
                            <span
                                v-for="h in floatingHearts[peer.player_id] ||
                                []"
                                :key="h.id"
                                class="heart-particle"
                                >❤️</span
                            >
                        </span>
                    </div>
                </div>

                <div
                    v-if="getComments(peer.player_id).length > 0"
                    class="comments-section"
                >
                    <div
                        v-for="c in getComments(peer.player_id)"
                        :key="c.id"
                        class="comment-item"
                    >
                        <el-tag
                            size="small"
                            :type="c.is_host ? 'warning' : 'info'"
                            effect="plain"
                            class="comment-author"
                        >
                            {{
                                c.is_host
                                    ? $t('interaction.from_teacher')
                                    : c.name
                            }}
                        </el-tag>
                        <span class="comment-text">{{ c.content }}</span>
                        <el-button
                            v-if="isHost && !c.id.startsWith('local-')"
                            type="danger"
                            link
                            size="small"
                            class="delete-btn"
                            @click="
                                emit('delete-comment', peer.player_id, c.id)
                            "
                            >×</el-button
                        >
                    </div>
                </div>

                <div class="comment-input-row">
                    <el-input
                        v-model="commentInputs[peer.player_id]"
                        :placeholder="$t('interaction.comment_placeholder')"
                        size="small"
                        @keyup.enter.prevent="submitComment(peer.player_id)"
                    />
                    <el-button
                        type="primary"
                        size="small"
                        plain
                        :disabled="!commentInputs[peer.player_id]?.trim()"
                        @click="submitComment(peer.player_id)"
                    >
                        {{ $t('interaction.send') }}
                    </el-button>
                </div>
            </div>
        </div>

        <!-- Choice mode: per-option discussion threads -->
        <div v-else class="feed">
            <div
                v-for="(label, idx) in optionLabels"
                :key="idx"
                class="answer-card"
            >
                <div class="card-head">
                    <span class="option-label">{{ label }}</span>
                    <span class="stat-chip"
                        >💬 {{ getCommentCount('opt_' + idx) }}</span
                    >
                </div>

                <div
                    v-if="getComments('opt_' + idx).length > 0"
                    class="comments-section"
                >
                    <div
                        v-for="c in getComments('opt_' + idx)"
                        :key="c.id"
                        class="comment-item"
                    >
                        <el-tag
                            size="small"
                            :type="c.is_host ? 'warning' : 'info'"
                            effect="plain"
                            class="comment-author"
                        >
                            {{
                                c.is_host
                                    ? $t('interaction.from_teacher')
                                    : c.name
                            }}
                        </el-tag>
                        <span class="comment-text">{{ c.content }}</span>
                        <el-button
                            v-if="isHost && !c.id.startsWith('local-')"
                            type="danger"
                            link
                            size="small"
                            class="delete-btn"
                            @click="emit('delete-comment', 'opt_' + idx, c.id)"
                            >×</el-button
                        >
                    </div>
                </div>

                <div class="comment-input-row">
                    <el-input
                        v-model="commentInputs['opt_' + idx]"
                        :placeholder="$t('interaction.comment_placeholder')"
                        size="small"
                        @keyup.enter.prevent="submitComment('opt_' + idx)"
                    />
                    <el-button
                        type="primary"
                        size="small"
                        plain
                        :disabled="!commentInputs['opt_' + idx]?.trim()"
                        @click="submitComment('opt_' + idx)"
                    >
                        {{ $t('interaction.send') }}
                    </el-button>
                </div>
            </div>
        </div>
    </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { renderMarkdown } from '../utils/markdown'
import type { PeerAnswer, QuestionInteractions } from '../types/interaction'

const props = defineProps<{
    visible: boolean
    question: any | null
    peerAnswers: PeerAnswer[]
    interactions: QuestionInteractions
    myPlayerId: string
    isHost: boolean
}>()

const emit = defineEmits<{
    'update:visible': [value: boolean]
    like: [ownerId: string]
    unlike: [ownerId: string]
    comment: [ownerId: string, content: string]
    'delete-comment': [ownerId: string, commentId: string]
}>()

const { t } = useI18n()

const commentInputs = reactive<Record<string, string>>({})
const floatingHearts = reactive<Record<string, { id: number }[]>>({})

// ── Helpers ─────────────────────────────────────────────────────────────────

const isTextType = computed(
    () => !props.question || ['short', 'essay'].includes(props.question.type)
)

const parsedOptions = computed<string[]>(() => {
    const opts = props.question?.options
    if (!opts) return []
    if (Array.isArray(opts)) return opts
    try {
        const p = JSON.parse(opts)
        return Array.isArray(p) ? p : []
    } catch {
        return []
    }
})

const optionLabels = computed<string[]>(() => {
    const q = props.question
    if (!q) return []
    const opts = parsedOptions.value
    if (q.type === 'boolean') {
        return opts.length > 0
            ? opts
            : [t('common.true_option'), t('common.false_option')]
    }
    return opts.map(
        (text: string, idx: number) =>
            `${String.fromCharCode(65 + idx)}. ${text}`
    )
})

const hasLiked = (ownerId: string) =>
    props.interactions[ownerId]?.likes.some(
        (l) => l.from_id === props.myPlayerId
    ) ?? false

const getLikeCount = (ownerId: string) =>
    props.interactions[ownerId]?.likes.length ?? 0

const getCommentCount = (ownerId: string) =>
    props.interactions[ownerId]?.comments.length ?? 0

const getComments = (ownerId: string) =>
    props.interactions[ownerId]?.comments ?? []

// ── Actions ──────────────────────────────────────────────────────────────────

const onLike = (ownerId: string) => {
    if (hasLiked(ownerId)) {
        emit('unlike', ownerId)
    } else {
        spawnHeart(ownerId)
        emit('like', ownerId)
    }
}

const submitComment = (ownerId: string) => {
    const content = commentInputs[ownerId]?.trim()
    if (!content) return
    emit('comment', ownerId, content)
    commentInputs[ownerId] = ''
}

// ── Heart animation ───────────────────────────────────────────────────────────

const spawnHeart = (ownerId: string) => {
    if (!floatingHearts[ownerId]) floatingHearts[ownerId] = []
    const id = Date.now() + Math.random()
    floatingHearts[ownerId].push({ id })
    setTimeout(() => {
        floatingHearts[ownerId] = floatingHearts[ownerId].filter(
            (h) => h.id !== id
        )
    }, 900)
}

const cleanupHearts = () => {
    Object.keys(floatingHearts).forEach((k) => delete floatingHearts[k])
}
</script>

<style scoped>
.feed {
    display: flex;
    flex-direction: column;
    gap: 16px;
    max-height: 60vh;
    overflow-y: auto;
    padding-right: 4px;
}

/* Answer Card */
.answer-card {
    border: 1px solid var(--el-border-color);
    border-radius: 10px;
    padding: 16px 20px;
    background-color: var(--el-bg-color-overlay);
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.card-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.head-stats {
    display: flex;
    gap: 12px;
}

.stat-chip {
    font-size: 0.85rem;
    color: var(--el-text-color-secondary);
}

.option-label {
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--el-text-color-primary);
}

/* Answer content */
.answer-content {
    font-size: 1rem;
    line-height: 1.6;
    color: var(--el-text-color-primary);
    word-break: break-word;
}

.answer-content.markdown-body {
    padding: 10px 14px;
    background-color: var(--el-fill-color-light);
    border-radius: 6px;
}

/* Like row */
.actions-row {
    display: flex;
    align-items: center;
}

.like-wrapper {
    position: relative;
    display: inline-flex;
    align-items: center;
}

.hearts-container {
    position: absolute;
    left: 50%;
    bottom: 100%;
    pointer-events: none;
    width: 0;
    height: 0;
}

.heart-particle {
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    font-size: 1.1rem;
    line-height: 1;
    animation: float-up 0.9s ease-out forwards;
    pointer-events: none;
}

@keyframes float-up {
    0% {
        opacity: 1;
        transform: translateX(-50%) translateY(0) scale(1);
    }
    60% {
        opacity: 0.8;
        transform: translateX(-50%) translateY(-28px) scale(1.25);
    }
    100% {
        opacity: 0;
        transform: translateX(-50%) translateY(-52px) scale(0.8);
    }
}

/* Comments */
.comments-section {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 10px 12px;
    background-color: var(--el-fill-color-light);
    border-radius: 6px;
}

.comment-item {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    font-size: 0.9rem;
}

.comment-author {
    flex-shrink: 0;
    margin-top: 1px;
}

.comment-text {
    flex: 1;
    color: var(--el-text-color-primary);
    line-height: 1.5;
    word-break: break-word;
}

.delete-btn {
    flex-shrink: 0;
    padding: 0;
    font-size: 1rem;
    line-height: 1;
}

/* Comment input */
.comment-input-row {
    display: flex;
    gap: 8px;
    align-items: center;
}

.comment-input-row .el-input {
    flex: 1;
}
</style>
