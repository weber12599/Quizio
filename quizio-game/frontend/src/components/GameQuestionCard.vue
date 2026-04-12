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
            :type="bannerType"
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

        <div v-if="role === 'host'" class="host-area mb-x">
            <div v-if="isChoiceType" class="choice-options flex-col gap-2">
                <el-card
                    v-for="(opt, idx) in options"
                    :key="idx"
                    shadow="never"
                    class="option-graded-card"
                    :class="
                        isCorrectOption(idx)
                            ? 'border-success bg-success-light'
                            : ''
                    "
                    :body-style="{ padding: '10px 16px' }"
                >
                    <div class="flex-align-start">
                        <el-tag
                            :type="isCorrectOption(idx) ? 'success' : 'info'"
                            effect="plain"
                            class="mr-3 option-letter-tag"
                            round
                        >
                            {{ String.fromCharCode(65 + idx) }}
                        </el-tag>
                        <span
                            class="option-text"
                            :class="{
                                'font-bold text-success': isCorrectOption(idx)
                            }"
                        >
                            {{ opt }}
                        </span>
                    </div>
                </el-card>
            </div>

            <div
                v-else-if="
                    question.reference_answer !== undefined &&
                    question.reference_answer !== null &&
                    question.reference_answer !== ''
                "
                class="mt-4"
            >
                <div class="custom-result-box box-ref-ans">
                    <div class="box-header">
                        <span class="mr-2">📝</span>
                        {{ $t('common.reference_answer') }}
                    </div>
                    <div
                        class="box-body markdown-body"
                        v-html="
                            renderMarkdown(String(question.reference_answer))
                        "
                    ></div>
                </div>
            </div>
        </div>

        <div v-if="role === 'client'" class="client-area">
            <div v-if="isChoiceType" class="choice-options">
                <template v-if="submittedAnswer === undefined">
                    <el-radio-group
                        v-if="isSingleChoice"
                        v-model="localAnswer"
                        class="w-full flex-col gap-2"
                    >
                        <el-radio
                            v-for="(opt, idx) in options"
                            :key="idx"
                            :value="idx"
                            border
                            class="w-full option-interactive-item"
                        >
                            {{ opt }}
                        </el-radio>
                    </el-radio-group>
                    <el-checkbox-group
                        v-else
                        v-model="localAnswer"
                        class="w-full flex-col gap-2"
                    >
                        <el-checkbox
                            v-for="(opt, idx) in options"
                            :key="idx"
                            :value="idx"
                            border
                            class="w-full option-interactive-item"
                        >
                            {{ opt }}
                        </el-checkbox>
                    </el-checkbox-group>
                </template>

                <template v-else>
                    <div class="flex-col gap-2">
                        <el-card
                            v-for="(opt, idx) in options"
                            :key="idx"
                            shadow="never"
                            class="option-graded-card"
                            :class="getGradingClass(idx)"
                            :body-style="{ padding: '10px 16px' }"
                        >
                            <div class="flex-align-start">
                                <span class="mr-3 option-icon">{{
                                    getGradingIcon(idx)
                                }}</span>
                                <span class="option-text">{{ opt }}</span>
                            </div>
                        </el-card>
                    </div>
                </template>
            </div>

            <div v-else class="text-options">
                <template v-if="submittedAnswer === undefined">
                    <GameTiptapEditor
                        v-if="question.type === 'essay'"
                        v-model="localAnswer"
                        :placeholder="$t('placeholder.essay')"
                    />
                    <el-input
                        v-else
                        v-model="localAnswer"
                        type="textarea"
                        :rows="4"
                        :placeholder="$t('placeholder.short')"
                        class="custom-textarea"
                    />
                </template>

                <template v-else>
                    <div class="flex-col gap-4">
                        <div
                            class="custom-result-box"
                            :class="
                                gradingResult?.is_correct === true
                                    ? 'box-correct'
                                    : gradingResult?.is_correct === false
                                      ? 'box-incorrect'
                                      : 'box-pending'
                            "
                        >
                            <div class="box-header">
                                <span class="mr-2">{{
                                    gradingResult?.is_correct === true
                                        ? '✅'
                                        : gradingResult?.is_correct === false
                                          ? '❌'
                                          : '📝'
                                }}</span>
                                {{ $t('client.your_answer') }}
                            </div>
                            <div
                                class="box-body markdown-body"
                                v-html="renderMarkdown(String(submittedAnswer))"
                            ></div>
                        </div>

                        <div
                            v-if="gradingResult && !gradingResult.is_correct"
                            class="custom-result-box box-ref-ans"
                        >
                            <div class="box-header">
                                <span class="mr-2">🎯</span>
                                {{ $t('common.reference_answer') }}
                            </div>
                            <div
                                class="box-body markdown-body"
                                v-html="
                                    renderMarkdown(
                                        String(gradingResult.correct_answer)
                                    )
                                "
                            ></div>
                        </div>
                    </div>
                </template>
            </div>
        </div>

        <div v-else-if="role === 'screen'" class="screen-area">
            <div
                v-if="isChoiceType"
                class="choice-stats-layout flex-col gap-4 mt-4"
            >
                <div
                    v-for="(opt, idx) in options"
                    :key="idx"
                    class="screen-option-card"
                    :class="{
                        'is-correct-answer':
                            displayState === 'answer' && isCorrectOption(idx)
                    }"
                >
                    <div
                        class="flex-align-center"
                        :class="{
                            'mb-3':
                                displayState === 'stats' ||
                                displayState === 'answer'
                        }"
                    >
                        <el-tag
                            v-if="isChoiceType"
                            :type="
                                displayState === 'answer' &&
                                isCorrectOption(idx)
                                    ? 'success'
                                    : 'info'
                            "
                            effect="plain"
                            class="mr-3 option-letter-tag"
                            round
                        >
                            {{
                                isBooleanType
                                    ? idx === 0
                                        ? 'True'
                                        : 'False'
                                    : String.fromCharCode(65 + idx)
                            }}
                        </el-tag>
                        <span
                            v-if="!isBooleanType"
                            class="text-lg font-bold text-main"
                            :class="{
                                'text-success':
                                    displayState === 'answer' &&
                                    isCorrectOption(idx)
                            }"
                        >
                            {{ opt }}
                        </span>
                        <span
                            v-if="
                                displayState === 'answer' &&
                                isCorrectOption(idx)
                            "
                            class="ml-3 text-xl"
                            >✅</span
                        >
                    </div>

                    <el-progress
                        v-if="
                            displayState === 'stats' ||
                            displayState === 'answer'
                        "
                        :percentage="getStatPercentage(idx)"
                        :stroke-width="36"
                        text-inside
                        :color="getProgressColor(idx)"
                    >
                        <span class="progress-text"
                            >{{ stats?.counts[idx] || 0 }} ({{
                                getStatPercentage(idx)
                            }}%)</span
                        >
                    </el-progress>
                </div>
            </div>

            <div v-else class="text-stats-layout flex-col mt-4">
                <div
                    v-if="displayState === 'stats' || displayState === 'answer'"
                    class="text-stats text-center py-5"
                >
                    <div
                        class="font-black"
                        style="
                            font-size: 7rem;
                            color: var(--el-color-primary);
                            line-height: 1;
                        "
                    >
                        {{ stats?.total || 0 }}
                    </div>
                    <div
                        class="text-xl text-muted mt-3"
                        style="font-size: 2rem; font-weight: bold"
                    >
                        {{ $t('screen.responses_received') }}
                    </div>
                </div>

                <div
                    v-if="
                        displayState === 'answer' && question.reference_answer
                    "
                    class="custom-result-box box-ref-ans mt-5"
                >
                    <div class="box-header" style="font-size: 2rem">
                        <span class="mr-2">💡</span>
                        {{ $t('common.reference_answer') }}
                    </div>
                    <div
                        class="box-body markdown-body screen-huge-text"
                        v-html="
                            renderMarkdown(String(question.reference_answer))
                        "
                    ></div>
                </div>
            </div>
        </div>

        <div class="q-actions border-t" v-if="$slots.actions">
            <slot name="actions"></slot>
        </div>
    </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatQuestionType } from '../utils/locales'
