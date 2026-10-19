
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

type Accent = 'accent' | 'purple' | 'sky' | 'success' | 'warning' | 'muted' | 'danger';

const ICON_BG: Record<Accent, string> = {
  accent:  'bg-accent/10',
  purple:  'bg-purple-500/10',
  sky:     'bg-sky-500/10',
  success: 'bg-success/10',
  warning: 'bg-warning/10',
  danger:  'bg-danger/10',
  muted:   'bg-overlay',
};

const ICON_FG: Record<Accent, string> = {
  accent:  'text-accent',
  purple:  'text-purple-500',
  sky:     'text-sky-500',
  success: 'text-success',
  warning: 'text-warning',
  danger:  'text-danger',
  muted:   'text-ink-3',
};

export default function ListRow({
  to,
  onClick,
  icon: Icon,
  accent = 'accent',
  title,
  subtitle,
  meta,
  trailing,
  external = false,
  className = '',
}: {
  to?: string;
  onClick?: () => void;
  icon?: LucideIcon;
  accent?: Accent;
  title: ReactNode;
  subtitle?: ReactNode;
  meta?: ReactNode;
  trailing?: ReactNode;
  external?: boolean;
  className?: string;
}) {
  const inner = (
    <div
      className={
        'group flex items-start gap-3 px-3 py-3 rounded-md transition-colors ' +
        (to || onClick ? 'hover:bg-overlay cursor-pointer ' : '') +
        className
      }
    >
      {Icon && (
        <div
          className={
            'w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ' +
            ICON_BG[accent]
          }
        >
          <Icon size={15} className={ICON_FG[accent]} />
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="text-sm text-ink-2 leading-snug group-hover:text-accent transition-colors line-clamp-2">
          {title}
        </div>
        {subtitle && (
          <div className="text-xs text-ink-3 leading-relaxed mt-1 line-clamp-2">
            {subtitle}
          </div>
        )}
        {meta && <div className="flex flex-wrap gap-1.5 mt-1.5">{meta}</div>}
      </div>
      <div className="flex items-center gap-2 flex-shrink-0 self-center">
        {trailing}
        {(to || onClick) && !external && (
          <ChevronRight
            size={14}
            className="text-ink-4 group-hover:text-accent group-hover:translate-x-0.5 transition-all duration-200 ease-apple"
          />
        )}
      </div>
    </div>
  );

  if (to && !external) {
    return <Link to={to}>{inner}</Link>;
  }
  if (to && external) {
    return (
      <a href={to} target="_blank" rel="noreferrer">
        {inner}
      </a>
    );
  }
  if (onClick) {
    return (
      <button type="button" onClick={onClick} className="w-full text-left">
        {inner}
      </button>
    );
  }
  return inner;
}
