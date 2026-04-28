const KEYS = {
    APP_LANG: 'app_lang',
    APP_THEME: 'app_theme'
} as const

export const storage = {
    appLang: {
        get: (): 'zh' | 'en' | null =>
            localStorage.getItem(KEYS.APP_LANG) as 'zh' | 'en' | null,
        set: (v: 'zh' | 'en') => localStorage.setItem(KEYS.APP_LANG, v),
        clear: () => localStorage.removeItem(KEYS.APP_LANG)
    },
    appTheme: {
        get: (): 'light' | 'dark' | 'system' | null =>
            localStorage.getItem(KEYS.APP_THEME) as
                | 'light'
                | 'dark'
                | 'system'
                | null,
        set: (v: 'light' | 'dark' | 'system') =>
            localStorage.setItem(KEYS.APP_THEME, v),
        clear: () => localStorage.removeItem(KEYS.APP_THEME)
    }
}
