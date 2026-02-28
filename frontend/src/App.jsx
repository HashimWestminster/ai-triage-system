import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import PatientDashboard from './pages/PatientDashboard';
import SubmitCasePage from './pages/SubmitCasePage';
import ClinicianDashboard from './pages/ClinicianDashboard';
import CaseDetailPage from './pages/CaseDetailPage';
import NavigatorDashboard from './pages/NavigatorDashboard';
import UserManagement from './pages/UserManagement';
import DashboardStats from './pages/DashboardStats';
import SurgeryHoursPage from './pages/SurgeryHoursPage';

function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex items-center justify-center h-screen text-gray-400">Loading...</div>;
  if (!user) return <Navigate to="/login" />;
  if (allowedRoles && !allowedRoles.includes(user.role)) return <Navigate to="/" />;
  return children;
}

function HomeRedirect() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" />;
  if (user.role === 'patient') return <Navigate to="/patient" />;
  if (user.role === 'clinician') return <Navigate to="/clinician" />;
  if (user.role === 'care_navigator') return <Navigate to="/navigator" />;
  if (user.role === 'superuser') return <Navigate to="/admin" />;
  return <Navigate to="/login" />;
}

const STAFF = ['clinician', 'care_navigator', 'superuser'];
const NAVIGATORS = ['care_navigator', 'superuser'];

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={<HomeRedirect />} />

      {/* Patient routes */}
      <Route path="/patient" element={
        <ProtectedRoute allowedRoles={['patient']}>
          <Layout><PatientDashboard /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/patient/submit" element={
        <ProtectedRoute allowedRoles={['patient']}>
          <Layout><SubmitCasePage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/patient/case/:id" element={
        <ProtectedRoute allowedRoles={['patient']}>
          <Layout><CaseDetailPage /></Layout>
        </ProtectedRoute>
      } />

      {/* Clinician routes */}
      <Route path="/clinician" element={
        <ProtectedRoute allowedRoles={['clinician']}>
          <Layout><ClinicianDashboard /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/clinician/case/:id" element={
        <ProtectedRoute allowedRoles={['clinician']}>
          <Layout><CaseDetailPage /></Layout>
        </ProtectedRoute>
      } />

      {/* Care navigator routes */}
      <Route path="/navigator" element={
        <ProtectedRoute allowedRoles={NAVIGATORS}>
          <Layout><NavigatorDashboard /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/navigator/case/:id" element={
        <ProtectedRoute allowedRoles={NAVIGATORS}>
          <Layout><CaseDetailPage /></Layout>
        </ProtectedRoute>
      } />

      {/* Site superuser routes */}
      <Route path="/admin" element={
        <ProtectedRoute allowedRoles={['superuser']}>
          <Layout><NavigatorDashboard /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/admin/case/:id" element={
        <ProtectedRoute allowedRoles={['superuser']}>
          <Layout><CaseDetailPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/admin/users" element={
        <ProtectedRoute allowedRoles={NAVIGATORS}>
          <Layout><UserManagement /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/admin/surgery-hours" element={
        <ProtectedRoute allowedRoles={['superuser']}>
          <Layout><SurgeryHoursPage /></Layout>
        </ProtectedRoute>
      } />

      {/* Shared staff routes */}
      <Route path="/dashboard" element={
        <ProtectedRoute allowedRoles={STAFF}>
          <Layout><DashboardStats /></Layout>
        </ProtectedRoute>
      } />
    </Routes>
  );
}
