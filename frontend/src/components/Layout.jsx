import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  ClipboardList, LayoutDashboard, Users, LogOut, User,
  Activity, Menu, X
} from 'lucide-react';
import { useState } from 'react';

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
      <nav className="bg-emerald-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-3">
              <Activity className="w-6 h-6" />
              <span className="font-bold text-lg tracking-wide">AI TRIAGE</span>
            </div>

            {/* Desktop nav */}
            <div className="hidden md:flex items-center gap-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2 px-3 py-2 rounded text-sm transition-colors ${
                    isActive(item.path)
                      ? 'bg-emerald-700 text-white'
                      : 'text-emerald-100 hover:bg-emerald-500'
                  }`}
                >
                  {item.icon}
                  {item.label}
                </Link>
              ))}
            </div>

            {/* User info & logout */}
            <div className="hidden md:flex items-center gap-3">
              <div className="text-right text-sm">
                <div className="font-medium">{user?.full_name || user?.email}</div>
                <div className="text-emerald-200 text-xs capitalize">{user?.role}</div>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 rounded hover:bg-emerald-500 transition-colors"
                title="Log out"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>

            {/* Mobile menu button */}
            <button
              className="md:hidden p-2"
              onClick={() => setMobileOpen(!mobileOpen)}
            >
              {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile nav */}
        {mobileOpen && (
          <div className="md:hidden border-t border-emerald-500 pb-3">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setMobileOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 text-sm ${
                  isActive(item.path) ? 'bg-emerald-700' : 'hover:bg-emerald-500'
                }`}
              >
                {item.icon}
                {item.label}
              </Link>
            ))}
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 px-4 py-3 text-sm w-full hover:bg-emerald-500"
            >
              <LogOut className="w-4 h-4" />
              Log out
            </button>
          </div>
        )}
      </nav>

      {/* Main content */}
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
      { path: '/patient/submit', label: 'Submit New Case', icon: <Activity className="w-4 h-4" /> },
    ],
    clinician: [
      { path: '/clinician', label: 'Patient Cases', icon: <ClipboardList className="w-4 h-4" /> },
      { path: '/admin/dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
    ],
    admin: [
      { path: '/admin', label: 'Patient Cases', icon: <ClipboardList className="w-4 h-4" /> },
      { path: '/admin/dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
      { path: '/admin/users', label: 'User Administration', icon: <Users className="w-4 h-4" /> },
    ],
  };
  return items[role] || [];
}
