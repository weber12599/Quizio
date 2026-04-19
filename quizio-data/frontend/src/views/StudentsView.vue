<template>
    <div class="students-container">
        <el-card>
            <template #header>
                <div class="card-header">
                    <h2>Student Management</h2>
                    <el-button type="primary" @click="openAddDialog">
                        <el-icon><Plus /></el-icon> Add Student
                    </el-button>
                </div>
            </template>

            <el-form class="filter-bar" inline>
                <el-form-item label="Admission Year">
                    <el-input-number
                        v-model="filterYear"
                        :placeholder="`e.g., ${new Date().getFullYear() - 1911}`"
                        align="left"
                        :controls="false"
                    />
                </el-form-item>
                <el-form-item label="Class Name">
                    <el-input
                        v-model="filterClass"
                        placeholder="e.g., 701"
                        clearable
                    />
                </el-form-item>
                <el-form-item label="Status">
                    <el-select
                        v-model="filterStatus"
                        clearable
                        style="width: 150px"
                    >
                        <el-option label="Active" :value="true" />
                        <el-option label="Deleted" :value="false" />
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
                <el-table-column
                    prop="student_id"
                    label="Student ID"
                    width="120"
                />
                <el-table-column prop="name" label="Name" width="120" />
                <el-table-column prop="email" label="Email" min-width="180" />
                <el-table-column
                    prop="admission_year"
                    label="Admission Year"
                    width="150"
                />
                <el-table-column prop="class_name" label="Class" width="100" />
                <el-table-column label="Actions" min-width="180" fixed="right">
                    <template #default="scope">
                        <el-button
                            size="small"
                            @click="openEditDialog(scope.row)"
                        >
                            <el-icon><Edit /></el-icon> Edit
                        </el-button>
                        <el-button
                            v-if="!scope.row.deleted_at"
                            size="small"
                            type="danger"
                            @click="handleDelete(scope.row)"
                        >
                            <el-icon><Delete /></el-icon> Delete
                        </el-button>
                        <el-button
                            v-if="scope.row.deleted_at"
                            size="small"
                            type="warning"
                            @click="handleRestore(scope.row)"
                        >
                            <el-icon><RefreshLeft /></el-icon> Restore
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>

        <el-dialog
            v-model="dialogVisible"
            :title="dialogType === 'add' ? 'Add Student' : 'Edit Student'"
            width="500px"
        >
            <el-form
                ref="formRef"
                :model="formData"
                :rules="rules"
                label-width="120px"
            >
                <el-form-item label="Student ID" prop="student_id" required>
                    <el-input
                        v-model="formData.student_id"
                        :disabled="dialogType === 'edit'"
                        placeholder="Please enter student ID"
                    />
                </el-form-item>

                <el-form-item label="Name" required>
                    <el-input
                        v-model="formData.name"
                        placeholder="Please enter student name"
                    />
                </el-form-item>

                <el-form-item
                    label="Password"
                    prop="password"
                    :required="dialogType === 'add'"
                    :rules="
                        dialogType === 'edit'
                            ? []
                            : [
                                  {
                                      required: true,
                                      message: 'Password is required',
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
                                ? 'Leave blank to keep current password'
                                : 'Please enter password'
                        "
                    />
                </el-form-item>

                <el-form-item label="Email" prop="email">
                    <el-input
                        v-model="formData.email"
                        placeholder="Please enter valid email"
                    />
                </el-form-item>

                <el-form-item label="Admission Year" prop="admission_year">
                    <el-input-number
                        v-model="formData.admission_year"
                        placeholder="Please enter admission year"
                        align="left"
                        :controls="false"
                        :style="{ width: '100%' }"
                    />
                </el-form-item>

                <el-form-item label="Class Name" prop="class_name">
                    <el-input
                        v-model="formData.class_name"
                        placeholder="Please enter class name"
                    />
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
import type { FormInstance, FormRules } from 'element-plus'

import dataAPI, { type ApiError } from '../api'
import type {
    StudentCreate,
    StudentResponse,
    StudentsGet,
    StudentUpdate
} from '../api/types/students'

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
const filterYear = ref<number | null>(null)
const filterClass = ref<string | null>(null)
const filterStatus = ref<boolean | null>(true)

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
        { required: true, message: 'Student ID is required', trigger: 'blur' }
    ],
    name: [
        { required: true, message: 'Student name is required', trigger: 'blur' }
    ],
    email: [
        {
            type: 'email',
            message: 'Please enter a valid email',
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
            ElMessage.error('Session expired. Please login again.')
            // Optional: Handle redirect to login here via router
        } else {
            ElMessage.error('Failed to fetch students.')
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
                ElMessage.success('Student added successfully')
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
                ElMessage.success('Student updated successfully')
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
    ElMessageBox.confirm(
        `Are you sure you want to delete student: ${row.name}?`,
        'Warning',
        {
            confirmButtonText: 'Delete',
            cancelButtonText: 'Cancel',
            type: 'warning'
        }
    )
        .then(async () => {
            try {
                await dataAPI.deleteStudent(row.id)
                ElMessage.success('Student deleted successfully')
                fetchStudents()
            } catch (err: unknown) {
                const error = err as ApiError
                ElMessage.error(
                    error.response?.data?.detail || 'Failed to delete student'
                )
            }
        })
        .catch(() => {
            // Action cancelled by user
        })
}

// Restore
const handleRestore = (row: StudentRow) => {
    ElMessageBox.confirm(
        `Are you sure you want to restore student: ${row.name}?`,
        'Warning',
        {
            confirmButtonText: 'Restore',
            cancelButtonText: 'Cancel',
            type: 'warning'
        }
    )
        .then(async () => {
            try {
                await dataAPI.restoreStudent(row.id)
                ElMessage.success('Student restored successfully')
                fetchStudents()
            } catch (err: unknown) {
                const error = err as ApiError
                ElMessage.error(
                    error.response?.data?.detail || 'Failed to restore student'
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
    color: #303133;
}
.filter-bar {
    margin-bottom: 20px;
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 4px;
}
</style>
