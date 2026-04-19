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

            <el-form :inline="true" class="filter-bar">
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

                <el-table-column
                    prop="title"
                    label="Title"
                    width="200"
                    show-overflow-tooltip
                />

                <el-table-column
                    prop="description"
                    label="Description"
                    width="250"
                    show-overflow-tooltip
                />

                <el-table-column
                    prop="target_date"
                    label="Target Date"
                    width="130"
                    show-overflow-tooltip
                >
                    <template #default="scope">
                        {{
                            scope.row.target_date
                                ? dayjs(new Date(scope.row.target_date)).format(
                                      'YYYY/MM/DD'
                                  )
                                : null
                        }}
                    </template>
                </el-table-column>

                <el-table-column
                    prop="updated_at"
                    label="Last Updated"
                    width="180"
                >
                    <template #default="scope">
                        {{
                            dayjs(new Date(scope.row.updated_at)).format(
                                'YYYY/MM/DD HH:mm:ss'
                            )
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
                                <span>Preview</span>
                            </template>
                            <el-button
                                link
                                size="small"
                                @click="openEditDialog(scope.row)"
                                :disabled="isEditable(scope.row)"
                            >
                                <el-icon>
                                    <View />
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
                                        type="info"
                                        style="margin-right: 8px"
                                        >{{ `ID: ${q.id}` }}</el-tag
                                    >
                                    <el-tag
                                        size="small"
                                        type="primary"
                                        style="margin-right: 8px"
                                        >{{ q.type }}</el-tag
                                    >
                                    <el-tag
                                        v-if="q.is_archived"
                                        size="small"
                                        type="warning"
                                        style="margin-right: 8px"
                                        >Archived</el-tag
                                    >
                                    <el-tag
                                        v-if="q.deleted_at != null"
                                        size="small"
                                        type="danger"
                                        style="margin-right: 8px"
                                        >Deleted</el-tag
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
                                                65 +
                                                    (q.reference_answer as number)
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
                                                    q.reference_answer as string
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
                                                65 +
                                                    (q.reference_answer as number)
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
                                                    q.reference_answer as string
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
                        <el-form
                            ref="formRef"
                            :model="formData"
                            :rules="rules"
                            label-position="top"
                        >
                            <el-form-item
                                label="Exam Title"
                                prop="title"
                                required
                            >
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
                                                        65 +
                                                            (q.reference_answer as number)
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
                                                            q.reference_answer as string
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
                        @click="handleSubmit"
                        :loading="submitLoading"
                        >Save Exam</el-button
                    >
                </span>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, nextTick, computed, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox, dayjs } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'

import { useAuthStore } from '../stores/auth'

import dataAPI, { type ApiError } from '../api'
import type { QuestionResponse } from '../api/types/questions'
import type {
    ExamResponse,
    ExamCreate,
    ExamUpdate,
    ExamsGet
} from '../api/types/exams'

import { renderMarkdown } from '../utils/markdown'
import { stripMarkdown } from '../utils/format'

const authStore = useAuthStore()

type ExamRow = ExamResponse
type SelectedQuestion = QuestionResponse & { score: number }

interface ExamFormData {
    id: number | null
    title: string
    description: string | null
    target_date: string | null
}

// State management
const rows = ref<ExamRow[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit' | 'preview'>('add')
const submitLoading = ref(false)
const formRef = ref<FormInstance>()
const filterLockStatus = ref<boolean | null>(null)
const filterArchiveStatus = ref<boolean | null>(false)
const filterDeleteStatus = ref<boolean | null>(false)
const isPreviewing = ref(false)
const currentPrintMode = ref<'questions' | 'answers'>('questions')
const expandedBankQs = ref<number[]>([])
const expandedSelectedQs = ref<number[]>([])

// Form Data
const formData = reactive<ExamFormData>({
    id: null,
    title: '',
    description: '',
    target_date: null
})

// Validation Rules
const rules = reactive<FormRules>({
    title: [
        { required: true, message: 'Exam title is required', trigger: 'blur' }
    ]
})

// Question Bank State
const bankQuestions = ref<QuestionResponse[]>([])
const questionsLoading = ref(false)
const searchKeyword = ref('')
const selectedQuestions = ref<SelectedQuestion[]>([])

// Computed property for filtering question bank
const filteredQuestions = computed(() => {
    const selectedIds = new Set(selectedQuestions.value.map((q) => q.id))

    const activeQuestions = bankQuestions.value.filter(
        (q) => (!q.is_archived && q.deleted_at == null) || selectedIds.has(q.id)
    )

    if (!searchKeyword.value) {
        return activeQuestions
    }

    const lowerKeyword = searchKeyword.value.toLowerCase()
    return activeQuestions.filter(
        (q) =>
            q.content.toLowerCase().includes(lowerKeyword) ||
            (q.lesson && q.lesson.toLowerCase().includes(lowerKeyword))
    )
})

const totalScore = computed(() => {
    return selectedQuestions.value.reduce((sum, q) => sum + (q.score || 0), 0)
})

// Fetch all exams
const fetchExams = async () => {
    loading.value = true
    try {
        const params: ExamsGet = {}
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

        const response = await dataAPI.getExams(params)
        rows.value = response.data
    } catch (err: unknown) {
        const error = err as ApiError
        ElMessage.error(
            error.response?.data?.detail || 'Failed to fetch exams.'
        )
    } finally {
        loading.value = false
    }
}

const handleSearch = () => {
    fetchExams()
}

const resetFilters = () => {
    filterLockStatus.value = null
    filterArchiveStatus.value = false
    filterDeleteStatus.value = false
    fetchExams()
}

// Helpers
const isEditable = (row: ExamRow) => {
    if (
        row.is_archived ||
        (row.deleted_at !== null && row.deleted_at !== undefined)
    ) {
        return false
    }
    return !row.is_locked && authStore.user?.id === row.owner_id
}

const isStatusEditable = (row: ExamRow) => {
    return authStore.user?.is_superuser || authStore.user?.id === row.owner_id
}

const fetchQuestions = async () => {
    questionsLoading.value = true
    try {
        const response = await dataAPI.getQuestions({ is_locked: true })
        bankQuestions.value = response.data
    } catch (err: unknown) {
        const error = err as ApiError
        ElMessage.error(
            error.response?.data?.detail || 'Failed to fetch question bank.'
        )
    } finally {
        questionsLoading.value = false
    }
}

const toggleBankQ = (id: number) => {
    const index = expandedBankQs.value.indexOf(id)
    if (index > -1) {
        expandedBankQs.value.splice(index, 1)
    } else {
        expandedBankQs.value.push(id)
    }
}

const toggleSelectedQ = (index: number) => {
    const pos = expandedSelectedQs.value.indexOf(index)
    if (pos > -1) {
        expandedSelectedQs.value.splice(pos, 1)
    } else {
        expandedSelectedQs.value.push(index)
    }
}

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

const handlePrint = async (mode: 'questions' | 'answers') => {
    currentPrintMode.value = mode
    await nextTick()
    window.print()
}

const addQuestionToExam = (question: QuestionResponse) => {
    selectedQuestions.value.push({ ...question, score: 10 })
}

const removeQuestionFromExam = (index: number) => {
    selectedQuestions.value.splice(index, 1)
    expandedSelectedQs.value = expandedSelectedQs.value
        .filter((i) => i !== index)
        .map((i) => (i > index ? i - 1 : i))
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

// Submit Data
const handleSubmit = async () => {
    if (!formRef.value) {
        return
    }

    await formRef.value.validate(async (valid) => {
        if (!valid) {
            return
        }

        if (selectedQuestions.value.length === 0) {
            ElMessage.warning('Please select at least one question.')
            return
        }

        submitLoading.value = true
        try {
            const { id, ...payloadBase } = formData

            const payload: ExamCreate | ExamUpdate = {
                title: payloadBase.title,
                description: payloadBase.description || null,
                target_date: payloadBase.target_date || null,
                questions: selectedQuestions.value.map((q) => ({
                    question_id: q.id,
                    score: q.score || 10
                }))
            }

            if (dialogType.value === 'add') {
                await dataAPI.createExam(payload as ExamCreate)
                ElMessage.success('Exam created successfully')
            } else if (formData.id != null) {
                await dataAPI.updateExam(formData.id, payload as ExamUpdate)
                ElMessage.success('Exam updated successfully')
            }

            dialogVisible.value = false
            fetchExams()
        } catch (err: unknown) {
            const error = err as ApiError
            ElMessage.error(error.response?.data?.detail || 'Operation failed')
        } finally {
            submitLoading.value = false
        }
    })
}

// Lock
const handleLock = (row: ExamRow) => {
    ElMessageBox.confirm(
        'Locking this exam means it is ready to be dispatched. It will become read-only and cannot be edited. Proceed?',
        'Warning',
        {
            confirmButtonText: 'Lock',
            cancelButtonText: 'Cancel',
            type: 'warning'
        }
    )
        .then(async () => {
            try {
                await dataAPI.lockExam(row.id)
                ElMessage.success('Exam locked successfully')
                fetchExams()
            } catch (err: unknown) {
                const error = err as ApiError
                ElMessage.error(
                    error.response?.data?.detail || 'Failed to lock exam'
                )
            }
        })
        .catch(() => {
            // Action cancelled by user
        })
}

// Archive
const handleArchive = (row: ExamRow) => {
    ElMessageBox.confirm(
        'Are you sure you want to archive this exam?',
        'Warning',
        {
            confirmButtonText: 'Archive',
            cancelButtonText: 'Cancel',
            type: 'warning'
        }
    )
        .then(async () => {
            try {
                await dataAPI.archiveExam(row.id, true)
                ElMessage.success('Exam archived successfully')
                fetchExams()
            } catch (err: unknown) {
                const error = err as ApiError
                ElMessage.error(
                    error.response?.data?.detail || 'Failed to archive exam'
                )
            }
        })
        .catch(() => {
            // Action cancelled by user
        })
}

// Unarchive
const handleUnarchive = (row: ExamRow) => {
    ElMessageBox.confirm(
        'Are you sure you want to unarchive this exam?',
        'Warning',
        {
            confirmButtonText: 'Unarchive',
            cancelButtonText: 'Cancel',
            type: 'warning'
        }
    )
        .then(async () => {
            try {
                await dataAPI.archiveExam(row.id, false)
                ElMessage.success('Exam unarchived successfully')
                fetchExams()
            } catch (err: unknown) {
                const error = err as ApiError
                ElMessage.error(
                    error.response?.data?.detail || 'Failed to unarchive exam'
                )
            }
        })
        .catch(() => {
            // Action cancelled by user
        })
}

// Delete
const handleDelete = (row: ExamRow) => {
    ElMessageBox.confirm(
        'Are you sure you want to delete this exam?',
        'Warning',
        {
            confirmButtonText: 'Delete',
            cancelButtonText: 'Cancel',
            type: 'warning'
        }
    )
        .then(async () => {
            try {
                await dataAPI.deleteExam(row.id)
                ElMessage.success('Exam deleted successfully')
                fetchExams()
            } catch (err: unknown) {
                const error = err as ApiError
                ElMessage.error(
                    error.response?.data?.detail || 'Failed to delete exam'
                )
            }
        })
        .catch(() => {
            // Action cancelled by user
        })
}

// Restore
const handleRestore = (row: ExamRow) => {
    ElMessageBox.confirm(
        'Are you sure you want to restore this exam?',
        'Warning',
        {
            confirmButtonText: 'Restore',
            cancelButtonText: 'Cancel',
            type: 'warning'
        }
    )
        .then(async () => {
            try {
                await dataAPI.restoreExam(row.id)
                ElMessage.success('Exam restored successfully')
                fetchExams()
            } catch (err: unknown) {
                const error = err as ApiError
                ElMessage.error(
                    error.response?.data?.detail || 'Failed to restore exam'
                )
            }
        })
        .catch(() => {
            // Action cancelled by user
        })
}

// Dialog Handlers
const openAddDialog = async () => {
    dialogType.value = 'add'
    isPreviewing.value = false
    resetForm()
    dialogVisible.value = true
    await fetchQuestions()
}

const openEditDialog = async (row: ExamRow) => {
    dialogType.value =
        row.is_locked || row.deleted_at != null ? 'preview' : 'edit'
    isPreviewing.value = false
    resetForm()

    Object.assign(formData, {
        id: row.id,
        title: row.title,
        description: row.description || '',
        target_date: row.target_date || null
    })

    const sortedExamQs = [...row.exam_questions].sort(
        (a, b) => a.sort_order - b.sort_order
    )
    selectedQuestions.value = sortedExamQs.map((eq) => ({
        ...eq.question,
        score: eq.score
    }))

    dialogVisible.value = true

    if (dialogType.value !== 'preview') {
        await fetchQuestions()
    }
}

const resetForm = () => {
    if (formRef.value) formRef.value.clearValidate()
    Object.assign(formData, {
        id: null,
        title: '',
        description: '',
        target_date: null
    })
    selectedQuestions.value = []
    searchKeyword.value = ''
    expandedBankQs.value = []
    expandedSelectedQs.value = []
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
.filter-bar {
    margin-bottom: 20px;
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 4px;
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
   Expanded View
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
   Test Paper View
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
   Global Print CSS
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
