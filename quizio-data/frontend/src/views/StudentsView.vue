<template>
    <div class="students-container">
        <el-card>
            <template #header>
                <div class="card-header">
                    <h2>{{ $t('students.title') }}</h2>
                    <div class="header-buttons">
                        <el-button
                            v-if="selectedRows.length > 0"
                            @click="batchEditVisible = true"
                        >
                            {{
                                $t('students.batch_edit', {
                                    count: selectedRows.length
                                })
                            }}
                        </el-button>
                        <el-button @click="importDialogVisible = true">
                            <el-icon><Upload /></el-icon>
                            {{ $t('students.import_students') }}
                        </el-button>
                        <el-button type="primary" @click="openAddDialog">
                            <el-icon><Plus /></el-icon>
                            {{ $t('students.add_student') }}
                        </el-button>
                    </div>
                </div>
            </template>

            <el-form class="filter-bar" inline>
                <el-form-item :label="$t('students.filter.by_year')">
                    <el-input-number
                        v-model="filterYear"
                        :placeholder="
                            $t('students.placeholder.admission_year', {
                                year: new Date().getFullYear() - 1911
                            })
                        "
                        align="left"
                        :controls="false"
                    />
                </el-form-item>
                <el-form-item :label="$t('students.filter.by_class')">
                    <el-input
                        v-model="filterClass"
                        :placeholder="$t('students.placeholder.class')"
                        clearable
                    />
                </el-form-item>
                <el-form-item :label="$t('students.filter.by_status')">
                    <el-select
                        v-model="filterStatus"
                        clearable
                        style="width: 150px"
                    >
                        <el-option
                            :label="$t('students.status_active')"
                            :value="true"
                        />
                        <el-option
                            :label="$t('students.status_deleted')"
                            :value="false"
                        />
                    </el-select>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="handleSearch">
                        <el-icon><Search /></el-icon> {{ $t('common.search') }}
                    </el-button>
                    <el-button @click="resetFilters">{{
                        $t('common.cancel')
                    }}</el-button>
                </el-form-item>
            </el-form>

            <el-table
                ref="tableRef"
                :data="rows"
                v-loading="loading"
                border
                style="width: 100%"
                @selection-change="(rows) => (selectedRows = rows)"
            >
                <el-table-column type="selection" width="40" />
                <el-table-column
                    prop="student_id"
                    :label="$t('students.columns.student_id')"
                    width="120"
                />
                <el-table-column
                    prop="name"
                    :label="$t('students.columns.full_name')"
                    width="120"
                />
                <el-table-column
                    prop="email"
                    :label="$t('students.columns.email')"
                    min-width="180"
                />
                <el-table-column
                    prop="admission_year"
                    :label="$t('students.columns.admission_year')"
                    width="150"
                />
                <el-table-column
                    prop="class_name"
                    :label="$t('students.columns.class')"
                    width="100"
                />
                <el-table-column
                    :label="$t('common.edit')"
                    min-width="180"
                    fixed="right"
                >
                    <template #default="scope">
                        <el-button
                            size="small"
                            @click="openEditDialog(scope.row)"
                        >
                            <el-icon><Edit /></el-icon> {{ $t('common.edit') }}
                        </el-button>
                        <el-button
                            v-if="!scope.row.deleted_at"
                            size="small"
                            type="danger"
                            @click="handleDelete(scope.row)"
                        >
                            <el-icon><Delete /></el-icon>
                            {{ $t('common.delete') }}
                        </el-button>
                        <el-button
                            v-if="scope.row.deleted_at"
                            size="small"
                            type="warning"
                            @click="handleRestore(scope.row)"
                        >
                            <el-icon><RefreshLeft /></el-icon>
                            {{ $t('common.restore') }}
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>

        <el-dialog
            v-model="dialogVisible"
            :title="
                dialogType === 'add'
                    ? $t('students.add_student')
                    : $t('students.edit_student')
            "
            width="500px"
        >
            <el-form
                ref="formRef"
                :model="formData"
                :rules="rules"
                label-width="120px"
            >
                <el-form-item
                    :label="$t('students.form.student_id')"
                    prop="student_id"
                    required
                >
                    <el-input
                        v-model="formData.student_id"
                        :disabled="dialogType === 'edit'"
                        :placeholder="$t('students.placeholder.student_id')"
                    />
                </el-form-item>

                <el-form-item :label="$t('students.form.full_name')" required>
                    <el-input
                        v-model="formData.name"
                        :placeholder="$t('students.placeholder.full_name')"
                    />
                </el-form-item>

                <el-form-item
                    :label="$t('students.form.password')"
                    prop="password"
                    :required="dialogType === 'add'"
                    :rules="
                        dialogType === 'edit'
                            ? []
                            : [
                                  {
                                      required: true,
                                      message: $t('common.error_required'),
                                      trigger: 'blur'
                                  }
                              ]
                    "
                >
                    <el-input
                        v-model="formData.password"
                        type="password"
                        show-password
                        :placeholder="
                            dialogType === 'edit'
                                ? $t('students.placeholder.student_id')
                                : $t('students.placeholder.student_id')
                        "
                    />
                </el-form-item>

                <el-form-item :label="$t('students.form.email')" prop="email">
                    <el-input
                        v-model="formData.email"
                        :placeholder="$t('students.placeholder.email')"
                    />
                </el-form-item>

                <el-form-item
                    :label="$t('students.form.admission_year')"
                    prop="admission_year"
                >
                    <el-input-number
                        v-model="formData.admission_year"
                        align="left"
                        :controls="false"
                        :style="{ width: '100%' }"
                    />
                </el-form-item>

                <el-form-item
                    :label="$t('students.form.class')"
                    prop="class_name"
                >
                    <el-input
                        v-model="formData.class_name"
                        :placeholder="$t('students.placeholder.class')"
                    />
                </el-form-item>
            </el-form>

            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="dialogVisible = false">{{
                        $t('common.cancel')
                    }}</el-button>
                    <el-button
                        type="primary"
                        @click="handleSubmit"
                        :loading="submitLoading"
                        >{{ $t('common.confirm') }}</el-button
                    >
                </span>
            </template>
        </el-dialog>

        <el-dialog
            v-model="batchEditVisible"
            :title="$t('students.batch_edit_title')"
            width="400px"
        >
            <el-form label-width="120px">
                <el-form-item :label="$t('students.batch_edit_year')">
                    <el-input-number
                        v-model="batchEditYear"
                        align="left"
                        :controls="false"
                        clearable
                        :placeholder="
                            $t('students.batch_edit_year_placeholder')
                        "
                        :style="{ width: '100%' }"
                    />
                </el-form-item>

                <el-form-item :label="$t('students.batch_edit_class')">
                    <el-input
                        v-model="batchEditClass"
                        clearable
                        :placeholder="
                            $t('students.batch_edit_class_placeholder')
                        "
                    />
                </el-form-item>
            </el-form>

            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="batchEditVisible = false">{{
                        $t('common.cancel')
                    }}</el-button>
                    <el-button
                        type="primary"
                        :loading="batchEditLoading"
                        @click="handleBatchEdit"
                    >
                        {{ $t('common.confirm') }}
                    </el-button>
                </span>
            </template>
        </el-dialog>

        <StudentImportDialog
            v-model="importDialogVisible"
            @imported="fetchStudents"
        />
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, ElTable } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Plus, Upload } from '@element-plus/icons-vue'