import { renderMarkdown } from '../utils/markdown'
import GameTiptapEditor from './GameTiptapEditor.vue'

const { t } = useI18n()

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

const localAnswer = computed({
    get() {
        if (
            props.question.type === 'multiple' &&
            !Array.isArray(props.modelValue)
        ) {
            return []
        }
        return props.modelValue
    },
    set(val) {
        emit('update:modelValue', val)
    }
})
const isBooleanType = computed(() => ['boolean'].includes(props.question.type))
const isChoiceType = computed(() =>
    ['single', 'multiple', 'boolean'].includes(props.question.type)
)
const isSingleChoice = computed(() =>
    ['single', 'boolean'].includes(props.question.type)
)

const options = computed(() => {
    let optsRaw = props.question.options
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
    if (props.question.type === 'boolean' && parsedOpts.length === 0) {
        return [t('common.true_option'), t('common.false_option')]
    }
    return parsedOpts
})

const isCorrectOption = (idx: number) => {
    const refAns = props.question.reference_answer
    if (refAns === undefined || refAns === null || refAns === '') return false

    if (props.question.type === 'multiple') {
        if (!Array.isArray(refAns)) return false
        // 強制轉字串比對，避免 [0, 1] 遇到 ["0", "1"] 失效
        return refAns.map(String).includes(String(idx))
    }

    if (props.question.type === 'boolean') {
        const isTrueAns =
            String(refAns).toLowerCase() === 'true' ||
            refAns === true ||
            refAns === 1 ||
            refAns === '1'
        return isTrueAns ? idx === 0 : idx === 1
    }

    return String(refAns).trim() === String(idx).trim()
}

