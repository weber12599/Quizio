<template>
    <div class="login-container">
        <el-card class="login-card" shadow="hover">
            <template #header>
                <div class="card-header">
                    <h2>Quizio Admin</h2>
                </div>
            </template>

            <el-form
                ref="loginFormRef"
                :model="loginForm"
                :rules="rules"
                label-position="top"
                @keyup.enter="handleLogin"
            >
                <el-form-item label="Username" prop="username">
                    <el-input
                        v-model="loginForm.username"
                        placeholder="Enter your username"
                        prefix-icon="User"
                    />
                </el-form-item>

                <el-form-item label="Password" prop="password">
                    <el-input
                        v-model="loginForm.password"
                        type="password"
                        placeholder="Enter your password"
                        prefix-icon="Lock"
                        show-password
                    />
                </el-form-item>

                <el-form-item>
                    <el-button
                        type="primary"
                        class="login-button"
                        :loading="isLoading"
                        @click="handleLogin"
                    >
                        Sign In
                    </el-button>
                </el-form-item>
            </el-form>

            <div v-if="errorMessage" class="error-msg">
                <el-text type="danger">{{ errorMessage }}</el-text>
            </div>
        </el-card>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import type { FormInstance, FormRules } from 'element-plus'

const authStore = useAuthStore()
const router = useRouter()

const loginFormRef = ref<FormInstance>()
const isLoading = ref(false)
const errorMessage = ref('')

const loginForm = reactive({
    username: '',
    password: ''
})

// Element Plus form validation rules
const rules = reactive<FormRules>({
    username: [
        { required: true, message: 'Please input username', trigger: 'blur' }
    ],
    password: [
        { required: true, message: 'Please input password', trigger: 'blur' }
    ]
})

const handleLogin = async () => {
    if (!loginFormRef.value) return

    await loginFormRef.value.validate(async (valid) => {
        if (valid) {
            isLoading.value = true
            errorMessage.value = ''

            const success = await authStore.login(
                loginForm.username,
                loginForm.password
            )

            if (success) {
                // Redirect to admin dashboard on success
                router.push('/admin/students')
            } else {
                errorMessage.value = 'Invalid username or password'
            }

            isLoading.value = false
        }
    })
}
</script>

<style scoped>
.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    background-color: #f5f7fa;
}

.login-card {
    width: 100%;
    max-width: 400px;
    border-radius: 8px;
}

.card-header h2 {
    margin: 0;
    text-align: center;
    color: #303133;
}

.login-button {
    width: 100%;
    margin-top: 10px;
}

.error-msg {
    margin-top: 15px;
    text-align: center;
}
</style>
