<template>
    <div class="exams-container">
        <el-card>
            <template #header>
                <div class="card-header">
                    <h2>Exam Management</h2>
                    <el-button type="primary" @click="openAddDialog">
                        <el-icon><Plus /></el-icon> Create Exam
                    </el-button>
                </div>
            </template>

            <el-table
                :data="exams"
                v-loading="loading"
                border
                style="width: 100%"
            >
                <el-table-column prop="id" label="ID" width="60" />
                <el-table-column
                    prop="title"
                    label="Title"
                    min-width="200"
                    show-overflow-tooltip
                />
                <el-table-column
                    prop="description"
                    label="Description"
                    min-width="250"
                    show-overflow-tooltip
                />
                <el-table-column label="Status" width="120" align="center">
                    <template #default="scope">
                        <el-tag
                            :type="scope.row.is_locked ? 'danger' : 'success'"
                        >
                            {{ scope.row.is_locked ? 'Locked' : 'Draft' }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column label="Target Date" width="130" align="center">
                    <template #default="scope">
                        {{ scope.row.target_date || '-' }}
                    </template>
                </el-table-column>
                <el-table-column label="Last Updated" width="180">
                    <template #default="scope">
                        {{
                            new Date(
                                scope.row.updated_at || scope.row.created_at
                            ).toLocaleString()
                        }}
                    </template>
                </el-table-column>
                <el-table-column label="Created At" width="180">
                    <template #default="scope">
                        {{ new Date(scope.row.created_at).toLocaleString() }}
                    </template>
                </el-table-column>
                <el-table-column label="Actions" width="280" fixed="right">
                    <template #default="scope">
                        <el-button
                            size="small"
                            @click="openEditDialog(scope.row)"
                            :type="scope.row.is_locked ? 'info' : 'default'"
                            :plain="scope.row.is_locked"
                        >
                            <el-icon>
                                <View v-if="scope.row.is_locked" />
                                <Edit v-else />
                            </el-icon>
                            {{ scope.row.is_locked ? 'Preview' : 'Edit' }}
                        </el-button>
                        <el-button
                            size="small"
                            type="warning"
                            @click="handleLock(scope.row)"
                            :disabled="scope.row.is_locked"
                        >
                            <el-icon><Lock /></el-icon> Lock
                        </el-button>
                        <el-button
                            size="small"
                            type="danger"
                            plain
                            @click="handleDelete(scope.row)"
                            :disabled="scope.row.is_locked"
                        >
                            <el-icon><Delete /></el-icon> Delete
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>

        <el-dialog
            v-model="dialogVisible"
            fullscreen
            destroy-on-close
            :show-close="false"
        >
            <template #header>
                <div
                    style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        width: 100%;
                    "
                >
                    <span class="el-dialog__title">
                        {{
                            dialogType === 'add'
                                ? 'Create New Exam'
                                : dialogType === 'preview'
                                  ? 'Preview Exam'
                                  : 'Edit Exam'
                        }}
                    </span>
                    <div>
                        <el-switch
                            v-if="dialogType !== 'preview'"
                            v-model="isPreviewing"
                            active-text="Preview Paper"
                            inactive-text="Edit Mode"
                            style="margin-right: 20px"
                        />
                        <el-button @click="dialogVisible = false" circle>
                            <el-icon><Close /></el-icon>
                        </el-button>
                    </div>
                </div>
            </template>

            <div class="editor-layout">
                <div
                    class="left-panel"
                    v-if="dialogType !== 'preview' && !isPreviewing"
                >
                    <h3>Question Bank</h3>
                    <el-input
                        v-model="searchKeyword"
                        placeholder="Search questions..."
                        :prefix-icon="Search"
                        clearable
                        style="margin-bottom: 15px"
                    />
                    <div class="question-list" v-loading="questionsLoading">
                        <el-card
                            v-for="q in filteredQuestions"
                            :key="q.id"
                            class="question-card"
                            shadow="hover"
                            :body-style="{ padding: '15px' }"
                        >
                            <div class="q-card-content">
                                <div
                                    style="
                                        display: flex;
                                        align-items: center;
                                        overflow: hidden;
                                        flex: 1;
                                    "
                                >
                                    <el-button
                                        link
                                        @click="toggleBankQ(q.id)"
                                        style="margin-right: 5px; padding: 0"
                                    >
                                        <el-icon>
                                            <ArrowDown
                                                v-if="
                                                    expandedBankQs.includes(
                                                        q.id
                                                    )
                                                "
                                            />
                                            <ArrowRight v-else />
                                        </el-icon>
                                    </el-button>
                                    <el-tag
                                        size="small"
                                        style="margin-right: 8px"
                                        >{{ q.type }}</el-tag
                                    >
                                    <span
                                        class="q-text"
                                        :title="stripMarkdown(q.content)"
                                        >{{ stripMarkdown(q.content) }}</span
                                    >
                                </div>
                                <el-button
                                    type="primary"
                                    size="small"
                                    circle
                                    @click="addQuestionToExam(q)"
                                >
                                    <el-icon><Plus /></el-icon>
                                </el-button>
                            </div>

                            <div
                                v-if="expandedBankQs.includes(q.id)"
                                class="q-expanded-view"
                            >
                                <div
                                    class="q-content"
                                    v-html="renderMarkdown(q.content)"
                                ></div>

                                <div
                                    v-if="
                                        ['single', 'multiple'].includes(
                                            q.type
                                        ) && q.options
                                    "
                                    class="q-options"
                                >
                                    <div
                                        v-for="(opt, optIndex) in q.options"
                                        :key="optIndex"
                                        class="q-option"
                                    >
                                        <span class="opt-label"
                                            >{{
                                                String.fromCharCode(
                                                    65 + optIndex
                                                )
                                            }}.</span
                                        >
                                        <div
                                            class="opt-content"
                                            v-html="renderMarkdown(opt)"
                                        ></div>
                                    </div>
                                </div>

                                <div class="q-answer-box">
                                    <span class="answer-label">【解答】</span>
                                    <template v-if="q.type === 'single'">
                                        {{
                                            String.fromCharCode(
                                                65 + q.reference_answer
                                            )
                                        }}
                                    </template>
                                    <template v-else-if="q.type === 'multiple'">
                                        {{
                                            Array.isArray(q.reference_answer)
                                                ? q.reference_answer
                                                      .map((ans: number) =>
                                                          String.fromCharCode(
                                                              65 + ans
                                                          )
                                                      )
                                                      .join(', ')
                                                : ''
                                        }}
                                    </template>
                                    <template v-else-if="q.type === 'boolean'">
                                        {{
                                            q.reference_answer
                                                ? 'O (True)'
                                                : 'X (False)'
                                        }}
                                    </template>
                                    <template v-else>
                                        <div
                                            v-html="
                                                renderMarkdown(
                                                    q.reference_answer
                                                )
                                            "
                                            class="answer-content"
                                        ></div>
                                    </template>
                                </div>
                            </div>
                        </el-card>
                        <el-empty
                            v-if="filteredQuestions.length === 0"
                            description="No questions found"
                        />
                    </div>
                </div>

                <div
                    class="right-panel"
                    :class="{
                        'is-preview-mode':
                            dialogType === 'preview' || isPreviewing
                    }"
                >
                    <div
                        v-if="dialogType === 'preview' || isPreviewing"
                        class="exam-preview-paper"
                        :class="`print-mode-${currentPrintMode}`"
                    >
                        <div class="paper-header">
                            <h1 class="paper-title">
                                {{ formData.title || 'Untitled Exam' }}
                            </h1>
                            <p v-if="formData.description" class="paper-desc">
                                {{ formData.description }}
                            </p>
                        </div>

                        <div class="paper-body">
                            <div
                                v-for="(q, index) in selectedQuestions"
                                :key="index"
                                class="paper-question"
                            >
                                <div class="q-title">
                                    <span class="q-number"
                                        >{{ index + 1 }}.</span
                                    >
                                    <span
                                        style="
                                            margin-right: 10px;
                                            color: #909399;
                                            font-size: 0.9em;
                                            white-space: nowrap;
                                        "
                                    >
                                        ({{ q.score }} pts)
                                    </span>
                                    <div
                                        class="q-content"
                                        v-html="renderMarkdown(q.content)"
                                    ></div>
                                </div>

                                <div
                                    v-if="
                                        ['single', 'multiple'].includes(
                                            q.type
                                        ) && q.options
                                    "
                                    class="q-options"
                                >
                                    <div
                                        v-for="(opt, optIndex) in q.options"
                                        :key="optIndex"
                                        class="q-option"
                                    >
                                        <span class="opt-label"
                                            >{{
                                                String.fromCharCode(
                                                    65 + optIndex
                                                )
                                            }}.</span
                                        >
                                        <div
                                            class="opt-content"
                                            v-html="renderMarkdown(opt)"
                                        ></div>
                                    </div>
                                </div>

                                <div class="q-answer-box">
                                    <span class="answer-label">【解答】</span>
                                    <template v-if="q.type === 'single'">
                                        {{
                                            String.fromCharCode(
                                                65 + q.reference_answer
                                            )
                                        }}
                                    </template>
                                    <template v-else-if="q.type === 'multiple'">
                                        {{
                                            Array.isArray(q.reference_answer)
                                                ? q.reference_answer
                                                      .map((ans: number) =>
                                                          String.fromCharCode(
                                                              65 + ans
                                                          )
                                                      )
                                                      .join(', ')
                                                : ''
                                        }}
                                    </template>
                                    <template v-else-if="q.type === 'boolean'">
                                        {{
                                            q.reference_answer
                                                ? 'O (True)'
                                                : 'X (False)'
                                        }}
                                    </template>
                                    <template v-else>
                                        <div
                                            v-html="
                                                renderMarkdown(
                                                    q.reference_answer
                                                )
                                            "
                                            class="answer-content"
                                        ></div>
                                    </template>
                                </div>
                            </div>
                            <el-empty
                                v-if="selectedQuestions.length === 0"
                                description="No questions selected yet"
                            />
                        </div>
                    </div>

                    <div v-else class="edit-mode-container">
                        <h3>Exam Details</h3>
                        <el-form :model="formData" label-position="top">
                            <el-form-item label="Exam Title" required>
                                <el-input
                                    v-model="formData.title"
                                    placeholder="Enter exam title..."
                                />
                            </el-form-item>
                            <el-form-item label="Target Date">
                                <el-date-picker
                                    v-model="formData.target_date"
                                    type="date"
                                    placeholder="Select scheduled date"
                                    format="YYYY-MM-DD"
                                    value-format="YYYY-MM-DD"
                                    style="width: 100%"
                                />
                            </el-form-item>
                            <el-form-item label="Description">
                                <el-input
                                    v-model="formData.description"
                                    type="textarea"
                                    :rows="2"
                                    placeholder="Optional description or instructions..."
                                />
                            </el-form-item>
                        </el-form>

                        <el-divider>
                            Selected Questions ({{ selectedQuestions.length }})
                            <span style="margin-left: 10px; color: #409eff"
                                >| Total Score: {{ totalScore }}</span
                            >
                        </el-divider>

                        <div class="selected-list">
                            <el-card
                                v-for="(q, index) in selectedQuestions"
                                :key="index"
                                class="selected-card"
                                shadow="never"
                            >
                                <div class="s-card-header">
                                    <div
                                        style="
                                            display: flex;
                                            align-items: center;
                                            gap: 15px;
                                        "
                                    >
                                        <strong>Q{{ index + 1 }}</strong>
                                        <div
                                            style="
                                                display: flex;
                                                align-items: center;
                                                gap: 5px;
                                                background-color: #f4f4f5;
                                                padding: 2px 8px;
                                                border-radius: 4px;
                                            "
                                        >
                                            <span
                                                style="
                                                    font-size: 12px;
                                                    color: #909399;
                                                "
                                                >Score:</span
                                            >
                                            <el-input-number
                                                v-model="q.score"
                                                :min="0"
                                                :max="100"
                                                size="small"
                                                style="width: 100px"
                                            />
                                        </div>
                                    </div>

                                    <div class="s-card-actions">
                                        <el-button
                                            size="small"
                                            @click="toggleSelectedQ(index)"
                                            circle
                                        >
                                            <el-icon>
                                                <ArrowDown
                                                    v-if="
                                                        expandedSelectedQs.includes(
                                                            index
                                                        )
                                                    "
                                                />
                                                <ArrowRight v-else />
                                            </el-icon>
                                        </el-button>
                                        <el-button
                                            size="small"
                                            @click="moveUp(index)"
                                            :disabled="index === 0"
                                            circle
                                        >
                                            <el-icon><Top /></el-icon>
                                        </el-button>
                                        <el-button
                                            size="small"
                                            @click="moveDown(index)"
                                            :disabled="
                                                index ===
                                                selectedQuestions.length - 1
                                            "
                                            circle
                                        >
                                            <el-icon><Bottom /></el-icon>
                                        </el-button>
                                        <el-button
                                            size="small"
                                            type="danger"
                                            @click="
                                                removeQuestionFromExam(index)
                                            "
                                            circle
                                        >
                                            <el-icon><Minus /></el-icon>
                                        </el-button>
                                    </div>
                                </div>
                                <div class="s-card-body">
                                    <div
                                        v-if="
                                            !expandedSelectedQs.includes(index)
                                        "
                                    >
                                        <el-tag
                                            size="small"
                                            type="info"
                                            style="margin-right: 8px"
                                            >{{ q.type }}</el-tag
                                        >
                                        {{ stripMarkdown(q.content) }}
                                    </div>

                                    <div
                                        v-else
                                        class="q-expanded-view"
                                        style="
                                            margin-top: 0;
                                            padding-top: 5px;
                                            border-top: none;
                                        "
                                    >
                                        <el-tag
                                            size="small"
                                            type="info"
                                            style="margin-bottom: 12px"
                                            >{{ q.type }}</el-tag
                                        >
                                        <div
                                            class="q-content"
                                            v-html="renderMarkdown(q.content)"
                                        ></div>

                                        <div
                                            v-if="
                                                ['single', 'multiple'].includes(
                                                    q.type
                                                ) && q.options
                                            "
                                            class="q-options"
                                        >
                                            <div
                                                v-for="(
                                                    opt, optIndex
                                                ) in q.options"
                                                :key="optIndex"
                                                class="q-option"
                                            >
                                                <span class="opt-label"
                                                    >{{
                                                        String.fromCharCode(
                                                            65 + optIndex
                                                        )
                                                    }}.</span
                                                >
                                                <div
                                                    class="opt-content"
                                                    v-html="renderMarkdown(opt)"
                                                ></div>
                                            </div>
                                        </div>

                                        <div class="q-answer-box">
                                            <span class="answer-label"
                                                >【解答】</span
                                            >
                                            <template
                                                v-if="q.type === 'single'"
                                            >
                                                {{
                                                    String.fromCharCode(
                                                        65 + q.reference_answer
                                                    )
                                                }}
                                            </template>
                                            <template
                                                v-else-if="
                                                    q.type === 'multiple'
                                                "
                                            >
                                                {{
                                                    Array.isArray(
                                                        q.reference_answer
                                                    )
                                                        ? q.reference_answer
                                                              .map(
                                                                  (
                                                                      ans: number
                                                                  ) =>
                                                                      String.fromCharCode(
                                                                          65 +
                                                                              ans
                                                                      )
                                                              )
                                                              .join(', ')
                                                        : ''
                                                }}
                                            </template>
                                            <template
                                                v-else-if="q.type === 'boolean'"
                                            >
                                                {{
                                                    q.reference_answer
                                                        ? 'O (True)'
                                                        : 'X (False)'
                                                }}
                                            </template>
                                            <template v-else>
                                                <div
                                                    v-html="
                                                        renderMarkdown(
                                                            q.reference_answer
                                                        )
                                                    "
                                                    class="answer-content"
                                                ></div>
                                            </template>
                                        </div>
                                    </div>
                                </div>
                            </el-card>
                            <el-empty
                                v-if="selectedQuestions.length === 0"
                                description="No questions selected"
                            />
                        </div>
                    </div>
                </div>
            </div>

            <template #footer>
                <span class="dialog-footer">
                    <template v-if="dialogType === 'preview'">
                        <el-button @click="handlePrint('questions')">
                            <el-icon><Printer /></el-icon> Print (Questions)
                        </el-button>
                        <el-button @click="handlePrint('answers')">
                            <el-icon><Printer /></el-icon> Print (With Answers)
                        </el-button>
                    </template>

                    <el-button @click="dialogVisible = false"
                        >{{ dialogType === 'preview' ? 'Close' : 'Cancel' }}
                    </el-button>
                    <el-button
                        v-if="dialogType !== 'preview'"
                        type="primary"
                        @click="submitForm"
                        :loading="submitLoading"
                        >Save Exam</el-button
                    >
                </span>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, nextTick, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
    Plus,
    Edit,
    Delete,
    Lock,
    Search,
    Top,
    Bottom,
    Minus,
    View,
    Printer,
    Close,
    ArrowDown,
    ArrowRight
} from '@element-plus/icons-vue'
import { renderMarkdown } from '../utils/markdown'
import { stripMarkdown } from '../utils/format'
import api from '../api'

