export interface UserResponse {
    id: number
    username: string
    full_name?: string | null
    email?: string | null
    is_superuser: boolean
    deleted_at?: string | null
    created_at: string
}

export interface UserCreate {
    username: string
    password: string
    full_name?: string | null
    email?: string | null
    is_superuser: boolean
}

export interface UserUpdate {
    password?: string | null
    full_name?: string | null
    email?: string | null
}
