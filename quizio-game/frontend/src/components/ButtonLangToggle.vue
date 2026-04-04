<template>
    <button @click="toggleLanguage" class="btn-lang-toggle">
        <span class="icon">🌐</span>
        {{ locale === 'zh' ? 'English' : '中文' }}
    </button>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

// Extract locale from useI18n
const { locale } = useI18n()

// Function to toggle language and save preference to localStorage
const toggleLanguage = () => {
    const newLang = locale.value === 'zh' ? 'en' : 'zh'
    locale.value = newLang
    localStorage.setItem('app_lang', newLang)
}
</script>

<style scoped>
/* Basic styling for the toggle button, you can adjust to match your UI */
.btn-lang-toggle {
    position: absolute;
    top: 20px;
    right: 20px;
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    border-radius: 20px;
    background-color: var(--primary-color, #4f46e5);
    color: white;
    border: none;
    cursor: pointer;
    font-weight: 600;
    transition:
        background-color 0.2s,
        transform 0.1s;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.btn-lang-toggle:hover {
    background-color: var(--primary-hover, #4338ca);
    transform: translateY(-1px);
}
</style>
