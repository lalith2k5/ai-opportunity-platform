import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Search, MessageSquare, FileText, Activity, LogOut, User as UserIcon, Shield, UserCircle, TrendingUp, BarChart3 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import NotificationBell from './NotificationBell';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/search', label: 'Search', icon: Search },
  { path: '/chat', label: 'AI Chat', icon: MessageSquare },
  { path: '/reports', label: 'Reports', icon: FileText },
  { path: '/problems', label: 'Problems', icon: TrendingUp },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen bg-brand-dark">
      <aside className="w-64 bg-brand-panel border-r border-brand-border p-6 flex flex-col">
        <div className="flex items-center gap-2 mb-6">
          <Activity className="text-brand-accent" size={28} />
          <div>
            <h1 className="text-white font-bold text-lg leading-tight">Opportunity AI</h1>
            <p className="text-xs text-gray-500">Innovation Intelligence</p>
          </div>
        </div>

        <div className="flex items-center justify-between mb-4">
          <NotificationBell />
          <Link to="/profile" className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-brand-border transition-colors">
            <UserCircle size={20} />
          </Link>
        </div>

        {user && (
          <Link to="/profile" className="mb-6 px-3 py-3 bg-brand-dark border border-brand-border hover:border-brand-accent rounded-lg transition-colors block">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-brand-accent flex items-center justify-center flex-shrink-0">
                <UserIcon size={16} />
              </div>
              <div className="min-w-0">
                <p className="text-sm text-white font-medium truncate">{user.name}</p>
                <p className="text-xs text-gray-500 capitalize truncate">{user.role}</p>
              </div>
            </div>
          </Link>
        )}

        <nav className="flex flex-col gap-2">
          {navItems.map(item => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive ? 'bg-brand-accent text-white' : 'text-gray-400 hover:bg-brand-border hover:text-white'
                }`}
              >
                <Icon size={20} />
                <span className="font-medium">{item.label}</span>
              </Link>
            );
          })}

          {user?.role === 'admin' && (
            <Link
              to="/admin"
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                location.pathname === '/admin' ? 'bg-brand-accent text-white' : 'text-yellow-400 hover:bg-brand-border hover:text-yellow-300'
              }`}
            >
              <Shield size={20} />
              <span className="font-medium">Admin</span>
            </Link>
          )}
        </nav>

        <button
          onClick={async () => { await logout(); window.location.href = '/login'; }}
          className="mt-auto flex items-center gap-3 px-4 py-3 rounded-lg text-gray-400 hover:bg-brand-border hover:text-white transition-colors"
        >
          <LogOut size={20} />
          <span className="font-medium">Sign out</span>
        </button>
      </aside>

      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
