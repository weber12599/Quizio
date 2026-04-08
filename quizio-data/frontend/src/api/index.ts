import axios from 'axios'
import router from '../router'

// Create a centralized Axios instance
const api = axios.create({
    baseURL: '/api',
    timeout: 10000
})

// Request Interceptor: Auto-attach token to headers
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token')
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Response Interceptor: Global error handling (e.g., 401 Unauthorized)
api.interceptors.response.use(
    (response) => {
        return response
    },
    (error) => {
        if (error.response && error.response.status === 401) {
            console.warn('Unauthorized. Redirecting to login...')
            localStorage.removeItem('token')
            // Prevent infinite loop if already on login page
            if (router.currentRoute.value.path !== '/login') {
                router.push('/login')
            }
        }
        return Promise.reject(error)
    }
)

export interface MediaUploadResponse {
    fid: string
    filename: string
    content_type: string
    size: number
    url: string
}

export interface ExamGradeHeader {
    id: number
    title: string
    target_date: string | null
    max_attempts: number
}

export interface SubmissionScoreDetail {
    submission_id: number
    score: number
    record_at: string | null
}

export interface StudentGradeEntry {
    student_db_id: number | null
    student_id: string
    name: string
    class_name: string | null
    exam_submissions: Record<string, SubmissionScoreDetail[]>
}

export interface GradeReportResponse {
    exams: ExamGradeHeader[]
    students: StudentGradeEntry[]
}

export interface Student {
    id: number
    student_id: string
    name: string
    email?: string | null
    admission_year?: number | null
    class_name?: string | null
    teacher_id?: number | null
}

/**
 * Upload a media file to the backend, which proxies it to SeaweedFS
 * @param file The file object to upload (preferably compressed WebP)
 * @returns A Promise resolving to the upload response containing the fid
 */
export const uploadMedia = async (file: File): Promise<MediaUploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/media/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })

    return response.data
}

/**
 * Fetch all distinct classes for the current teacher
 */
export const getTeacherClasses = () => {
    return api.get<string[]>('/students/classes')
}

/**
 * Fetch the pivot table grade report
 */
export const getGradeReport = (params: {
    class_name?: string
    student_id?: string
    date_start?: string
    date_end?: string
    exam_ids?: number[]
}) => {
    return api.get<GradeReportResponse>('/submissions/', {
        params,
        paramsSerializer: { indexes: null }
    })
}

/**
 * Fetch all students for the current teacher.
 * Can be optionally filtered by class_name or admission_year.
 */
export const getStudents = (params?: {
    class_name?: string
    admission_year?: number
}) => {
    return api.get<Student[]>('/students/', { params })
}

/**
 * Fetch all exams (used for the multiple select filter)
 */
export const getExams = () => {
    return api.get<any[]>('/exams/')
}

/**
 * Fetch detailed submission including answers and questions for a specific student and exam
 */
export const getSubmissionDetails = (submissionId: number) => {
    return api.get<any>(`/submissions/details/${submissionId}`)
}

/**
 * Manually update a student's score for a specific answer
 */
export const gradeStudentAnswer = (answerId: number, score: number) => {
    return api.put<any>(`/submissions/answers/${answerId}/grade`, { score })
}

export default api
