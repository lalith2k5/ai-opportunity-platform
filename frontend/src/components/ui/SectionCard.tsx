
import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';

type Accent = 'accent' | 'purple' | 'sky' | 'success' | 'warning' | 'orange' | 'muted';

const ACCENT: Record<Accent, string> = {
  accent:  'text-accent',
  purple:  'text-purple-500',
  sky:     'text-sky-500',
  success: 'text-success',
  warning: 'text-warning',
  orange:  'text-orange-500',
  muted:   'text-ink-3',
};

export default function SectionCard({
  icon: Icon,
  title,
  accent = 'accent',
  actions,
  children,
  className = '',
  density = 'normal',
}: {
  icon?: LucideIcon;
  title?: string;
  accent?: Accent;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  density?: 'normal' | 'compact';
}) {
  const pad = density === 'compact' ? 'p-4' : 'p-5';
  return (
    <div className={'card ' + pad + ' mb-5 ' + className}>
      {(Icon || title) && (
        <div className="flex items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-2 min-w-0">
            {Icon && <Icon size={14} className={ACCENT[accent]} />}
            {title && (
              <h2 className="text-2xs font-semibold text-ink uppercase tracking-[0.08em] truncate">
                {title}
              </h2>
            )}
          </div>
          {actions && <div className="flex items-center gap-1.5 flex-shrink-0">{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

export function EmptyNote({ children }: { children: ReactNode }) {
  return <p className="text-xs text-ink-4 italic">{children}</p>;
}
