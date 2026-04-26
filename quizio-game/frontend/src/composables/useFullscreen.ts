import { ref, readonly } from 'vue'

const isFullscreen = ref(!!document.fullscreenElement)

document.addEventListener('fullscreenchange', () => {
    isFullscreen.value = !!document.fullscreenElement
})

export function useFullscreen() {
    async function toggleFullscreen(): Promise<void> {
        if (document.fullscreenElement) {
            await document.exitFullscreen()
        } else {
            await document.documentElement.requestFullscreen()
        }
    }

    return { isFullscreen: readonly(isFullscreen), toggleFullscreen }
}
