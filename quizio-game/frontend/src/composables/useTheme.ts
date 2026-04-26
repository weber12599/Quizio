import { ref, readonly } from 'vue'
import { storage } from '../utils/storage'

export type ThemeMode = 'light' | 'dark' | 'system'

const themeMode = ref<ThemeMode>(storage.appTheme.get() ?? 'system')
const mql = window.matchMedia('(prefers-color-scheme: dark)')

function applyTheme(mode: ThemeMode): void {
    const el = document.documentElement
    el.classList.remove('dark', 'light')
    if (mode === 'dark') el.classList.add('dark')
    else if (mode === 'light') el.classList.add('light')
    else mql.matches ? el.classList.add('dark') : el.classList.add('light')
}

function handleOsChange(e: MediaQueryListEvent): void {
    if (themeMode.value !== 'system') return
    document.documentElement.classList.remove('dark', 'light')
    e.matches
        ? document.documentElement.classList.add('dark')
        : document.documentElement.classList.add('light')
}

export function useTheme() {
    function setTheme(mode: ThemeMode): void {
        themeMode.value = mode
        storage.appTheme.set(mode)
        applyTheme(mode)
    }

    function cycleTheme(): void {
        const order: ThemeMode[] = ['system', 'light', 'dark']
        setTheme(order[(order.indexOf(themeMode.value) + 1) % order.length])
    }

    function initTheme(): void {
        applyTheme(themeMode.value)
        mql.addEventListener('change', handleOsChange)
    }

    return { themeMode: readonly(themeMode), cycleTheme, initTheme }
}
