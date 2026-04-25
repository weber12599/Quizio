<template>
    <el-dialog
        :model-value="visible"
        :fullscreen="true"
        class="ig-dialog"
        :show-close="false"
        @update:model-value="emit('update:visible', $event)"
        @closed="cleanupHearts"
    >
        <template #header>
            <div class="ig-header">
                <span class="ig-header-title">{{ $t('interaction.dialog_title') }}</span>
                <button class="ig-close-btn" type="button" @click="emit('update:visible', false)">
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M6 18L18 6M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                </button>
            </div>
        </template>

        <!-- Question banner (shared across both modes) -->
        <div v-if="question" class="question-banner">
            <div
                class="question-banner-body markdown-body"
                v-html="renderMarkdown(String(question.content ?? ''))"
            />
        </div>

        <!-- Text mode: empty state -->
        <el-empty
            v-if="isTextType && peerAnswers.length === 0"
            :description="$t('interaction.no_peer_answers')"
            :image-size="80"
            class="empty-state"
        />

        <!-- Text mode: per-answer feed -->
        <div v-else-if="isTextType" class="ig-feed">
            <div
                v-for="peer in peerAnswers"
                :key="peer.player_id"
                class="ig-post"
            >
                <!-- Post header -->
                <div class="post-header">
                    <div
                        class="avatar-circle"
                        :style="{ background: avatarColor(peer.name) }"
                        aria-hidden="true"
                    >
                        {{ peer.name.charAt(0).toUpperCase() }}
                    </div>
                    <div class="author-info">
                        <span class="author-name">{{ peer.name }}</span>
                        <span v-if="peer.is_guest" class="guest-badge">訪客</span>
                    </div>
                    <span v-if="peer.player_id === myPlayerId" class="own-badge">
                        {{ $t('client.your_answer') }}
                    </span>
                </div>

                <!-- Answer content -->
                <div
                    class="post-body markdown-body"
                    v-html="renderMarkdown(String(peer.answer ?? ''))"
                />

                <!-- Action row: heart + comment count -->
                <div class="post-actions">
                    <div class="like-wrapper">
                        <button
                            class="action-btn like-btn"
                            :class="{ liked: hasLiked(peer.player_id) }"
                            type="button"
                            :aria-pressed="hasLiked(peer.player_id)"
                            @click="onLike(peer.player_id)"
                        >
                            <svg class="heart-icon" viewBox="0 0 24 24" aria-hidden="true">
                                <path d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 4.875 5.25 8.625 9 11.25 3.75-2.625 9-6.375 9-11.25Z"/>
                            </svg>
                        </button>
                        <span v-if="getLikeCount(peer.player_id) > 0" class="action-count">
                            {{ getLikeCount(peer.player_id) }}
                        </span>
                        <!-- Floating hearts -->
                        <span class="hearts-container" aria-hidden="true">
                            <span
                                v-for="h in floatingHearts[peer.player_id] || []"
                                :key="h.id"
                                class="heart-particle"
                            >
                                <svg viewBox="0 0 24 24">
                                    <path d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 4.875 5.25 8.625 9 11.25 3.75-2.625 9-6.375 9-11.25Z"/>
                                </svg>
                            </span>
                        </span>
                    </div>
                    <div class="comment-stat">
                        <svg class="comment-icon" viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M2.25 12.76c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.076-4.076a1.526 1.526 0 0 1 1.037-.443 48.282 48.282 0 0 0 5.68-.494c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z"/>
                        </svg>
                        <span v-if="getCommentCount(peer.player_id) > 0" class="action-count">
                            {{ getCommentCount(peer.player_id) }}
                        </span>
                    </div>
                </div>

                <!-- Comments section -->
                <div class="comments-section">
                    <TransitionGroup name="comment" tag="div" class="comments-list">
                        <div
                            v-for="c in getComments(peer.player_id)"
                            :key="c.id"
                            class="comment-row"
                        >
                            <span
                                class="comment-author"
                                :class="{ 'comment-author--host': c.is_host }"
                            >{{ c.is_host ? $t('interaction.from_teacher') : c.name }}</span>
                            <span class="comment-text">{{ c.content }}</span>
                            <button
                                class="comment-like-btn"
                                :class="{ liked: hasLikedComment(c) }"
                                type="button"
                                @click="onLikeComment(peer.player_id, c.id)"
                            >
                                <svg class="heart-icon-sm" viewBox="0 0 24 24" aria-hidden="true">
                                    <path d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 4.875 5.25 8.625 9 11.25 3.75-2.625 9-6.375 9-11.25Z"/>
                                </svg>
                                <span v-if="(c.likes?.length ?? 0) > 0" class="comment-like-count">
                                    {{ c.likes.length }}
                                </span>
                            </button>
                        </div>
                    </TransitionGroup>
                    <p v-if="getComments(peer.player_id).length === 0" class="no-comments-hint">
                        {{ $t('interaction.be_first_to_comment') }}
                    </p>
                </div>

                <!-- Comment input -->
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
        <div v-else class="ig-feed">
            <div
                v-for="(label, idx) in optionLabels"
                :key="idx"
                class="ig-post"
            >
                <div class="post-header">
                    <span class="option-label">{{ label }}</span>
                    <div class="comment-stat">
                        <svg class="comment-icon" viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M2.25 12.76c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.076-4.076a1.526 1.526 0 0 1 1.037-.443 48.282 48.282 0 0 0 5.68-.494c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z"/>
                        </svg>
                        <span v-if="getCommentCount('opt_' + idx) > 0" class="action-count">
                            {{ getCommentCount('opt_' + idx) }}
                        </span>
                    </div>
                </div>

                <div class="comments-section">
                    <TransitionGroup name="comment" tag="div" class="comments-list">
                        <div
                            v-for="c in getComments('opt_' + idx)"
                            :key="c.id"
                            class="comment-row"
                        >
                            <span
                                class="comment-author"
                                :class="{ 'comment-author--host': c.is_host }"
                            >{{ c.is_host ? $t('interaction.from_teacher') : c.name }}</span>
                            <span class="comment-text">{{ c.content }}</span>
                            <button
                                class="comment-like-btn"
                                :class="{ liked: hasLikedComment(c) }"
                                type="button"
                                @click="onLikeComment('opt_' + idx, c.id)"
                            >
                                <svg class="heart-icon-sm" viewBox="0 0 24 24" aria-hidden="true">
                                    <path d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 4.875 5.25 8.625 9 11.25 3.75-2.625 9-6.375 9-11.25Z"/>
                                </svg>
                                <span v-if="(c.likes?.length ?? 0) > 0" class="comment-like-count">
                                    {{ c.likes.length }}
                                </span>
                            </button>
                        </div>
                    </TransitionGroup>
                    <p v-if="getComments('opt_' + idx).length === 0" class="no-comments-hint">
                        {{ $t('interaction.be_first_to_comment') }}
                    </p>
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
import type { Comment, PeerAnswer, QuestionInteractions } from '../types/interaction'

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
    'like-comment': [ownerId: string, commentId: string]
    'unlike-comment': [ownerId: string, commentId: string]
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

