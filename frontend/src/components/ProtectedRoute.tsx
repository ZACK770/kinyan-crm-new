import { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

interface ProtectedRouteProps {
  children: ReactNode
  requiredRole?: string
  requiredPermission?: number
  fallback?: ReactNode
}

export function ProtectedRoute({ 
  children, 
  requiredRole, 
  requiredPermission, 
  fallback 
}: ProtectedRouteProps) {
  const { user, loading, isAuthenticated } = useAuth()
  const location = useLocation()

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '200px' 
      }}>
        <div>טוען...</div>
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to=\"/auth/login\" state={{ from: location }} replace />
  }

  // Check if user account is pending
  if (user?.role_name === 'pending') {
    return <Navigate to=\"/welcome\" replace />
  }

  // Check role requirement
  if (requiredRole && user?.role_name !== requiredRole) {
    if (fallback) {
      return <>{fallback}</>
    }
    return (
      <div style={{ 
        padding: '2rem', 
        textAlign: 'center', 
        color: '#dc2626' 
      }}>
        <h2>אין הרשאה</h2>
        <p>אין לך הרשאה לצפות בעמוד זה. נדרש תפקיד: {requiredRole}</p>
      </div>
    )
  }

  // Check permission level requirement
  if (requiredPermission !== undefined && (user?.permission_level || 0) < requiredPermission) {
    if (fallback) {
      return <>{fallback}</>
    }
    return (
      <div style={{ 
        padding: '2rem', 
        textAlign: 'center', 
        color: '#dc2626' 
      }}>
        <h2>אין הרשאה</h2>
        <p>אין לך הרשאה לצפות בעמוד זה. נדרש רמת הרשאה: {requiredPermission}</p>
      </div>
    )
  }

  return <>{children}</>
}

// Helper components for common permission checks
export function AdminRoute({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute requiredPermission={40}>
      {children}
    </ProtectedRoute>
  )
}

export function ManagerRoute({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute requiredPermission={30}>
      {children}
    </ProtectedRoute>
  )
}

export function EditorRoute({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute requiredPermission={20}>
      {children}
    </ProtectedRoute>
  )
}

export function ViewerRoute({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute requiredPermission={10}>
      {children}
    </ProtectedRoute>
  )
}