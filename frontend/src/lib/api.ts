/* ============================================================
   API Client — clean fetch wrapper for the FastAPI backend
   ============================================================ */

// Single server - frontend and API are on the same origin!
// Always use relative path - no need for VITE_API_URL
const BASE = '/api'

interface ApiError {
  status: number
  message: string
}

class ApiClient {
  private authToken: string | null = null

  setAuthToken(token: string | null) {
    this.authToken = token
  }

  private getHeaders(customHeaders?: HeadersInit): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    if (customHeaders) {
      if (customHeaders instanceof Headers) {
        customHeaders.forEach((v, k) => { headers[k] = v })
      } else if (Array.isArray(customHeaders)) {
        customHeaders.forEach(([k, v]) => { headers[k] = v })
      } else {
        Object.assign(headers, customHeaders)
      }
    }

    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`
    }

    return headers
  }

  async request<T>(path: string, options?: RequestInit): Promise<T> {
    // Always prepend BASE (/api) unless path already includes it
    const cleanPath = path.startsWith('/') ? path : `/${path}`
    const url = cleanPath.startsWith(BASE) ? cleanPath : `${BASE}${cleanPath}`

    const res = await fetch(url, {
      headers: this.getHeaders(options?.headers),
      ...options,
    })

    if (!res.ok) {
      let message = `שגיאה ${res.status}`
      try {
        const body = await res.json()
        // Handle Pydantic validation errors (FastAPI)
        if (Array.isArray(body.detail)) {
          message = body.detail.map((e: any) => e.msg || e.message).join(', ')
        } else if (typeof body.detail === 'string') {
          message = body.detail
        } else if (body.message) {
          message = body.message
        }
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

  async upload<T>(path: string, formData: FormData): Promise<T> {
    const cleanPath = path.startsWith('/') ? path : `/${path}`
    const url = cleanPath.startsWith(BASE) ? cleanPath : `${BASE}${cleanPath}`

    const headers: Record<string, string> = {}
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`
    }

    const res = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    })

    if (!res.ok) {
      let message = `שגיאה ${res.status}`
      try {
        const body = await res.json()
        if (Array.isArray(body.detail)) {
          message = body.detail.map((e: any) => e.msg || e.message).join(', ')
        } else if (typeof body.detail === 'string') {
          message = body.detail
        } else if (body.message) {
          message = body.message
        }
      } catch { /* ignore */ }
      const err: ApiError = { status: res.status, message }
      throw err
    }

    return res.json()
  }
}

export const api = new ApiClient()
