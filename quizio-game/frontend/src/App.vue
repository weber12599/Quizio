<template>
    <div class="app-wrapper">
        <main class="main-content">
            <router-view></router-view>
        </main>
    </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useTheme } from './composables/useTheme'

const { initTheme } = useTheme()

onMounted(() => {
    initTheme()
})
</script>

<style scoped>
.app-wrapper,
.main-content {
    overflow: hidden;
}

.app-wrapper {
    height: 100dvh;
}

.main-content {
    height: 100dvh;
}
</style>
