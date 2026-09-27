import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Search, MessageSquare, FileText, Activity,
  TrendingUp, BarChart3, Zap, Shield,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import NotificationBell from './NotificationBell';
import ThemeToggle from './ThemeToggle';
import UserMenu from './UserMenu';

const sections = [
  {
    label: 'Workspace',
    items: [
      { path: '/', label: 'Dashboard', icon: LayoutDashboard },
      { path: '/search', label: 'Search', icon: Search },
      { path: '/chat', label: 'AI Chat', icon: MessageSquare },
      { path: '/opportunities', label: 'Opportunities', icon: Zap },
      { path: '/problems', label: 'Problems', icon: TrendingUp },
    ],
  },
  {
    label: 'Insights',
    items: [
      { path: '/reports', label: 'Reports', icon: FileText },
      { path: '/analytics', label: 'Analytics', icon: BarChart3 },
    ],
  },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const { user } = useAuth();

  return (
    <div className="flex h-screen overflow-hidden bg-canvas">
      <aside className="w-[248px] flex-shrink-0 bg-surface border-r border-edge flex flex-col h-screen">

        {/* Logo */}
        <div className="px-4 pt-5 pb-4 flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-accent flex items-center justify-center flex-shrink-0">
            <Activity className="text-accent-fg" size={16} />
          </div>
          <div className="min-w-0">
            <h1 className="text-ink font-semibold text-sm leading-tight tracking-tight">Opportunity AI</h1>
            <p className="text-2xs text-ink-4 uppercase tracking-wider leading-tight">Innovation Intelligence</p>
          </div>
        </div>

        {/* Quick actions row */}
        <div className="px-3 pb-3 flex items-center gap-1 border-b border-edge-subtle">
          <ThemeToggle />
          <NotificationBell />
        </div>

        {/* Nav sections */}
        <nav className="flex-1 overflow-y-auto px-3 py-3">
          {sections.map((section) => (
            <div key={section.label} className="mb-4">
              <p className="px-2 mb-1.5 text-2xs font-semibold text-ink-4 uppercase tracking-wider">
                {section.label}
              </p>
              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`relative flex items-center gap-2.5 px-2 py-1.5 rounded-md text-sm transition-colors ${
                        isActive
                          ? 'bg-accent/10 text-ink font-medium'
                          : 'text-ink-2 hover:bg-overlay hover:text-ink'
                      }`}
                    >
                      {isActive && (
                        <span className="absolute left-0 top-1.5 bottom-1.5 w-[2px] rounded-full bg-accent" />
                      )}
                      <Icon size={15} className={isActive ? 'text-accent' : ''} />
                      <span className="truncate">{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}

          {user?.role === 'admin' && (
            <div className="mb-4">
              <p className="px-2 mb-1.5 text-2xs font-semibold text-ink-4 uppercase tracking-wider">
                Admin
              </p>
              <Link
                to="/admin"
                className={`relative flex items-center gap-2.5 px-2 py-1.5 rounded-md text-sm transition-colors ${
                  location.pathname === '/admin'
                    ? 'bg-warning/10 text-ink font-medium'
                    : 'text-ink-2 hover:bg-overlay hover:text-ink'
                }`}
              >
                {location.pathname === '/admin' && (
                  <span className="absolute left-0 top-1.5 bottom-1.5 w-[2px] rounded-full bg-warning" />
                )}
                <Shield size={15} className={location.pathname === '/admin' ? 'text-warning' : ''} />
                <span>Admin</span>
              </Link>
            </div>
          )}
        </nav>

        {/* User menu */}
        <div className="border-t border-edge p-3">
          <UserMenu />
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto h-screen bg-canvas">{children}</main>
    </div>
  );
}
