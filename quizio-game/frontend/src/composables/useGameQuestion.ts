import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

export function useGameQuestion(props: any, emit: any) {
    const { t } = useI18n()

    // --- Answer V-Model Logic ---
    const localAnswer = computed({
        get() {
            if (
                props.question.type === 'multiple' &&
                !Array.isArray(props.modelValue)
            ) {
                return []
            }
            return props.modelValue
        },
        set(val) {
            emit('update:modelValue', val)
        }
    })

    // --- Question Type Checks ---
    const isBooleanType = computed(() =>
        ['boolean'].includes(props.question.type)
    )
    const isChoiceType = computed(() =>
        ['single', 'multiple', 'boolean'].includes(props.question.type)
    )
    const isSingleChoice = computed(() =>
        ['single', 'boolean'].includes(props.question.type)
    )

    // --- Options Parsing ---
    const options = computed(() => {
        let optsRaw = props.question.options
        let parsedOpts: string[] = []
        if (Array.isArray(optsRaw)) {
            parsedOpts = optsRaw
        } else if (typeof optsRaw === 'string') {
            try {
                const parsed = JSON.parse(optsRaw)
                if (Array.isArray(parsed)) parsedOpts = parsed
                else
                    parsedOpts = Object.entries(parsed).map(
                        ([k, v]) => `${k}: ${v}`
                    )
            } catch {
                parsedOpts = []
            }
        }
        if (props.question.type === 'boolean' && parsedOpts.length === 0) {
            return [t('common.true_option'), t('common.false_option')]
        }
        return parsedOpts
    })

    // --- Grading Logic ---
    const isCorrectOption = (idx: number) => {
        const refAns = props.question.reference_answer
        if (refAns === undefined || refAns === null || refAns === '')
            return false

        if (props.question.type === 'multiple') {
            if (!Array.isArray(refAns)) return false
            return refAns.map(String).includes(String(idx))
        }

        if (props.question.type === 'boolean') {
            const isTrueAns =
                String(refAns).toLowerCase() === 'true' ||
                refAns === true ||
                refAns === 1 ||
                refAns === '1'
            return isTrueAns ? idx === 0 : idx === 1
        }

        return String(refAns).trim() === String(idx).trim()
    }

    const bannerType = computed(() => {
        if (props.gradingResult?.is_correct === true) return 'success'
        if (props.gradingResult?.is_correct === false) return 'error'
        return 'info' // null, undefined (Needs manual grading)
    })

    const bannerIcon = computed(() => '')

    const bannerText = computed(() => {
        if (props.gradingResult?.is_correct === true) return t('banner.correct')
        if (props.gradingResult?.is_correct === false)
            return t('banner.incorrect')
        return t('banner.pending_review') // null, undefined
    })

    const getGradingClass = (idx: number) => {
        if (!props.gradingResult) return ''

        const valToCheck = props.question.type === 'boolean' ? idx === 0 : idx
        const stuAns = props.submittedAnswer
        const corrAns = props.gradingResult.correct_answer

        let isStuSelected = false
        let isCorrectAns = false

        // Check if option is the correct answer
        if (props.question.type === 'multiple' && Array.isArray(corrAns)) {
            isCorrectAns = corrAns.map(String).includes(String(valToCheck))
        } else {
            isCorrectAns = String(corrAns) === String(valToCheck)
        }

        // Check if student selected this option
        if (Array.isArray(stuAns)) {
            isStuSelected = stuAns.map(String).includes(String(valToCheck))
        } else {
            isStuSelected = String(stuAns) === String(valToCheck)
        }

        if (isStuSelected && isCorrectAns)
            return 'border-success bg-success-light'
        if (isStuSelected && !isCorrectAns)
            return 'border-danger bg-danger-light'
        if (!isStuSelected && isCorrectAns)
            return 'border-dashed-success bg-success-light-alt'

        return ''
    }

    const getGradingIcon = (idx: number) => {
        const cls = getGradingClass(idx)
        if (cls.includes('border-success')) return '✅'
        if (cls.includes('border-danger')) return '❌'
        if (cls.includes('border-dashed-success')) return '🎯'
        return '⬜'
    }

    // --- Stats Logic ---
    const getStatPercentage = (idx: number | string) => {
        if (!props.stats || props.stats.total === 0) return 0
        const count = props.stats.counts[idx] || 0
        return Math.round((count / props.stats.total) * 100)
    }

    return {
        localAnswer,
        isBooleanType,
        isChoiceType,
        isSingleChoice,
        options,
        isCorrectOption,
        bannerType,
        bannerIcon,
        bannerText,
        getGradingClass,
        getGradingIcon,
        getStatPercentage
    }
}
