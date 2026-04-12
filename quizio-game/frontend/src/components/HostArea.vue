<template>
    <div class="host-area mb-x">
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
                        {{
                            isBooleanType
                                ? idx === 0
                                    ? $t('common.true_option')
                                    : $t('common.false_option')
                                : String.fromCharCode(65 + idx)
                        }}
                    </el-tag>
                    <span
                        v-if="!isBooleanType"
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

        <div v-else-if="hasReferenceAnswer" class="mt-4">
            <div class="custom-result-box box-ref-ans">
                <div class="box-header">
                    <span class="mr-2">📝</span>
                    {{ $t('common.reference_answer') }}
                </div>
                <div
                    class="box-body markdown-body"
                    v-html="renderMarkdown(String(question.reference_answer))"
                ></div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { renderMarkdown } from '../utils/markdown'

const { t } = useI18n()

const props = defineProps<{
    question: any
    options: string[]
    isChoiceType: boolean
    isBooleanType: boolean
    isCorrectOption: (idx: number) => boolean
}>()

const hasReferenceAnswer = computed(() => {
    return (
        props.question?.reference_answer !== undefined &&
        props.question?.reference_answer !== null &&
        String(props.question?.reference_answer).trim() !== ''
    )
})
</script>

<style scoped>
.mb-x {
    margin-bottom: 24px;
}
.mt-4 {
    margin-top: 24px;
}

.flex-col {
    display: flex;
    flex-direction: column;
}
.flex-align-start {
    display: flex;
    align-items: flex-start;
}
.gap-2 {
    gap: 8px;
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

.option-letter-tag {
    font-size: 1rem;
    font-weight: bold;
    height: 30px;
    text-align: center;
    line-height: 28px;
    min-width: 30px;
}
.option-graded-card {
    border-width: 2px;
    border-radius: 8px;
    transition: all 0.3s;
    background-color: var(--el-fill-color-blank);
}
.option-text {
    font-size: 1.05rem;
    line-height: 1.5;
    color: var(--el-text-color-primary);
    word-break: break-word;
}

.border-success {
    border-color: var(--el-color-success) !important;
}
.bg-success-light {
    background-color: var(--el-color-success-light-9) !important;
}
.text-success {
    color: var(--el-color-success) !important;
}

/* Result Box */
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

<style scoped>
/* 補上 Markdown 渲染的必要樣式，以免在 HostArea 裡跑版 */
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
.markdown-body :deep(p) {
    margin-top: 0;
    margin-bottom: 1em;
    font-size: 1.15rem;
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
</style>
