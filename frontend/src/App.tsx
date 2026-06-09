import { Routes, Route, Navigate } from 'react-router-dom'
import DashboardPage from '@/pages/DashboardPage'
import LoginPage from '@/pages/LoginPage'
import EmissionsPage from '@/pages/EmissionsPage'
import ReportsPage from '@/pages/ReportsPage'
import OrganizationPage from '@/pages/OrganizationPage'
import SettingsPage from '@/pages/SettingsPage'
import NotFoundPage from '@/pages/NotFoundPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/emissions" element={<EmissionsPage />} />
      <Route path="/reports" element={<ReportsPage />} />
      <Route path="/organization" element={<OrganizationPage />} />
      <Route path="/settings" element={<SettingsPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default App
