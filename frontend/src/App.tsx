import React, { Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from '@/components/ProtectedRoute'
import AppLayout from '@/components/AppLayout'

// Public pages (Keep static for fast initial paint)
import LandingPage from '@/pages/LandingPage'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import NotFoundPage from '@/pages/NotFoundPage'

// Lazy-loaded protected pages
const DashboardPage = React.lazy(() => import('@/pages/DashboardPage'))
const AICoach = React.lazy(() => import('@/pages/AICoach'))
const Goals = React.lazy(() => import('@/pages/Goals'))
const HabitTracker = React.lazy(() => import('@/pages/HabitTracker'))
const EmissionsPage = React.lazy(() => import('@/pages/EmissionsPage'))
const ReportsPage = React.lazy(() => import('@/pages/ReportsPage'))
const OrganizationPage = React.lazy(() => import('@/pages/OrganizationPage'))
const SettingsPage = React.lazy(() => import('@/pages/SettingsPage'))
const AssessmentForm = React.lazy(() => import('@/pages/AssessmentForm'))
const AssessmentHistory = React.lazy(() => import('@/pages/AssessmentHistory'))
const AssessmentResult = React.lazy(() => import('@/pages/AssessmentResult'))
const Simulator = React.lazy(() => import('@/pages/Simulator'))
const SimulatorHistory = React.lazy(() => import('@/pages/SimulatorHistory'))
const Forecast = React.lazy(() => import('@/pages/Forecast').then(m => ({ default: m.Forecast })))
const Profile = React.lazy(() => import('@/pages/Profile'))
const Journey = React.lazy(() => import('@/pages/Journey'))

// Tier Components
const LittleExplorerLayout = React.lazy(() => import('@/components/tiers/LittleExplorerLayout'))
const LittleExplorerDashboard = React.lazy(() => import('@/pages/tiers/LittleExplorerDashboard'))
const LittleExplorerAssessment = React.lazy(() => import('@/pages/tiers/LittleExplorerAssessment'))
const LittleExplorerCoach = React.lazy(() => import('@/pages/tiers/LittleExplorerCoach'))
const StudentLayout = React.lazy(() => import('@/components/tiers/StudentLayout'))
const StudentDashboard = React.lazy(() => import('@/pages/tiers/StudentDashboard'))
const StudentAssessment = React.lazy(() => import('@/pages/tiers/StudentAssessment'))
const StudentCoach = React.lazy(() => import('@/pages/tiers/StudentCoach'))

import { useAuth } from '@/context/AuthContext'

function App() {
  const { user } = useAuth()
  const age = user?.age ?? 18 // Default safely to 18+ for backwards compatibility

  const isLittleExplorer = age >= 4 && age <= 12
  const isStudent = age >= 13 && age <= 17

  const fallback = <div className="flex justify-center p-20"><i className="ti ti-loader animate-spin text-4xl text-accent"></i></div>

  return (
    <Suspense fallback={fallback}>
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
    </Suspense>
  )
}

export default App
