<template>
    <div class="teachers-container">
        <el-card>
            <template #header>
                <div class="card-header">
                    <h2>Teacher Management (Admin)</h2>
                    <el-button type="primary" @click="openAddDialog">
                        <el-icon><Plus /></el-icon> Add Teacher
                    </el-button>
                </div>
            </template>

            <el-table
                :data="teachers"
                v-loading="loading"
                border
                style="width: 100%"
            >
                <el-table-column prop="id" label="ID" width="80" />
                <el-table-column prop="username" label="Username" width="150" />
                <el-table-column
                    prop="full_name"
                    label="Full Name"
                    width="180"
                />
                <el-table-column prop="email" label="Email" min-width="200" />

                <el-table-column label="Role" width="120" align="center">
                    <template #default="scope">
                        <el-tag
                            :type="scope.row.is_superuser ? 'danger' : 'info'"
                        >
                            {{
                                scope.row.is_superuser
                                    ? 'Superadmin'
                                    : 'Teacher'
                            }}
                        </el-tag>
                    </template>
                </el-table-column>

                <el-table-column label="Status" width="120" align="center">
                    <template #default="scope">
                        <el-switch
                            v-model="scope.row.is_active"
                            active-color="#13ce66"
                            inactive-color="#ff4949"
                            @change="
                                (val) =>
                                    handleStatusChange(
                                        scope.row,
                                        val as boolean
                                    )
                            "
                            :disabled="scope.row.id === authStore.user?.id"
                        />
                    </template>
                </el-table-column>

                <el-table-column label="Actions" width="120" fixed="right">
                    <template #default="scope">
                        <el-button
                            size="small"
                            @click="openEditDialog(scope.row)"
                        >
                            <el-icon><Edit /></el-icon> Edit
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>

        <el-dialog
            v-model="dialogVisible"
            :title="dialogType === 'add' ? 'Add Teacher' : 'Edit Teacher'"
            width="500px"
            @closed="resetForm"
        >
            <el-form
                ref="formRef"
                :model="formData"
                :rules="rules"
                label-width="120px"
            >
                <el-form-item label="Username" prop="username">
                    <el-input
                        v-model="formData.username"
                        :disabled="dialogType === 'edit'"
                        placeholder="e.g., teacher_wang"
                    />
                </el-form-item>

                <el-form-item label="Full Name" prop="full_name">
                    <el-input
                        v-model="formData.full_name"
                        placeholder="Teacher's full name"
                    />
                </el-form-item>

                <el-form-item
                    label="Password"
                    prop="password"
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
                                : 'Initial password'
                        "
                    />
                </el-form-item>

                <el-form-item label="Email" prop="email">
                    <el-input
                        v-model="formData.email"
                        placeholder="Required for regular teachers"
                    />
                </el-form-item>

                <el-form-item label="Is Superadmin" v-if="dialogType === 'add'">
                    <el-switch v-model="formData.is_superuser" />
                </el-form-item>
            </el-form>

            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="dialogVisible = false">Cancel</el-button>
                    <el-button
                        type="primary"
                        @click="handleSubmit"
                        :loading="submitLoading"
                    >
                        Confirm
                    </el-button>
                </span>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Edit } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

// State management
const teachers = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const submitLoading = ref(false)
const formRef = ref<FormInstance>()

// Form Data
const formData = reactive({
    id: null as number | null,
    username: '',
    full_name: '',
    email: '',
    password: '',
    is_superuser: false,
    is_active: true
})

// Validation Rules
const rules = reactive<FormRules>({
    username: [
        { required: true, message: 'Username is required', trigger: 'blur' }
    ],
    email: [
        {
            type: 'email',
            message: 'Please enter a valid email',
            trigger: 'blur'
        }
    ]
})

// Fetch all teachers
const fetchTeachers = async () => {
    loading.value = true
    try {
        // 🌟 注意結尾斜線，避免 307 導向錯誤
        const response = await api.get('/api/users/')
        teachers.value = response.data
    } catch (error: any) {
        ElMessage.error(
            error.response?.data?.detail || 'Failed to fetch teachers'
        )
    } finally {
        loading.value = false
    }
}

// Dialog Handlers
const openAddDialog = () => {
    dialogType.value = 'add'
    dialogVisible.value = true
}

const openEditDialog = (row: any) => {
    dialogType.value = 'edit'
    Object.assign(formData, {
        id: row.id,
        username: row.username,
        full_name: row.full_name || '',
        email: row.email || '',
        password: '', // Leave blank deliberately
        is_superuser: row.is_superuser,
        is_active: row.is_active
    })
    dialogVisible.value = true
}

// Submit Data
const handleSubmit = async () => {
    if (!formRef.value) return

    await formRef.value.validate(async (valid) => {
        if (valid) {
            submitLoading.value = true
            try {
                const payload = { ...formData }
                // 如果編輯時沒有填寫密碼，就不要送出這個欄位
                if (dialogType.value === 'edit' && !payload.password) {
                    delete payload.password
                }

                if (dialogType.value === 'add') {
                    // 🌟 注意結尾斜線
                    await api.post('/api/users/', payload)
                    ElMessage.success('Teacher added successfully')
                } else {
                    await api.put(`/api/users/${formData.id}`, payload)
                    ElMessage.success('Teacher updated successfully')
                }

                dialogVisible.value = false
                fetchTeachers()
            } catch (error: any) {
                ElMessage.error(
                    error.response?.data?.detail || 'Operation failed'
                )
            } finally {
                submitLoading.value = false
            }
        }
    })
}

// Inline toggle for active status
const handleStatusChange = async (row: any, isActive: boolean) => {
    try {
        await api.put(`/api/users/${row.id}`, { is_active: isActive })
        ElMessage.success(
            `User status updated to ${isActive ? 'Active' : 'Inactive'}`
        )
    } catch (error: any) {
        // Rollback UI change if API fails
        row.is_active = !isActive
        ElMessage.error(
            error.response?.data?.detail || 'Failed to update status'
        )
    }
}

const resetForm = () => {
    if (formRef.value) formRef.value.resetFields()
    Object.assign(formData, {
        id: null,
        username: '',
        full_name: '',
        email: '',
        password: '',
        is_superuser: false,
        is_active: true
    })
}

onMounted(() => {
    fetchTeachers()
})
</script>

<style scoped>
.teachers-container {
    background-color: #fff;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

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
</style>
