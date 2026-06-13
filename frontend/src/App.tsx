import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from '@/components/ProtectedRoute'
import AppLayout from '@/components/AppLayout'

// Public pages
import Login from '@/pages/Login'
import Register from '@/pages/Register'

// Protected pages
import DashboardPage from '@/pages/DashboardPage'
import NotFoundPage from '@/pages/NotFoundPage'

// Lazy-loaded protected pages (kept as stubs for now)
import AICoach from '@/pages/AICoach'
import Goals from '@/pages/Goals'
import HabitTracker from '@/pages/HabitTracker'
import EmissionsPage from '@/pages/EmissionsPage'
import ReportsPage from '@/pages/ReportsPage'
import OrganizationPage from '@/pages/OrganizationPage'
import SettingsPage from '@/pages/SettingsPage'
import AssessmentForm from '@/pages/AssessmentForm'
import AssessmentHistory from '@/pages/AssessmentHistory'
import AssessmentDetail from '@/pages/AssessmentDetail'
import Simulator from '@/pages/Simulator'
import SimulatorHistory from '@/pages/SimulatorHistory'
import { Forecast } from '@/pages/Forecast'

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login"    element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Protected routes — require valid JWT in AuthContext */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard"           element={<DashboardPage />} />
          <Route path="/assessment"           element={<AssessmentForm />} />
          <Route path="/assessment/history"   element={<AssessmentHistory />} />
          <Route path="/assessment/history/:id" element={<AssessmentDetail />} />
          <Route path="/simulator"              element={<Simulator />} />
          <Route path="/simulator/history"      element={<SimulatorHistory />} />
          <Route path="/forecast"               element={<Forecast />} />
          <Route path="/coach"                  element={<AICoach />} />
          <Route path="/goals"                  element={<Goals />} />
          <Route path="/habits"                 element={<HabitTracker />} />
          <Route path="/emissions"    element={<EmissionsPage />} />
          <Route path="/reports"      element={<ReportsPage />} />
          <Route path="/organization" element={<OrganizationPage />} />
          <Route path="/settings"     element={<SettingsPage />} />
        </Route>
      </Route>

      {/* Root redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* 404 */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default App
