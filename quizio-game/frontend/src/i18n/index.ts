// src/i18n/index.ts
import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import zh from './locales/zh.json'
import { storage } from '../utils/storage'

// Define the messages structure
const messages = {
    en,
    zh
}

// Create i18n instance
const i18n = createI18n({
    legacy: false, // Must set to false to use Composition API
    locale: storage.appLang.get() ?? 'zh',
    fallbackLocale: 'en',
    messages
})

export default i18n
