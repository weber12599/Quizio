<template>
    <div class="grades-container">
        <el-card>
            <template #header>
                <div class="card-header">
                    <h2>Grades Management</h2>
                </div>
            </template>

            <el-form
                :inline="true"
                :model="filters"
                class="filter-bar filter-form"
            >
                <el-form-item label="Class">
                    <el-select
                        v-model="filters.class_name"
                        placeholder="Select Class"
                        clearable
                        @change="handleClassChange"
                    >
                        <el-option
                            v-for="className in classOptions"
                            :key="className"
                            :label="className"
                            :value="className"
                        />
                    </el-select>
                </el-form-item>

                <el-form-item label="Student ID">
                    <el-select
                        v-model="filters.student_id"
                        placeholder="Select Student"
                        clearable
                        filterable
                    >
                        <el-option
                            v-for="student in studentOptions"
                            :key="student.student_id"
                            :label="`${student.student_id} - ${student.name}`"
                            :value="student.student_id"
                        />
                    </el-select>
                </el-form-item>

                <el-form-item label="Exams">
                    <el-select
                        v-model="filters.exam_ids"
                        multiple
                        collapse-tags
                        placeholder="Select Exams"
                        clearable
                    >
                        <el-option
                            v-for="exam in examOptions"
                            :key="exam.id"
                            :label="exam.title"
                            :value="exam.id"
                        />
                    </el-select>
                </el-form-item>

                <el-form-item label="Record Date">
                    <el-date-picker
                        v-model="dateRange"
                        type="daterange"
                        range-separator="To"
                        start-placeholder="Start Date"
                        end-placeholder="End Date"
                        value-format="YYYY-MM-DD"
                    />
                </el-form-item>

                <el-form-item>
                    <el-button
                        type="primary"
                        @click="fetchReport"
                        :loading="loading"
                    >
                        <el-icon><Search /></el-icon> Search
                    </el-button>
                    <el-button @click="resetFilters">Reset</el-button>
                </el-form-item>
            </el-form>

            <div v-loading="loading" class="table-container">
                <el-table
                    v-if="reportData && reportData.students.length > 0"
                    :data="reportData.students"
                    border
                    style="width: 100%"
                >
                    <el-table-column
                        prop="class_name"
                        label="Class"
                        width="120"
                        fixed="left"
                    />
                    <el-table-column
                        prop="student_id"
                        label="Student ID"
                        width="150"
                        fixed="left"
                    />
                    <el-table-column
                        prop="name"
                        label="Name"
                        width="120"
                        fixed="left"
                    />

                    <el-table-column
                        v-for="exam in reportData.exams"
                        :key="exam.id"
                        :label="exam.title"
                        min-width="180"
                        align="center"
                    >
                        <template #header>
                            <el-tooltip
                                :content="`預定考試日期: ${exam.target_date || '未設定'}`"
                                placement="top"
                                effect="dark"
                            >
                                <span style="cursor: help">
                                    {{ exam.title }}
                                </span>
                            </el-tooltip>
                        </template>

                        <template #default="{ row }">
                            <div
                                v-if="row.exam_submissions[exam.id]"
                                class="score-container"
                            >
                                <template
                                    v-for="(sub, idx) in row.exam_submissions[
                                        exam.id
                                    ]"
                                    :key="sub.submission_id"
                                >
                                    <el-tooltip
                                        :content="`測驗時間: ${formatRecordAt(sub.record_at)}`"
                                        placement="top"
                                        effect="dark"
                                    >
                                        <span
                                            class="score-val"
                                            :class="{
                                                'no-score-val': sub.score === 0
                                            }"
                                            @click="
                                                openGradingDialog(
                                                    sub.submission_id,
                                                    row.name,
                                                    exam.title,
                                                    idx + 1
                                                )
                                            "
                                        >
                                            {{ sub.score }}
                                        </span>
                                    </el-tooltip>
                                    <span
                                        v-if="
                                            idx <
                                            row.exam_submissions[exam.id]
                                                .length -
                                                1
                                        "
                                        class="score-divider"
                                    >
                                        /
                                    </span>
                                </template>
                            </div>
                            <span v-else class="text-muted">-</span>
                        </template>
                    </el-table-column>
                </el-table>

                <el-empty
                    v-else-if="hasSearched && !loading"
                    description="No grade records found for the selected criteria."
                />
                <el-empty
                    v-else-if="!hasSearched"
                    description="Please select criteria and click Search to view grades."
                />
            </div>
        </el-card>

        <el-dialog
            v-model="gradingDialogVisible"
            :title="`Grading: ${currentStudentName} - ${currentExamTitle}`"
            width="800px"
            destroy-on-close
        >
            <div v-loading="submissionLoading" class="grading-container">
                <el-empty
                    v-if="!currentSubmission"
                    description="No submission found."
                />

                <div v-else>
                    <el-card
                        v-for="(ans, index) in currentSubmission.answers"
                        :key="ans.id"
                        class="grading-card"
                        shadow="hover"
                    >
                        <div class="q-header">
                            <el-tag
                                :type="
                                    ans.question?.needs_manual_grading
                                        ? 'danger'
                                        : 'info'
                                "
                                size="small"
                            >
                                Q{{ index + 1 }} -
                                {{ ans.question?.type }}
                                {{
                                    ans.question?.needs_manual_grading
                                        ? '(Needs Manual Grading)'
                                        : ''
                                }}
                            </el-tag>
                        </div>

                        <div
                            class="q-content"
                            v-html="renderMarkdown(ans.question?.content)"
                        ></div>

                        <div
                            v-if="
                                ans.question?.type === 'single' ||
                                ans.question?.type === 'multiple'
                            "
                            class="options-display"
                        >
                            <div
                                v-for="(opt, oIdx) in parseOptions(
                                    ans.question.options
                                )"
                                :key="oIdx"
                                class="option-item"
                            >
                                <span class="option-label"
                                    >{{ String.fromCharCode(65 + oIdx) }}.</span
                                >
                                <span class="option-text">{{ opt }}</span>
                            </div>
                        </div>

                        <div class="ref-answer-box">
                            <span class="label">Reference Answer:</span>
                            <div class="ans-text">
                                {{
                                    formatDisplayAnswer(
                                        ans.question?.type,
                                        ans.question?.reference_answer
                                    )
                                }}
                            </div>
                        </div>

                        <div class="student-answer-box">
                            <span class="label">Student's Answer:</span>
                            <div class="ans-text">
                                {{
                                    formatDisplayAnswer(
                                        ans.question?.type,
                                        ans.answer_content
                                    )
                                }}
                            </div>
                        </div>

                        <div class="grading-controls">
                            <span style="margin-right: 10px; font-weight: bold"
                                >Score:</span
                            >
                            <el-input-number
                                v-model="ans.score"
                                :min="0"
                                :max="100"
                                size="small"
                                style="width: 130px; margin-right: 10px"
                            />
                            <el-button
                                type="success"
                                plain
                                size="small"
                                @click="submitGrade(ans)"
                                :loading="savingAnswerId === ans.id"
                            >
                                <el-icon><Check /></el-icon> Save Score
                            </el-button>
                        </div>
                    </el-card>
                </div>
            </div>
            <template #footer>
                <el-button @click="closeGradingDialog">Close</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Check } from '@element-plus/icons-vue'
