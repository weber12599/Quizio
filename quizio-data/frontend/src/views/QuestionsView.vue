<template>
    <div class="questions-container">
        <el-card>
            <template #header>
                <div class="card-header">
                    <h2>{{ $t('questions.title') }}</h2>
                    <el-button type="primary" @click="openAddDialog">
                        <el-icon><Plus /></el-icon>
                        {{ $t('questions.add_question') }}
                    </el-button>
                </div>
            </template>

            <el-form :inline="true" class="filter-bar">
                <el-form-item :label="t('questions.filter.by_type')">
                    <el-select
                        v-model="filterType"
                        clearable
                        style="width: 150px"
                    >
                        <el-option
                            :label="t('question_type.single')"
                            value="single"
                        />
                        <el-option
                            :label="t('question_type.boolean')"
                            value="boolean"
                        />
                        <el-option
                            :label="t('question_type.multiple')"
                            value="multiple"
                        />
                        <el-option
                            :label="t('question_type.short')"
                            value="short"
                        />
                        <el-option
                            :label="t('question_type.essay')"
                            value="essay"
                        />
                    </el-select>
                </el-form-item>
                <el-form-item :label="t('questions.filter.by_difficulty')">
                    <el-select
                        v-model="filterDifficulty"
                        clearable
                        style="width: 120px"
                    >
                        <el-option label="★ 1" :value="1" />
                        <el-option label="★★ 2" :value="2" />
                        <el-option label="★★★ 3" :value="3" />
                    </el-select>
                </el-form-item>
                <el-form-item :label="t('questions.filter.by_lesson')">
                    <el-input
                        v-model="filterLesson"
                        :placeholder="t('questions.filter.lesson_placeholder')"
                        clearable
                    />
                </el-form-item>
                <el-form-item :label="t('questions.filter.by_lock_status')">
                    <el-select
                        v-model="filterLockStatus"
                        clearable
                        style="width: 150px"
                    >
                        <el-option
                            :label="t('questions.filter.draft')"
                            :value="false"
                        />
                        <el-option :label="t('common.lock')" :value="true" />
                    </el-select>
                </el-form-item>
                <el-form-item :label="t('questions.filter.by_archive_status')">
                    <el-select
                        v-model="filterArchiveStatus"
                        clearable
                        style="width: 150px"
                    >
                        <el-option
                            :label="t('questions.filter.active')"
                            :value="false"
                        />
                        <el-option :label="t('common.archive')" :value="true" />
                    </el-select>
                </el-form-item>
                <el-form-item :label="t('questions.filter.by_delete_status')">
                    <el-select
                        v-model="filterDeleteStatus"
                        clearable
                        style="width: 150px"
                    >
                        <el-option
                            :label="t('questions.filter.not_deleted')"
                            :value="false"
                        />
                        <el-option :label="t('common.delete')" :value="true" />
                    </el-select>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="handleSearch">
                        <el-icon><Search /></el-icon> {{ t('common.search') }}
                    </el-button>
                    <el-button @click="resetFilters">{{
                        t('questions.filter.reset')
                    }}</el-button>
                </el-form-item>
            </el-form>

            <el-table
                :data="rows"
                v-loading="loading"
                border
                style="width: 100%"
            >
                <el-table-column
                    prop="id"
                    :label="t('questions.columns.id')"
                    width="60"
                />

                <el-table-column
                    prop="status"
                    :label="t('questions.columns.status')"
                    width="100"
                >
                    <template #default="scope">
                        <el-tag
                            v-if="scope.row.is_locked"
                            size="small"
                            type="success"
                            >{{ t('common.lock') }}</el-tag
                        >
                        <el-tag v-else size="small" type="info">{{
                            t('questions.filter.draft')
                        }}</el-tag>

                        <el-tag
                            v-if="scope.row.is_archived"
                            size="small"
                            type="warning"
                            >{{ t('common.archive') }}</el-tag
                        >
                        <el-tag
                            v-if="
                                scope.row.deleted_at !== null &&
                                scope.row.deleted_at !== undefined
                            "
                            size="small"
                            type="danger"
                            >{{ t('common.delete') }}</el-tag
                        >
                    </template>
                </el-table-column>

                <el-table-column
                    prop="type"
                    :label="t('questions.columns.type')"
                    width="130"
                >
                    <template #default="scope">
                        <el-tag
                            size="small"
                            :type="getTypeConfig(scope.row.type).tagType"
                        >
                            {{ getTypeConfig(scope.row.type).label }}
                        </el-tag>
                    </template>
                </el-table-column>

                <el-table-column
                    prop="content"
                    :label="t('questions.columns.content')"
                    show-overflow-tooltip
                    min-width="250"
                >
                    <template #default="scope">
                        {{ stripMarkdown(scope.row.content) }}
                    </template>
                </el-table-column>

                <el-table-column
                    prop="difficulty"
                    :label="t('questions.columns.difficulty')"
                    width="120"
                    align="center"
                >
                    <template #default="scope">
                        <el-rate
                            :model-value="scope.row.difficulty"
                            :max="3"
                            disabled
                            text-color="#ff9900"
                        />
                    </template>
                </el-table-column>

                <el-table-column
                    :label="t('questions.columns.tags')"
                    min-width="150"
                >
                    <template #default="scope">
                        <el-tag
                            v-for="tag in scope.row.literacy_tags"
                            :key="tag"
                            size="small"
                            class="tag-item"
                        >
                            {{ tag }}
                        </el-tag>
                    </template>
                </el-table-column>

                <el-table-column
                    prop="lesson"
                    :label="t('questions.columns.lesson')"
                    width="150"
                    show-overflow-tooltip
                />

                <el-table-column
                    :label="t('questions.columns.last_updated')"
                    width="180"
                >
                    <template #default="scope">
                        {{
                            new Date(
                                scope.row.updated_at || scope.row.created_at
                            ).toLocaleString()
                        }}
                    </template>
                </el-table-column>

                <el-table-column
                    :label="t('questions.columns.actions')"
                    width="120"
                    fixed="right"
                    align="center"
                >
                    <template #default="scope">
                        <el-tooltip placement="top">
                            <template #content>
                                <span>{{
                                    isEditable(scope.row)
                                        ? t('common.edit')
                                        : t('questions.action.preview')
                                }}</span>
                            </template>
                            <el-button
                                link
                                size="small"
                                @click="openEditDialog(scope.row)"
                            >
                                <el-icon>
                                    <Edit v-if="isEditable(scope.row)" />
                                    <View v-else />
                                </el-icon>
                            </el-button>
                        </el-tooltip>

                        <el-tooltip placement="top">
                            <template #content>
                                <span>{{ t('questions.action.adjust') }}</span>
                            </template>

                            <el-button
                                link
                                size="small"
                                @click="openAdjustDialog(scope.row)"
                            >
                                <el-icon>
                                    <CopyDocument />
                                </el-icon>
                            </el-button>
                        </el-tooltip>

                        <el-tooltip placement="top">
                            <template #content>
                                <span>{{ t('questions.action.more') }}</span>
                            </template>
                            <el-dropdown
                                v-if="isStatusEditable(scope.row)"
                                trigger="click"
                                style="
                                    margin-left: 12px;
                                    vertical-align: middle;
                                "
                            >
                                <el-button link size="small">
                                    <el-icon><More /></el-icon>
                                </el-button>

                                <template #dropdown>
                                    <el-dropdown-menu>
                                        <el-dropdown-item
                                            v-if="!scope.row.is_locked"
                                            @click="handleLock(scope.row)"
                                        >
                                            <el-icon><Lock /></el-icon>
                                            {{ t('common.lock') }}
                                        </el-dropdown-item>

                                        <el-dropdown-item
                                            @click="
                                                scope.row.is_archived
                                                    ? handleUnarchive(scope.row)
                                                    : handleArchive(scope.row)
                                            "
                                        >
                                            <el-icon
                                                v-if="!scope.row.is_archived"
                                                ><Box
                                            /></el-icon>
                                            <el-icon v-else
                                                ><RefreshLeft
                                            /></el-icon>
                                            {{
                                                scope.row.is_archived
                                                    ? t('common.unarchive')
                                                    : t('common.archive')
                                            }}
                                        </el-dropdown-item>

                                        <el-dropdown-item
                                            @click="
                                                !scope.row.deleted_at
                                                    ? handleDelete(scope.row)
                                                    : handleRestore(scope.row)
                                            "
                                            :style="{
                                                color: !scope.row.deleted_at
                                                    ? 'var(--el-color-danger)'
                                                    : 'var(--el-color-warning)'
                                            }"
                                        >
                                            <el-icon
                                                v-if="!scope.row.deleted_at"
                                                ><Delete
                                            /></el-icon>
                                            <el-icon v-else
                                                ><RefreshLeft
                                            /></el-icon>
                                            {{
                                                !scope.row.deleted_at
                                                    ? t('common.delete')
                                                    : t('common.restore')
                                            }}
                                        </el-dropdown-item>
                                    </el-dropdown-menu>
                                </template>
                            </el-dropdown>
                        </el-tooltip>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>

        <el-dialog
            v-model="dialogVisible"
            :title="
                ((dialogType: string) => {
                    switch (dialogType) {
                        case 'add':
                            return t('questions.dialog.add_title')
                        case 'adjust':
                            return t('questions.dialog.adjust_title')
                        case 'edit':
                            return t('questions.dialog.edit_title')
                        case 'preview':
                            return t('questions.dialog.preview_title')
                        default:
                            break
                    }
                    return ''
                })(dialogType)
            "
            width="650px"
            destroy-on-close
        >
            <el-form
                ref="formRef"
                :model="formData"
                :rules="rules"
                :disabled="dialogType === 'preview'"
                label-width="140px"
            >
                <el-form-item
                    :label="t('questions.form.type')"
                    prop="type"
                    required
                >
                    <el-select
                        v-model="formData.type"
                        @change="handleTypeChange"
                        style="width: 100%"
                    >
                        <el-option
                            :label="t('question_type.single')"
                            value="single"
                        />
                        <el-option
                            :label="t('question_type.boolean')"
                            value="boolean"
                        />
                        <el-option
                            :label="t('question_type.multiple')"
                            value="multiple"
                        />
                        <el-option
                            :label="t('question_type.short')"
                            value="short"
                        />
                        <el-option
                            :label="t('question_type.essay')"
                            value="essay"
                        />
                    </el-select>
                </el-form-item>

                <el-form-item
                    :label="t('questions.form.content')"
                    prop="content"
                    required
                >
                    <TiptapEditor
                        v-model="formData.content"
                        :placeholder="t('questions.form.content_placeholder')"
                        :disabled="dialogType === 'preview'"
                    />
                </el-form-item>

                <template
                    v-if="
                        ['single', 'multiple'].includes(formData.type) &&
                        formData.options
                    "
                >
                    <el-divider>{{ t('questions.form.options') }}</el-divider>

                    <el-form-item
                        :label="t('questions.form.options')"
                        prop="options"
                        required
                    >
                        <div class="options-container">
                            <div
                                v-for="(_, index) in formData.options"
                                :key="index"
                                class="option-row"
                            >
                                <div class="option-prefix">
                                    {{ String.fromCharCode(65 + index) }}
                                </div>

                                <div class="option-editor-wrapper">
                                    <TiptapEditor
                                        v-model="formData.options[index]"
                                        minimal
                                        :placeholder="
                                            t(
                                                'questions.form.option_placeholder'
                                            )
                                        "
                                        :disabled="dialogType === 'preview'"
                                    />
                                </div>

                                <el-button
                                    type="danger"
                                    plain
                                    @click="removeOption(index)"
                                    :icon="Delete"
                                    :disabled="
                                        formData.options === null ||
                                        formData.options.length <= 2
                                    "
                                    class="option-delete-btn"
                                />
                            </div>

                            <el-button
                                @click="addOption"
                                plain
                                style="margin-top: 10px"
                            >
                                <el-icon><Plus /></el-icon>
                                {{ t('questions.action.add_option') }}
                            </el-button>
                        </div>
                    </el-form-item>
                </template>

                <el-divider>{{
                    t('questions.form.reference_answer')
                }}</el-divider>

                <el-form-item
                    :label="t('questions.form.reference_answer')"
                    prop="reference_answer"
                    required
                >
                    <el-radio-group
                        v-if="formData.type === 'single'"
                        v-model="formData.reference_answer"
                    >
                        <el-radio
                            v-for="(_, index) in formData.options"
                            :key="index"
                            :value="index"
                        >
                            Option {{ String.fromCharCode(65 + index) }}
                        </el-radio>
                    </el-radio-group>

                    <el-checkbox-group
                        v-if="formData.type === 'multiple'"
                        v-model="formData.reference_answer"
                    >
                        <el-checkbox
                            v-for="(_, index) in formData.options"
                            :key="index"
                            :value="index"
                        >
                            Option {{ String.fromCharCode(65 + index) }}
                        </el-checkbox>
                    </el-checkbox-group>

                    <el-radio-group
                        v-if="formData.type === 'boolean'"
                        v-model="formData.reference_answer"
                    >
                        <el-radio :value="true">True (O)</el-radio>
                        <el-radio :value="false">False (X)</el-radio>
                    </el-radio-group>

                    <el-input
                        v-if="['short', 'essay'].includes(formData.type)"
                        v-model="formData.reference_answer"
                        type="textarea"
                        :rows="3"
                        :placeholder="
                            t('questions.form.reference_answer_placeholder')
                        "
                    />
                </el-form-item>

                <el-divider>{{ t('questions.form.metadata') }}</el-divider>

                <el-form-item
                    :label="t('questions.form.manual_grading')"
                    prop="needs_manual_grading"
                >
                    <el-switch
                        v-model="formData.needs_manual_grading"
                        :active-text="t('questions.form.manual_grading_yes')"
                        :inactive-text="t('questions.form.manual_grading_no')"
                    />
                    <div
                        style="
                            font-size: 12px;
                            color: #909399;
                            line-height: 1.2;
                            margin-top: 4px;
                        "
                    >
                        {{ t('questions.form.manual_grading_help') }}
                    </div>
                </el-form-item>

                <el-form-item
                    :label="t('questions.form.difficulty')"
                    prop="difficulty"
                >
                    <el-rate
                        v-model="formData.difficulty"
                        :max="3"
                        clearable
                        style="margin-top: 6px"
                    />
                </el-form-item>

                <el-form-item :label="t('questions.form.lesson')" prop="lesson">
                    <el-input
                        v-model="formData.lesson"
                        :placeholder="t('questions.form.lesson_placeholder')"
                    />
                </el-form-item>

                <el-form-item
                    :label="t('questions.form.tags')"
                    prop="literacy_tags"
                >
                    <el-select
                        v-model="formData.literacy_tags"
                        multiple
                        filterable
                        allow-create
                        default-first-option
                        :placeholder="t('questions.form.tags_placeholder')"
                        style="width: 100%"
                    >
                    </el-select>
                </el-form-item>

                <el-form-item
                    :label="t('questions.form.visibility')"
                    prop="is_public"
                >
                    <el-switch
                        v-model="formData.is_public"
                        :active-text="t('questions.form.public')"
                        :inactive-text="t('questions.form.private')"
                        :disabled="
                            dialogType === 'edit' && formData.original_is_public
                        "
                    />
                    <div
                        style="
                            font-size: 12px;
                            color: #909399;
                            line-height: 1.2;
                            margin-top: 4px;
                        "
                    >
                        {{ t('questions.form.visibility_help') }}
                    </div>
                </el-form-item>
            </el-form>

            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="dialogVisible = false">{{
                        dialogType === 'preview'
                            ? t('common.close')
                            : t('common.cancel')
                    }}</el-button>
                    <el-button
                        v-if="dialogType !== 'preview'"
                        type="primary"
                        @click="handleSubmit"
                        :loading="submitLoading"
                        >{{ t('common.confirm') }}</el-button
                    >
                </span>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useI18n } from 'vue-i18n'

