<template>
    <div class="app-wrapper">
        <main class="main-content">
            <router-view></router-view>
        </main>
    </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)')
    const toggleDark = (e: MediaQueryListEvent | MediaQueryList) => {
        if (e.matches) {
            document.documentElement.classList.add('dark')
        } else {
            document.documentElement.classList.remove('dark')
        }
    }
    toggleDark(prefersDark)
    prefersDark.addEventListener('change', toggleDark)
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
