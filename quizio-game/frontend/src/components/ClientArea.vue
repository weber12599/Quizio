<template>
    <div class="client-area">
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
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { renderMarkdown } from '../utils/markdown'
import GameTiptapEditor from './GameTiptapEditor.vue'

const { t } = useI18n()

const props = defineProps<{
    modelValue: any
    question: any
    options: string[]
    submittedAnswer: any
    gradingResult: any
    isChoiceType: boolean
    isSingleChoice: boolean
    getGradingClass: (idx: number) => string
    getGradingIcon: (idx: number) => string
}>()

const emit = defineEmits(['update:modelValue'])

const localAnswer = computed({
    get: () => props.modelValue,
    set: (val) => emit('update:modelValue', val)
})
</script>

<style scoped>
.w-full {
    width: 100%;
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
.gap-4 {
    gap: 16px;
}
.mr-2 {
    margin-right: 8px;
}
.mr-3 {
    margin-right: 12px;
}

.option-interactive-item {
    margin-right: 0 !important;
    height: auto !important;
    padding: 10px 16px;
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

.option-graded-card {
    border-width: 2px;
    border-radius: 8px;
    transition: all 0.3s;
    background-color: var(--el-fill-color-blank);
}
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

/* Classes generated by getGradingClass */
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

/* Custom Textarea */
.custom-textarea :deep(.el-textarea__inner) {
    font-size: 1.05rem;
    padding: 12px 16px;
    line-height: 1.6;
    border-radius: 8px;
    background-color: var(--el-fill-color-blank);
}

/* Custom Result Box */
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
