<template>
    <el-card
        class="game-question-card"
        shadow="hover"
        :body-style="{ padding: '28px 32px' }"
        :class="{ 'is-screen-mode': role === 'screen' }"
    >
        <div class="q-header flex-between mb-x">
            <div class="flex-align-center gap-3">
                <slot name="header-left">
                    <el-tag
                        v-if="index !== undefined"
                        type="info"
                        effect="plain"
                        size="large"
                    >
                        Q{{ index + 1 }}
                    </el-tag>
                    <el-tag type="info" effect="plain" size="large">
                        {{ formatQuestionType(question.type) }}
                    </el-tag>
                </slot>
            </div>
            <div class="header-right">
                <slot name="header-right"></slot>
            </div>
        </div>

        <el-alert
            v-if="role === 'client' && gradingResult"
            :title="bannerText"
            :type="bannerType as any"
            :icon="bannerIcon"
            show-icon
            :closable="false"
            class="mb-x graded-alert"
        />
        <el-alert
            v-else-if="role === 'client' && submittedAnswer !== undefined"
            :title="$t('banner.pending_review')"
            type="info"
            show-icon
            :closable="false"
            class="mb-x graded-alert"
        />

        <div
            class="markdown-body q-content"
            :class="{
                'screen-huge-text': role === 'screen',
                'mb-x': role !== 'host' || !isChoiceType
            }"
            v-html="renderMarkdown(question.content)"
        ></div>

        <HostArea
            v-if="role === 'host'"
            :question="question"
            :options="options"
            :isChoiceType="isChoiceType"
            :isCorrectOption="isCorrectOption"
        />

        <ClientArea
            v-else-if="role === 'client'"
            v-model="localAnswer"
            :question="question"
            :options="options"
            :submittedAnswer="submittedAnswer"
            :gradingResult="gradingResult"
            :isChoiceType="isChoiceType"
            :isSingleChoice="isSingleChoice"
            :getGradingClass="getGradingClass"
            :getGradingIcon="getGradingIcon"
        />

        <ScreenArea
            v-else-if="role === 'screen'"
            :question="question"
            :options="options"
            :isChoiceType="isChoiceType"
            :isBooleanType="isBooleanType"
            :displayState="displayState"
            :stats="stats"
            :isCorrectOption="isCorrectOption"
            :getStatPercentage="getStatPercentage"
            :getProgressColor="getProgressColor"
        />

        <div class="q-actions border-t" v-if="$slots.actions">
            <slot name="actions"></slot>
        </div>
    </el-card>
</template>

<script setup lang="ts">
import { formatQuestionType } from '../utils/locales'
import { renderMarkdown } from '../utils/markdown'
import { useGameQuestion } from '../composables/useGameQuestion'
import HostArea from './HostArea.vue'
import ClientArea from './ClientArea.vue'
import ScreenArea from './ScreenArea.vue'

const props = defineProps({
    question: { type: Object, required: true },
    index: { type: Number, default: undefined },
    role: { type: String, default: 'client' },
    modelValue: { type: [String, Number, Boolean, Array], default: undefined },
    submittedAnswer: {
        type: [String, Number, Boolean, Array],
        default: undefined
    },
    displayState: { type: String, default: 'question' },
    gradingResult: { type: Object, default: undefined },
    stats: { type: Object, default: () => ({ counts: {}, total: 0 }) }
})

const emit = defineEmits(['update:modelValue'])

const {
    localAnswer,
    isBooleanType,
    isChoiceType,
    isSingleChoice,
    options,
    isCorrectOption,
    bannerType,
    bannerIcon,
    bannerText,
    getGradingClass,
    getGradingIcon,
    getStatPercentage,
    getProgressColor
} = useGameQuestion(props, emit)
</script>

<style scoped>
.game-question-card {
    border-radius: 12px;
}

.mb-x {
    margin-bottom: 24px;
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
.gap-3 {
    gap: 12px;
}
.border-t {
    border-top: 1px dashed var(--el-border-color-lighter);
    margin-top: 24px;
    padding-top: 20px;
}

.graded-alert {
    border-radius: 8px;
    padding: 12px 16px;
}
.graded-alert :deep(.el-alert__title) {
    font-size: 1.05rem;
    font-weight: bold;
}

.is-screen-mode {
    border: 4px solid var(--el-color-primary-light-5);
    border-radius: 24px;
    background-color: var(--el-bg-color-overlay);
}

/* ==========================================
   Markdown Styles (Shared down to child areas)
========================================== */
.markdown-body {
    width: 100%;
    color: var(--el-text-color-primary);
    line-height: 1.6;
    word-wrap: break-word;
}
.markdown-body :deep(> *:first-child) {
    margin-top: 0 !important;
}
.markdown-body :deep(> *:last-child) {
    margin-bottom: 0 !important;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    font-weight: 600;
    line-height: 1.25;
    color: var(--el-text-color-primary);
}
.markdown-body :deep(h1) {
    font-size: 2em;
}
.markdown-body :deep(h2) {
    font-size: 1.5em;
    border-bottom: 1px solid var(--el-border-color-lighter);
    padding-bottom: 0.3em;
}
.markdown-body :deep(h3) {
    font-size: 1.25em;
}
.markdown-body :deep(p) {
    margin-top: 0;
    margin-bottom: 1em;
    font-size: 1.15rem;
}
.markdown-body :deep(blockquote) {
    margin: 0 0 1em 0;
    padding: 0.8em 1.2em;
    color: var(--el-text-color-secondary);
    border-left: 0.3em solid var(--el-border-color);
    background-color: var(--el-fill-color-light);
    border-radius: 0 4px 4px 0;
}
.markdown-body :deep(ul) {
    list-style-type: disc;
    margin-bottom: 1em;
}
.markdown-body :deep(ol) {
    list-style-type: decimal;
    margin-bottom: 1em;
}
.markdown-body :deep(li) {
    margin-bottom: 0.5em;
    font-size: 1.15rem;
}
.markdown-body :deep(img) {
    max-width: 100%;
    max-height: 40vh;
    height: auto;
    border-radius: 8px;
    margin: 12px 0;
    box-shadow: var(--el-box-shadow-light);
    object-fit: contain;
    display: block;
}
.markdown-body :deep(pre) {
    background-color: #282c34;
    color: #abb2bf;
    padding: 1.2rem;
    border-radius: 8px;
    overflow-x: auto;
    font-family: monospace;
    font-size: 1.05rem;
    margin: 1em 0;
}
.markdown-body :deep(code) {
    background-color: var(--el-fill-color-dark);
    color: var(--el-text-color-regular);
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.9em;
}
.markdown-body :deep(pre code) {
    background-color: transparent;
    color: inherit;
    padding: 0;
    border-radius: 0;
}
.markdown-body :deep(hr) {
    height: 1px;
    background-color: var(--el-border-color-lighter);
    border: none;
    margin: 2em 0;
}

.screen-huge-text :deep(p) {
    font-size: clamp(2rem, 4.5vh, 3.5rem) !important;
    font-weight: 800;
    text-align: center;
}
.screen-huge-text :deep(pre) {
    font-size: clamp(1.2rem, 2.5vh, 2rem) !important;
    max-width: 90%;
    margin: 0 auto;
}
</style>
