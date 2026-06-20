import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from '@/components/ProtectedRoute'
import AppLayout from '@/components/AppLayout'

// Public pages
import LandingPage from '@/pages/LandingPage'
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
import AssessmentResult from '@/pages/AssessmentResult'
import Simulator from '@/pages/Simulator'
import SimulatorHistory from '@/pages/SimulatorHistory'
import { Forecast } from '@/pages/Forecast'
import Profile from '@/pages/Profile'
import Journey from '@/pages/Journey'

// Tier Components
import LittleExplorerLayout from '@/components/tiers/LittleExplorerLayout'
import LittleExplorerDashboard from '@/pages/tiers/LittleExplorerDashboard'
import LittleExplorerAssessment from '@/pages/tiers/LittleExplorerAssessment'
import LittleExplorerCoach from '@/pages/tiers/LittleExplorerCoach'
import StudentLayout from '@/components/tiers/StudentLayout'
import StudentDashboard from '@/pages/tiers/StudentDashboard'
import StudentAssessment from '@/pages/tiers/StudentAssessment'
import StudentCoach from '@/pages/tiers/StudentCoach'

import { useAuth } from '@/context/AuthContext'

function App() {
  const { user } = useAuth()
  const age = user?.age ?? 18 // Default safely to 18+ for backwards compatibility

  const isLittleExplorer = age >= 4 && age <= 12
  const isStudent = age >= 13 && age <= 17

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login"    element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Protected routes — require valid JWT in AuthContext */}
      <Route element={<ProtectedRoute />}>
        {isLittleExplorer ? (
          <Route element={<LittleExplorerLayout />}>
            <Route path="/dashboard" element={<LittleExplorerDashboard />} />
            <Route path="/assessment" element={<LittleExplorerAssessment />} />
            <Route path="/coach" element={<LittleExplorerCoach />} />
            {/* Catch-all for restricted tier */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
        ) : isStudent ? (
          <Route element={<StudentLayout />}>
            <Route path="/dashboard" element={<StudentDashboard />} />
            <Route path="/assessment" element={<StudentAssessment />} />
            <Route path="/coach" element={<StudentCoach />} />
            <Route path="/journey" element={<Journey />} />
            {/* Catch-all for restricted tier */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
        ) : (
          <Route element={<AppLayout />}>
            <Route path="/dashboard"           element={<DashboardPage />} />
            <Route path="/assessment"           element={<AssessmentForm />} />
            <Route path="/assessment/history"   element={<AssessmentHistory />} />
            <Route path="/assessment/history/:id" element={<AssessmentResult />} />
            <Route path="/assessment/result" element={<AssessmentResult />} />
            <Route path="/simulator"              element={<Simulator />} />
            <Route path="/simulator/history"      element={<SimulatorHistory />} />
            <Route path="/forecast"               element={<Forecast />} />
            <Route path="/profile"                element={<Profile />} />
            <Route path="/settings"               element={<SettingsPage />} />
            <Route path="/coach"                  element={<AICoach />} />
            <Route path="/goals"                  element={<Goals />} />
            <Route path="/habits"                 element={<HabitTracker />} />
            <Route path="/journey"                element={<Journey />} />
            <Route path="/emissions"    element={<EmissionsPage />} />
            <Route path="/reports"      element={<ReportsPage />} />
            <Route path="/organization" element={<OrganizationPage />} />
          </Route>
        )}
      </Route>

      {/* Root */}
      <Route path="/" element={<LandingPage />} />

      {/* 404 */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default App