// Interfaces
interface Question {
    id: number
    type: string
    content: string
    options: any
    reference_answer: any
    difficulty: number
    lesson: string | null
    literacy_tags: string[] | null
    is_public: boolean
    owner_id: number
}

interface SelectedQuestion extends Question {
    score: number
}

interface ExamQuestionResponse {
    exam_id: number
    question_id: number
    sort_order: number
    score: number
    question: Question
}

interface Exam {
    id: number
    title: string
    description: string | null
    is_locked: boolean
    target_date: string | null
    created_at: string
    updated_at: string | null
    owner_id: number
    exam_questions: ExamQuestionResponse[]
}

// State
const exams = ref<Exam[]>([])
const loading = ref(false)
const submitLoading = ref(false)
const isPreviewing = ref(false)
const currentPrintMode = ref<'questions' | 'answers'>('questions')

// Expand states
const expandedBankQs = ref<number[]>([])
const expandedSelectedQs = ref<number[]>([])

// Editor State
const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit' | 'preview'>('add')
const formData = ref({
    id: null as number | null,
    title: '',
    description: '',
    target_date: null as string | null
})

// Question Bank State
const bankQuestions = ref<Question[]>([])
const questionsLoading = ref(false)
const searchKeyword = ref('')
const selectedQuestions = ref<SelectedQuestion[]>([])