const bannerType = computed(() => {
    if (props.gradingResult?.is_correct === true) return 'success'
    if (props.gradingResult?.is_correct === false) return 'error'
    return 'info' // null, undefined (Needs manual grading)
})
const bannerIcon = computed(() => {
    return ''
})
const bannerText = computed(() => {
    if (props.gradingResult?.is_correct === true) return t('banner.correct')
    if (props.gradingResult?.is_correct === false) return t('banner.incorrect')
    return t('banner.pending_review') // null, undefined
})

const getGradingClass = (idx: number) => {
    if (!props.gradingResult) return ''

    const valToCheck = props.question.type === 'boolean' ? idx === 0 : idx
    const stuAns = props.submittedAnswer
    const corrAns = props.gradingResult.correct_answer

    let isStuSelected = false
    let isCorrectAns = false

    // 判斷該選項是否為「正確答案」
    if (props.question.type === 'multiple' && Array.isArray(corrAns)) {
        isCorrectAns = corrAns.map(String).includes(String(valToCheck))
    } else {
        isCorrectAns = String(corrAns) === String(valToCheck)
    }

    // 判斷學生是否「選了這個選項」
    if (Array.isArray(stuAns)) {
        isStuSelected = stuAns.map(String).includes(String(valToCheck))
    } else {
        isStuSelected = String(stuAns) === String(valToCheck)
    }

    // UI 邏輯：
    // 1. 學生選了，且這確實是答案 -> 標記正確 (Solid Green)
    if (isStuSelected && isCorrectAns) return 'border-success bg-success-light'
    // 2. 學生選了，但這不是答案 -> 標記錯誤 (Solid Red)
    if (isStuSelected && !isCorrectAns) return 'border-danger bg-danger-light'
    // 3. 學生沒選，但這是正確答案 -> 標記漏選的答案 (Dashed Green)
    if (!isStuSelected && isCorrectAns)
        return 'border-dashed-success bg-success-light-alt'

    return ''
}

