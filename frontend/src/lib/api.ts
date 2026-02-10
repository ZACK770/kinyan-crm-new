/* ============================================================
   API Client — clean fetch wrapper for the FastAPI backend
   ============================================================ */

// In production (Render), use VITE_API_URL. In dev, use relative path (Vite proxy)
const API_HOST = import.meta.env.VITE_API_URL
  ? `https://${import.meta.env.VITE_API_URL}`
  : ''
const BASE = `${API_HOST}/api`

interface ApiError {
  status: number
  message: string
}

class ApiClient {
  private authToken: string | null = null

  setAuthToken(token: string | null) {
    this.authToken = token
  }

  private getHeaders(customHeaders?: HeadersInit): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...customHeaders,
    }

    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`
    }

    return headers
  }

  async request<T>(path: string, options?: RequestInit): Promise<T> {
    const url = path.startsWith('/') ? path : `${BASE}${path}`

    const res = await fetch(url, {
      headers: this.getHeaders(options?.headers),
      ...options,
    })

    if (!res.ok) {
      let message = `שגיאה ${res.status}`
      try {
        const body = await res.json()
        message = body.detail || body.message || message
      } catch { /* ignore */ }
      const err: ApiError = { status: res.status, message }
      throw err
    }

    // Handle 204 No Content
    if (res.status === 204) return undefined as T

    return res.json()
  }

  get<T>(path: string) {
    return this.request<T>(path)
  }

  post<T>(path: string, body?: unknown) {
    return this.request<T>(path, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  patch<T>(path: string, body?: unknown) {
    return this.request<T>(path, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  put<T>(path: string, body?: unknown) {
    return this.request<T>(path, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  delete<T>(path: string) {
    return this.request<T>(path, { method: 'DELETE' })
  }
}

export const api = new ApiClient()
