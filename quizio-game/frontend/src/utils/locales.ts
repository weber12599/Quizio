// src/utils/helpers.ts
import i18n from '../i18n'

export const formatQuestionType = (type: string): string => {
    // Access the global t() function directly from the i18n instance
    const i18nKey = `question_type.${type}`

    // i18n.global.te checks if the key exists
    return i18n.global.te(i18nKey) ? i18n.global.t(i18nKey) : type
}