import dataAPI, { type ApiError } from '../api'
import type {
    StudentCreate,
    StudentResponse,
    StudentsGet,
    StudentUpdate
} from '../api/types/students'
import StudentImportDialog from '../components/StudentImportDialog.vue'

const { t } = useI18n()

type StudentRow = StudentResponse

interface StudentFormData {
    id: number | null
    student_id: string
    name: string
    password: string | null
    email: string | null
    admission_year: number | null
    class_name: string | null
}

// State management
const rows = ref<StudentRow[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const submitLoading = ref(false)
const formRef = ref<FormInstance>()
const tableRef = ref<InstanceType<typeof ElTable>>()
const filterYear = ref<number | null>(null)
const filterClass = ref<string | null>(null)
const filterStatus = ref<boolean | null>(true)
const importDialogVisible = ref(false)
const selectedRows = ref<StudentRow[]>([])
const batchEditVisible = ref(false)
const batchEditYear = ref<number | null>(null)
const batchEditClass = ref<string | null>(null)
const batchEditLoading = ref(false)

// Form Data
const formData = reactive<StudentFormData>({
    id: null as number | null,
    student_id: '',
    name: '',
    password: null as string | null,
    email: '',
    admission_year: null as number | null,
    class_name: null as string | null
})

// Validation Rules
const rules = reactive<FormRules>({
    student_id: [
        { required: true, message: t('common.error_required'), trigger: 'blur' }
    ],
    name: [
        { required: true, message: t('common.error_required'), trigger: 'blur' }
    ],
    email: [
        {
            type: 'email',
            message: t('common.error_required'),
            trigger: 'blur'
        }
    ]
})

// Fetch all students
const fetchStudents = async () => {
    loading.value = true
    try {
        const params: StudentsGet = {}
        if (filterYear.value) {
            params.admission_year = filterYear.value
        }
        if (filterClass.value) {
            params.class_name = filterClass.value
        }
        if (filterStatus.value !== null && filterStatus.value !== undefined) {
            params.is_deleted = !filterStatus.value
        }

        const response = await dataAPI.getStudents(params)
        rows.value = response.data
    } catch (err: unknown) {
        const error = err as ApiError
        if (error.response?.status === 401) {
            ElMessage.error(t('common.error'))
            // Optional: Handle redirect to login here via router
        } else {
            ElMessage.error(t('common.error'))
        }
    } finally {
        loading.value = false
    }
}

const handleSearch = () => {
    fetchStudents()
}

const resetFilters = () => {
    filterYear.value = null
    filterClass.value = null
    filterStatus.value = true
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
            if (dialogType.value === 'add') {
                const payload: StudentCreate = {
                    student_id: formData.student_id,
                    name: formData.name,
                    password: formData.password as string,
                    email: formData.email || null,
                    admission_year: formData.admission_year || null,
                    class_name: formData.class_name || null
                }
                await dataAPI.createStudent(payload)
                ElMessage.success(t('common.success'))
            } else if (formData.id !== null && formData.id !== undefined) {
                const payload: StudentUpdate = {
                    name: formData.name,
                    email: formData.email || null,
                    admission_year: formData.admission_year || null,
                    class_name: formData.class_name || null
                }
                if (formData.password) {
                    payload.password = formData.password
                }

                await dataAPI.updateStudent(formData.id, payload)
                ElMessage.success(t('common.success'))
            }
            dialogVisible.value = false
            fetchStudents()
        } catch (err: unknown) {
            const error = err as ApiError
            if (
                error.response?.status === 409 ||
                error.response?.data?.detail === 'STUDENT_ID_EXISTS'
            ) {
                ElMessage.warning('Student ID already exists!')
            } else {
                ElMessage.error(
                    error.response?.data?.detail || 'Operation failed'
                )
            }
        } finally {
            submitLoading.value = false
        }
    })
}