// Computed property for filtering question bank
const filteredQuestions = computed(() => {
    if (!searchKeyword.value) return bankQuestions.value
    const lowerKeyword = searchKeyword.value.toLowerCase()
    return bankQuestions.value.filter(
        (q) =>
            q.content.toLowerCase().includes(lowerKeyword) ||
            (q.lesson && q.lesson.toLowerCase().includes(lowerKeyword))
    )
})

const totalScore = computed(() => {
    return selectedQuestions.value.reduce((sum, q) => sum + (q.score || 0), 0)
})

// Expand Handlers
const toggleBankQ = (id: number) => {
    const index = expandedBankQs.value.indexOf(id)
    if (index > -1) expandedBankQs.value.splice(index, 1)
    else expandedBankQs.value.push(id)
}

const toggleSelectedQ = (index: number) => {
    const pos = expandedSelectedQs.value.indexOf(index)
    if (pos > -1) expandedSelectedQs.value.splice(pos, 1)
    else expandedSelectedQs.value.push(index)
}

// Helper to swap expand state when moving items
const swapExpandedState = (idx1: number, idx2: number) => {
    const has1 = expandedSelectedQs.value.includes(idx1)
    const has2 = expandedSelectedQs.value.includes(idx2)

    if (has1 !== has2) {
        if (has1) {
            expandedSelectedQs.value = expandedSelectedQs.value.filter(
                (i) => i !== idx1
            )
            expandedSelectedQs.value.push(idx2)
        } else {
            expandedSelectedQs.value = expandedSelectedQs.value.filter(
                (i) => i !== idx2
            )
            expandedSelectedQs.value.push(idx1)
        }
    }
}

