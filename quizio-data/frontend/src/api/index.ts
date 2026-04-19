import axios from 'axios'
import router from '../router'
import type { TokenResponse } from './types/auth'
import type { UserCreate, UserResponse, UserUpdate } from './types/users'
import type { MediaUploadResponse } from './types/media'
import type {
    StudentCreate,
    StudentResponse,
    StudentsGet,
    StudentUpdate
} from './types/students'
import type {
    QuestionCreate,
    QuestionResponse,
    QuestionsGet,
    QuestionUpdate
} from './types/questions'
import type {
    ExamCreate,
    ExamResponse,
    ExamsGet,
    ExamUpdate
} from './types/exams'
import type {
    GetGradeReport,
    GradeReportResponse,
    StudentAnswerResponse,
    StudentSubmissionResponse
} from './types/submissions'

// Create a centralized Axios instance
const instance = axios.create({
    baseURL: '/api',
    timeout: 10000
})

// Request Interceptor: Auto-attach token to headers
instance.interceptors.request.use(
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
instance.interceptors.response.use(
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

export interface ApiError {
    response?: {
        status: number
        data?: {
            detail?: string
        }
    }
}

const dataAPI = {
    // Auth
    verifyUser: async (username: string, password: string) => {
        const formData = new URLSearchParams()
        formData.append('username', username)
        formData.append('password', password)

        return await instance.post<TokenResponse>('/auth/login', formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        })
    },
    // Media
    uploadMedia: async (file: File): Promise<MediaUploadResponse> => {
        const formData = new FormData()
        formData.append('file', file)

        const response = await instance.post('/media/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })

        return response.data
    },
    // User
    getUsers: async () => {
        return await instance.get<UserResponse[]>('/users/')
    },
    getMe: async () => {
        return await instance.get<UserResponse>('/users/me')
    },
    createUser: async (data: UserCreate) => {
        return await instance.post<UserResponse>('/users/', data)
    },
    updateUser: async (id: number, data: UserUpdate) => {
        return await instance.put<UserResponse>(`/users/${id}`, data)
    },
    restoreUser: async (id: number) => {
        return await instance.post<UserResponse>(`/users/${id}/restore`)
    },
    deleteUser: async (id: number) => {
        return await instance.delete(`/users/${id}`)
    },
    // Student
    getTeacherClasses: async () => {
        return await instance.get<string[]>('/students/classes')
    },
    getStudents: async (params: StudentsGet) => {
        return await instance.get<StudentResponse[]>('/students/', { params })
    },
    getStudent: async (id: number) => {
        return await instance.get<StudentResponse>(`/students/${id}`)
    },
    createStudent: async (data: StudentCreate) => {
        return await instance.post<StudentResponse>('/students/', data)
    },
    updateStudent: async (id: number, data: StudentUpdate) => {
        return await instance.put<StudentResponse>(`/students/${id}`, data)
    },
    restoreStudent: async (id: number) => {
        return await instance.post<StudentResponse>(`/students/${id}/restore`)
    },
    deleteStudent: async (id: number) => {
        return await instance.delete(`/students/${id}`)
    },
    // Question
    getQuestions: async (params: QuestionsGet) => {
        return await instance.get<QuestionResponse[]>('/questions/', { params })
    },
    getQuestion: async (id: number) => {
        return await instance.get<QuestionResponse>(`/questions/${id}`)
    },
    createQuestion: async (data: QuestionCreate) => {
        return await instance.post<QuestionResponse>('/questions/', data)
    },
    updateQuestion: async (id: number, data: QuestionUpdate) => {
        return await instance.put<QuestionResponse>(`/questions/${id}`, data)
    },
    lockQuestion: async (id: number) => {
        return await instance.post<QuestionResponse>(`/questions/${id}/lock`)
    },
    archiveQuestion: async (id: number, is_archived: boolean) => {
        return await instance.put<QuestionResponse>(
            `/questions/${id}/archive`,
            null,
            {
                params: { is_archived: is_archived }
            }
        )
    },
    restoreQuestion: async (id: number) => {
        return await instance.post<QuestionResponse>(`/questions/${id}/restore`)
    },
    deleteQuestion: async (id: number) => {
        return await instance.delete(`/questions/${id}`)
    },
    // Exam
    getExams: async (params: ExamsGet) => {
        return await instance.get<ExamResponse[]>('/exams/', { params })
    },
    getExam: async (id: number) => {
        return await instance.get<ExamResponse>(`/exams/${id}`)
    },
    createExam: async (data: ExamCreate) => {
        return await instance.post<ExamResponse>('/exams/', data)
    },
    updateExam: async (id: number, data: ExamUpdate) => {
        return await instance.put<ExamResponse>(`/exams/${id}`, data)
    },
    lockExam: async (id: number) => {
        return await instance.post<ExamResponse>(`/exams/${id}/lock`)
    },
    archiveExam: async (id: number, is_archived: boolean) => {
        return await instance.put<ExamResponse>(`/exams/${id}/archive`, null, {
            params: { is_archived: is_archived }
        })
    },
    restoreExam: async (id: number) => {
        return await instance.post<ExamResponse>(`/exams/${id}/restore`)
    },
    deleteExam: async (id: number) => {
        return await instance.delete(`/exams/${id}`)
    },
    // Submission
    getGradeReport: async (params: GetGradeReport) => {
        return await instance.get<GradeReportResponse>('/submissions/', {
            params,
            paramsSerializer: { indexes: null }
        })
    },
    getSubmissionDetails: async (submissionId: number) => {
        return await instance.get<StudentSubmissionResponse>(
            `/submissions/${submissionId}`
        )
    },
    gradeStudentAnswer: async (answerId: number, score: number) => {
        return await instance.put<StudentAnswerResponse>(
            `/submissions/answers/${answerId}/grade`,
            {
                score
            }
        )
    }
}

export default dataAPI
