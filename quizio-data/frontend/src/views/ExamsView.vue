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
                            :disabled="scope.row.is_locked"
                        >
                            <el-icon><Edit /></el-icon> Edit
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
            :title="dialogType === 'add' ? 'Create New Exam' : 'Edit Exam'"
            fullscreen
            destroy-on-close
        >
            <div class="editor-layout">
                <div class="left-panel">
                    <h3>Question Bank</h3>
                    <el-input
                        v-model="searchKeyword"
                        placeholder="Search questions..."
                        prefix-icon="Search"
                        clearable
                        style="margin-bottom: 15px"
                    />
                    <div class="question-list" v-loading="questionsLoading">
                        <el-card
                            v-for="q in filteredQuestions"
                            :key="q.id"
                            class="question-card"
                            shadow="hover"
                        >
                            <div class="q-card-content">
                                <div>
                                    <el-tag
                                        size="small"
                                        style="margin-right: 8px"
                                        >{{ q.type }}</el-tag
                                    >
                                    <span class="q-text">{{ q.content }}</span>
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
                        </el-card>
                        <el-empty
                            v-if="filteredQuestions.length === 0"
                            description="No questions found"
                        />
                    </div>
                </div>

                <div class="right-panel">
                    <h3>Exam Details</h3>
                    <el-form :model="formData" label-position="top">
                        <el-form-item label="Exam Title" required>
                            <el-input
                                v-model="formData.title"
                                placeholder="Enter exam title..."
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

                    <el-divider
                        >Selected Questions ({{
                            selectedQuestions.length
                        }})</el-divider
                    >

                    <div class="selected-list">
                        <el-card
                            v-for="(q, index) in selectedQuestions"
                            :key="index"
                            class="selected-card"
                            shadow="never"
                        >
                            <div class="s-card-header">
                                <strong>Q{{ index + 1 }}</strong>
                                <div class="s-card-actions">
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
                                        @click="removeQuestionFromExam(index)"
                                        circle
                                    >
                                        <el-icon><Minus /></el-icon>
                                    </el-button>
                                </div>
                            </div>
                            <div class="s-card-body">
                                <el-tag
                                    size="small"
                                    type="info"
                                    style="margin-right: 8px"
                                    >{{ q.type }}</el-tag
                                >
                                {{ q.content }}
                            </div>
                        </el-card>
                        <el-empty
                            v-if="selectedQuestions.length === 0"
                            description="No questions selected"
                        />
                    </div>
                </div>
            </div>

            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="dialogVisible = false">Cancel</el-button>
                    <el-button
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
    Plus,
    Edit,
    Delete,
    Lock,
    Search,
    Top,
    Bottom,
    Minus
} from '@element-plus/icons-vue'
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

interface ExamQuestionResponse {
    exam_id: number
    question_id: number
    sort_order: number
    question: Question
}

interface Exam {
    id: number
    title: string
    description: string | null
    is_locked: boolean
    created_at: string
    owner_id: number
    exam_questions: ExamQuestionResponse[]
}

// State
const exams = ref<Exam[]>([])
const loading = ref(false)
const submitLoading = ref(false)

// Editor State
const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const formData = ref({
    id: null as number | null,
    title: '',
    description: ''
})

// Question Bank State
const bankQuestions = ref<Question[]>([])
const questionsLoading = ref(false)
const searchKeyword = ref('')
const selectedQuestions = ref<Question[]>([])

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

// API Calls
const fetchExams = async () => {
    loading.value = true
    try {
        // MUST include trailing slash
        const response = await api.get('/api/exams/')
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
        // MUST include trailing slash
        const response = await api.get('/api/questions/')
        bankQuestions.value = response.data
    } catch (error) {
        ElMessage.error('Failed to fetch question bank')
    } finally {
        questionsLoading.value = false
    }
}

// Handlers
const openAddDialog = async () => {
    dialogType.value = 'add'
    formData.value = { id: null, title: '', description: '' }
    selectedQuestions.value = []
    searchKeyword.value = ''
    dialogVisible.value = true
    await fetchQuestions()
}

const openEditDialog = async (row: Exam) => {
    dialogType.value = 'edit'
    formData.value = {
        id: row.id,
        title: row.title,
        description: row.description || ''
    }

    // Map the nested questions to the flat selected array, ordered by sort_order
    const sortedExamQs = [...row.exam_questions].sort(
        (a, b) => a.sort_order - b.sort_order
    )
    selectedQuestions.value = sortedExamQs.map((eq) => eq.question)

    searchKeyword.value = ''
    dialogVisible.value = true
    await fetchQuestions()
}

// Editor actions
const addQuestionToExam = (question: Question) => {
    // Optional: Prevent duplicates if desired
    // if (selectedQuestions.value.some(q => q.id === question.id)) {
    //     ElMessage.warning('Question already added')
    //     return
    // }
    selectedQuestions.value.push(question)
}

const removeQuestionFromExam = (index: number) => {
    selectedQuestions.value.splice(index, 1)
}

const moveUp = (index: number) => {
    if (index > 0) {
        const temp = selectedQuestions.value[index]
        selectedQuestions.value[index] = selectedQuestions.value[index - 1]
        selectedQuestions.value[index - 1] = temp
    }
}

const moveDown = (index: number) => {
    if (index < selectedQuestions.value.length - 1) {
        const temp = selectedQuestions.value[index]
        selectedQuestions.value[index] = selectedQuestions.value[index + 1]
        selectedQuestions.value[index + 1] = temp
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
            // Extract IDs in the current sorted order
            question_ids: selectedQuestions.value.map((q) => q.id)
        }

        if (dialogType.value === 'add') {
            // MUST include trailing slash
            await api.post('/api/exams/', payload)
            ElMessage.success('Exam created successfully')
        } else {
            // MUST include trailing slash
            await api.put(`/api/exams/${formData.value.id}/`, payload)
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
                // MUST include trailing slash
                await api.delete(`/api/exams/${row.id}/`)
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
                // MUST include trailing slash
                await api.put(`/api/exams/${row.id}/`, { is_locked: true })
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
</style>