// API Calls
const fetchExams = async () => {
    loading.value = true
    try {
        const response = await api.get('/exams/')
        exams.value = response.data
    } catch (error) {
        ElMessage.error('Failed to fetch exams')
    } finally {
        loading.value = false
    }
}

const fetchQuestions = async () => {
    questionsLoading.value = true
    try {
        const response = await api.get('/questions/')
        bankQuestions.value = response.data
    } catch (error) {
        ElMessage.error('Failed to fetch question bank')
    } finally {
        questionsLoading.value = false
    }
}

// Handlers
const handlePrint = async (mode: 'questions' | 'answers') => {
    currentPrintMode.value = mode
    await nextTick()
    window.print()
}

const openAddDialog = async () => {
    dialogType.value = 'add'
    isPreviewing.value = false
    expandedBankQs.value = []
    expandedSelectedQs.value = []

    formData.value = { id: null, title: '', description: '', target_date: null }
    selectedQuestions.value = []
    searchKeyword.value = ''
    dialogVisible.value = true
    await fetchQuestions()
}

const openEditDialog = async (row: Exam) => {
    dialogType.value = row.is_locked ? 'preview' : 'edit'
    isPreviewing.value = false
    expandedBankQs.value = []
    expandedSelectedQs.value = []

    formData.value = {
        id: row.id,
        title: row.title,
        description: row.description || '',
        target_date: row.target_date || null
    }

    const sortedExamQs = [...row.exam_questions].sort(
        (a, b) => a.sort_order - b.sort_order
    )
    selectedQuestions.value = sortedExamQs.map((eq) => ({
        ...eq.question,
        score: eq.score
    }))

    searchKeyword.value = ''
    dialogVisible.value = true

    if (dialogType.value !== 'preview') {
        await fetchQuestions()
    }
}

