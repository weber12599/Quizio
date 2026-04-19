<template>
    <div class="questions-container">
        <el-card>
            <template #header>
                <div class="card-header">
                    <h2>Question Management</h2>
                    <el-button type="primary" @click="openAddDialog">
                        <el-icon><Plus /></el-icon> Add Question
                    </el-button>
                </div>
            </template>

            <el-form :inline="true" class="filter-bar">
                <el-form-item label="Type">
                    <el-select
                        v-model="filterType"
                        clearable
                        style="width: 150px"
                    >
                        <el-option label="Single Choice" value="single" />
                        <el-option label="True/False" value="boolean" />
                        <el-option label="Multiple Choice" value="multiple" />
                        <el-option label="Short Answer" value="short" />
                        <el-option label="Essay" value="essay" />
                    </el-select>
                </el-form-item>
                <el-form-item label="Difficulty">
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
                <el-form-item label="Lesson">
                    <el-input
                        v-model="filterLesson"
                        placeholder="e.g., Lesson 1"
                        clearable
                    />
                </el-form-item>
                <el-form-item label="Lock Status">
                    <el-select
                        v-model="filterLockStatus"
                        clearable
                        style="width: 150px"
                    >
                        <el-option label="Draft" :value="false" />
                        <el-option label="Locked" :value="true" />
                    </el-select>
                </el-form-item>
                <el-form-item label="Archive Status">
                    <el-select
                        v-model="filterArchiveStatus"
                        clearable
                        style="width: 150px"
                    >
                        <el-option label="Active" :value="false" />
                        <el-option label="Archived" :value="true" />
                    </el-select>
                </el-form-item>
                <el-form-item label="Delete Status">
                    <el-select
                        v-model="filterDeleteStatus"
                        clearable
                        style="width: 150px"
                    >
                        <el-option label="Not Deleted" :value="false" />
                        <el-option label="Deleted" :value="true" />
                    </el-select>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="handleSearch">
                        <el-icon><Search /></el-icon> Search
                    </el-button>
                    <el-button @click="resetFilters">Reset</el-button>
                </el-form-item>
            </el-form>

            <el-table
                :data="rows"
                v-loading="loading"
                border
                style="width: 100%"
            >
                <el-table-column prop="id" label="ID" width="60" />

                <el-table-column prop="status" label="Status" width="100">
                    <template #default="scope">
                        <el-tag
                            v-if="scope.row.is_locked"
                            size="small"
                            type="success"
                            >Locked</el-tag
                        >
                        <el-tag v-else size="small" type="info">Draft</el-tag>

                        <el-tag
                            v-if="scope.row.is_archived"
                            size="small"
                            type="warning"
                            >Archived</el-tag
                        >
                        <el-tag
                            v-if="
                                scope.row.deleted_at !== null &&
                                scope.row.deleted_at !== undefined
                            "
                            size="small"
                            type="danger"
                            >Deleted</el-tag
                        >
                    </template>
                </el-table-column>

                <el-table-column prop="type" label="Type" width="130">
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
                    label="Content"
                    show-overflow-tooltip
                    min-width="250"
                >
                    <template #default="scope">
                        {{ stripMarkdown(scope.row.content) }}
                    </template>
                </el-table-column>

                <el-table-column
                    prop="difficulty"
                    label="Difficulty"
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

                <el-table-column label="Tags" min-width="150">
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
                    label="Lesson"
                    width="150"
                    show-overflow-tooltip
                />

                <el-table-column label="Last Updated" width="180">
                    <template #default="scope">
                        {{
                            new Date(
                                scope.row.updated_at || scope.row.created_at
                            ).toLocaleString()
                        }}
                    </template>
                </el-table-column>

                <el-table-column
                    label="Actions"
                    width="120"
                    fixed="right"
                    align="center"
                >
                    <template #default="scope">
                        <el-tooltip placement="top">
                            <template #content>
                                <span>Edit</span>
                            </template>
                            <el-button
                                link
                                size="small"
                                @click="openEditDialog(scope.row)"
                                :disabled="!isEditable(scope.row)"
                            >
                                <el-icon>
                                    <Edit />
                                </el-icon>
                            </el-button>
                        </el-tooltip>

                        <el-tooltip placement="top">
                            <template #content>
                                <span>Adjust (Edit & Copy)</span>
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
                                <span>More</span>
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
                                            <el-icon><Lock /></el-icon> Lock
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
                                                    ? 'Unarchive'
                                                    : 'Archive'
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
                                                    ? 'Delete'
                                                    : 'Restore'
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
                            return 'Add Question'
                        case 'adjust':
                            return 'Adjust Question'
                        case 'edit':
                            return 'Edit Question'
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
                label-width="140px"
            >
                <el-form-item label="Type" prop="type" required>
                    <el-select
                        v-model="formData.type"
                        @change="handleTypeChange"
                        style="width: 100%"
                    >
                        <el-option
                            label="Single Choice (單選)"
                            value="single"
                        />
                        <el-option label="True/False (是非)" value="boolean" />
                        <el-option
                            label="Multiple Choice (多選)"
                            value="multiple"
                        />
                        <el-option label="Short Answer (簡答)" value="short" />
                        <el-option label="Essay (申論)" value="essay" />
                    </el-select>
                </el-form-item>

                <el-form-item label="Content" prop="content" required>
                    <TiptapEditor
                        v-model="formData.content"
                        placeholder="Please enter the question text; pasting or dragging and dropping images is supported."
                    />
                </el-form-item>

                <template
                    v-if="
                        ['single', 'multiple'].includes(formData.type) &&
                        formData.options
                    "
                >
                    <el-divider>Options</el-divider>

                    <el-form-item label="Options" prop="options" required>
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
                                        placeholder="Option text..."
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
                                <el-icon><Plus /></el-icon> Add Option
                            </el-button>
                        </div>
                    </el-form-item>
                </template>

                <el-divider>Reference Answer</el-divider>

                <el-form-item
                    label="Reference Answer"
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
                        placeholder="Enter reference answer or grading criteria..."
                    />
                </el-form-item>

                <el-divider>Metadata</el-divider>

                <el-form-item
                    label="Manual Grading"
                    prop="needs_manual_grading"
                >
                    <el-switch
                        v-model="formData.needs_manual_grading"
                        active-text="Yes (Teacher reviews)"
                        inactive-text="No (Auto-graded)"
                    />
                    <div
                        style="
                            font-size: 12px;
                            color: #909399;
                            line-height: 1.2;
                            margin-top: 4px;
                        "
                    >
                        * If enabled, the system will not auto-score this
                        question. You must grade it manually in the Grades
                        section.
                    </div>
                </el-form-item>

                <el-form-item label="Difficulty" prop="difficulty">
                    <el-rate
                        v-model="formData.difficulty"
                        :max="3"
                        clearable
                        style="margin-top: 6px"
                    />
                </el-form-item>

                <el-form-item label="Lesson" prop="lesson">
                    <el-input
                        v-model="formData.lesson"
                        placeholder="e.g., Lesson 1"
                    />
                </el-form-item>

                <el-form-item label="Tags" prop="literacy_tags">
                    <el-select
                        v-model="formData.literacy_tags"
                        multiple
                        filterable
                        allow-create
                        default-first-option
                        placeholder="Type and press Enter to create tags"
                        style="width: 100%"
                    >
                    </el-select>
                </el-form-item>

                <el-form-item label="Visibility" prop="is_public">
                    <el-switch
                        v-model="formData.is_public"
                        active-text="Public"
                        inactive-text="Private"
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
                        * Once set to public, it cannot be reverted to private
                        and will be available to all teachers.
                    </div>
                </el-form-item>
            </el-form>

            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="dialogVisible = false">Cancel</el-button>
                    <el-button
                        type="primary"
                        @click="handleSubmit"
                        :loading="submitLoading"
                        >Confirm</el-button
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
const dialogType = ref<'add' | 'edit' | 'adjust'>('add')
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
        'Locking this question means it is ready to be dispatched. It will become read-only and cannot be edited. Proceed?',
        'Warning',
        {
            confirmButtonText: 'Lock',
            cancelButtonText: 'Cancel',
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
        'Are you sure you want to archive this question?',
        'Warning',
        {
            confirmButtonText: 'Archive',
            cancelButtonText: 'Cancel',
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
        'Are you sure you want to unarchive this question?',
        'Warning',
        {
            confirmButtonText: 'Unarchive',
            cancelButtonText: 'Cancel',
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
        'Are you sure you want to delete this question?',
        'Warning',
        {
            confirmButtonText: 'Delete',
            cancelButtonText: 'Cancel',
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
        'Are you sure you want to restore this question?',
        'Warning',
        {
            confirmButtonText: 'Restore',
            cancelButtonText: 'Cancel',
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
    ElMessage.info(
        'You are copying a question. Saving will create a new copy in your bank.'
    )
    dialogType.value = 'adjust'
    resetForm()
    Object.assign(formData, copyRowToForm(row))
    dialogVisible.value = true
}

const openEditDialog = (row: QuestionRow) => {
    dialogType.value = 'edit'
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
    color: #303133;
}
.filter-bar {
    margin-bottom: 20px;
    background-color: #f8f9fa;
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
