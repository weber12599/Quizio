<template>
    <el-container class="layout-container">
        <el-aside :width="isCollapse ? '64px' : '250px'" class="aside">
            <el-tooltip
                :content="`v${appVersion}`"
                placement="right"
                effect="dark"
            >
                <div class="logo">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 100 100"
                        class="logo-icon"
                    >
                        <defs>
                            <mask id="q-mask">
                                <rect width="100%" height="100%" fill="white" />
                                <path
                                    d="M 40 55 L 65 80 L 95 30"
                                    fill="none"
                                    stroke="black"
                                    stroke-width="16"
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                />
                            </mask>
                            <linearGradient
                                id="primary-grad"
                                x1="0%"
                                y1="0%"
                                x2="100%"
                                y2="100%"
                            >
                                <stop offset="0%" stop-color="#66b1ff" />
                                <stop offset="100%" stop-color="#409eff" />
                            </linearGradient>
                        </defs>

                        <circle
                            cx="48"
                            cy="48"
                            r="28"
                            fill="none"
                            stroke="#ffffff"
                            stroke-width="10"
                            mask="url(#q-mask)"
                        />

                        <path
                            d="M 40 55 L 65 80 L 95 30"
                            fill="none"
                            stroke="url(#primary-grad)"
                            stroke-width="10"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                        />
                    </svg>

                    <h2 v-if="!isCollapse" class="logo-text">Quizio CMS</h2>
                </div>
            </el-tooltip>

            <el-menu
                :default-active="route.path"
                class="el-menu-vertical"
                background-color="#304156"
                text-color="#bfcbd9"
                active-text-color="#409eff"
                :collapse="isCollapse"
                router
            >
                <el-menu-item
                    v-if="authStore.user?.is_superuser"
                    index="/admin/teachers"
                >
                    <el-icon><Avatar /></el-icon>
                    <template #title>Teacher Management</template>
                </el-menu-item>

                <el-menu-item index="/admin/students">
                    <el-icon><User /></el-icon>
                    <template #title>Student Management</template>
                </el-menu-item>

                <el-menu-item index="/admin/questions">
                    <el-icon><Collection /></el-icon>
                    <template #title>Question Management</template>
                </el-menu-item>

                <el-menu-item index="/admin/exams">
                    <el-icon><MessageBox /></el-icon>
                    <template #title>Exam Management</template>
                </el-menu-item>

                <el-menu-item index="/admin/grades">
                    <el-icon><EditPen /></el-icon>
                    <template #title>Grade Management</template>
                </el-menu-item>
            </el-menu>
        </el-aside>

        <el-container>
            <el-header class="header">
                <div class="header-left">
                    <el-icon class="collapse-btn" @click="toggleCollapse">
                        <Fold v-if="!isCollapse" />
                        <Expand v-else />
                    </el-icon>

                    <el-breadcrumb separator="/">
                        <el-breadcrumb-item :to="{ path: '/admin' }"
                            >CMS</el-breadcrumb-item
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
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Fold, Expand } from '@element-plus/icons-vue'

import { useAuthStore } from '../stores/auth'

import packageJson from '../../package.json'

const appVersion = packageJson.version

const route = useRoute()
const authStore = useAuthStore()

const isCollapse = ref(false)

const toggleCollapse = () => {
    isCollapse.value = !isCollapse.value
}

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
.logo {
    height: 60px;
    display: flex;
    align-items: center;
    /* 收合時置中，展開時稍微靠左讓文字有空間 */
    justify-content: center;
    gap: 12px;
    color: #fff;
    border-bottom: 1px solid #1f2d3d;
    background-color: #2b3643;
    transition: all 0.3s ease;
    overflow: hidden;
    padding: 0 16px;
}

.logo-icon {
    width: 32px;
    height: 32px;
    flex-shrink: 0; /* 防止 SVG 被壓縮 */
    transition: transform 0.3s ease;
}

/* 當側邊欄收起時，稍微放大 Logo 讓它更明顯 */
.aside:not([width='250px']) .logo-icon {
    transform: scale(1.1);
}

.logo-text {
    margin: 0;
    font-size: 20px;
    letter-spacing: 1px;
    font-weight: 600;
    white-space: nowrap;
    animation: fadeIn 0.3s ease forwards;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateX(-10px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.layout-container {
    height: 100vh;
    width: 100vw;
}

.aside {
    background-color: #304156;
    display: flex;
    flex-direction: column;
    transition: width 0.3s ease;
    overflow: hidden;
}

.logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    border-bottom: 1px solid #1f2d3d;
    background-color: #2b3643;
    transition: all 0.3s ease;
}

.logo h2 {
    margin: 0;
    font-size: 22px;
    letter-spacing: 1px;
    white-space: nowrap;
}

.el-menu-vertical {
    border-right: none;
    flex: 1;
}

.el-menu-vertical:not(.el-menu--collapse) {
    width: 250px;
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

.header-left {
    display: flex;
    align-items: center;
    gap: 15px;
}

.collapse-btn {
    font-size: 20px;
    cursor: pointer;
    color: #606266;
    transition: color 0.2s;
}

.collapse-btn:hover {
    color: #409eff;
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
