
import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';

type Accent = 'accent' | 'purple' | 'sky' | 'success' | 'warning';

const ACCENT_BG: Record<Accent, string> = {
  accent:  'bg-accent/10',
  purple:  'bg-purple-500/10',
  sky:     'bg-sky-500/10',
  success: 'bg-success/10',
  warning: 'bg-warning/10',
};

const ACCENT_TEXT: Record<Accent, string> = {
  accent:  'text-accent',
  purple:  'text-purple-500',
  sky:     'text-sky-500',
  success: 'text-success',
  warning: 'text-warning',
};

export default function PageHeader({
  icon: Icon,
  title,
  subtitle,
  accent = 'accent',
  actions,
  className = '',
}: {
  icon?: LucideIcon;
  title: string;
  subtitle?: string;
  accent?: Accent;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div className={'mb-6 animate-fade-up ' + className}>
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3.5 min-w-0 flex-1">
          {Icon && (
            <div
              className={
                'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-[inset_0_1px_0_0_rgb(255_255_255/0.05)] ' +
                ACCENT_BG[accent]
              }
            >
              <Icon size={18} className={ACCENT_TEXT[accent]} />
            </div>
          )}
          <div className="min-w-0">
            <h1 className="text-3xl font-bold text-ink tracking-tight leading-tight">
              {title}
            </h1>
            {subtitle && (
              <p className="text-sm text-ink-3 mt-1 leading-relaxed">{subtitle}</p>
            )}
          </div>
        </div>
        {actions && <div className="flex items-center gap-2 flex-shrink-0">{actions}</div>}
      </div>
    </div>
  );
}