import { renderMarkdown } from '../utils/markdown'
import {
    getTeacherClasses,
    getGradeReport,
    getStudents,
    getExams,
    getSubmissionDetails,
    gradeStudentAnswer,
    type GradeReportResponse,
    type Student
} from '../api'

// --- State: Filters ---
const filters = ref({
    class_name: '',
    student_id: '',
    exam_ids: [] as number[]
})
const dateRange = ref<[string, string] | null>(null)

// --- State: Dropdown Options ---
const classOptions = ref<string[]>([])
const allStudents = ref<Student[]>([])
const studentOptions = ref<Student[]>([])
const examOptions = ref<any[]>([])

// --- State: Table Data ---
const loading = ref(false)
const hasSearched = ref(false)
const reportData = ref<GradeReportResponse | null>(null)

// --- State: Grading Dialog ---
const gradingDialogVisible = ref(false)
const submissionLoading = ref(false)
const currentSubmission = ref<any>(null)
const currentStudentName = ref('')
const currentExamTitle = ref('')
const savingAnswerId = ref<number | null>(null)

// --- Initialization ---
onMounted(async () => {
    try {
        const [classRes, studentRes, examRes] = await Promise.all([
            getTeacherClasses(),
            getStudents(),
            getExams()
        ])
        classOptions.value = classRes.data
        allStudents.value = studentRes.data
        studentOptions.value = studentRes.data
        examOptions.value = examRes.data
    } catch (error) {
        ElMessage.error('Failed to load initial data')
        console.error(error)
    }
})