// Editor actions
const addQuestionToExam = (question: Question) => {
    selectedQuestions.value.push({ ...question, score: 10 })
}

const removeQuestionFromExam = (index: number) => {
    selectedQuestions.value.splice(index, 1)

    // Shift the expanded states down for items after the deleted one
    expandedSelectedQs.value = expandedSelectedQs.value
        .filter((i) => i !== index) // Remove the deleted one
        .map((i) => (i > index ? i - 1 : i)) // Shift others down
}

const moveUp = (index: number) => {
    if (index > 0) {
        const temp = selectedQuestions.value[index]
        selectedQuestions.value[index] = selectedQuestions.value[index - 1]
        selectedQuestions.value[index - 1] = temp
        swapExpandedState(index, index - 1)
    }
}

const moveDown = (index: number) => {
    if (index < selectedQuestions.value.length - 1) {
        const temp = selectedQuestions.value[index]
        selectedQuestions.value[index] = selectedQuestions.value[index + 1]
        selectedQuestions.value[index + 1] = temp
        swapExpandedState(index, index + 1)
    }
}

// Submit Form
const submitForm = async () => {
    if (!formData.value.title.trim()) {
        ElMessage.warning('Exam title is required')
        return
    }

    submitLoading.value = true
    try {
        const payload = {
            title: formData.value.title,
            description: formData.value.description || null,
            target_date: formData.value.target_date || null,
            questions: selectedQuestions.value.map((q) => ({
                question_id: q.id,
                score: q.score || 10
            }))
        }

        if (dialogType.value === 'add') {
            await api.post('/exams/', payload)
            ElMessage.success('Exam created successfully')
        } else {
            await api.put(`/exams/${formData.value.id}`, payload)
            ElMessage.success('Exam updated successfully')
        }

        dialogVisible.value = false
        fetchExams()
    } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || 'Operation failed')
    } finally {
        submitLoading.value = false
    }
}

