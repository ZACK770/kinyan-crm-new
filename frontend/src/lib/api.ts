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

    console.log(`🌐 [API] Starting request`, {
      method: options?.method || 'GET',
      url: url,
      path: path,
      cleanPath: cleanPath,
      hasAuth: !!this.authToken,
      headers: this.getHeaders(options?.headers)
    })

    if (options?.body) {
      console.log(`📤 [API] Request body:`, options.body)
    }

    const startTime = performance.now()
    
    try {
      const res = await fetch(url, {
        headers: this.getHeaders(options?.headers),
        ...options,
      })

      const endTime = performance.now()
      const duration = `${(endTime - startTime).toFixed(2)}ms`

      console.log(`📡 [API] Response received`, {
        status: res.status,
        statusText: res.statusText,
        ok: res.ok,
        duration: duration,
        url: url,
        headers: Object.fromEntries(res.headers.entries())
      })

      if (!res.ok) {
        let message = `שגיאה ${res.status}`
        let errorBody: any = null
        
        try {
          errorBody = await res.json()
          console.log(`❌ [API] Error response body:`, errorBody)
          
          // Handle Pydantic validation errors (FastAPI)
          if (Array.isArray(errorBody.detail)) {
            message = errorBody.detail.map((e: any) => e.msg || e.message).join(', ')
          } else if (typeof errorBody.detail === 'string') {
            message = errorBody.detail
          } else if (errorBody.message) {
            message = errorBody.message
          }
        } catch (parseErr) {
          console.log(`⚠️ [API] Could not parse error response as JSON:`, parseErr)
        }
        
        const err: ApiError = { status: res.status, message }
        console.error(`❌ [API] Request failed:`, {
          url: url,
          status: res.status,
          message: message,
          errorBody: errorBody,
          duration: duration
        })
        throw err
      }

      // Handle 204 No Content
      if (res.status === 204) {
        console.log(`✅ [API] Request successful (204 No Content)`, { url, duration })
        return undefined as T
      }

      const responseData = await res.json()
      console.log(`✅ [API] Request successful`, {
        url: url,
        status: res.status,
        duration: duration,
        responseData: responseData
      })

      return responseData
    } catch (err) {
      const endTime = performance.now()
      const duration = `${(endTime - startTime).toFixed(2)}ms`
      
      console.error(`❌ [API] Network or parsing error:`, {
        url: url,
        error: err,
        message: err instanceof Error ? err.message : 'Unknown error',
        duration: duration
      })
      throw err
    }
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
