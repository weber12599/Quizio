<template>
    <div v-if="isOpen" class="fab-overlay" @click="isOpen = false"></div>

    <div class="fab-container">
        <transition name="el-zoom-in-bottom">
            <div v-show="isOpen" class="fab-menu">
                <el-button
                    round
                    size="large"
                    class="fab-item shadow-hover version-btn"
                >
                    <span style="font-size: 1.1rem; margin-right: 8px">🏷️</span>
                    <span style="font-weight: bold">v{{ appVersion }}</span>
                </el-button>

                <el-button
                    round
                    size="large"
                    @click="toggleLanguage"
                    class="fab-item shadow-hover"
                >
                    <span style="font-size: 1.1rem; margin-right: 8px">🌐</span>
                    <span style="font-weight: bold">
                        {{ locale === 'zh' ? 'English' : '中文' }}
                    </span>
                </el-button>
            </div>
        </transition>

        <el-button
            :type="isOpen ? 'danger' : 'primary'"
            circle
            class="fab-main shadow-hover"
            plain
            @click="toggleMenu"
        >
            <el-icon :size="24" class="icon-spin">
                <Close v-if="isOpen" />
                <ArrowDown v-else />
            </el-icon>
        </el-button>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowDown, Close } from '@element-plus/icons-vue'
import { storage } from '../utils/storage'

// Import package.json to access the app version (adjust the relative path if your folder structure differs)
import packageJson from '../../package.json'

const { locale } = useI18n()
const isOpen = ref(false)

// Extract the version number
const appVersion = packageJson.version

const toggleMenu = () => {
    isOpen.value = !isOpen.value
}

const toggleLanguage = () => {
    const newLang = locale.value === 'zh' ? 'en' : 'zh'
    locale.value = newLang
    storage.appLang.set(newLang)
    isOpen.value = false
}
</script>

<style scoped>
/* Overlay: Retains simple fixed positioning */
.fab-overlay {
    position: fixed;
    inset: 0;
    z-index: 999;
}

/* Container positioning */
.fab-container {
    position: fixed;
    bottom: 30px;
    right: 30px;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 16px;
}

/* Menu layout */
.fab-menu {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 12px;
    margin-bottom: 8px;
}

/* Override Element Plus button styles for floating shadow and hover scale */
.shadow-hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    transition:
        transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275),
        background-color 0.3s !important;
}

.shadow-hover:hover {
    transform: scale(1.08);
}

/* Specific style for the version button to indicate it's not clickable */
.version-btn {
    cursor: default;
}

.fab-main {
    width: 48px !important;
    height: 48px !important;
}

.icon-spin {
    transition: transform 0.3s ease;
}
.fab-main:hover .icon-spin {
    transform: rotate(180deg);
}
</style>