const getGradingIcon = (idx: number) => {
    const cls = getGradingClass(idx)
    if (cls.includes('border-success')) return '✅'
    if (cls.includes('border-danger')) return '❌'
    if (cls.includes('border-dashed-success')) return '🎯'
    return '⬜'
}

const getStatPercentage = (idx: number | string) => {
    if (!props.stats || props.stats.total === 0) return 0
    const count = props.stats.counts[idx] || 0
    return Math.round((count / props.stats.total) * 100)
}
const getProgressColor = (idx: number) => {
    const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#8E44AD']
    return colors[idx % colors.length]
}
</script>

<style scoped>
.game-question-card {
    border-radius: 12px;
}

/* ==========================================
   Utilities & Gap Spacing
========================================== */
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
.flex-align-start {
    display: flex;
    align-items: flex-start;
}
.gap-2 {
    gap: 8px;
} /* 強制縮小選項之間的間距 */
.gap-3 {
    gap: 12px;
}
.gap-4 {
    gap: 16px;
}
.w-full {
    width: 100%;
}
.flex-col {
    display: flex;
    flex-direction: column;
}
.border-t {
    border-top: 1px dashed var(--el-border-color-lighter);
    margin-top: 24px;
    padding-top: 20px;
}
.mr-2 {
    margin-right: 8px;
}
.mr-3 {
    margin-right: 12px;
}
.font-bold {
    font-weight: bold;
}
.text-lg {
    font-size: 1.25rem;
}
.text-main {
    color: var(--el-text-color-primary);
}
.text-center {
    text-align: center;
}
.text-muted {
    color: var(--el-text-color-secondary);
}

/* ==========================================
   Host Specific UI 
========================================== */
.option-letter-tag {
    font-size: 1rem;
    font-weight: bold;
    height: 30px;
    text-align: center;
    line-height: 28px;
}

/* ==========================================
   Interactive Options (Radio / Checkbox)
========================================== */
.option-interactive-item {
    margin-right: 0 !important;
    height: auto !important;
    padding: 10px 16px; /* 嚴格限制高度 */
    border-radius: 8px;
    display: flex;
    align-items: flex-start;
    transition: all 0.2s ease;
    background-color: var(--el-fill-color-blank);
}
.option-interactive-item:hover {
    border-color: var(--el-color-primary);
    background-color: var(--el-color-primary-light-9);
}
.option-interactive-item :deep(.el-radio__input),
.option-interactive-item :deep(.el-checkbox__input) {
    margin-top: 3px;
}
.option-interactive-item :deep(.el-radio__label),
.option-interactive-item :deep(.el-checkbox__label) {
    white-space: normal;
    line-height: 1.5;
    font-size: 1.05rem;
    flex: 1;
    padding-left: 10px;
    color: var(--el-text-color-regular);
}

/* ==========================================
   Graded Options (el-card)
========================================== */
.option-graded-card {
    border-width: 2px;
    border-radius: 8px;
    transition: all 0.3s;
    background-color: var(--el-fill-color-blank);
}
/* 在 Template 已經加上 :body-style="{ padding: '10px 16px' }" */

.option-icon {
    font-size: 1.15rem;
    line-height: 1.5;
}
.option-text {
    font-size: 1.05rem;
    line-height: 1.5;
    color: var(--el-text-color-primary);
    word-break: break-word;
}

