<template>
    <div class="screen-area">
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
                            displayState === 'answer' && isCorrectOption(idx)
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
                        v-if="displayState === 'answer' && isCorrectOption(idx)"
                        class="ml-3 text-xl"
                        >✅</span
                    >
                </div>

                <el-progress
                    v-if="displayState === 'stats' || displayState === 'answer'"
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
                v-if="displayState === 'answer' && question.reference_answer"
                class="custom-result-box box-ref-ans mt-5"
            >
                <div class="box-header" style="font-size: 2rem">
                    <span class="mr-2">💡</span>
                    {{ $t('common.reference_answer') }}
                </div>
                <div
                    class="box-body markdown-body screen-huge-text"
                    v-html="renderMarkdown(String(question.reference_answer))"
                ></div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { renderMarkdown } from '../utils/markdown'

const { t } = useI18n()

defineProps<{
    question: any
    options: string[]
    isChoiceType: boolean
    isBooleanType: boolean
    displayState: string
    stats: any
    isCorrectOption: (idx: number) => boolean
    getStatPercentage: (idx: number | string) => number
    getProgressColor: (idx: number) => string
}>()
</script>

<style scoped>
.flex-col {
    display: flex;
    flex-direction: column;
}
.flex-align-center {
    display: flex;
    align-items: center;
}
.gap-4 {
    gap: 16px;
}
.mt-4 {
    margin-top: 24px;
}
.mt-5 {
    margin-top: 40px;
}
.mb-3 {
    margin-bottom: 12px;
}
.mr-2 {
    margin-right: 8px;
}
.mr-3 {
    margin-right: 12px;
}
.ml-3 {
    margin-left: 12px;
}
.text-center {
    text-align: center;
}
.py-5 {
    padding-top: 40px;
    padding-bottom: 40px;
}

.font-bold {
    font-weight: bold;
}
.font-black {
    font-weight: 900;
}
.text-lg {
    font-size: 1.25rem;
}
.text-xl {
    font-size: 1.5rem;
}
.text-main {
    color: var(--el-text-color-primary);
}
.text-muted {
    color: var(--el-text-color-secondary);
}
.text-success {
    color: var(--el-color-success) !important;
}

.progress-text {
    font-size: 1.1rem;
    font-weight: bold;
}

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
</style>
