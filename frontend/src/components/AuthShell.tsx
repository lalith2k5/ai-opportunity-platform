import type { ReactNode } from 'react';
import { Sparkles, Zap, Shield, TrendingUp } from 'lucide-react';

const features = [
  { icon: Sparkles, title: 'Multi-source intelligence', text: 'GitHub, arXiv, Reddit, News — analyzed by 10 AI agents.' },
  { icon: Zap,      title: 'Explainable scores',        text: 'Every opportunity scored on 8 factors with evidence.' },
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
    <div className="min-h-screen bg-canvas flex relative">

      {/* LEFT — Brand panel */}
      <div className="hidden lg:flex lg:w-[460px] xl:w-[520px] flex-shrink-0 relative overflow-hidden border-r border-edge/60">
        {/* Mesh gradient background */}
        <div
          className="absolute inset-0"
          style={{
            backgroundImage:
              'radial-gradient(at 20% 25%, rgba(24,119,242,0.28) 0px, transparent 55%), ' +
              'radial-gradient(at 85% 75%, rgba(56,182,255,0.20) 0px, transparent 55%), ' +
              'radial-gradient(at 60% 15%, rgba(100,180,255,0.16) 0px, transparent 50%)',
          }}
        />
        {/* Subtle noise overlay */}
        <div
          className="absolute inset-0 opacity-[0.15] mix-blend-overlay pointer-events-none"
          style={{
            backgroundImage:
              'url("data:image/svg+xml;utf8,<svg viewBox=\'0 0 200 200\' xmlns=\'http://www.w3.org/2000/svg\'><filter id=\'n\'><feTurbulence type=\'fractalNoise\' baseFrequency=\'0.9\' numOctaves=\'3\' stitchTiles=\'stitch\'/></filter><rect width=\'100%\' height=\'100%\' filter=\'url(%23n)\'/></svg>")',
          }}
        />

        <div className="relative z-10 flex flex-col p-10 xl:p-14 w-full">

          {/* Logo */}
          <div className="flex items-center gap-3 mb-16">
            <div>
              <h2 className="text-ink font-semibold text-base leading-tight tracking-tight">Opportunity AI</h2>
              <p className="text-2xs text-ink-4 uppercase tracking-[0.1em] leading-tight mt-0.5">Innovation Intelligence</p>
            </div>
          </div>

          {/* Pitch */}
          <div className="mb-14">
            <h3 className="text-4xl xl:text-5xl font-bold text-ink leading-[1.05] tracking-tight mb-5">
              Discover your next
              <br />
              <span className="bg-gradient-to-r from-accent to-sky-300 bg-clip-text text-transparent">
                breakthrough.
              </span>
            </h3>
            <p className="text-base text-ink-2 leading-relaxed max-w-md">
              An AI-powered platform that finds startup and research opportunities by analyzing millions of signals across the developer, academic, and market web.
            </p>
          </div>

          {/* Features */}
          <div className="space-y-6 mt-auto">
            {features.map((f) => {
              const Icon = f.icon;
              return (
                <div key={f.title} className="flex gap-3.5 items-start">
                  <div className="w-9 h-9 rounded-lg glass flex items-center justify-center flex-shrink-0">
                    <Icon size={15} className="text-accent" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm text-ink font-medium leading-tight">{f.title}</p>
                    <p className="text-xs text-ink-3 leading-snug mt-1">{f.text}</p>
                  </div>
                </div>
              );
            })}
          </div>

        </div>
      </div>

      {/* RIGHT — Form panel */}
      <div className="flex-1 flex flex-col relative z-10">
        {/* Mobile logo */}
        <div className="lg:hidden flex items-center gap-2.5 p-6 border-b border-edge/60">
          <h2 className="text-ink font-semibold text-sm">Opportunity AI</h2>
        </div>

        <div className="flex-1 flex items-center justify-center p-6">
          <div className="w-full max-w-[420px] animate-fade-up">

            <div className="mb-8">
              <h1 className="text-3xl font-bold text-ink tracking-tight">{title}</h1>
              {subtitle && <p className="text-sm text-ink-3 mt-2.5 leading-relaxed">{subtitle}</p>}
            </div>

            {children}

            {footer && (
              <div className="mt-7 text-center text-sm text-ink-3">
                {footer}
              </div>
            )}
          </div>
        </div>
      </div>

    </div>
  );
}