const avatarColor = (name: string): string => {
    const colors = ['#f87171', '#fb923c', '#fbbf24', '#34d399', '#60a5fa', '#a78bfa', '#f472b6']
    let h = 0
    for (const c of name) h = (h * 31 + c.charCodeAt(0)) % colors.length
    return colors[h]
}

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

const hasLikedComment = (c: Comment): boolean => {
    if (!c.likes?.length) return false
    const meId = props.isHost ? '__host__' : props.myPlayerId
    return c.likes.some((l) => l.from_id === meId)
}

// ── Actions ──────────────────────────────────────────────────────────────────

const onLike = (ownerId: string) => {
    if (hasLiked(ownerId)) {
        emit('unlike', ownerId)
    } else {
        spawnHeart(ownerId)
        emit('like', ownerId)
    }
}

const onLikeComment = (ownerId: string, commentId: string) => {
    const c = getComments(ownerId).find((x) => x.id === commentId)
    if (!c) return
    if (hasLikedComment(c)) emit('unlike-comment', ownerId, commentId)
    else emit('like-comment', ownerId, commentId)
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
/* ── Dialog shell ─────────────────────────────────────────────────────────── */

:deep(.ig-dialog .el-dialog__header) {
    padding: 0;
    margin: 0;
    border-bottom: 1px solid var(--el-border-color-lighter);
}

:deep(.ig-dialog .el-dialog__body) {
    padding: 0;
    height: calc(100dvh - 57px);
    overflow-y: auto;
    display: flex;
    flex-direction: column;
}

/* Bottom-sheet slide-in animation */
:deep(.ig-dialog.el-dialog) {
    animation: sheet-in 0.32s cubic-bezier(0.32, 0.72, 0, 1) both;
}

@keyframes sheet-in {
    from { transform: translateY(40px); opacity: 0; }
    to   { transform: translateY(0);    opacity: 1; }
}

/* ── Header ──────────────────────────────────────────────────────────────── */

.ig-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 20px;
    height: 57px;
    box-sizing: border-box;
}