// Delete Exam
const handleDelete = (row: Exam) => {
    ElMessageBox.confirm(
        'Are you sure you want to delete this exam?',
        'Warning',
        {
            type: 'warning'
        }
    )
        .then(async () => {
            try {
                await api.delete(`/exams/${row.id}`)
                ElMessage.success('Exam deleted')
                fetchExams()
            } catch (error) {
                ElMessage.error('Failed to delete exam')
            }
        })
        .catch(() => {})
}

// Lock Exam
const handleLock = (row: Exam) => {
    ElMessageBox.confirm(
        'Locking this exam means it is ready to be dispatched. It will become read-only and cannot be edited or deleted. Proceed?',
        'Lock Exam',
        { type: 'warning' }
    )
        .then(async () => {
            try {
                await api.put(`/exams/${row.id}`, { is_locked: true })
                ElMessage.success('Exam locked successfully')
                fetchExams()
            } catch (error) {
                ElMessage.error('Failed to lock exam')
            }
        })
        .catch(() => {})
}

onMounted(() => {
    fetchExams()
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
.editor-layout {
    display: flex;
    height: calc(100vh - 150px);
    gap: 20px;
}
.left-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    border-right: 1px solid #dcdfe6;
    padding-right: 20px;
}
.right-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding-left: 10px;
    overflow-y: auto;
}
.question-list {
    flex: 1;
    overflow-y: auto;
    padding-right: 10px;
}
.question-card {
    margin-bottom: 10px;
}
.q-card-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.q-text {
    font-size: 0.9rem;
    color: #606266;
    display: inline-block;
    max-width: 300px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    vertical-align: middle;
}
.selected-list {
    flex: 1;
    overflow-y: auto;
    padding-right: 10px;
    margin-top: 10px;
}
.selected-card {
    margin-bottom: 10px;
    border-left: 4px solid #409eff;
}
.s-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}
.s-card-actions {
    display: flex;
    gap: 5px;
}
.s-card-body {
    font-size: 0.95rem;
    color: #303133;
}

