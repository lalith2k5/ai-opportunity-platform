
import { Link, useLocation } from 'react-router-dom';
import { Home } from 'lucide-react';
import type { ReactNode } from 'react';
import ParticleField from './ParticleField';

export default function NeonShell({
  children,
  title,
  fullBleed = false,
}: {
  children: ReactNode;
  title?: string;
  fullBleed?: boolean;
}) {
  const location = useLocation();
  const isEntrance = location.pathname === '/entrance';

  return (
    <div className="neon-theme relative min-h-screen">
      <div className="fixed inset-0 z-0 opacity-70">
        <ParticleField count={70} color="0, 212, 255" />
      </div>
      <div className="neon-grid-overlay" />

      {!isEntrance && (
        <nav className="relative z-20 border-b border-[rgba(0,212,255,0.15)] bg-[rgba(5,8,22,0.6)] backdrop-blur-lg">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <Link
              to="/entrance"
              className="flex items-center gap-2 text-[var(--neon-text-dim)] hover:text-[var(--neon-blue)] transition-colors text-sm"
            >
              <Home size={16} />
              <span>Entrance</span>
            </Link>
            {title && (
              <h1 className="text-[var(--neon-text)] text-lg font-semibold tracking-tight">
                {title}
              </h1>
            )}
            <div className="w-20" />
          </div>
        </nav>
      )}

      <main
        className={`relative z-10 ${
          fullBleed ? '' : 'max-w-7xl mx-auto px-6 py-10'
        }`}
      >
        {children}
      </main>
    </div>
  );
}