.ig-header-title {
    font-weight: 700;
    font-size: 1rem;
    color: var(--el-text-color-primary);
}

.ig-close-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: none;
    border: none;
    padding: 6px;
    cursor: pointer;
    border-radius: 50%;
    color: var(--el-text-color-regular);
    line-height: 0;
}

.ig-close-btn:hover { color: var(--el-text-color-primary); }
.ig-close-btn:focus-visible { outline: 2px solid var(--el-color-primary); outline-offset: 2px; }

.ig-close-btn svg {
    width: 22px;
    height: 22px;
}

/* ── Question banner ─────────────────────────────────────────────────────── */

.question-banner {
    max-width: 720px;
    width: 100%;
    margin: 0 auto;
    padding: 14px 16px 0;
    box-sizing: border-box;
}

.question-banner-body {
    padding: 12px 16px;
    background: var(--el-color-primary-light-9);
    border-left: 3px solid var(--el-color-primary);
    border-radius: 6px;
    font-size: 0.95rem;
    line-height: 1.6;
    color: var(--el-text-color-primary);
    word-break: break-word;
}

/* ── Feed ────────────────────────────────────────────────────────────────── */

.ig-feed {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0;
    max-width: 720px;
    width: 100%;
    margin: 0 auto;
    padding: 16px 16px 32px;
    box-sizing: border-box;
}