import { useAuthStore } from '../stores/auth'

import dataAPI, { type ApiError } from '../api'
import type {
    QuestionCreate,
    QuestionResponse,
    QuestionsGet,
    QuestionUpdate
} from '../api/types/questions'

import TiptapEditor from '../components/TiptapEditor.vue'
import { stripMarkdown } from '../utils/format'

const authStore = useAuthStore()
const { t } = useI18n()

type QuestionRow = QuestionResponse

interface QuestionFormData {
    id: number | null
    type: 'single' | 'boolean' | 'multiple' | 'short' | 'essay'
    content: string
    options: string[] | null
    reference_answer: boolean | number | string | number[]
    needs_manual_grading: boolean
    difficulty: number | null
    lesson: string | null
    literacy_tags: string[] | null
    is_public: boolean
    original_is_public: boolean
}

// State management
const rows = ref<QuestionRow[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit' | 'adjust' | 'preview'>('add')
const submitLoading = ref(false)
const formRef = ref<FormInstance>()
const filterType = ref<string>('')
const filterDifficulty = ref<number | null>(null)
const filterLesson = ref<string>('')
const filterLockStatus = ref<boolean | null>(null)
const filterArchiveStatus = ref<boolean | null>(false)
const filterDeleteStatus = ref<boolean | null>(false)

// Form Data
const formData = reactive<QuestionFormData>({
    id: null,
    type: 'single',
    content: '',
    options: ['', '', '', ''],
    reference_answer: 0,
    difficulty: 1,
    lesson: '',
    literacy_tags: [],
    needs_manual_grading: false,
    is_public: false,
    original_is_public: false
})

// Validation Rules
const rules = reactive<FormRules>({
    content: [
        {
            required: true,
            validator: (_, value, callback) => {
                const clean = value ? value.trim() : ''
                // Tiptap: <p></p>
                if (clean === '' || clean === '<p></p>') {
                    callback(new Error('Question content is required.'))
                } else {
                    callback()
                }
            },
            trigger: 'change'
        }
    ],
    options: [
        {
            validator: (_, value: string[], callback) => {
                if (!['single', 'multiple'].includes(formData.type)) {
                    return callback()
                }
                const hasEmptyOption = value.some((opt: string) => {
                    const cleanOpt = opt ? opt.trim() : ''
                    return cleanOpt === '' || cleanOpt === '<p></p>'
                })
                if (hasEmptyOption) {
                    return callback(new Error('All options must be filled.'))
                }
                callback()
            },
            trigger: 'change'
        }
    ],
    reference_answer: [
        {
            validator: (_, value, callback) => {
                if (formData.type === 'single') {
                    if (value === null || value === undefined || value === '') {
                        return callback(
                            new Error('Please select a correct answer.')
                        )
                    }
                } else if (formData.type === 'multiple') {
                    if (!Array.isArray(value) || value.length === 0) {
                        return callback(
                            new Error(
                                'Please select at least one correct answer.'
                            )
                        )
                    }
                }
                callback()
            },
            trigger: 'change'
        }
    ]
})

// Fetch all questions
const fetchQuestions = async () => {
    loading.value = true
    try {
        const params: QuestionsGet = {}
        if (filterType.value) {
            params.question_type = filterType.value
        }
        if (filterDifficulty.value) {
            params.difficulty = filterDifficulty.value
        }
        if (filterLesson.value) {
            params.lesson = filterLesson.value
        }
        if (
            filterLockStatus.value !== null &&
            filterLockStatus.value !== undefined
        ) {
            params.is_locked = filterLockStatus.value
        }
        if (
            filterDeleteStatus.value !== null &&
            filterDeleteStatus.value !== undefined
        ) {
            params.is_deleted = filterDeleteStatus.value
        }
        if (
            filterArchiveStatus.value !== null &&
            filterArchiveStatus.value !== undefined
        ) {
            params.is_archived = filterArchiveStatus.value
        }

        const response = await dataAPI.getQuestions(params)
        rows.value = response.data
    } catch (err: unknown) {
        const error = err as ApiError
        ElMessage.error(
            error.response?.data?.detail || 'Failed to fetch questions.'
        )
    } finally {
        loading.value = false
    }
}

const handleSearch = () => {
    fetchQuestions()
}

const resetFilters = () => {
    filterType.value = ''
    filterDifficulty.value = null
    filterLesson.value = ''
    filterLockStatus.value = null
    filterArchiveStatus.value = false
    filterDeleteStatus.value = false
    fetchQuestions()
}

// Helpers
const isEditable = (row: QuestionRow) => {
    if (
        row.is_archived ||
        (row.deleted_at !== null && row.deleted_at !== undefined)
    ) {
        return false
    }
    return !row.is_locked && authStore.user?.id === row.owner_id
}

const isStatusEditable = (row: QuestionRow) => {
    return authStore.user?.is_superuser || authStore.user?.id === row.owner_id
}

const getTypeConfig = (type: string) => {
    const configs: Record<string, { label: string; tagType: string }> = {
        single: { label: 'Single Choice', tagType: 'primary' },
        boolean: { label: 'True/False', tagType: 'success' },
        multiple: { label: 'Multiple Choice', tagType: 'warning' },
        short: { label: 'Short Answer', tagType: 'info' },
        essay: { label: 'Essay', tagType: 'danger' }
    }
    return configs[type] || { label: 'Unknown', tagType: '' }
}

const handleTypeChange = (newType: string) => {
    if (newType === 'single') {
        formData.options = ['', '', '', '']
        formData.reference_answer = 0
        formData.needs_manual_grading = false
    } else if (newType === 'multiple') {
        formData.options = ['', '', '', '', '']
        formData.reference_answer = []
        formData.needs_manual_grading = false
    } else if (newType === 'boolean') {
        formData.options = []
        formData.reference_answer = true
        formData.needs_manual_grading = false
    } else {
        formData.options = []
        formData.reference_answer = ''
        formData.needs_manual_grading = true
    }

    if (formRef.value) {
        formRef.value.clearValidate()
    }
}

const addOption = () => {
    if (!Array.isArray(formData.options)) {
        return
    }
    formData.options.push('')
}

const removeOption = (index: number) => {
    if (!Array.isArray(formData.options)) {
        return
    }
    formData.options.splice(index, 1)
    if (
        formData.type === 'single' &&
        (formData.reference_answer as number) >= formData.options.length
    ) {
        formData.reference_answer = ''
    } else if (formData.type === 'multiple') {
        formData.reference_answer = (formData.reference_answer as number[])
            .filter((ans: number) => ans !== index)
            .map((ans: number) => (ans > index ? ans - 1 : ans))
    }
}

// Submit Data
const handleSubmit = async () => {
    if (!formRef.value) {
        return
    }

    await formRef.value.validate(async (valid) => {
        if (!valid) {
            return
        }

        submitLoading.value = true
        try {
            const { id, original_is_public, ...payloadBase } = formData

            if (!['single', 'multiple'].includes(payloadBase.type)) {
                payloadBase.options = null
            }
            if (payloadBase.lesson === '') {
                payloadBase.lesson = null
            }
            if (
                payloadBase.literacy_tags &&
                payloadBase.literacy_tags.length === 0
            ) {
                payloadBase.literacy_tags = null
            }
            if (!payloadBase.difficulty) {
                payloadBase.difficulty = 1
            }

            if (dialogType.value === 'add' || dialogType.value === 'adjust') {
                const payload: QuestionCreate = payloadBase
                await dataAPI.createQuestion(payload)
                ElMessage.success('Question added successfully')
            } else if (formData.id !== null && formData.id !== undefined) {
                const payload: QuestionUpdate = payloadBase
                await dataAPI.updateQuestion(formData.id, payload)
                ElMessage.success('Question updated successfully')
            }
            dialogVisible.value = false
            fetchQuestions()
        } catch (err: unknown) {
            const error = err as ApiError
            ElMessage.error(error.response?.data?.detail || 'Operation failed')
        } finally {
            submitLoading.value = false
        }
    })
}

// Lock
const handleLock = (row: QuestionRow) => {
    ElMessageBox.confirm(
        t('questions.dialog.lock_message'),
        t('common.warning'),
        {
            confirmButtonText: t('common.lock'),
            cancelButtonText: t('common.cancel'),
            type: 'warning'
        }
    )
        .then(async () => {
            try {
                await dataAPI.lockQuestion(row.id)
                ElMessage.success('Question locked successfully')
                fetchQuestions()
            } catch (err: unknown) {
                const error = err as ApiError
                ElMessage.error(
                    error.response?.data?.detail || 'Failed to lock question'
                )
            }
        })
        .catch(() => {
            // Action cancelled by user
        })
}

// Archive
const handleArchive = (row: QuestionRow) => {
    ElMessageBox.confirm(
        t('questions.dialog.archive_message'),
        t('common.warning'),
        {
            confirmButtonText: t('common.archive'),
            cancelButtonText: t('common.cancel'),
            type: 'warning'
        }
    )
        .then(async () => {
            try {
                await dataAPI.archiveQuestion(row.id, true)
                ElMessage.success('Question archived successfully')
                fetchQuestions()
            } catch (err: unknown) {
                const error = err as ApiError
                ElMessage.error(
                    error.response?.data?.detail || 'Failed to archive question'
                )
            }
        })
        .catch(() => {
            // Action cancelled by user
        })
}

// Unarchive
const handleUnarchive = (row: QuestionRow) => {
    ElMessageBox.confirm(
        t('questions.dialog.unarchive_message'),
        t('common.warning'),
        {
            confirmButtonText: t('common.unarchive'),
            cancelButtonText: t('common.cancel'),
            type: 'warning'
        }
    )
        .then(async () => {
            try {
                await dataAPI.archiveQuestion(row.id, false)
                ElMessage.success('Question unarchived successfully')
                fetchQuestions()
            } catch (err: unknown) {
                const error = err as ApiError
                ElMessage.error(
                    error.response?.data?.detail ||
                        'Failed to unarchive question'
                )
            }
        })
        .catch(() => {
            // Action cancelled by user
        })
}

// Delete
const handleDelete = (row: QuestionRow) => {
    ElMessageBox.confirm(
        t('questions.dialog.delete_message'),
        t('common.warning'),
        {
            confirmButtonText: t('common.delete'),
            cancelButtonText: t('common.cancel'),
            type: 'warning'
        }
    )
        .then(async () => {
            try {
                await dataAPI.deleteQuestion(row.id)
                ElMessage.success('Question deleted successfully')
                fetchQuestions()
            } catch (err: unknown) {
                const error = err as ApiError
                ElMessage.error(
                    error.response?.data?.detail || 'Failed to delete question'
                )
            }
        })
        .catch(() => {
            // Action cancelled by user
        })
}

// Restore
const handleRestore = (row: QuestionRow) => {
    ElMessageBox.confirm(
        t('questions.dialog.restore_message'),
        t('common.warning'),
        {
            confirmButtonText: t('common.restore'),
            cancelButtonText: t('common.cancel'),
            type: 'warning'
        }
    )
        .then(async () => {
            try {
                await dataAPI.restoreQuestion(row.id)
                ElMessage.success('Question restored successfully')
                fetchQuestions()
            } catch (err: unknown) {
                const error = err as ApiError
                ElMessage.error(
                    error.response?.data?.detail || 'Failed to restore question'
                )
            }
        })
        .catch(() => {
            // Action cancelled by user
        })
}

// Dialog Handlers
const openAddDialog = () => {
    dialogType.value = 'add'
    resetForm()
    dialogVisible.value = true
}

const openAdjustDialog = (row: QuestionRow) => {
    ElMessage.info(t('questions.dialog.adjust_info'))
    dialogType.value = 'adjust'
    resetForm()
    Object.assign(formData, copyRowToForm(row))
    dialogVisible.value = true
}

const openEditDialog = (row: QuestionRow) => {
    dialogType.value = isEditable(row) ? 'edit' : 'preview'
    resetForm()
    Object.assign(formData, copyRowToForm(row))
    dialogVisible.value = true
}

const resetForm = () => {
    if (formRef.value) {
        formRef.value.clearValidate()
    }

    Object.assign(formData, {
        id: null,
        type: 'single',
        content: '',
        options: ['', '', '', ''],
        reference_answer: 0,
        difficulty: 1,
        lesson: '',
        literacy_tags: [],
        needs_manual_grading: false,
        is_public: false,
        original_is_public: false
    })
}

const copyRowToForm = (row: QuestionRow) => {
    return {
        id: row.id,
        type: row.type,
        content: row.content,
        options: row.options ? [...row.options] : [],
        reference_answer: Array.isArray(row.reference_answer)
            ? [...row.reference_answer]
            : row.reference_answer,
        difficulty: row.difficulty || 1,
        lesson: row.lesson || '',
        literacy_tags: row.literacy_tags ? [...row.literacy_tags] : [],
        needs_manual_grading: row.needs_manual_grading || false,
        is_public: row.is_public,
        original_is_public: row.is_public
    }
}

onMounted(() => {
    fetchQuestions()
})
</script>

<style scoped>
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.card-header h2 {
    margin: 0;
    font-size: 1.2rem;
    color: var(--el-text-color-primary);
}
.filter-bar {
    margin-bottom: 20px;
    background-color: var(--el-fill-color-light);
    padding: 15px;
    border-radius: 4px;
}
.tag-item {
    margin-right: 5px;
    margin-bottom: 5px;
}
.options-container {
    width: 100%;
}

.option-row {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 12px;
    width: 100%;
}

.option-prefix {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    background-color: var(--el-fill-color-light);
    border: 1px solid var(--el-border-color);
    border-radius: 4px;
    font-weight: bold;
    color: var(--el-text-color-regular);
    flex-shrink: 0;
    margin-top: 2px;
}

.option-editor-wrapper {
    flex-grow: 1;
    min-width: 0;
}

.option-delete-btn {
    flex-shrink: 0;
    height: 36px;
    margin-top: 2px;
}
</style>
