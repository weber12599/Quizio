<template>
    <div v-if="isOpen" class="fab-overlay" @click="isOpen = false"></div>

    <div class="fab-container">
        <transition name="el-zoom-in-bottom">
            <div v-show="isOpen" class="fab-menu">
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

const { locale } = useI18n()
const isOpen = ref(false)

const toggleMenu = () => {
    isOpen.value = !isOpen.value
}

const toggleLanguage = () => {
    const newLang = locale.value === 'zh' ? 'en' : 'zh'
    locale.value = newLang
    localStorage.setItem('app_lang', newLang)
    isOpen.value = false
}
</script>

<style scoped>
/* 遮罩：保留最簡單的 fixed 定位 */
.fab-overlay {
    position: fixed;
    inset: 0; /* 等同於 top:0; left:0; right:0; bottom:0; */
    z-index: 999;
}

/* 容器定位 */
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

/* 選單排列 */
.fab-menu {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 12px;
    margin-bottom: 8px;
}

/* 覆寫 Element Plus 按鈕樣式，加入浮空陰影與 Hover 放大效果 */
.shadow-hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    transition:
        transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275),
        background-color 0.3s !important;
}

.shadow-hover:hover {
    transform: scale(1.08);
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