.empty-state {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* ── Post card ───────────────────────────────────────────────────────────── */

.ig-post {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 20px 0;
    border-bottom: 1px solid var(--el-border-color-lighter);
}

.ig-post:last-child { border-bottom: none; }

/* ── Post header ─────────────────────────────────────────────────────────── */

.post-header {
    display: flex;
    align-items: center;
    gap: 10px;
}

.avatar-circle {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    font-weight: 700;
    color: #fff;
    flex-shrink: 0;
    user-select: none;
}

.author-info {
    display: flex;
    align-items: center;
    gap: 6px;
    flex: 1;
    min-width: 0;
}

.author-name {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--el-text-color-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.guest-badge {
    font-size: 0.7rem;
    padding: 1px 6px;
    border-radius: 999px;
    background: var(--el-color-warning-light-9);
    color: var(--el-color-warning-dark-2);
    font-weight: 500;
    flex-shrink: 0;
}

.own-badge {
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 999px;
    background: var(--el-color-primary-light-9);
    color: var(--el-color-primary);
    font-weight: 600;
    flex-shrink: 0;
}

/* ── Post body ───────────────────────────────────────────────────────────── */

.post-body {
    font-size: 1rem;
    line-height: 1.6;
    color: var(--el-text-color-primary);
    word-break: break-word;
    padding: 10px 14px;
    background-color: var(--el-fill-color-light);
    border-radius: 8px;
    overflow: hidden;
}

.post-body :deep(img),
.question-banner-body :deep(img) {
    max-width: 100%;
    height: auto;
    display: block;
    border-radius: 4px;
}

/* ── Action row ──────────────────────────────────────────────────────────── */

.post-actions {
    display: flex;
    align-items: center;
    gap: 16px;
}

.like-wrapper {
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.action-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: none;
    border: none;
    padding: 4px;
    cursor: pointer;
    border-radius: 50%;
    line-height: 0;
}

.action-btn:focus-visible { outline: 2px solid var(--el-color-primary); outline-offset: 2px; }
.action-btn:disabled { opacity: 0.35; cursor: not-allowed; }

/* Heart icon — hollow gray by default */
.heart-icon {
    width: 24px;
    height: 24px;
    display: block;
    overflow: visible;
}

.heart-icon path {
    fill: none;
    stroke: var(--el-text-color-secondary);
    stroke-width: 1.5;
    transition: fill 0.2s ease, stroke 0.2s ease;
}

/* Liked: filled red */
.like-btn.liked .heart-icon path {
    fill: #ef4444;
    stroke: #ef4444;
}

/* Hover preview */
.like-btn:hover:not(:disabled) .heart-icon path { stroke: #ef4444; }

/* Bounce on like */
@keyframes heart-pop {
    0%   { transform: scale(1); }
    40%  { transform: scale(1.4); }
    70%  { transform: scale(0.9); }
    100% { transform: scale(1); }
}

.like-btn.liked .heart-icon {
    animation: heart-pop 0.35s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
}

.action-count {
    font-size: 0.85rem;
    color: var(--el-text-color-secondary);
    line-height: 1;
}

.comment-stat {
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.comment-icon {
    width: 22px;
    height: 22px;
    display: block;
}

.comment-icon path {
    fill: none;
    stroke: var(--el-text-color-secondary);
    stroke-width: 1.5;
    stroke-linejoin: round;
    stroke-linecap: round;
}

.option-label {
    flex: 1;
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--el-text-color-primary);
}

/* ── Floating hearts ─────────────────────────────────────────────────────── */

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
    width: 20px;
    height: 20px;
    transform: translateX(-50%);
    animation: float-up 0.9s ease-out forwards;
    pointer-events: none;
    display: block;
}

.heart-particle svg { width: 100%; height: 100%; display: block; }

.heart-particle svg path { fill: #ef4444; stroke: none; }

@keyframes float-up {
    0%   { opacity: 1;   transform: translateX(-50%) translateY(0)    scale(1);    }
    60%  { opacity: 0.8; transform: translateX(-50%) translateY(-28px) scale(1.25); }
    100% { opacity: 0;   transform: translateX(-50%) translateY(-52px) scale(0.8);  }
}

/* ── Comments ────────────────────────────────────────────────────────────── */

.comments-section {
    display: flex;
    flex-direction: column;
    gap: 0;
}

.comments-list {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.comment-row {
    display: flex;
    align-items: baseline;
    gap: 6px;
    font-size: 0.88rem;
    padding: 3px 0;
    line-height: 1.5;
}

.comment-author {
    font-weight: 600;
    color: var(--el-text-color-primary);
    flex-shrink: 0;
}

.comment-author--host { color: var(--el-color-warning-dark-2); }

.comment-text {
    flex: 1;
    color: var(--el-text-color-regular);
    word-break: break-word;
}

.no-comments-hint {
    font-size: 0.82rem;
    color: var(--el-text-color-placeholder);
    margin: 4px 0 0;
    padding: 0;
}

/* Comment like button */
.comment-like-btn {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    background: none;
    border: none;
    padding: 2px;
    cursor: pointer;
    line-height: 0;
    flex-shrink: 0;
    align-self: center;
}

.comment-like-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.comment-like-btn:focus-visible { outline: 2px solid var(--el-color-primary); outline-offset: 1px; border-radius: 4px; }

.heart-icon-sm {
    width: 14px;
    height: 14px;
    display: block;
    overflow: visible;
}

.heart-icon-sm path {
    fill: none;
    stroke: var(--el-text-color-placeholder);
    stroke-width: 1.8;
    transition: fill 0.2s ease, stroke 0.2s ease;
}

.comment-like-btn.liked .heart-icon-sm path { fill: #ef4444; stroke: #ef4444; }
.comment-like-btn:hover:not(:disabled) .heart-icon-sm path { stroke: #ef4444; }

.comment-like-count {
    font-size: 0.75rem;
    color: var(--el-text-color-secondary);
    line-height: 1;
}

.comment-like-btn.liked .comment-like-count { color: #ef4444; }

/* Comment slide-in animation */
.comment-enter-active { transition: all 0.25s ease; }
.comment-enter-from   { opacity: 0; transform: translateY(8px); }

/* ── Comment input ───────────────────────────────────────────────────────── */

.comment-input-row {
    display: flex;
    gap: 8px;
    align-items: center;
    padding-top: 4px;
}

.comment-input-row .el-input { flex: 1; }
</style>
