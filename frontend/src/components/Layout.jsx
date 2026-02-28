import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  ClipboardList, LayoutDashboard, Users, LogOut,
  Activity, Menu, X, Clock, Settings, PlusCircle, BarChart3
} from 'lucide-react';
import { useState } from 'react';

const ROLE_LABELS = {
  patient: 'Patient',
  clinician: 'Clinician',
  care_navigator: 'Care Navigator',
  superuser: 'Site Administrator',
};

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = getNavItems(user?.role);
  const isActive = (path) => location.pathname === path;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top navigation bar */}
      <nav className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Brand */}
            <Link to="/" className="flex items-center gap-2.5">
              <div className="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center">
                <Activity className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="font-bold text-gray-900 text-sm tracking-wide">AI TRIAGE</span>
                <span className="hidden sm:inline text-gray-400 text-xs ml-2">Addison Road Medical Practice</span>
              </div>
            </Link>

            {/* Desktop nav links */}
            <div className="hidden md:flex items-center gap-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive(item.path)
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  {item.icon}
                  {item.label}
                </Link>
              ))}
            </div>

            {/* User info + logout */}
            <div className="hidden md:flex items-center gap-3">
              <div className="text-right">
                <div className="text-sm font-medium text-gray-900">{user?.full_name || user?.email}</div>
                <div className="text-xs text-gray-500">{ROLE_LABELS[user?.role] || user?.role}</div>
              </div>
              <div className="w-px h-8 bg-gray-200" />
              <button
                onClick={handleLogout}
                className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-red-600 transition-colors px-2 py-1.5 rounded-lg hover:bg-red-50"
                title="Log out"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden lg:inline">Sign out</span>
              </button>
            </div>

            {/* Mobile menu toggle */}
            <button
              className="md:hidden p-2 rounded-lg hover:bg-gray-100"
              onClick={() => setMobileOpen(!mobileOpen)}
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile nav */}
        {mobileOpen && (
          <div className="md:hidden border-t bg-white pb-3">
            <div className="px-2 pt-2 space-y-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm ${
                    isActive(item.path)
                      ? 'bg-emerald-50 text-emerald-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {item.icon}
                  {item.label}
                </Link>
              ))}
            </div>
            <div className="border-t mt-2 pt-2 px-2">
              <div className="px-3 py-2 text-xs text-gray-400">
                Signed in as {user?.full_name} ({ROLE_LABELS[user?.role]})
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center gap-3 px-3 py-2.5 text-sm text-red-600 hover:bg-red-50 rounded-lg w-full"
              >
                <LogOut className="w-4 h-4" />
                Sign out
              </button>
            </div>
          </div>
        )}
      </nav>

      {/* Page content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {children}
      </main>
    </div>
  );
}

function getNavItems(role) {
  const items = {
    patient: [
      { path: '/patient', label: 'My Cases', icon: <ClipboardList className="w-4 h-4" /> },
      { path: '/patient/submit', label: 'Submit Case', icon: <PlusCircle className="w-4 h-4" /> },
    ],
    clinician: [
      { path: '/clinician', label: 'Patient Cases', icon: <ClipboardList className="w-4 h-4" /> },
      { path: '/dashboard', label: 'Dashboard', icon: <BarChart3 className="w-4 h-4" /> },
    ],
    care_navigator: [
      { path: '/navigator', label: 'Patient Cases', icon: <ClipboardList className="w-4 h-4" /> },
      { path: '/dashboard', label: 'Dashboard', icon: <BarChart3 className="w-4 h-4" /> },
      { path: '/admin/users', label: 'Users', icon: <Users className="w-4 h-4" /> },
    ],
    superuser: [
      { path: '/admin', label: 'Patient Cases', icon: <ClipboardList className="w-4 h-4" /> },
      { path: '/dashboard', label: 'Dashboard', icon: <BarChart3 className="w-4 h-4" /> },
      { path: '/admin/users', label: 'Users', icon: <Users className="w-4 h-4" /> },
      { path: '/admin/surgery-hours', label: 'Surgery Hours', icon: <Clock className="w-4 h-4" /> },
    ],
  };
  return items[role] || [];
}
