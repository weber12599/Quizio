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

                <el-button
                    round
                    size="large"
                    @click="cycleTheme"
                    class="fab-item shadow-hover"
                >
                    <el-icon :size="18" style="margin-right: 8px">
                        <component :is="themeIcon" />
                    </el-icon>
                    <span style="font-weight: bold">{{ themeLabel }}</span>
                </el-button>

                <el-button
                    v-if="isScreenRoute"
                    round
                    size="large"
                    @click="toggleFullscreen"
                    class="fab-item shadow-hover"
                >
                    <el-icon :size="18" style="margin-right: 8px">
                        <ScaleToOriginal v-if="isFullscreen" />
                        <FullScreen v-else />
                    </el-icon>
                    <span style="font-weight: bold">
                        {{ isFullscreen ? t('fab.exit_fullscreen') : t('fab.fullscreen') }}
                    </span>
                </el-button>

                <el-button
                    v-if="isScreenRoute"
                    round
                    size="large"
                    @click="cycleFontSize"
                    class="fab-item shadow-hover"
                >
                    <el-icon :size="18" style="margin-right: 8px">
                        <Rank />
                    </el-icon>
                    <span style="font-weight: bold">{{ fontSizeLabel }}</span>
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
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import {
    ArrowDown,
    Close,
    Sunny,
    Moon,
    Monitor,
    FullScreen,
    ScaleToOriginal,
    Rank,
} from '@element-plus/icons-vue'
import { storage } from '../utils/storage'
import { useTheme } from '../composables/useTheme'
import { useFullscreen } from '../composables/useFullscreen'
import packageJson from '../../package.json'

const { locale, t } = useI18n()
const route = useRoute()
const isOpen = ref(false)
const appVersion = packageJson.version

const isScreenRoute = computed(() => route.name === 'screen')

// Theme
const { themeMode, cycleTheme } = useTheme()
const themeIcon = computed(() => ({ light: Sunny, dark: Moon, system: Monitor }[themeMode.value]))
const themeLabel = computed(() => t(`fab.theme_${themeMode.value}`))

// Fullscreen
const { isFullscreen, toggleFullscreen } = useFullscreen()

// Font size
const fontSizes = ['normal', 'large', 'xlarge'] as const
type FontSize = (typeof fontSizes)[number]
const fontSize = ref<FontSize>(storage.appFontSize.get() ?? 'normal')

function cycleFontSize(): void {
    const next = fontSizes[(fontSizes.indexOf(fontSize.value) + 1) % fontSizes.length]
    fontSize.value = next
    storage.appFontSize.set(next)
    if (next === 'normal') {
        document.documentElement.removeAttribute('data-fontsize')
    } else {
        document.documentElement.setAttribute('data-fontsize', next)
    }
}

const fontSizeLabel = computed(() => t(`fab.font_${fontSize.value}`))

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
