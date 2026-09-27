import type { LucideIcon } from 'lucide-react';

export default function StatCard({
  label,
  value,
  sublabel,
  icon: Icon,
  accent = false,
}: {
  label: string;
  value: string | number;
  sublabel?: string;
  icon?: LucideIcon;
  accent?: boolean;
}) {
  return (
    <div className="group relative bg-surface border border-edge rounded-lg p-4 hover:border-edge-strong transition-colors">
      <div className="flex items-center justify-between mb-3">
        <p className="text-2xs font-medium text-ink-4 uppercase tracking-wider">{label}</p>
        {Icon && (
          <Icon
            size={14}
            className={accent ? 'text-accent' : 'text-ink-4 group-hover:text-ink-3 transition-colors'}
          />
        )}
      </div>
      <p className="text-2xl font-semibold text-ink font-mono tabular-nums tracking-tight">
        {value}
      </p>
      {sublabel && <p className="text-2xs text-ink-4 mt-1">{sublabel}</p>}
    </div>
  );
}
