<template>
    <el-container class="layout-container">
        <el-aside width="250px" class="aside">
            <div class="logo">
                <h2>Quizio Admin</h2>
            </div>

            <el-menu
                :default-active="route.path"
                class="el-menu-vertical"
                background-color="#304156"
                text-color="#bfcbd9"
                active-text-color="#409eff"
                router
            >
                <el-menu-item
                    v-if="authStore.user?.is_superuser"
                    index="/admin/teachers"
                >
                    <el-icon><Avatar /></el-icon>
                    <span>Teacher Management</span>
                </el-menu-item>

                <el-menu-item index="/admin/students">
                    <el-icon><User /></el-icon>
                    <span>Student Management</span>
                </el-menu-item>

                <el-menu-item index="/admin/questions">
                    <el-icon><Collection /></el-icon>
                    <span>Question Management</span>
                </el-menu-item>

                <el-menu-item index="/admin/exams">
                    <el-icon><MessageBox /></el-icon>
                    <span>Exam Management</span>
                </el-menu-item>

                <el-menu-item index="/admin/grades">
                    <el-icon><EditPen /></el-icon>
                    <span>Grade Management</span>
                </el-menu-item>
            </el-menu>
        </el-aside>

        <el-container>
            <el-header class="header">
                <div class="header-left">
                    <el-breadcrumb separator="/">
                        <el-breadcrumb-item :to="{ path: '/admin' }"
                            >admin</el-breadcrumb-item
                        >
                        <el-breadcrumb-item>{{
                            currentRouteName
                        }}</el-breadcrumb-item>
                    </el-breadcrumb>
                </div>

                <div class="header-right">
                    <span class="welcome-text">
                        Welcome,
                        <strong>{{
                            authStore.user?.full_name ||
                            authStore.user?.username ||
                            'Teacher'
                        }}</strong>
                    </span>
                    <el-button
                        type="danger"
                        plain
                        size="small"
                        @click="handleLogout"
                    >
                        <el-icon class="el-icon--left"
                            ><SwitchButton
                        /></el-icon>
                        Logout
                    </el-button>
                </div>
            </el-header>

            <el-main class="main-content">
                <router-view v-slot="{ Component }">
                    <transition name="fade" mode="out-in">
                        <component :is="Component" />
                    </transition>
                </router-view>
            </el-main>
        </el-container>
    </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { MessageBox } from '@element-plus/icons-vue'

const route = useRoute()
const authStore = useAuthStore()

// Dynamically compute the current page name for the breadcrumb
const currentRouteName = computed(() => {
    return route.path.split('/').slice(-1)[0]
})

const handleLogout = () => {
    authStore.logout()
}

onMounted(async () => {
    // Check if token exists but user data is missing after page reload
    if (authStore.token && !authStore.user) {
        await authStore.fetchUserProfile()
    }
})
</script>

<style scoped>
.layout-container {
    height: 100vh;
    width: 100vw;
}

.aside {
    background-color: #304156;
    display: flex;
    flex-direction: column;
}

.logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    border-bottom: 1px solid #1f2d3d;
    background-color: #2b3643;
}

.logo h2 {
    margin: 0;
    font-size: 22px;
    letter-spacing: 1px;
}

.el-menu-vertical {
    border-right: none;
    flex: 1;
}

.header {
    background-color: #fff;
    border-bottom: 1px solid #e6e6e6;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    height: 60px;
}

.header-right {
    display: flex;
    align-items: center;
    gap: 20px;
}

.welcome-text {
    font-size: 14px;
    color: #606266;
}

.main-content {
    background-color: #f0f2f5;
    padding: 24px;
}

/* Page transition effects */
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
</style>
