<template>
    <div class="login-container">
        <div class="toolbar">
            <el-tooltip :content="locale === 'zh' ? $t('lang.en') : $t('lang.zh')">
                <el-button text @click="toggleLang" class="toggle-btn">
                    <span style="font-size: 1.2rem">🌐</span>
                </el-button>
            </el-tooltip>

            <el-tooltip :content="$t(`theme.${themeMode}`)">
                <el-button text @click="cycleTheme" class="toggle-btn">
                    <el-icon v-if="themeMode === 'light'"><Sunny /></el-icon>
                    <el-icon v-else-if="themeMode === 'dark'"><Moon /></el-icon>
                    <el-icon v-else><Monitor /></el-icon>
                </el-button>
            </el-tooltip>
        </div>

        <el-card class="login-card" shadow="hover">
            <template #header>
                <div class="card-header">
                    <h2>{{ $t('login.title') }}</h2>
                </div>
            </template>

            <el-form
                ref="loginFormRef"
                :model="loginForm"
                :rules="rules"
                label-position="top"
                @keyup.enter="handleLogin"
            >
                <el-form-item :label="$t('login.username')" prop="username">
                    <el-input
                        v-model="loginForm.username"
                        :placeholder="$t('login.username_placeholder')"
                        prefix-icon="User"
                    />
                </el-form-item>

                <el-form-item :label="$t('login.password')" prop="password">
                    <el-input
                        v-model="loginForm.password"
                        type="password"
                        :placeholder="$t('login.password_placeholder')"
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
                        {{ $t('login.login_button') }}
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
import { useI18n } from 'vue-i18n'
import { Sunny, Moon, Monitor } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useTheme } from '../composables/useTheme'
import { storage } from '../utils/storage'
import type { FormInstance, FormRules } from 'element-plus'

const authStore = useAuthStore()
const router = useRouter()
const { locale, t } = useI18n()
const { themeMode, cycleTheme } = useTheme()

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
        { required: true, message: t('login.error_required'), trigger: 'blur' }
    ],
    password: [
        { required: true, message: t('login.error_required'), trigger: 'blur' }
    ]
})

const toggleLang = () => {
    const newLang = locale.value === 'zh' ? 'en' : 'zh'
    locale.value = newLang
    storage.appLang.set(newLang)
}

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
                errorMessage.value = t('login.error_invalid_credentials')
            }

            isLoading.value = false
        }
    })
}
</script>

<style scoped>
.login-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100vh;
    background-color: var(--el-bg-color-page);
    position: relative;
}

.toolbar {
    position: absolute;
    top: 20px;
    right: 20px;
    display: flex;
    gap: 8px;
}

.toggle-btn {
    font-size: 18px;
}

.login-card {
    width: 100%;
    max-width: 400px;
    border-radius: 8px;
}

.card-header h2 {
    margin: 0;
    text-align: center;
    color: var(--el-text-color-primary);
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
