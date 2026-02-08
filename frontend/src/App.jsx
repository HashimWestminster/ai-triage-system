import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import PatientDashboard from './pages/PatientDashboard';
import SubmitCasePage from './pages/SubmitCasePage';
import ClinicianDashboard from './pages/ClinicianDashboard';
import CaseDetailPage from './pages/CaseDetailPage';
import AdminDashboard from './pages/AdminDashboard';
import UserManagement from './pages/UserManagement';
import DashboardStats from './pages/DashboardStats';

function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex items-center justify-center h-screen">Loading...</div>;
  if (!user) return <Navigate to="/login" />;
  if (allowedRoles && !allowedRoles.includes(user.role)) return <Navigate to="/" />;
  return children;
}

function HomeRedirect() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" />;
  if (user.role === 'patient') return <Navigate to="/patient" />;
  if (user.role === 'clinician') return <Navigate to="/clinician" />;
  if (user.role === 'admin') return <Navigate to="/admin" />;
  return <Navigate to="/login" />;
}

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

      {/* Admin routes */}
      <Route path="/admin" element={
        <ProtectedRoute allowedRoles={['admin']}>
          <Layout><AdminDashboard /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/admin/case/:id" element={
        <ProtectedRoute allowedRoles={['admin']}>
          <Layout><CaseDetailPage /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/admin/users" element={
        <ProtectedRoute allowedRoles={['admin']}>
          <Layout><UserManagement /></Layout>
        </ProtectedRoute>
      } />
      <Route path="/admin/dashboard" element={
        <ProtectedRoute allowedRoles={['admin', 'clinician']}>
          <Layout><DashboardStats /></Layout>
        </ProtectedRoute>
      } />
    </Routes>
  );
}
