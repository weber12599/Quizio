<template>
    <div class="grades-container">
        <el-card>
            <template #header>
                <div class="card-header">
                    <h2>{{ $t('grades.title') }}</h2>
                </div>
            </template>

            <el-form
                :inline="true"
                :model="filters"
                class="filter-bar filter-form"
            >
                <el-form-item :label="t('grades.filter.by_class')">
                    <el-select
                        v-model="filters.class_name"
                        :placeholder="t('grades.placeholder.select_class')"
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

                <el-form-item :label="t('grades.filter.by_student_id')">
                    <el-select
                        v-model="filters.student_id"
                        :placeholder="t('grades.placeholder.select_student')"
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

                <el-form-item :label="t('grades.filter.by_exams')">
                    <el-select
                        v-model="filters.exam_ids"
                        multiple
                        collapse-tags
                        :placeholder="t('grades.placeholder.select_exams')"
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

                <el-form-item :label="t('grades.filter.by_record_date')">
                    <el-date-picker
                        v-model="dateRange"
                        type="daterange"
                        :range-separator="t('grades.filter.date_range_separator')"
                        :start-placeholder="t('grades.filter.start_date')"
                        :end-placeholder="t('grades.filter.end_date')"
                        value-format="YYYY-MM-DD"
                    />
                </el-form-item>

                <el-form-item>
                    <el-button
                        type="primary"
                        @click="fetchReport"
                        :loading="loading"
                    >
                        <el-icon><Search /></el-icon> {{ t('common.search') }}
                    </el-button>
                    <el-button @click="resetFilters">{{ t('grades.filter.reset') }}</el-button>
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
                        :label="t('grades.columns.class')"
                        width="120"
                        fixed="left"
                    />
                    <el-table-column
                        prop="student_id"
                        :label="t('grades.columns.student_id')"
                        width="150"
                        fixed="left"
                    />
                    <el-table-column
                        prop="name"
                        :label="t('grades.columns.name')"
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
                                :content="`Target date: ${
                                    exam.target_date
                                        ? dayjs(
                                              new Date(exam.target_date)
                                          ).format('YYYY/MM/DD')
                                        : '-'
                                }`"
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
                                        :content="`Record: ${dayjs(
                                            new Date(sub.record_at)
                                        ).format('YYYY/MM/DD HH:mm:ss')}`"
                                        placement="top"
                                        effect="dark"
                                    >
                                        <span
                                            class="score-val"
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
                    :description="t('grades.empty.no_records')"
                />
                <el-empty
                    v-else-if="!hasSearched"
                    :description="t('grades.empty.no_search')"
                />
            </div>
        </el-card>

        <el-dialog
            v-model="gradingDialogVisible"
            :title="`${t('grades.dialog.grading')}: ${currentStudentName} - ${currentExamTitle}`"
            width="860px"
            destroy-on-close
        >
            <el-tabs v-model="activeTab" @tab-click="onTabClick">
                <el-tab-pane :label="t('grades.dialog.tab_answers')" name="grading">
                    <div
                        v-loading="submissionLoading"
                        class="grading-container"
                    >
                        <el-empty
                            v-if="!currentSubmission"
                            :description="t('grades.empty.no_submission')"
                        />

                        <div v-else>
                            <el-card
                                v-for="(
                                    ans, index
                                ) in currentSubmission.answers"
                                :key="ans.id"
                                class="grading-card"
                                shadow="hover"
                            >
                                <div class="q-header">
                                    <el-tag
                                        :type="getTagType(ans.question?.needs_manual_grading ? 'danger' : 'info')"
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
                                    v-html="
                                        renderMarkdown(ans.question?.content)
                                    "
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
                                            >{{
                                                String.fromCharCode(65 + oIdx)
                                            }}.</span
                                        >
                                        <span class="option-text">{{
                                            opt
                                        }}</span>
                                    </div>
                                </div>

                                <div class="ref-answer-box">
                                    <span class="label">{{ t('grades.dialog.reference_answer') }}:</span>
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
                                    <span class="label">{{ t('grades.dialog.student_answer') }}:</span>
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
                                    <span
                                        style="
                                            margin-right: 10px;
                                            font-weight: bold;
                                        "
                                        >{{ t('grades.dialog.score') }}:</span
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
                                        <el-icon><Check /></el-icon> {{ t('grades.dialog.save_score') }}
                                    </el-button>
                                </div>
                            </el-card>
                        </div>
                    </div>
                </el-tab-pane>

                <el-tab-pane :label="t('grades.dialog.tab_interactions')" name="interactions">
                    <div class="grading-container">
                        <!-- Discussion Score row -->
                        <div
                            class="discussion-score-bar"
                            v-if="currentSubmission"
                        >
                            <span class="discussion-score-label"
                                >{{ t('grades.interaction.title') }}：</span
                            >
                            <el-input-number
                                v-model="discussionScore"
                                :min="0"
                                :max="100"
                                size="small"
                                style="width: 130px; margin-right: 10px"
                                :placeholder="t('grades.interaction.ungraded')"
                            />
                            <el-button
                                type="primary"
                                plain
                                size="small"
                                @click="saveDiscussionScore"
                                :loading="savingDiscussionScore"
                            >
                                <el-icon><Check /></el-icon> {{ t('common.save') }}
                            </el-button>
                        </div>

                        <el-divider />

                        <div v-loading="interactionsLoading">
                            <el-empty
                                v-if="
                                    !interactionsLoading &&
                                    sessionInteractions.length === 0
                                "
                                :description="t('grades.empty.no_interactions')"
                            />

                            <div
                                v-for="qSection in sessionInteractions"
                                :key="qSection.question_id"
                                class="interaction-question-section"
                            >
                                <div
                                    class="interaction-q-title"
                                    v-html="
                                        renderMarkdown(qSection.question_title)
                                    "
                                ></div>

                                <!-- Closed-choice questions: discussion is per-OPTION -->
                                <template
                                    v-if="isChoiceType(qSection.question_type)"
                                >
                                    <div
                                        v-for="opt in qSection.options"
                                        :key="opt.option_index"
                                        class="interaction-answer-block"
                                    >
                                        <div class="ia-answer-header">
                                            <el-tag size="small" type="info">
                                                {{
                                                    optionLabel(
                                                        qSection,
                                                        opt.option_index
                                                    )
                                                }}
                                            </el-tag>
                                            <span class="ia-answer-content">{{
                                                opt.option_text
                                            }}</span>
                                            <span
                                                class="ia-likes-count"
                                                v-if="
                                                    opt.option_likes.length > 0
                                                "
                                            >
                                                ♥ {{ opt.option_likes.length }}
                                                <el-tooltip
                                                    :content="
                                                        opt.option_likes
                                                            .map(
                                                                (l) =>
                                                                    l.author
                                                                        .name
                                                            )
                                                            .join('、')
                                                    "
                                                    placement="top"
                                                >
                                                    <span
                                                        v-for="like in opt.option_likes"
                                                        :key="like.id"
                                                        class="ia-like-dot"
                                                        :class="{
                                                            'ia-like-dot-me':
                                                                isCurrentStudent(
                                                                    like.author
                                                                )
                                                        }"
                                                    ></span>
                                                </el-tooltip>
                                            </span>
                                        </div>

                                        <div
                                            v-for="comment in opt.comments"
                                            :key="comment.id"
                                            class="ia-comment"
                                            :class="{
                                                'ia-highlight-me':
                                                    isCurrentStudent(
                                                        comment.author
                                                    )
                                            }"
                                        >
                                            <el-tag
                                                size="small"
                                                :type="getTagType(getAuthorTagType(comment.author))"
                                            >
                                                {{ comment.author.name }}
                                            </el-tag>
                                            <span class="ia-comment-text">{{
                                                comment.content
                                            }}</span>
                                            <span
                                                class="ia-likes-count"
                                                v-if="
                                                    comment.comment_likes
                                                        .length > 0
                                                "
                                            >
                                                ♥
                                                {{
                                                    comment.comment_likes.length
                                                }}
                                                <span
                                                    v-for="cl in comment.comment_likes"
                                                    :key="cl.id"
                                                    class="ia-like-dot"
                                                    :class="{
                                                        'ia-like-dot-me':
                                                            isCurrentStudent(
                                                                cl.author
                                                            )
                                                    }"
                                                ></span>
                                            </span>
                                        </div>
                                    </div>
                                    <div
                                        v-if="qSection.options.length === 0"
                                        class="ia-empty-hint"
                                    >
                                        {{ t('grades.empty.no_option_interactions') }}
                                    </div>
                                </template>

                                <!-- Open-ended questions: discussion is per-ANSWER -->
                                <template v-else>
                                    <div
                                        v-for="ans in qSection.answers"
                                        :key="ans.answer_id"
                                        class="interaction-answer-block"
                                        :class="{
                                            'ia-highlight-owner':
                                                isCurrentStudent(ans.author)
                                        }"
                                    >
                                        <div class="ia-answer-header">
                                            <el-tag
                                                size="small"
                                                :type="getTagType(getAnswerTagType(ans.author))"
                                            >
                                                {{ ans.author.name }}
                                                <span
                                                    v-if="
                                                        isCurrentStudent(
                                                            ans.author
                                                        )
                                                    "
                                                >
                                                    (此學生)</span
                                                >
                                            </el-tag>
                                            <span class="ia-answer-content">{{
                                                ans.answer_content ||
                                                t('grades.interaction.no_answer')
                                            }}</span>
                                            <span
                                                class="ia-likes-count"
                                                v-if="
                                                    ans.answer_likes.length > 0
                                                "
                                            >
                                                ♥ {{ ans.answer_likes.length }}
                                                <el-tooltip
                                                    :content="
                                                        ans.answer_likes
                                                            .map(
                                                                (l) =>
                                                                    l.author
                                                                        .name
                                                            )
                                                            .join('、')
                                                    "
                                                    placement="top"
                                                >
                                                    <span
                                                        v-for="like in ans.answer_likes"
                                                        :key="like.id"
                                                        class="ia-like-dot"
                                                        :class="{
                                                            'ia-like-dot-me':
                                                                isCurrentStudent(
                                                                    like.author
                                                                )
                                                        }"
                                                    ></span>
                                                </el-tooltip>
                                            </span>
                                        </div>

                                        <div
                                            v-for="comment in ans.comments"
                                            :key="comment.id"
                                            class="ia-comment"
                                            :class="{
                                                'ia-highlight-me':
                                                    isCurrentStudent(
                                                        comment.author
                                                    )
                                            }"
                                        >
                                            <el-tag
                                                size="small"
                                                :type="getTagType(getAuthorTagType(comment.author))"
                                            >
                                                {{ comment.author.name }}
                                            </el-tag>
                                            <span class="ia-comment-text">{{
                                                comment.content
                                            }}</span>
                                            <span
                                                class="ia-likes-count"
                                                v-if="
                                                    comment.comment_likes
                                                        .length > 0
                                                "
                                            >
                                                ♥
                                                {{
                                                    comment.comment_likes.length
                                                }}
                                                <span
                                                    v-for="cl in comment.comment_likes"
                                                    :key="cl.id"
                                                    class="ia-like-dot"
                                                    :class="{
                                                        'ia-like-dot-me':
                                                            isCurrentStudent(
                                                                cl.author
                                                            )
                                                    }"
                                                ></span>
                                            </span>
                                        </div>
                                    </div>
                                </template>
                            </div>
                        </div>
                    </div>
                </el-tab-pane>
            </el-tabs>

            <template #footer>
                <el-button @click="closeGradingDialog">{{ t('common.close') }}</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, unref } from 'vue'
import { ElMessage, dayjs } from 'element-plus'
import { useI18n } from 'vue-i18n'

import dataAPI from '../api'
import type { StudentResponse } from '../api/types/students'
import type { ExamResponse } from '../api/types/exams'
import type {
    GradeReportResponse,
    StudentSubmissionResponse,
    StudentAnswerResponse,
    GetGradeReport,
    QuestionInteractionRead,
    InteractionAuthor
} from '../api/types/submissions'

import { renderMarkdown } from '../utils/markdown'

const { t } = useI18n()

// --- State: Filters ---
const filters = ref({
    class_name: '',
    student_id: '',
    exam_ids: [] as number[]
})
const dateRange = ref<[string, string] | null>(null)

// --- State: Dropdown Options ---
const classOptions = ref<string[]>([])
const allStudents = ref<StudentResponse[]>([])
const studentOptions = ref<StudentResponse[]>([])
const examOptions = ref<ExamResponse[]>([])

// --- State: Table Data ---
const loading = ref(false)
const hasSearched = ref(false)
const reportData = ref<GradeReportResponse | null>(null)

// --- State: Grading Dialog ---
const gradingDialogVisible = ref(false)
const submissionLoading = ref(false)
const currentSubmission = ref<StudentSubmissionResponse | null>(null)
const currentStudentName = ref('')
const currentExamTitle = ref('')
const savingAnswerId = ref<number | null>(null)
const activeTab = ref('grading')

// --- State: Interactions Tab ---
const interactionsLoading = ref(false)
const sessionInteractions = ref<QuestionInteractionRead[]>([])
const discussionScore = ref<number | null>(null)
const savingDiscussionScore = ref(false)

// --- Initialization ---
onMounted(async () => {
    try {
        const [classRes, studentRes, examRes] = await Promise.all([
            dataAPI.getTeacherClasses(),
            dataAPI.getStudents({}),
            dataAPI.getExams({})
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
        const params: GetGradeReport = {}
        if (filters.value.class_name)
            params.class_name = filters.value.class_name
        if (filters.value.student_id)
            params.student_id = filters.value.student_id

        if (dateRange.value && dateRange.value.length === 2) {
            params.date_start = dateRange.value[0]
            params.date_end = dateRange.value[1]
        }

        if (filters.value.exam_ids && filters.value.exam_ids.length > 0) {
            params.exam_ids = filters.value.exam_ids
        }

        const res = await dataAPI.getGradeReport(params)
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
const parseOptions = (
    optsRaw: string | string[] | null | undefined
): string[] => {
    if (Array.isArray(optsRaw)) {
        return optsRaw
    }
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

const formatDisplayAnswer = (
    type?: 'boolean' | 'single' | 'multiple' | 'short' | 'essay' | string,
    val?: boolean | number | string | number[] | null
): string => {
    if (val === undefined || val === null || val === '') {
        return '*(No Answer)*'
    }

    // true/false
    if (type === 'boolean') {
        const isTrue =
            val === 0 ||
            val === '0' ||
            val === true ||
            String(val).toLowerCase() === 'true'
        return isTrue ? 'True (O)' : 'False (X)'
    }

    // single
    if (type === 'single') {
        const idx = parseInt(String(val))
        return isNaN(idx) ? String(val) : String.fromCharCode(65 + idx)
    }

    // multiple
    if (type === 'multiple') {
        let arr: (string | number)[] = []
        if (Array.isArray(val)) {
            arr = val
        } else if (typeof val === 'string') {
            try {
                arr = JSON.parse(val)
                if (!Array.isArray(arr)) arr = [val]
            } catch {
                arr = val.split(',').map((s) => s.trim())
            }
        } else {
            arr = [val as number]
        }

        return arr
            .map((v) => {
                const idx = parseInt(String(v))
                return isNaN(idx) ? String(v) : String.fromCharCode(65 + idx)
            })
            .sort()
            .join(', ')
    }

    // short, essay
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
    currentExamTitle.value = `${examTitle} (Attempt ${attempt})`
    gradingDialogVisible.value = true
    submissionLoading.value = true
    currentSubmission.value = null
    activeTab.value = 'grading'
    sessionInteractions.value = []
    discussionScore.value = null

    try {
        const response = await dataAPI.getSubmissionDetails(submissionId)
        currentSubmission.value = response.data
        discussionScore.value = response.data.discussion_score ?? null
    } catch (error) {
        ElMessage.error('Failed to fetch submission details')
    } finally {
        submissionLoading.value = false
    }
}

const loadInteractions = async () => {
    if (!currentSubmission.value) return
    interactionsLoading.value = true
    try {
        const res = await dataAPI.getSessionInteractions(
            currentSubmission.value.id
        )
        sessionInteractions.value = res.data
    } catch (error) {
        ElMessage.error('Failed to fetch interaction records')
    } finally {
        interactionsLoading.value = false
    }
}

const onTabClick = (tab: { paneName: string }) => {
    if (
        tab.paneName === 'interactions' &&
        sessionInteractions.value.length === 0
    ) {
        loadInteractions()
    }
}

const saveDiscussionScore = async () => {
    if (!currentSubmission.value) return
    savingDiscussionScore.value = true
    try {
        await dataAPI.updateDiscussionScore(
            currentSubmission.value.id,
            discussionScore.value
        )
        ElMessage.success('討論互動分數已儲存')
    } catch (error) {
        ElMessage.error('儲存失敗')
    } finally {
        savingDiscussionScore.value = false
    }
}

const isCurrentStudent = (author: InteractionAuthor): boolean => {
    if (!currentSubmission.value) return false
    if (currentSubmission.value.student_id) {
        return (
            author.role === 'student' &&
            author.id === String(currentSubmission.value.student_id)
        )
    }
    if (currentSubmission.value.guest_name) {
        return (
            author.role === 'guest' &&
            author.name === currentSubmission.value.guest_name
        )
    }
    return false
}

const isChoiceType = (type: string): boolean => {
    return type === 'single' || type === 'multiple' || type === 'boolean'
}

const optionLabel = (
    qSection: QuestionInteractionRead,
    idx: number
): string => {
    if (qSection.question_type === 'boolean') {
        return idx === 0 ? 'O (True)' : 'X (False)'
    }
    return String.fromCharCode(65 + idx)
}

const getTagType = (value: any): string => {
    const unwrapped = unref(value)
    const result = String(unwrapped ?? 'info')
    return result === 'null' ? 'info' : result
}

const getAuthorTagType = (author: InteractionAuthor): string => {
    if (author.role === 'teacher') return 'warning'
    if (isCurrentStudent(author)) return 'success'
    return 'info'
}

const getAnswerTagType = (author: InteractionAuthor): string => {
    return isCurrentStudent(author) ? 'success' : 'info'
}

const submitGrade = async (answer: StudentAnswerResponse) => {
    if (answer.score === null || answer.score === undefined) {
        ElMessage.warning('Please enter a valid score')
        return
    }

    savingAnswerId.value = answer.id
    try {
        await dataAPI.gradeStudentAnswer(answer.id, answer.score)
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
    color: var(--el-text-color-primary);
}
.filter-bar {
    margin-bottom: 20px;
    background-color: var(--el-fill-color-light);
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
    background-color: var(--el-color-success-light-9);
    border-left: 3px solid var(--el-color-success-light-5);
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 10px;
}
.student-answer-box {
    background-color: var(--el-color-warning-light-9);
    border-left: 4px solid var(--el-color-warning-light-5);
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 15px;
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
    color: var(--el-text-color-secondary);
    font-size: 0.85rem;
    text-transform: uppercase;
}
.grading-controls {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    border-top: 1px dashed var(--el-border-color-lighter);
    padding-top: 15px;
}

/* --- Interactions Tab Styles --- */
.discussion-score-bar {
    display: flex;
    align-items: center;
    padding: 10px 0;
}
.discussion-score-label {
    font-weight: bold;
    margin-right: 10px;
    white-space: nowrap;
}

.interaction-question-section {
    margin-bottom: 24px;
}
.interaction-q-title {
    font-weight: bold;
    font-size: 0.95rem;
    background-color: var(--el-fill-color-light);
    padding: 8px 12px;
    border-radius: 6px;
    margin-bottom: 10px;
}
.interaction-q-title :deep(p) {
    margin: 0;
}
.interaction-q-title :deep(img),
.interaction-q-title :deep(video) {
    max-width: 100%;
    height: auto;
}

.interaction-answer-block {
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 10px;
    background: var(--el-fill-color-blank);
}
.ia-highlight-owner {
    border-color: var(--el-color-success-light-5);
    background-color: var(--el-color-success-light-9);
}

.ia-answer-header {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 6px;
}
.ia-answer-content {
    font-size: 0.9rem;
    color: var(--el-text-color-regular);
    flex: 1;
}
.ia-likes-count {
    display: flex;
    align-items: center;
    gap: 3px;
    font-size: 0.82rem;
    color: #e65a8a;
}
.ia-like-dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: #e65a8a;
    opacity: 0.5;
}
.ia-like-dot-me {
    opacity: 1;
    background-color: var(--el-color-success);
}

.ia-comment {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 5px 8px;
    border-radius: 6px;
    margin-top: 4px;
    background: var(--el-fill-color-blank);
    flex-wrap: wrap;
}
.ia-highlight-me {
    background-color: var(--el-color-success-light-9);
}
.ia-comment-text {
    font-size: 0.88rem;
    color: var(--el-text-color-primary);
    flex: 1;
}
.ia-empty-hint {
    color: var(--el-text-color-placeholder);
    font-size: 0.85rem;
    padding: 8px 4px;
}
</style>
