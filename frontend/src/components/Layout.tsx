import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Search, MessageSquare, FileText, Activity,
  TrendingUp, BarChart3, Zap, Shield, Menu, X, Sparkles, Network, Target,
  GraduationCap, FlaskConical, Factory, Building2,
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
      { path: '/recommendations', label: 'Recommendations', icon: Sparkles },
      { path: '/opportunities', label: 'Opportunities', icon: Zap },
      { path: '/problems', label: 'Problems', icon: TrendingUp },
      { path: '/problem-profiles', label: 'Problem Profiles', icon: Target },
      { path: '/organizations',    label: 'Organizations',    icon: Building2 },
      { path: '/workflows/student',    label: 'Student flow',    icon: GraduationCap },
      { path: '/workflows/researcher', label: 'Researcher flow', icon: FlaskConical },
      { path: '/workflows/rd',         label: 'R&D flow',        icon: Factory },
    ],
  },
  {
    label: 'Insights',
    items: [
      { path: '/reports', label: 'Reports', icon: FileText },
      { path: '/analytics', label: 'Analytics', icon: BarChart3 },
      { path: '/knowledge-graph', label: 'Knowledge Graph', icon: Network },
    ],
  },
];

function SidebarContent({
  location, user, onClose,
}: {
  location: any;
  user: any;
  onClose?: () => void;
}) {
  return (
    <>
      <div className="px-4 pt-5 pb-4 flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-md bg-accent flex items-center justify-center flex-shrink-0">
          <Activity className="text-accent-fg" size={16} />
        </div>
        <div className="min-w-0 flex-1">
          <h1 className="text-ink font-semibold text-sm leading-tight tracking-tight">Opportunity AI</h1>
          <p className="text-2xs text-ink-4 uppercase tracking-wider leading-tight">Innovation Intelligence</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1.5 rounded-md text-ink-4 hover:text-ink hover:bg-overlay transition-colors"
            aria-label="Close menu"
          >
            <X size={15} />
          </button>
        )}
      </div>

      <div className="px-3 pb-3 flex items-center gap-1 border-b border-edge-subtle">
        <ThemeToggle />
        <NotificationBell />
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-3">
        {sections.map(section => (
          <div key={section.label} className="mb-4">
            <p className="px-2 mb-1.5 text-2xs font-semibold text-ink-4 uppercase tracking-wider">
              {section.label}
            </p>
            <div className="space-y-0.5">
              {section.items.map(item => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`relative flex items-center gap-2.5 px-2 py-2 rounded-md text-sm transition-colors ${
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
            <p className="px-2 mb-1.5 text-2xs font-semibold text-ink-4 uppercase tracking-wider">Admin</p>
            <Link
              to="/admin"
              className={`relative flex items-center gap-2.5 px-2 py-2 rounded-md text-sm transition-colors ${
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

      <div className="border-t border-edge p-3">
        <UserMenu />
      </div>
    </>
  );
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const { user } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => { setMobileOpen(false); }, [location.pathname]);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [mobileOpen]);

  return (
    <div className="flex h-screen overflow-hidden bg-canvas">

      {/* Mobile topbar */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-14 bg-surface border-b border-edge flex items-center justify-between px-3 z-30">
        <button
          onClick={() => setMobileOpen(true)}
          className="p-2 -ml-1 rounded-md text-ink-2 hover:bg-overlay transition-colors"
          aria-label="Open menu"
        >
          <Menu size={18} />
        </button>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-accent flex items-center justify-center">
            <Activity className="text-accent-fg" size={13} />
          </div>
          <span className="text-ink font-semibold text-sm tracking-tight">Opportunity AI</span>
        </div>
        <div className="flex items-center gap-0.5">
          <ThemeToggle />
          <NotificationBell />
        </div>
      </div>

      {/* Desktop sidebar — always in flow, hidden below lg */}
      <aside className="hidden lg:flex w-64 flex-shrink-0 bg-surface border-r border-edge flex-col h-screen">
        <SidebarContent location={location} user={user} />
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <>
          <div
            className="lg:hidden fixed inset-0 bg-black/50 z-40 animate-fade-in"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />
          <aside className="lg:hidden fixed inset-y-0 left-0 z-50 w-64 bg-surface border-r border-edge flex flex-col animate-slide-in-left">
            <SidebarContent location={location} user={user} onClose={() => setMobileOpen(false)} />
          </aside>
        </>
      )}

      {/* Main content */}
      <main className="flex-1 overflow-y-auto h-screen bg-canvas pt-14 lg:pt-0">
        <div key={location.pathname} className="animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
}
