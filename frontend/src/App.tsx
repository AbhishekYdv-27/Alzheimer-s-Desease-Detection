import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { AuthProvider } from './context/AuthContext'
import { AppLayout } from './components/layout/AppLayout'
import { PublicLayout } from './components/layout/PublicLayout'
import { ProtectedRoute, RoleRoute } from './components/auth/ProtectedRoute'

import HomePage from './pages/public/HomePage'
import PlatformPage from './pages/public/PlatformPage'
import TechnologyPage from './pages/public/TechnologyPage'
import ResearchPage from './pages/public/ResearchPage'
import AboutPage from './pages/public/AboutPage'
import LoginPage from './pages/auth/LoginPage'
import SignupPage from './pages/auth/SignupPage'

import DashboardPage from './pages/app/DashboardPage'
import AnalysisPage from './pages/app/AnalysisPage'
import CasesPage from './pages/app/CasesPage'
import ModelsPage from './pages/app/ModelsPage'
import ExplainabilityPage from './pages/app/ExplainabilityPage'
import AnalyticsPage from './pages/app/AnalyticsPage'
import ReportsPage from './pages/app/ReportsPage'
import ResearchWorkspacePage from './pages/app/ResearchWorkspacePage'
import SettingsPage from './pages/app/SettingsPage'
import FindDoctorsPage from './pages/app/FindDoctorsPage'
import AppointmentsPage from './pages/app/AppointmentsPage'
import ProgressPage from './pages/app/ProgressPage'
import DoctorDashboardPage from './pages/app/DoctorDashboardPage'
import DoctorProfilePage from './pages/app/DoctorProfilePage'
import DoctorPatientsPage from './pages/app/DoctorPatientsPage'

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <Routes>
            {/* Public Routes */}
            <Route element={<PublicLayout />}>
              <Route path="/" element={<HomePage />} />
              <Route path="/platform" element={<PlatformPage />} />
              <Route path="/technology" element={<TechnologyPage />} />
              <Route path="/research-public" element={<ResearchPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/signup" element={<SignupPage />} />
            </Route>

            {/* Protected App Routes */}
            <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
              <Route path="/dashboard" element={<RoleRoute role="patient"><DashboardPage /></RoleRoute>} />
              <Route path="/analysis" element={<AnalysisPage />} />
              <Route path="/cases" element={<CasesPage />} />
              <Route path="/models" element={<ModelsPage />} />
              <Route path="/explainability" element={<ExplainabilityPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/research" element={<ResearchWorkspacePage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/doctors" element={<RoleRoute role="patient"><FindDoctorsPage /></RoleRoute>} />
              <Route path="/appointments" element={<RoleRoute role="patient"><AppointmentsPage /></RoleRoute>} />
              <Route path="/progress" element={<RoleRoute role="patient"><ProgressPage /></RoleRoute>} />
              <Route path="/doctor" element={<RoleRoute role="doctor"><DoctorDashboardPage /></RoleRoute>} />
              <Route path="/doctor/patients" element={<RoleRoute role="doctor"><DoctorPatientsPage /></RoleRoute>} />
              <Route path="/doctor/appointments" element={<RoleRoute role="doctor"><AppointmentsPage /></RoleRoute>} />
              <Route path="/doctor/profile" element={<RoleRoute role="doctor"><DoctorProfilePage /></RoleRoute>} />
            </Route>
          </Routes>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}

export default App