// Delete
const handleDelete = (row: StudentRow) => {
    ElMessageBox.confirm(`${t('common.delete_confirm')}`, t('common.warning'), {
        confirmButtonText: t('common.delete'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
    })
        .then(async () => {
            try {
                await dataAPI.deleteStudent(row.id)
                ElMessage.success(t('common.success'))
                fetchStudents()
            } catch (err: unknown) {
                const error = err as ApiError
                ElMessage.error(
                    error.response?.data?.detail || t('common.error')
                )
            }
        })
        .catch(() => {
            // Action cancelled by user
        })
}

// Restore
const handleRestore = (row: StudentRow) => {
    ElMessageBox.confirm(t('common.restore_confirm'), t('common.warning'), {
        confirmButtonText: t('common.restore'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
    })
        .then(async () => {
            try {
                await dataAPI.restoreStudent(row.id)
                ElMessage.success(t('common.success'))
                fetchStudents()
            } catch (err: unknown) {
                const error = err as ApiError
                ElMessage.error(
                    error.response?.data?.detail || t('common.error')
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

const openEditDialog = (row: StudentRow) => {
    dialogType.value = 'edit'
    resetForm()
    Object.assign(formData, {
        id: row.id,
        student_id: row.student_id,
        name: row.name,
        password: row.password,
        email: row.email || '',
        admission_year: row.admission_year || null,
        class_name: row.class_name || ''
    })
    dialogVisible.value = true
}

const resetForm = () => {
    if (formRef.value) {
        formRef.value.clearValidate()
    }

    Object.assign(formData, {
        id: null,
        student_id: '',
        name: '',
        password: '',
        email: '',
        admission_year: null,
        class_name: ''
    })
}

// Batch Edit
const handleBatchEdit = async () => {
    if (batchEditYear.value === null && !batchEditClass.value) {
        ElMessage.warning(t('students.batch_edit_no_fields'))
        return
    }

    batchEditLoading.value = true
    try {
        const payload = selectedRows.value.map((row) => ({
            id: row.id,
            ...(batchEditYear.value !== null
                ? { admission_year: batchEditYear.value }
                : {}),
            ...(batchEditClass.value
                ? { class_name: batchEditClass.value }
                : {})
        }))

        await dataAPI.batchUpdateStudents(payload)
        ElMessage.success(t('common.success'))
        batchEditVisible.value = false
        tableRef.value?.clearSelection()
        selectedRows.value = []
        batchEditYear.value = null
        batchEditClass.value = null
        fetchStudents()
    } catch (err: unknown) {
        const error = err as ApiError
        ElMessage.error(error.response?.data?.detail || t('common.error'))
    } finally {
        batchEditLoading.value = false
    }
}

onMounted(() => {
    fetchStudents()
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
.header-buttons {
    display: flex;
    gap: 8px;
}
.filter-bar {
    margin-bottom: 20px;
    background-color: var(--el-fill-color-light);
    padding: 15px;
    border-radius: 4px;
}
</style>
