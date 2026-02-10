/**
 * Hook for loading entity reference data (courses, campaigns, salespeople, etc.)
 * Used for dropdowns and entity linking throughout the app
 */
import { useState, useEffect, useCallback } from 'react'
import { api } from '@/lib/api'
import type { Course, Campaign, Salesperson } from '@/types'

// Types for reference data
export interface ReferenceData {
  courses: Course[]
  campaigns: Campaign[]
  salespeople: Salesperson[]
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
}

// Singleton cache for reference data
let cachedData: {
  courses: Course[]
  campaigns: Campaign[]
  salespeople: Salesperson[]
  timestamp: number
} | null = null

const CACHE_TTL = 5 * 60 * 1000  // 5 minutes

/**
 * Load all reference data for dropdowns
 */
export function useEntityData(): ReferenceData {
  const [courses, setCourses] = useState<Course[]>(cachedData?.courses ?? [])
  const [campaigns, setCampaigns] = useState<Campaign[]>(cachedData?.campaigns ?? [])
  const [salespeople, setSalespeople] = useState<Salesperson[]>(cachedData?.salespeople ?? [])
  const [loading, setLoading] = useState(!cachedData)
  const [error, setError] = useState<string | null>(null)

  const loadData = useCallback(async (force = false) => {
    // Use cache if fresh
    if (!force && cachedData && Date.now() - cachedData.timestamp < CACHE_TTL) {
      setCourses(cachedData.courses)
      setCampaigns(cachedData.campaigns)
      setSalespeople(cachedData.salespeople)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const [coursesRes, campaignsRes, salespeopleRes] = await Promise.all([
        api.get<Course[]>('courses').catch(() => []),
        api.get<Campaign[]>('campaigns').catch(() => []),
        api.get<Salesperson[]>('leads/salespersons').catch(() => []),
      ])

      setCourses(coursesRes)
      setCampaigns(campaignsRes)
      setSalespeople(salespeopleRes)

      // Update cache
      cachedData = {
        courses: coursesRes,
        campaigns: campaignsRes,
        salespeople: salespeopleRes,
        timestamp: Date.now(),
      }
    } catch (err) {
      setError((err as { message?: string }).message ?? 'שגיאה בטעינת נתונים')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const refresh = useCallback(async () => {
    await loadData(true)
  }, [loadData])

  return { courses, campaigns, salespeople, loading, error, refresh }
}

/**
 * Get course by ID with price info
 */
export function getCourseInfo(courses: Course[], courseId: number | undefined) {
  if (!courseId) return null
  const course = courses.find(c => c.id === courseId)
  return course ?? null
}
