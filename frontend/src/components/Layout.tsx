import { Link, Outlet, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { BookOpen, FileText, GraduationCap, Home, LogOut, Search, Bell, User } from 'lucide-react';

export default function Layout() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      <nav className="bg-white border-b border-[var(--color-border)] sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center gap-8">
              <Link to="/" className="flex items-center gap-2 text-[var(--color-primary)] font-bold text-xl">
                <GraduationCap className="w-6 h-6" />
                GrantAssist AI
              </Link>
              {isAuthenticated && (
                <div className="hidden md:flex items-center gap-6">
                  <Link to="/dashboard" className="flex items-center gap-1 text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">
                    <Home className="w-4 h-4" /> Dashboard
                  </Link>
                  <Link to="/grants" className="flex items-center gap-1 text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">
                    <Search className="w-4 h-4" /> Grants
                  </Link>
                  <Link to="/papers" className="flex items-center gap-1 text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">
                    <BookOpen className="w-4 h-4" /> Papers
                  </Link>
                  <Link to="/applications" className="flex items-center gap-1 text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">
                    <FileText className="w-4 h-4" /> Applications
                  </Link>
                  <Link to="/alerts" className="flex items-center gap-1 text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">
                    <Bell className="w-4 h-4" /> Alerts
                  </Link>
                </div>
              )}
            </div>
            <div className="flex items-center gap-4">
              {isAuthenticated ? (
                <>
                  <Link to="/profile" className="flex items-center gap-1 text-[var(--color-text-muted)] hover:text-[var(--color-text)]">
                    <User className="w-4 h-4" />
                    <span className="hidden sm:inline">{user?.name || user?.email}</span>
                  </Link>
                  <button onClick={handleLogout} className="flex items-center gap-1 text-[var(--color-text-muted)] hover:text-[var(--color-danger)]">
                    <LogOut className="w-4 h-4" />
                  </button>
                </>
              ) : (
                <div className="flex gap-3">
                  <Link to="/login" className="px-4 py-2 text-[var(--color-primary)] hover:bg-blue-50 rounded-lg transition-colors">
                    Login
                  </Link>
                  <Link to="/register" className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:bg-[var(--color-primary-hover)] transition-colors">
                    Sign Up
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  );
}