// --- Handlers ---
const handleClassChange = (selectedClass: string) => {
    filters.value.student_id = ''
    if (selectedClass) {
        studentOptions.value = allStudents.value.filter(
            (s) => s.class_name === selectedClass
        )
    } else {
        studentOptions.value = allStudents.value
    }
}

const resetFilters = () => {
    filters.value.class_name = ''
    filters.value.student_id = ''
    filters.value.exam_ids = []
    dateRange.value = null
    hasSearched.value = false
    reportData.value = null
    studentOptions.value = allStudents.value
}

const fetchReport = async () => {
    loading.value = true
    hasSearched.value = true

    try {
        const params: any = {
            class_name: filters.value.class_name || undefined,
            student_id: filters.value.student_id || undefined
        }

        if (dateRange.value && dateRange.value.length === 2) {
            params.date_start = dateRange.value[0]
            params.date_end = dateRange.value[1]
        }

        if (filters.value.exam_ids && filters.value.exam_ids.length > 0) {
            params.exam_ids = filters.value.exam_ids
        }

        const res = await getGradeReport(params)
        reportData.value = res.data
    } catch (error) {
        ElMessage.error('Failed to fetch grade report')
        console.error(error)
        reportData.value = null
    } finally {
        loading.value = false
    }
}

// --- Utility ---
const formatRecordAt = (dateStr?: string | null) => {
    if (!dateStr) return '無紀錄'
    const date = new Date(dateStr)
    return date.toLocaleString('zh-TW', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    })
}

// 🚀 解析選項字串或陣列
const parseOptions = (optsRaw: any): string[] => {
    if (Array.isArray(optsRaw)) return optsRaw
    if (typeof optsRaw === 'string') {
        try {
            const parsed = JSON.parse(optsRaw)
            return Array.isArray(parsed) ? parsed : []
        } catch {
            return []
        }
    }
    return []
}

// 🚀 優化：格式化顯示答案邏輯
const formatDisplayAnswer = (type: string, val: any): string => {
    if (val === undefined || val === null || val === '') return '*(No Answer)*'

    // 是非題：0 -> True, 1 -> False 或布林值處理
    if (type === 'boolean') {
        const isTrue =
            val === 0 ||
            val === '0' ||
            val === true ||
            String(val).toLowerCase() === 'true'
        return isTrue ? 'True' : 'False'
    }

    // 單選題：數字轉字母 A, B, C
    if (type === 'single') {
        const idx = parseInt(val)
        return isNaN(idx) ? String(val) : String.fromCharCode(65 + idx)
    }

    // 多選題：處理陣列或 JSON 字串
    if (type === 'multiple') {
        let arr: any[] = []
        try {
            arr = Array.isArray(val) ? val : JSON.parse(val)
        } catch {
            arr = []
        }
        if (!Array.isArray(arr)) return String(val)
        return arr
            .map((v) => {
                const idx = parseInt(v)
                return isNaN(idx) ? String(v) : String.fromCharCode(65 + idx)
            })
            .sort()
            .join(', ')
    }

    return String(val)
}

