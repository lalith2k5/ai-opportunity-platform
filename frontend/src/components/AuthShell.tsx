import type { ReactNode } from 'react';
import { Activity, Sparkles, Zap, Shield, TrendingUp } from 'lucide-react';

const features = [
  { icon: Sparkles, title: 'Multi-source intelligence', text: 'GitHub, arXiv, Reddit, News — analyzed by 10 AI agents.' },
  { icon: Zap,      title: 'Explainable scores',        text: 'Every opportunity scored on 7 factors with evidence.' },
  { icon: TrendingUp, title: 'Continuous monitoring',   text: 'Fresh insights every 6 hours, automatically.' },
  { icon: Shield,   title: 'Yours, privately',          text: 'JWT auth, bcrypt, and role-based access.' },
];

export default function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-canvas flex">

      {/* LEFT — Brand panel */}
      <div className="hidden lg:flex lg:w-[440px] xl:w-[500px] flex-shrink-0 relative overflow-hidden border-r border-edge bg-surface">
        {/* Mesh gradient */}
        <div className="absolute inset-0 opacity-60"
          style={{
            backgroundImage:
              'radial-gradient(at 20% 30%, rgba(94,106,210,0.15) 0px, transparent 60%), ' +
              'radial-gradient(at 80% 70%, rgba(139,92,246,0.12) 0px, transparent 55%), ' +
              'radial-gradient(at 60% 20%, rgba(59,130,246,0.10) 0px, transparent 50%)',
          }}
        />
        <div className="relative z-10 flex flex-col p-10 xl:p-12 w-full">

          {/* Logo */}
          <div className="flex items-center gap-2.5 mb-14">
            <div className="w-8 h-8 rounded-md bg-accent flex items-center justify-center">
              <Activity className="text-accent-fg" size={17} />
            </div>
            <div>
              <h2 className="text-ink font-semibold text-sm leading-tight tracking-tight">Opportunity AI</h2>
              <p className="text-2xs text-ink-4 uppercase tracking-wider leading-tight">Innovation Intelligence</p>
            </div>
          </div>

          {/* Pitch */}
          <div className="mb-12">
            <h3 className="text-2xl xl:text-3xl font-bold text-ink leading-tight tracking-tight mb-3">
              Discover your next<br />
              <span className="text-accent">breakthrough.</span>
            </h3>
            <p className="text-sm text-ink-2 leading-relaxed">
              An AI-powered platform that finds startup and research opportunities by analyzing millions of signals across the developer, academic, and market web.
            </p>
          </div>

          {/* Features */}
          <div className="space-y-5 mt-auto">
            {features.map((f) => {
              const Icon = f.icon;
              return (
                <div key={f.title} className="flex gap-3 items-start">
                  <div className="w-7 h-7 rounded-md bg-overlay border border-edge flex items-center justify-center flex-shrink-0">
                    <Icon size={13} className="text-accent" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm text-ink font-medium leading-tight">{f.title}</p>
                    <p className="text-xs text-ink-3 leading-snug mt-0.5">{f.text}</p>
                  </div>
                </div>
              );
            })}
          </div>

        </div>
      </div>

      {/* RIGHT — Form panel */}
      <div className="flex-1 flex flex-col">
        {/* Mobile logo */}
        <div className="lg:hidden flex items-center gap-2.5 p-6 border-b border-edge">
          <div className="w-7 h-7 rounded-md bg-accent flex items-center justify-center">
            <Activity className="text-accent-fg" size={15} />
          </div>
          <h2 className="text-ink font-semibold text-sm">Opportunity AI</h2>
        </div>

        <div className="flex-1 flex items-center justify-center p-6">
          <div className="w-full max-w-[400px] animate-fade-in">

            <div className="mb-8">
              <h1 className="text-2xl font-bold text-ink tracking-tight">{title}</h1>
              {subtitle && <p className="text-sm text-ink-3 mt-2">{subtitle}</p>}
            </div>

            {children}

            {footer && (
              <div className="mt-6 text-center text-sm text-ink-3">
                {footer}
              </div>
            )}
          </div>
        </div>
      </div>

    </div>
  );
}
