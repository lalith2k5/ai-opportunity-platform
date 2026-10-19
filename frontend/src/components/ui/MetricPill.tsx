
import type { LucideIcon } from 'lucide-react';

type Accent = 'default' | 'accent' | 'success' | 'warning' | 'purple' | 'sky';

const VALUE_COLOR: Record<Accent, string> = {
  default: 'text-ink',
  accent:  'text-accent',
  success: 'text-success',
  warning: 'text-warning',
  purple:  'text-purple-500',
  sky:     'text-sky-500',
};

export default function MetricPill({
  label,
  value,
  icon: Icon,
  accent = 'default',
  className = '',
}: {
  label: string;
  value: string | number;
  icon?: LucideIcon;
  accent?: Accent;
  className?: string;
}) {
  return (
    <div className={'card p-4 ' + className}>
      <div className="flex items-center justify-between mb-1.5">
        <p className="text-2xs text-ink-4 uppercase tracking-wider">{label}</p>
        {Icon && <Icon size={12} className="text-ink-4" />}
      </div>
      <p className={'text-2xl font-semibold font-mono tabular-nums leading-none ' + VALUE_COLOR[accent]}>
        {value}
      </p>
    </div>
  );
}
