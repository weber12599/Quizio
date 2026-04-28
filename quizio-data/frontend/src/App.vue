<template>
    <el-config-provider :locale="epLocale">
        <router-view />
    </el-config-provider>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTheme } from './composables/useTheme'
import zhTw from 'element-plus/es/locale/lang/zh-tw'
import en from 'element-plus/es/locale/lang/en'

const { locale } = useI18n()
const epLocale = computed(() => (locale.value === 'zh' ? zhTw : en))
const { initTheme } = useTheme()

onMounted(() => {
    initTheme()
})
</script>

<style>
/* Reset default browser margins so our layout takes full screen */
body {
    margin: 0;
    padding: 0;
    font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
        'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
    background-color: var(--el-bg-color-page);
}

#app {
    height: 100vh;
    width: 100vw;
}
</style>
