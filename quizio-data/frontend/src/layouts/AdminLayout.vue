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
                    <template #title>{{ $t('layout.nav.teachers') }}</template>
                </el-menu-item>

                <el-menu-item index="/admin/students">
                    <el-icon><User /></el-icon>
                    <template #title>{{ $t('layout.nav.students') }}</template>
                </el-menu-item>

                <el-menu-item index="/admin/questions">
                    <el-icon><Collection /></el-icon>
                    <template #title>{{ $t('layout.nav.questions') }}</template>
                </el-menu-item>

                <el-menu-item index="/admin/exams">
                    <el-icon><MessageBox /></el-icon>
                    <template #title>{{ $t('layout.nav.exams') }}</template>
                </el-menu-item>

                <el-menu-item index="/admin/grades">
                    <el-icon><EditPen /></el-icon>
                    <template #title>{{ $t('layout.nav.grades') }}</template>
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
                            >{{ $t('layout.breadcrumb_root') }}</el-breadcrumb-item
                        >
                        <el-breadcrumb-item>{{ breadcrumbRouteName }}</el-breadcrumb-item>
                    </el-breadcrumb>
                </div>

                <div class="header-right">
                    <span class="welcome-text">
                        {{ $t('layout.welcome', { name: authStore.user?.full_name || authStore.user?.username || $t('common.loading') }) }}
                    </span>

                    <el-popover
                        placement="bottom"
                        :width="220"
                        trigger="click"
                        popper-class="settings-popover"
                    >
                        <template #reference>
                            <el-button text class="toggle-btn">
                                <el-icon><MoreFilled /></el-icon>
                            </el-button>
                        </template>
                        <div class="settings-menu-content">
                            <div class="settings-menu-group">
                                <div class="settings-menu-header">
                                    <span style="margin-right: 8px">🌐</span>
                                    <span>{{ $t('layout.language') }}</span>
                                </div>
                                <div class="settings-menu-items">
                                    <div
                                        class="settings-menu-item"
                                        :class="{ active: locale === 'zh' }"
                                        @click="setLang('zh')"
                                    >
                                        <el-icon v-if="locale === 'zh'"><Check /></el-icon>
                                        <span v-else style="width: 18px"></span>
                                        {{ $t('lang.zh') }}
                                    </div>
                                    <div
                                        class="settings-menu-item"
                                        :class="{ active: locale === 'en' }"
                                        @click="setLang('en')"
                                    >
                                        <el-icon v-if="locale === 'en'"><Check /></el-icon>
                                        <span v-else style="width: 18px"></span>
                                        {{ $t('lang.en') }}
                                    </div>
                                </div>
                            </div>
                            <el-divider style="margin: 8px 0" />
                            <div class="settings-menu-group">
                                <div class="settings-menu-header">
                                    <el-icon style="margin-right: 8px">
                                        <Sunny v-if="themeMode === 'light'" />
                                        <Moon v-else-if="themeMode === 'dark'" />
                                        <Monitor v-else />
                                    </el-icon>
                                    <span>{{ $t('layout.theme') }}</span>
                                </div>
                                <div class="settings-menu-items">
                                    <div
                                        class="settings-menu-item"
                                        :class="{ active: themeMode === 'light' }"
                                        @click="setTheme('light')"
                                    >
                                        <el-icon v-if="themeMode === 'light'"><Check /></el-icon>
                                        <span v-else style="width: 18px"></span>
                                        {{ $t('theme.light') }}
                                    </div>
                                    <div
                                        class="settings-menu-item"
                                        :class="{ active: themeMode === 'dark' }"
                                        @click="setTheme('dark')"
                                    >
                                        <el-icon v-if="themeMode === 'dark'"><Check /></el-icon>
                                        <span v-else style="width: 18px"></span>
                                        {{ $t('theme.dark') }}
                                    </div>
                                    <div
                                        class="settings-menu-item"
                                        :class="{ active: themeMode === 'system' }"
                                        @click="setTheme('system')"
                                    >
                                        <el-icon v-if="themeMode === 'system'"><Check /></el-icon>
                                        <span v-else style="width: 18px"></span>
                                        {{ $t('theme.system') }}
                                    </div>
                                </div>
                            </div>
                            <el-divider style="margin: 8px 0" />
                            <div class="settings-menu-item settings-menu-logout" @click="handleLogout">
                                <el-icon><SwitchButton /></el-icon>
                                {{ $t('layout.logout') }}
                            </div>
                        </div>
                    </el-popover>
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
import { useI18n } from 'vue-i18n'
import { Fold, Expand, Sunny, Moon, Monitor, MoreFilled, Check, SwitchButton } from '@element-plus/icons-vue'

import { useAuthStore } from '../stores/auth'
import { useTheme } from '../composables/useTheme'
import { storage } from '../utils/storage'

import packageJson from '../../package.json'

const appVersion = packageJson.version

const route = useRoute()
const authStore = useAuthStore()
const { locale, t } = useI18n()
const { themeMode, setTheme } = useTheme()

const isCollapse = ref(false)

const toggleCollapse = () => {
    isCollapse.value = !isCollapse.value
}

const setLang = (lang: 'zh' | 'en') => {
    locale.value = lang
    storage.appLang.set(lang)
}

// Map route path to breadcrumb name key
const navKeys: Record<string, string> = {
    'teachers': 'layout.nav.teachers',
    'students': 'layout.nav.students',
    'questions': 'layout.nav.questions',
    'exams': 'layout.nav.exams',
    'grades': 'layout.nav.grades',
}

const breadcrumbRouteName = computed(() => {
    const routePath = route.path.split('/').slice(-1)[0]
    const key = navKeys[routePath]
    return key ? t(key) : routePath
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
    background-color: var(--el-bg-color);
    border-bottom: 1px solid var(--el-border-color-light);
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
    color: var(--el-text-color-regular);
    transition: color 0.2s;
}

.collapse-btn:hover {
    color: var(--el-color-primary);
}

.header-right {
    display: flex;
    align-items: center;
    gap: 12px;
}

.welcome-text {
    font-size: 14px;
    color: var(--el-text-color-regular);
}

.toggle-btn {
    font-size: 18px;
}

:deep(.settings-popover.el-popper) {
    padding: 8px !important;
    min-width: 200px !important;
}

.settings-menu-content {
    display: flex;
    flex-direction: column;
    gap: 0;
}

.settings-menu-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.settings-menu-header {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    font-size: 13px;
    font-weight: 600;
    color: var(--el-text-color-regular);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    opacity: 0.8;
}

.settings-menu-items {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding-left: 12px;
}

.settings-menu-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    color: var(--el-text-color-regular);
    transition: background-color 0.2s;
}

.settings-menu-item:hover {
    background-color: var(--el-fill-color-light);
}

.settings-menu-item.active {
    color: var(--el-color-primary);
    font-weight: 500;
}

.settings-menu-logout {
    color: var(--el-color-danger);
    padding-left: 12px !important;
    margin-top: 4px;
}

.settings-menu-logout:hover {
    background-color: var(--el-color-danger-light-7) !important;
}

.main-content {
    background-color: var(--el-bg-color-page);
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