// --- Manual Grading Handlers ---
const openGradingDialog = async (
    submissionId: number,
    studentName: string,
    examTitle: string,
    attempt: number
) => {
    currentStudentName.value = studentName
    currentExamTitle.value = `${examTitle} (第 ${attempt} 次測驗)`
    gradingDialogVisible.value = true
    submissionLoading.value = true
    currentSubmission.value = null

    try {
        const response = await getSubmissionDetails(submissionId)
        currentSubmission.value = response.data
    } catch (error) {
        ElMessage.error('Failed to fetch submission details')
    } finally {
        submissionLoading.value = false
    }
}

const submitGrade = async (answer: any) => {
    if (answer.score === null || answer.score === undefined) {
        ElMessage.warning('Please enter a valid score')
        return
    }

    savingAnswerId.value = answer.id
    try {
        await gradeStudentAnswer(answer.id, answer.score)
        ElMessage.success('Score updated successfully')
    } catch (error) {
        ElMessage.error('Failed to update score')
    } finally {
        savingAnswerId.value = null
    }
}

const closeGradingDialog = () => {
    gradingDialogVisible.value = false
    fetchReport()
}
</script>

<style scoped>
/* --- Card Header & Filter Bar Styles --- */
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

.table-container {
    min-height: 400px;
}

.no-score {
    color: #909399;
}
.filter-form .el-select {
    width: 200px;
}
.filter-form .el-date-editor {
    width: 260px;
}
.filter-form .el-form-item {
    margin-bottom: 15px;
}

.score-container {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
    font-size: 1.1em;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
}

.score-val {
    color: var(--el-color-primary);
    cursor: pointer;
    font-weight: bold;
    padding: 2px 6px;
    border-radius: 4px;
    transition: all 0.2s ease;
}

.score-val:hover {
    background-color: var(--el-color-primary-light-9);
    color: var(--el-color-primary-dark-2);
}

.no-score-val {
    color: #909399;
}

.no-score-val:hover {
    background-color: var(--el-fill-color-light);
    color: #606266;
}

.score-divider {
    color: var(--el-text-color-secondary);
    font-weight: normal;
}

.text-muted {
    color: var(--el-text-color-placeholder);
}

/* --- Grading Dialog Styles --- */
.grading-container {
    max-height: 60vh;
    overflow-y: auto;
    padding-right: 10px;
}
.grading-card {
    margin-bottom: 20px;
}
.q-header {
    margin-bottom: 10px;
}
.q-content :deep(p),
.q-content :deep(img) {
    margin: 0 0 10px 0;
    max-width: 100%;
}

/* 🚀 選項顯示樣式 */
.options-display {
    background-color: var(--el-fill-color-blank);
    border: 1px solid var(--el-border-color-lighter);
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 15px;
}
.option-item {
    margin-bottom: 6px;
    display: flex;
    align-items: flex-start;
}
.option-label {
    font-weight: bold;
    color: var(--el-color-primary);
    margin-right: 10px;
    min-width: 20px;
}
.option-text {
    color: var(--el-text-color-regular);
}

.ref-answer-box {
    background-color: #f0f9eb;
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 10px;
}
.student-answer-box {
    background-color: #fdf6ec;
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 15px;
    border-left: 4px solid #e6a23c;
}
.ans-text {
    font-size: 1.1rem;
    font-weight: bold;
    color: var(--el-text-color-primary);
    margin-top: 5px;
}
.label {
    font-weight: bold;
    display: block;
    margin-bottom: 5px;
    color: #606266;
    font-size: 0.85rem;
    text-transform: uppercase;
}
.grading-controls {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    border-top: 1px dashed #ebeef5;
    padding-top: 15px;
}
</style>
