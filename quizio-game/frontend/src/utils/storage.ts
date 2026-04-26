const KEYS = {
    APP_LANG:      'app_lang',
    APP_THEME:     'app_theme',
    APP_FONT_SIZE: 'app_font_size',
    HOST_TOKEN:    'host_token',
    SETUP_DATA:    'setup_data',
    STUDENT_CREDS: 'quizio_student_creds',
    UPLOAD_TOKEN:  'quizio_upload_token',
    SCREEN_PIN:    'quizio_screen_pin',
} as const

export interface StudentCreds {
    pin: string
    sid: string
    pwd: string
    gname: string
    isGuest: boolean
    player_id?: string
}

export interface SetupData {
    room_pin: string
    exam_id: number | null
    target_class: string
    allow_guests: boolean
    expected_students: string[]
    expected_student_info: Record<string, string>
}

function parseJson<T>(key: string): T | null {
    const raw = localStorage.getItem(key)
    if (!raw) return null
    try { return JSON.parse(raw) as T } catch { return null }
}

export const storage = {
    appLang: {
        get: (): 'zh' | 'en' | null => localStorage.getItem(KEYS.APP_LANG) as 'zh' | 'en' | null,
        set: (v: 'zh' | 'en') => localStorage.setItem(KEYS.APP_LANG, v),
        clear: () => localStorage.removeItem(KEYS.APP_LANG),
    },
    appTheme: {
        get: (): 'light' | 'dark' | 'system' | null =>
            localStorage.getItem(KEYS.APP_THEME) as 'light' | 'dark' | 'system' | null,
        set: (v: 'light' | 'dark' | 'system') => localStorage.setItem(KEYS.APP_THEME, v),
        clear: () => localStorage.removeItem(KEYS.APP_THEME),
    },
    appFontSize: {
        get: (): 'normal' | 'large' | 'xlarge' | null =>
            localStorage.getItem(KEYS.APP_FONT_SIZE) as 'normal' | 'large' | 'xlarge' | null,
        set: (v: 'normal' | 'large' | 'xlarge') => localStorage.setItem(KEYS.APP_FONT_SIZE, v),
        clear: () => localStorage.removeItem(KEYS.APP_FONT_SIZE),
    },
    hostToken: {
        get: (): string | null => localStorage.getItem(KEYS.HOST_TOKEN),
        set: (v: string) => localStorage.setItem(KEYS.HOST_TOKEN, v),
        clear: () => localStorage.removeItem(KEYS.HOST_TOKEN),
    },
    setupData: {
        get: (): SetupData | null => parseJson<SetupData>(KEYS.SETUP_DATA),
        set: (v: SetupData) => localStorage.setItem(KEYS.SETUP_DATA, JSON.stringify(v)),
        clear: () => localStorage.removeItem(KEYS.SETUP_DATA),
    },
    studentCreds: {
        get: (): StudentCreds | null => parseJson<StudentCreds>(KEYS.STUDENT_CREDS),
        set: (v: StudentCreds) => localStorage.setItem(KEYS.STUDENT_CREDS, JSON.stringify(v)),
        clear: () => localStorage.removeItem(KEYS.STUDENT_CREDS),
    },
    uploadToken: {
        get: (): string | null => localStorage.getItem(KEYS.UPLOAD_TOKEN),
        set: (v: string) => localStorage.setItem(KEYS.UPLOAD_TOKEN, v),
        clear: () => localStorage.removeItem(KEYS.UPLOAD_TOKEN),
    },
    screenPin: {
        get: (): string | null => localStorage.getItem(KEYS.SCREEN_PIN),
        set: (v: string) => localStorage.setItem(KEYS.SCREEN_PIN, v),
        clear: () => localStorage.removeItem(KEYS.SCREEN_PIN),
    },
}
