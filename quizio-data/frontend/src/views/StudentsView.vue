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

            <el-form :inline="true" class="filter-bar">
                <el-form-item label="Admission Year">
                    <el-input-number
                        v-model="filterYear"
                        :placeholder="`e.g., ${new Date().getFullYear() - 1911}`"
                        :controls="false"
                    />
                </el-form-item>
                <el-form-item label="Class">
                    <el-input
                        v-model="filterClass"
                        placeholder="e.g., 701"
                        clearable
                    />
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="handleSearch">
                        <el-icon><Search /></el-icon> Search
                    </el-button>
                    <el-button @click="resetFilters">Reset</el-button>
                </el-form-item>
            </el-form>

            <el-table
                :data="students"
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
                            size="small"
                            type="danger"
                            @click="handleDelete(scope.row)"
                        >
                            <el-icon><Delete /></el-icon> Delete
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
                :model="formData"
                label-width="120px"
                @keyup.enter="submitForm"
            >
                <el-form-item label="Student ID" required>
                    <el-input
                        v-model="formData.student_id"
                        :disabled="dialogType === 'edit'"
                    />
                </el-form-item>
                <el-form-item label="Name" required>
                    <el-input v-model="formData.name" />
                </el-form-item>
                <el-form-item label="Password" :required="dialogType === 'add'">
                    <el-input
                        v-model="formData.password"
                        type="password"
                        show-password
                        :placeholder="
                            dialogType === 'edit'
                                ? 'Leave blank to keep unchanged'
                                : ''
                        "
                    />
                </el-form-item>
                <el-form-item label="Email">
                    <el-input
                        v-model="formData.email"
                        placeholder="student@example.com"
                    />
                </el-form-item>
                <el-form-item label="Admission Year">
                    <el-input-number
                        v-model="formData.admission_year"
                        :controls="false"
                        placeholder="112"
                        style="width: 100%"
                    />
                </el-form-item>
                <el-form-item label="Class">
                    <el-input v-model="formData.class_name" placeholder="701" />
                </el-form-item>
            </el-form>
            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="dialogVisible = false">Cancel</el-button>
                    <el-button
                        type="primary"
                        @click="submitForm"
                        :loading="submitLoading"
                        >Confirm</el-button
                    >
                </span>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete } from '@element-plus/icons-vue'
import api from '../api'

// Define TypeScript interfaces
interface Student {
    id: number
    student_id: string
    name: string
    email: string | null
    admission_year: number | null
    class_name: string | null
}

// Component State
const students = ref<Student[]>([])
const loading = ref(false)
const submitLoading = ref(false)

// Filter State
const filterYear = ref<number | null>(null)
const filterClass = ref<string>('')

// Form State
const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const formData = ref({
    student_id: '',
    name: '',
    password: '',
    email: '',
    admission_year: null as number | null,
    class_name: ''
})

// Fetch Data
const fetchStudents = async () => {
    loading.value = true
    try {
        const params: any = {}
        if (filterYear.value) params.admission_year = filterYear.value
        if (filterClass.value) params.class_name = filterClass.value

        const response = await api.get('/students/', { params })
        students.value = response.data
    } catch (error: any) {
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
    filterYear.value = ''
    filterClass.value = ''
    fetchStudents()
}

// Dialog Handlers
const openAddDialog = () => {
    dialogType.value = 'add'
    formData.value = {
        student_id: '',
        name: '',
        password: '',
        email: '',
        admission_year: null,
        class_name: ''
    }
    dialogVisible.value = true
}

const openEditDialog = (row: Student) => {
    dialogType.value = 'edit'
    formData.value = {
        student_id: row.student_id,
        name: row.name,
        password: '',
        email: row.email || '',
        admission_year: row.admission_year,
        class_name: row.class_name || ''
    }
    dialogVisible.value = true
}

// Submit Data
const submitForm = async () => {
    if (!formData.value.student_id || !formData.value.name) {
        ElMessage.warning('Student ID and Name are required.')
        return
    }

    submitLoading.value = true
    try {
        if (dialogType.value === 'add') {
            if (!formData.value.password) {
                ElMessage.warning('Password is required for new students.')
                submitLoading.value = false
                return
            }
            // Convert empty strings to null for optional fields to keep DB clean
            const payload = { ...formData.value }
            if (payload.email === '') payload.email = null

            await api.post('/students/', payload)
            ElMessage.success('Student added successfully')
        } else {
            const updateData: any = { ...formData.value }
            // Remove password from payload if it was left blank
            if (!updateData.password) {
                delete updateData.password
            }
            if (updateData.email === '') updateData.email = null

            await api.put(`/students/${formData.value.student_id}`, updateData)
            ElMessage.success('Student updated successfully')
        }
        dialogVisible.value = false
        fetchStudents()
    } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || 'Operation failed')
    } finally {
        submitLoading.value = false
    }
}

// Delete Data
const handleDelete = (row: Student) => {
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
                await api.delete(`/students/${row.student_id}`)
                ElMessage.success('Student deleted successfully')
                fetchStudents()
            } catch (error) {
                ElMessage.error('Failed to delete student')
            }
        })
        .catch(() => {
            // Action cancelled by user
        })
}

// Initial Fetch
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
