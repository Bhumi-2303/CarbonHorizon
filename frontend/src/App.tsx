import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from '@/components/ProtectedRoute'

// Public pages
import Login from '@/pages/Login'
import Register from '@/pages/Register'

// Protected pages
import DashboardPage from '@/pages/DashboardPage'
import NotFoundPage from '@/pages/NotFoundPage'

// Lazy-loaded protected pages (kept as stubs for now)
import EmissionsPage from '@/pages/EmissionsPage'
import ReportsPage from '@/pages/ReportsPage'
import OrganizationPage from '@/pages/OrganizationPage'
import SettingsPage from '@/pages/SettingsPage'
import AssessmentForm from '@/pages/AssessmentForm'
import AssessmentHistory from '@/pages/AssessmentHistory'
import AssessmentDetail from '@/pages/AssessmentDetail'

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login"    element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Protected routes — require valid JWT in AuthContext */}
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard"           element={<DashboardPage />} />
        <Route path="/assessment"           element={<AssessmentForm />} />
        <Route path="/assessment/history"   element={<AssessmentHistory />} />
        <Route path="/assessment/history/:id" element={<AssessmentDetail />} />
        <Route path="/emissions"    element={<EmissionsPage />} />
        <Route path="/reports"      element={<ReportsPage />} />
        <Route path="/organization" element={<OrganizationPage />} />
        <Route path="/settings"     element={<SettingsPage />} />
      </Route>

      {/* Root redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* 404 */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default App
