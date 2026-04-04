<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()

// State to track if the FAB menu is expanded
const isOpen = ref(false)

// Toggle the entire FAB menu
const toggleMenu = () => {
    isOpen.value = !isOpen.value
}

// Language toggle action
const toggleLanguage = () => {
    const newLang = locale.value === 'zh' ? 'en' : 'zh'
    locale.value = newLang
    localStorage.setItem('app_lang', newLang)

    // Auto close the menu after clicking
    isOpen.value = false
}
</script>

<template>
    <div v-if="isOpen" class="fab-overlay" @click="isOpen = false"></div>

    <div class="fab-container">
        <transition name="fab-slide">
            <div v-if="isOpen" class="fab-menu">
                <button @click="toggleLanguage" class="fab-item">
                    <span class="icon">🌐</span>
                    <span class="label">{{
                        locale === 'zh' ? 'English' : '中文'
                    }}</span>
                </button>
            </div>
        </transition>

        <button
            @click="toggleMenu"
            class="fab-main"
            :class="{ 'is-open': isOpen }"
        >
            <div class="fab-icon-hamburger">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </button>
    </div>
</template>

<style scoped>
/* Full screen invisible overlay to capture outside clicks */
.fab-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 999;
}

/* FAB Container fixed to the bottom right */
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

/* Menu list styles */
.fab-menu {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 12px;
    margin-bottom: 8px;
}

/* Individual tool button (Pill shaped) */
.fab-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 18px;
    border-radius: 24px;
    background-color: var(--bg-card, #ffffff);
    color: var(--text-main, #333333);
    border: 2px solid var(--border-color, #e5e7eb);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    cursor: pointer;
    font-weight: 600;
    font-size: 0.95rem;
    transition: all 0.2s ease;
    white-space: nowrap;
}

.fab-item:hover {
    border-color: var(--primary-color, #4f46e5);
    color: var(--primary-color, #4f46e5);
    transform: scale(1.05);
}

/* Main floating button */
.fab-main {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background-color: var(--primary-color, #4f46e5);
    border: none;
    box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4);
    cursor: pointer;
    display: flex;
    justify-content: center;
    align-items: center;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.fab-main:hover {
    transform: scale(1.1);
    background-color: var(--primary-hover, #4338ca);
}

/* State when menu is open: Turns red */
.fab-main.is-open {
    background-color: var(--danger-color, #ef4444);
    box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4);
}

/* Animated Hamburger Icon */
.fab-icon-hamburger {
    width: 24px;
    height: 18px;
    position: relative;
    transform: rotate(0deg);
    transition: 0.5s ease-in-out;
}

.fab-icon-hamburger span {
    display: block;
    position: absolute;
    height: 3px;
    width: 100%;
    background: white;
    border-radius: 3px;
    opacity: 1;
    left: 0;
    transform: rotate(0deg);
    transition: 0.25s ease-in-out;
}

/* Initial state (Hamburger '≡') */
.fab-icon-hamburger span:nth-child(1) {
    top: 0px;
}
.fab-icon-hamburger span:nth-child(2) {
    top: 7.5px;
}
.fab-icon-hamburger span:nth-child(3) {
    top: 15px;
}

/* Open state (Transforms to 'X') */
.fab-main.is-open .fab-icon-hamburger span:nth-child(1) {
    top: 7.5px;
    transform: rotate(135deg);
}

.fab-main.is-open .fab-icon-hamburger span:nth-child(2) {
    opacity: 0;
    left: -10px; /* Slides out slightly while fading */
}

.fab-main.is-open .fab-icon-hamburger span:nth-child(3) {
    top: 7.5px;
    transform: rotate(-135deg);
}

/* Vue Transition Animations */
.fab-slide-enter-active,
.fab-slide-leave-active {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    transform-origin: bottom right;
}

.fab-slide-enter-from,
.fab-slide-leave-to {
    opacity: 0;
    transform: translateY(20px) scale(0.9);
}
</style>
