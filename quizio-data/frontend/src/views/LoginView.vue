<template>
    <div class="login-container">
        <el-card class="login-card">
            <template #header>
                <h2 class="login-title">Quizio Admin</h2>
            </template>

            <el-form :model="loginForm" @keyup.enter="handleLogin">
                <el-form-item>
                    <el-input
                        v-model="loginForm.username"
                        placeholder="Username"
                        prefix-icon="User"
                    />
                </el-form-item>

                <el-form-item>
                    <el-input
                        v-model="loginForm.password"
                        type="password"
                        placeholder="Password"
                        prefix-icon="Lock"
                        show-password
                    />
                </el-form-item>

                <el-button
                    type="primary"
                    class="login-button"
                    :loading="isLoading"
                    @click="handleLogin"
                >
                    Login
                </el-button>
            </el-form>
        </el-card>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const isLoading = ref(false)
const loginForm = reactive({
    username: '',
    password: ''
})

const handleLogin = async () => {
    if (!loginForm.username || !loginForm.password) {
        ElMessage.warning('Please enter username and password')
        return
    }

    isLoading.value = true
    const success = await authStore.login(
        loginForm.username,
        loginForm.password
    )
    isLoading.value = false

    if (success) {
        ElMessage.success('Login successful')
        router.push('/admin/students')
    } else {
        ElMessage.error('Invalid username or password')
    }
}
</script>

<style scoped>
.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    background-color: #2b3e50;
}
.login-card {
    width: 400px;
}
.login-title {
    margin: 0;
    text-align: center;
    color: #303133;
}
.login-button {
    width: 100%;
    margin-top: 10px;
}
</style>
