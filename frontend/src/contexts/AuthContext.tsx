import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from '@/lib/api'
import type { User, AuthResponse, LoginCredentials, RegisterData, GoogleAuthRequest } from '@/types/auth'

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  googleAuth: (data: GoogleAuthRequest) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
  isAuthenticated: boolean
  hasPermission: (minLevel: number) => boolean
  hasRole: (role: string) => boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

const TOKEN_KEY = 'kinyan_auth_token'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // Check if we have a saved token on mount, or try to get user from dev mode
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      api.setAuthToken(token)
    }
    // Always try to get user - backend may have DEV_SKIP_AUTH enabled
    refreshUser().finally(() => setLoading(false))
  }, [])

  const setAuthToken = (token: string) => {
    localStorage.setItem(TOKEN_KEY, token)
    api.setAuthToken(token)
  }

  const clearAuthToken = () => {
    localStorage.removeItem(TOKEN_KEY)
    api.setAuthToken(null)
  }

  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await api.post<AuthResponse>('/auth/login', credentials)
      setAuthToken(response.access_token)
      setUser(response.user)
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  const register = async (data: RegisterData) => {
    try {
      const response = await api.post<AuthResponse>('/auth/register', data)
      setAuthToken(response.access_token)
      setUser(response.user)
    } catch (error) {
      console.error('Registration failed:', error)
      throw error
    }
  }

  const googleAuth = async (data: GoogleAuthRequest) => {
    try {
      const endpoint = data.auth_code ? '/auth/google-code' : '/auth/google-token'
      const response = await api.post<AuthResponse>(endpoint, data)
      setAuthToken(response.access_token)
      setUser(response.user)
    } catch (error) {
      console.error('Google auth failed:', error)
      throw error
    }
  }

  const logout = () => {
    clearAuthToken()
    setUser(null)
  }

  const refreshUser = async () => {
    try {
      const token = localStorage.getItem(TOKEN_KEY)
      if (token) {
        api.setAuthToken(token)
      }
      
      // Always try to get user - backend may have DEV_SKIP_AUTH enabled
      const userData = await api.get<User>('/auth/me')
      setUser(userData)
    } catch (error) {
      // Token is invalid or expired (or no dev mode)
      clearAuthToken()
      setUser(null)
      console.error('Failed to refresh user:', error)
    }
  }

  const hasPermission = (minLevel: number): boolean => {
    if (!user) return false
    return user.permission_level >= minLevel
  }

  const hasRole = (role: string): boolean => {
    if (!user) return false
    return user.role_name === role
  }

  const value: AuthContextValue = {
    user,
    loading,
    login,
    register,
    googleAuth,
    logout,
    refreshUser,
    isAuthenticated: !!user,
    hasPermission,
    hasRole,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}