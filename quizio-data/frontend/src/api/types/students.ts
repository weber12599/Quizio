export interface StudentResponse {
    id: number
    teacher_id: number
    student_id: string
    name: string
    password: string
    email?: string | null
    admission_year?: number | null
    class_name?: string | null
    deleted_at?: string | null
}

export interface StudentsGet {
    admission_year?: number | null
    class_name?: string | null
    is_deleted?: boolean | null
}

export interface StudentCreate {
    student_id: string
    name: string
    password: string
    email?: string | null
    admission_year?: number | null
    class_name?: string | null
}

export interface StudentUpdate {
    name?: string | null
    password?: string | null
    email?: string | null
    admission_year?: number | null
    class_name?: string | null
}
