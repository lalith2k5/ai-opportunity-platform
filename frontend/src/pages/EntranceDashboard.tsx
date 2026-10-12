
import { Link } from 'react-router-dom';
import {
  ArrowRight, BookOpen, Cpu, Factory, Lightbulb, Sparkles,
  LogIn, UserPlus, LayoutDashboard,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface Module {
  number: string;
  title: string;
  subtitle: string;
  icon: any;
  to: string;
  iconBg: string;
  iconColor: string;
}

const MODULES: Module[] = [
  {
    number: '01',
    title: 'Find the Real-Time Ideas',
    subtitle:
      'Trending real-world problems across GitHub, Reddit, arXiv, news, and public challenges — ranked by evidence and momentum.',
    icon: Lightbulb,
    to: '/ideas',
    iconBg: 'bg-accent/10',
    iconColor: 'text-accent',
  },
  {
    number: '02',
    title: 'Choose the Technology',
    subtitle:
      'Explore trending technologies and the problems, research, and opportunities they connect to.',
    icon: Cpu,
    to: '/technologies',
    iconBg: 'bg-purple-500/10',
    iconColor: 'text-purple-500',
  },
  {
    number: '03',
    title: 'Research Analysis',
    subtitle:
      'Search, compare, and drill into papers with methodology, findings, limitations, and related work.',
    icon: BookOpen,
    to: '/research',
    iconBg: 'bg-sky-500/10',
    iconColor: 'text-sky-500',
  },
  {
    number: '04',
    title: 'R&D',
    subtitle:
      'From industry problems to technology landscape, evidence aggregation, and evidence-backed innovation opportunities.',
    icon: Factory,
    to: '/rd',
    iconBg: 'bg-warning/10',
    iconColor: 'text-warning',
  },
];

export default function EntranceDashboard() {
  const { user } = useAuth();
  const firstName = user?.name?.split(' ')[0] || '';

  return (
    <div className="min-h-screen bg-canvas relative overflow-hidden">
      <div
        className="fixed inset-0 pointer-events-none opacity-70"
        style={{
          background:
            'radial-gradient(ellipse 900px 700px at 20% 10%, rgb(24 119 242 / 0.10), transparent 60%), ' +
            'radial-gradient(ellipse 800px 600px at 85% 90%, rgb(56 189 248 / 0.08), transparent 60%)',
        }}
      />

      <header className="relative z-10 px-6 py-5 max-w-6xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-accent shadow-[0_0_10px_rgb(var(--accent)/0.8)]" />
          <span className="text-ink font-semibold text-sm tracking-tight">Opportunity AI</span>
        </div>

        <div className="flex items-center gap-2">
          {user ? (
            <Link to="/dashboard" className="btn-primary text-xs">
              <LayoutDashboard size={13} /> Go to dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className="btn-ghost text-xs">
                <LogIn size={13} /> Sign in
              </Link>
              <Link to="/register" className="btn-primary text-xs">
                <UserPlus size={13} /> Get started
              </Link>
            </>
          )}
        </div>
      </header>

      <main className="relative z-10 px-6 pb-20 pt-6 max-w-4xl mx-auto">
        <div className="text-center mb-14 animate-fade-up">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent/10 border border-accent/20 mb-7">
            <Sparkles size={12} className="text-accent" />
            <span className="text-2xs font-medium text-accent uppercase tracking-[0.08em]">
              Innovation Intelligence Platform
            </span>
          </div>

          <h1 className="text-4xl lg:text-5xl font-bold text-ink tracking-tight leading-[1.05] mb-5">
            Discover your next{' '}
            <span className="bg-gradient-to-r from-accent to-sky-300 bg-clip-text text-transparent">
              breakthrough
            </span>
            .
          </h1>

          <p className="text-lg text-ink-3 max-w-2xl mx-auto leading-relaxed">
            {firstName ? 'Welcome back, ' + firstName + '. ' : ''}
            Four connected modules to move from real-world problems to technologies,
            research, and evidence-backed innovation opportunities.
          </p>
        </div>

        <div className="space-y-3">
          {MODULES.map((m, i) => {
            const Icon = m.icon;
            return (
              <Link key={m.to} to={m.to} className="block group">
                <div
                  className="card card-hover p-5 lg:p-6 flex items-center gap-5 animate-fade-up"
                  style={{ animationDelay: `${150 + i * 100}ms` }}
                >
                  <span className="font-mono text-xs text-ink-4 tracking-[0.15em] w-7 flex-shrink-0">
                    {m.number}
                  </span>

                  <div
                    className={`w-11 h-11 rounded-lg ${m.iconBg} flex items-center justify-center flex-shrink-0 transition-transform duration-300 ease-apple group-hover:scale-105`}
                  >
                    <Icon size={18} className={m.iconColor} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <h3 className="text-base lg:text-lg font-semibold text-ink tracking-tight group-hover:text-accent transition-colors">
                      {m.title}
                    </h3>
                    <p className="text-xs lg:text-sm text-ink-3 mt-1 leading-relaxed">
                      {m.subtitle}
                    </p>
                  </div>

                  <ArrowRight
                    size={18}
                    className="flex-shrink-0 text-ink-4 group-hover:text-accent group-hover:translate-x-0.5 transition-all duration-200 ease-apple"
                  />
                </div>
              </Link>
            );
          })}
        </div>

        <p
          className="text-2xs text-ink-4 text-center mt-14 animate-fade-up"
          style={{ animationDelay: '600ms' }}
        >
          Powered by multi-agent AI · Semantic search · Knowledge graph · Evidence aggregation
        </p>
      </main>
    </div>
  );
}
