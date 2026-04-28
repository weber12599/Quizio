<template>
    <div class="teachers-container">
        <el-card>
            <template #header>
                <div class="card-header">
                    <h2>{{ $t('teachers.title') }}</h2>
                    <el-button type="primary" @click="openAddDialog">
                        <el-icon><Plus /></el-icon>
                        {{ $t('teachers.add_teacher') }}
                    </el-button>
                </div>
            </template>

            <el-table
                :data="rows"
                v-loading="loading"
                border
                style="width: 100%"
            >
                <el-table-column prop="id" label="ID" width="80" />
                <el-table-column
                    prop="username"
                    :label="$t('teachers.columns.username')"
                    width="150"
                />
                <el-table-column
                    prop="full_name"
                    :label="$t('teachers.columns.full_name')"
                    width="180"
                />
                <el-table-column
                    prop="email"
                    :label="$t('teachers.columns.email')"
                    min-width="200"
                />

                <el-table-column
                    :label="$t('common.edit')"
                    width="120"
                    align="center"
                >
                    <template #default="scope">
                        <el-tag
                            :type="scope.row.is_superuser ? 'danger' : 'info'"
                        >
                            {{ scope.row.is_superuser ? 'Admin' : 'Teacher' }}
                        </el-tag>
                    </template>
                </el-table-column>

                <el-table-column
                    :label="$t('teachers.columns.is_active')"
                    width="120"
                    align="center"
                >
                    <template #default="scope">
                        <el-switch
                            v-model="scope.row.is_active"
                            active-color="#13ce66"
                            inactive-color="#ff4949"
                            @change="
                                (val: boolean) =>
                                    handleStatusChange(scope.row, val)
                            "
                            :disabled="scope.row.id === authStore.user?.id"
                        />
                    </template>
                </el-table-column>

                <el-table-column
                    :label="$t('common.edit')"
                    width="120"
                    fixed="right"
                >
                    <template #default="scope">
                        <el-button
                            size="small"
                            @click="openEditDialog(scope.row)"
                        >
                            <el-icon><Edit /></el-icon> {{ $t('common.edit') }}
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>

        <el-dialog
            v-model="dialogVisible"
            :title="
                dialogType === 'add'
                    ? $t('teachers.add_teacher')
                    : $t('teachers.edit_teacher')
            "
            width="500px"
        >
            <el-form
                ref="formRef"
                :model="formData"
                :rules="rules"
                label-width="120px"
            >
                <el-form-item label="Username" prop="username" required>
                    <el-input
                        v-model="formData.username"
                        :disabled="dialogType === 'edit'"
                        placeholder="Please enter username"
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

                <el-form-item label="Full Name" prop="full_name">
                    <el-input
                        v-model="formData.full_name"
                        placeholder="Please enter full name"
                    />
                </el-form-item>

                <el-form-item label="Email" prop="email">
                    <el-input
                        v-model="formData.email"
                        placeholder="Please enter valid email"
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
import type { FormInstance, FormRules } from 'element-plus'

import { useAuthStore } from '../stores/auth'

import dataAPI, { type ApiError } from '../api'
import type { UserCreate, UserResponse, UserUpdate } from '../api/types/users'

const authStore = useAuthStore()

type UserRow = UserResponse & { is_active: boolean }

interface TeacherFormData {
    id: number | null
    username: string
    password: string | null
    full_name: string
    email: string
    is_superuser: boolean
}

// State management
const rows = ref<UserRow[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogType = ref<'add' | 'edit'>('add')
const submitLoading = ref(false)
const formRef = ref<FormInstance>()

// Form Data
const formData = reactive<TeacherFormData>({
    id: null as number | null,
    username: '',
    password: null as string | null,
    full_name: '',
    email: '',
    is_superuser: false
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
        const response = await dataAPI.getUsers()
        rows.value = response.data.map((teacher) => ({
            ...teacher,
            is_active: teacher.deleted_at === null
        }))
    } catch (err: unknown) {
        const error = err as ApiError
        ElMessage.error(
            error.response?.data?.detail || 'Failed to fetch teachers'
        )
    } finally {
        loading.value = false
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
            if (dialogType.value === 'add') {
                const payload: UserCreate = {
                    username: formData.username,
                    password: formData.password as string,
                    full_name: formData.full_name || null,
                    email: formData.email || null,
                    is_superuser: formData.is_superuser
                }
                await dataAPI.createUser(payload)
                ElMessage.success('Teacher added successfully')
            } else if (formData.id !== null && formData.id !== undefined) {
                const payload: UserUpdate = {
                    full_name: formData.full_name || null,
                    email: formData.email || null
                }
                if (formData.password) {
                    payload.password = formData.password
                }

                await dataAPI.updateUser(formData.id, payload)
                ElMessage.success('Teacher updated successfully')
            }

            dialogVisible.value = false
            fetchTeachers()
        } catch (err: unknown) {
            const error = err as ApiError
            if (
                error.response?.status === 409 ||
                error.response?.data?.detail?.includes('exists')
            ) {
                ElMessage.warning('Username or Email already exists!')
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

// Inline toggle for active status
const handleStatusChange = async (row: UserRow, isActive: boolean) => {
    try {
        if (isActive) {
            await dataAPI.restoreUser(row.id)
            row.deleted_at = null
            row.is_active = true
            ElMessage.success('User restored')
        } else {
            await dataAPI.deleteUser(row.id)
            row.deleted_at = new Date().toISOString()
            row.is_active = false
            ElMessage.success('User deleted')
        }
    } catch (err: unknown) {
        const error = err as ApiError
        row.is_active = !isActive
        ElMessage.error(
            error.response?.data?.detail || 'Failed to update status'
        )
    }
}

// Dialog Handlers
const openAddDialog = () => {
    dialogType.value = 'add'
    resetForm()
    dialogVisible.value = true
}

const openEditDialog = (row: UserRow) => {
    dialogType.value = 'edit'
    resetForm()
    Object.assign(formData, {
        id: row.id,
        username: row.username,
        password: '', // Leave blank deliberately
        full_name: row.full_name || '',
        email: row.email || '',
        is_superuser: row.is_superuser
    })
    dialogVisible.value = true
}

const resetForm = () => {
    if (formRef.value) {
        formRef.value.clearValidate()
    }

    Object.assign(formData, {
        id: null,
        username: '',
        password: '',
        full_name: '',
        email: '',
        is_superuser: false
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
    color: var(--el-text-color-primary);
}
</style>
