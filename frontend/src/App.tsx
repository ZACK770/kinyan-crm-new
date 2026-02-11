import { Routes, Route } from 'react-router-dom'
import { AppLayout } from '@/components/layout'
import { ProtectedRoute, ViewerRoute, AdminRoute, ManagerRoute } from '@/components/ProtectedRoute'
import { LoginPage, RegisterPage, WelcomePage, GoogleCallbackPage } from '@/pages/auth'
import { Dashboard } from '@/pages/Dashboard'
import { LeadsPage } from '@/pages/Leads'
import { StudentsPage } from '@/pages/Students'
import { CoursesPage } from '@/pages/Courses'
import { PaymentsPage } from '@/pages/Payments'
import { CollectionsPage } from '@/pages/Collections'
import { CommitmentsPage } from '@/pages/Commitments'
import { CampaignsPage } from '@/pages/Campaigns'
import { TasksPage } from '@/pages/Tasks'
import { InquiriesPage } from '@/pages/Inquiries'
import { MessagesPage } from '@/pages/Messages'
import { LecturersPage } from '@/pages/Lecturers'
import { ExpensesPage } from '@/pages/Expenses'
import { AuditLogsPage } from '@/pages/AuditLogs'
import { UsersManagePage } from '@/pages/UsersManagePage'
import { SalesAssignmentRulesPage } from '@/pages/SalesAssignmentRules'
import { WebhookLogsPage } from '@/pages/WebhookLogs'
import WebhookQueue from '@/pages/WebhookQueue'
import { ImportLeadsPage } from '@/pages/ImportLeads'
import { PlaceholderPage } from '@/pages/Placeholder'
import { TracksPage } from '@/pages/TracksPage'
import { EntryPointsPage } from '@/pages/EntryPointsPage'
import EmailTemplates from '@/pages/EmailTemplates'
import { CourseTopicsPage } from '@/pages/CourseTopics'
import { TopicLessonsPage } from '@/pages/TopicLessons'
import { LessonWorkspacePage } from '@/pages/LessonWorkspace'
import { StudentPortalPage } from '@/pages/StudentPortal'

export function App() {
  return (
    <Routes>
      {/* Public Auth Routes */}
      <Route path="/auth/login" element={<LoginPage />} />
      <Route path="/auth/register" element={<RegisterPage />} />
      <Route path="/auth/google/callback" element={<GoogleCallbackPage />} />
      
      {/* Pending user welcome page */}
      <Route path="/welcome" element={<WelcomePage />} />
      
      {/* Protected App Routes */}
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <AppLayout>
              <Routes>
                <Route path="/" element={<ViewerRoute><Dashboard /></ViewerRoute>} />
                <Route path="/leads" element={<ViewerRoute><LeadsPage /></ViewerRoute>} />
                <Route path="/students" element={<ViewerRoute><StudentsPage /></ViewerRoute>} />
                <Route path="/courses" element={<ViewerRoute><CoursesPage /></ViewerRoute>} />
                <Route path="/tracks" element={<ViewerRoute><TracksPage /></ViewerRoute>} />
                <Route path="/entry-points" element={<ViewerRoute><EntryPointsPage /></ViewerRoute>} />
                <Route path="/admin/courses/:courseId/topics" element={<ManagerRoute><CourseTopicsPage /></ManagerRoute>} />
                <Route path="/admin/topics/:topicId/lessons" element={<ManagerRoute><TopicLessonsPage /></ManagerRoute>} />
                <Route path="/admin/lessons/:lessonId" element={<ManagerRoute><LessonWorkspacePage /></ManagerRoute>} />
                <Route path="/student-portal/:studentId/:courseId" element={<ViewerRoute><StudentPortalPage /></ViewerRoute>} />
                <Route path="/payments" element={<ViewerRoute><PaymentsPage /></ViewerRoute>} />
                <Route path="/collections" element={<ViewerRoute><CollectionsPage /></ViewerRoute>} />
                <Route path="/commitments" element={<ViewerRoute><CommitmentsPage /></ViewerRoute>} />
                <Route path="/campaigns" element={<ViewerRoute><CampaignsPage /></ViewerRoute>} />
                <Route path="/tasks" element={<ViewerRoute><TasksPage /></ViewerRoute>} />
                <Route path="/inquiries" element={<ViewerRoute><InquiriesPage /></ViewerRoute>} />
                <Route path="/messages" element={<ViewerRoute><MessagesPage /></ViewerRoute>} />
                <Route path="/email-templates" element={<ViewerRoute><EmailTemplates /></ViewerRoute>} />
                <Route path="/lecturers" element={<ViewerRoute><LecturersPage /></ViewerRoute>} />
                <Route path="/expenses" element={<ViewerRoute><ExpensesPage /></ViewerRoute>} />
                <Route path="/admin/users" element={<AdminRoute><UsersManagePage /></AdminRoute>} />
                <Route path="/admin/audit-logs" element={<ManagerRoute><AuditLogsPage /></ManagerRoute>} />
                <Route path="/admin/webhook-logs" element={<ManagerRoute><WebhookLogsPage /></ManagerRoute>} />
                <Route path="/admin/webhook-queue" element={<AdminRoute><WebhookQueue /></AdminRoute>} />
                <Route path="/admin/sales-assignment" element={<ManagerRoute><SalesAssignmentRulesPage /></ManagerRoute>} />
                <Route path="/admin/import-leads" element={<AdminRoute><ImportLeadsPage /></AdminRoute>} />
                <Route path="*" element={<PlaceholderPage title="הדף לא נמצא" />} />
              </Routes>
            </AppLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}