/* ==========================================
   展開視圖專用樣式 (Expanded View)
========================================== */
.q-expanded-view {
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px dashed #ebeef5;
    background-color: #fafafa;
    border-radius: 4px;
    padding: 15px;
}
</style>

<style scoped>
/* ==========================================
   試卷預覽模式 (Test Paper View)
========================================== */
.right-panel.is-preview-mode {
    background-color: #f0f2f5;
    padding: 20px;
    align-items: center;
}

.exam-preview-paper {
    background-color: white;
    width: 100%;
    max-width: 800px;
    padding: 40px;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    color: #303133;
}

.paper-title {
    text-align: center;
    font-size: 24px;
    margin-bottom: 10px;
}

.paper-desc {
    text-align: center;
    color: #606266;
    margin-bottom: 30px;
    white-space: pre-wrap;
}

.paper-question {
    margin-bottom: 30px;
    border-bottom: 1px dashed #ebeef5;
    padding-bottom: 20px;
}
.paper-question:last-child {
    border-bottom: none;
}

.q-title {
    display: flex;
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 15px;
}

.q-number {
    margin-right: 8px;
    white-space: nowrap;
}

.q-content :deep(p) {
    margin: 0 0 10px 0;
}
.q-content :deep(img),
.opt-content :deep(img) {
    max-width: 100%;
    height: auto;
    border-radius: 4px;
    margin-top: 10px;
}

.q-options {
    padding-left: 25px;
    margin-bottom: 15px;
}

.q-option {
    display: flex;
    margin-bottom: 8px;
}

.opt-label {
    margin-right: 8px;
    font-weight: bold;
}

.q-answer-box {
    background-color: #fdf6ec;
    color: #e6a23c;
    padding: 10px 15px;
    border-radius: 4px;
    font-size: 14px;
    display: flex;
    align-items: flex-start;
    margin-top: 15px;
}
.answer-label {
    font-weight: bold;
    margin-right: 8px;
    flex-shrink: 0;
}
.answer-content :deep(p) {
    margin: 0;
}

.edit-mode-container {
    width: 100%;
    display: flex;
    flex-direction: column;
}
</style>

<style>
/* ==========================================
   全域列印樣式 (Global Print CSS)
========================================== */
@media print {
    body * {
        visibility: hidden !important;
    }
    .exam-preview-paper,
    .exam-preview-paper * {
        visibility: visible !important;
    }
    .exam-preview-paper {
        position: absolute !important;
        left: 0 !important;
        top: 0 !important;
        width: 100% !important;
        max-width: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    .el-overlay {
        background-color: transparent !important;
    }
    .el-dialog__header,
    .el-dialog__footer {
        display: none !important;
    }

    .exam-preview-paper.print-mode-questions .q-answer-box {
        display: none !important;
    }
}
</style>
