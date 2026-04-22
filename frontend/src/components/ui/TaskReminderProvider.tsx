import { createContext, useContext, useState, useEffect, useCallback, useRef, type FC, type ReactNode } from 'react'
import { api } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import TaskReminderPopup from './TaskReminderPopup'

interface TaskData {
  id: number
  title: string
  description?: string | null
  due_date: string
}

interface TaskReminderContextType {
  checkNow: () => void
}

const TaskReminderContext = createContext<TaskReminderContextType | null>(null)

export function useTaskReminders(): TaskReminderContextType {
  const ctx = useContext(TaskReminderContext)
  if (!ctx) throw new Error('useTaskReminders must be used within TaskReminderProvider')
  return ctx
}

const CHECK_INTERVAL = 30 * 1000 // Check every 30 seconds
const DISMISSED_TASKS_KEY = 'dismissed_task_reminders'

export const TaskReminderProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth()
  const [currentTask, setCurrentTask] = useState<TaskData | null>(null)
  const [dismissedTasks, setDismissedTasks] = useState<Set<number>>(new Set())
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const mountedRef = useRef(true)

  // Load dismissed tasks from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(DISMISSED_TASKS_KEY)
      if (stored) {
        const tasks = JSON.parse(stored) as number[]
        setDismissedTasks(new Set(tasks))
      }
    } catch {
      // Ignore localStorage errors
    }
  }, [])

  // Check for due tasks
  const checkDueTasks = useCallback(async () => {
    if (!mountedRef.current) return
    if (!isAuthenticated) return
    if (currentTask) return // Don't show multiple popups at once

    try {
      const data = await api.get<TaskData[]>('/tasks/due-reminders')
      if (!mountedRef.current) return

      // Find first task that hasn't been dismissed
      const dueTask = data.find(task => !dismissedTasks.has(task.id))
      if (dueTask) {
        setCurrentTask(dueTask)
      }
    } catch {
      // Silently ignore errors
    }
  }, [isAuthenticated, currentTask, dismissedTasks])

  // Start checking when authenticated
  useEffect(() => {
    if (!isAuthenticated) return

    // Initial check after a short delay
    const initialTimeout = setTimeout(checkDueTasks, 3000)

    // Periodic checking
    timerRef.current = setInterval(checkDueTasks, CHECK_INTERVAL)

    return () => {
      clearTimeout(initialTimeout)
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [isAuthenticated, checkDueTasks])

  // Cleanup
  useEffect(() => {
    mountedRef.current = true
    return () => { mountedRef.current = false }
  }, [])

  const handleDismiss = useCallback(() => {
    if (!currentTask) return

    // Mark task as dismissed
    setDismissedTasks(prev => {
      const newSet = new Set(prev)
      newSet.add(currentTask.id)
      
      // Save to localStorage
      try {
        localStorage.setItem(DISMISSED_TASKS_KEY, JSON.stringify(Array.from(newSet)))
      } catch {
        // Ignore localStorage errors
      }
      
      return newSet
    })

    setCurrentTask(null)
  }, [currentTask])

  const checkNow = useCallback(() => {
    checkDueTasks()
  }, [checkDueTasks])

  return (
    <TaskReminderContext.Provider value={{ checkNow }}>
      {children}
      {currentTask && (
        <TaskReminderPopup task={currentTask} onDismiss={handleDismiss} />
      )}
    </TaskReminderContext.Provider>
  )
}