/* Color Variables overrides */
.border-success {
    border-color: var(--el-color-success) !important;
}
.border-danger {
    border-color: var(--el-color-danger) !important;
}
.border-dashed-success {
    border-color: var(--el-color-success) !important;
    border-style: dashed;
}
.bg-success-light {
    background-color: var(--el-color-success-light-9) !important;
}
.bg-danger-light {
    background-color: var(--el-color-danger-light-9) !important;
}
.bg-success-light-alt {
    background-color: var(--el-color-success-light-8) !important;
}
.text-success {
    color: var(--el-color-success) !important;
}
.text-danger {
    color: var(--el-color-danger) !important;
}

/* ==========================================
   Custom Result Box (Bulletproof Structure)
========================================== */
.custom-result-box {
    border-radius: 8px;
    border-width: 2px;
    border-style: solid;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}
.box-header {
    padding: 12px 20px;
    font-weight: bold;
    font-size: 1.05rem;
    display: flex;
    align-items: center;
}
.box-body {
    padding: 16px 20px;
    flex: 1;
}

/* Colors for Box */
.box-ref-ans {
    border-color: var(--el-color-success);
    border-style: dashed;
    background-color: var(--el-color-success-light-9);
}
.box-ref-ans .box-header {
    color: var(--el-color-success);
    border-bottom: 1px dashed var(--el-color-success-light-5);
    background-color: var(--el-color-success-light-8);
}

.box-correct {
    border-color: var(--el-color-success);
    background-color: var(--el-color-success-light-9);
}
.box-correct .box-header {
    color: var(--el-color-success);
    border-bottom: 1px solid var(--el-color-success-light-5);
    background-color: var(--el-color-success-light-8);
}

.box-incorrect {
    border-color: var(--el-color-danger);
    background-color: var(--el-color-danger-light-9);
}
.box-incorrect .box-header {
    color: var(--el-color-danger);
    border-bottom: 1px solid var(--el-color-danger-light-5);
    background-color: var(--el-color-danger-light-8);
}

.box-pending {
    border-color: var(--el-border-color);
    background-color: var(--el-fill-color-light);
}
.box-pending .box-header {
    color: var(--el-text-color-primary);
    border-bottom: 1px solid var(--el-border-color-lighter);
    background-color: var(--el-fill-color);
}

html.dark .box-header {
    background-color: rgba(0, 0, 0, 0.15);
}

/* ==========================================
   Text Options Input
========================================== */
.custom-textarea :deep(.el-textarea__inner) {
    font-size: 1.05rem;
    padding: 12px 16px;
    line-height: 1.6;
    border-radius: 8px;
    background-color: var(--el-fill-color-blank);
}

/* ==========================================
   Alerts
========================================== */
.graded-alert {
    border-radius: 8px;
    padding: 12px 16px;
}
.graded-alert :deep(.el-alert__title) {
    font-size: 1.05rem;
    font-weight: bold;
}

/* ==========================================
   Screen Mode Layout Overrides
========================================== */
.is-screen-mode {
    border: 4px solid var(--el-color-primary-light-5);
    border-radius: 24px;
    background-color: var(--el-bg-color-overlay);
}
.progress-text {
    font-size: 1.1rem;
    font-weight: bold;
}
</style>

<style scoped>
/* ==========================================
   Markdown Content Styles
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
.markdown-body :deep(h4) {
    font-size: 1em;
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
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
    margin-top: 0;
    margin-bottom: 1em;
    /* padding-left: 2em; */
}
.markdown-body :deep(ul) {
    list-style-type: disc;
}
.markdown-body :deep(ol) {
    list-style-type: decimal;
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

/* ==========================================
   Screen Mode Option Cards
========================================== */
.screen-option-card {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 16px 24px;
    border-radius: 16px;
    background-color: var(--el-fill-color-light);
    border: 3px solid transparent;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.screen-option-card.is-correct-answer {
    background-color: var(--el-color-success-light-9);
    border-color: var(--el-color-success);
    transform: scale(1.02);
    box-shadow: 0 8px 16px rgba(103, 194, 58, 0.2);
}

.ml-3 {
    margin-left: 12px;
}

.text-stats-layout {
    gap: 16px;
}
</style>
