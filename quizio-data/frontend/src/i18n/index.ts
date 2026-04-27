import { createI18n } from 'vue-i18n'
import zh from './locales/zh.json'
import en from './locales/en.json'
import { storage } from '../utils/storage'

const i18n = createI18n({
    legacy: false,
    locale: storage.appLang.get() ?? 'zh',
    fallbackLocale: 'en',
    messages: { zh, en },
})

export default i18n
