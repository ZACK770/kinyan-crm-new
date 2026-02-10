export interface User {
  id: number
  email: string
  full_name: string
  role_name: string
  permission_level: number
  avatar_url?: string
  last_login?: string
  created_at: string
  is_active: boolean
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  full_name: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface PasswordResetRequest {
  email: string
}

export interface PasswordReset {
  token: string
  new_password: string
}

export interface GoogleAuthRequest {
  auth_code?: string
  id_token?: string
}

export type UserRole = 'pending' | 'viewer' | 'editor' | 'manager' | 'admin'