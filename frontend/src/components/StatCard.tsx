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
    <div className="group relative card card-hover p-5 overflow-hidden">
      {/* Ambient accent glow on hover */}
      {accent && (
        <div
          className="absolute -top-12 -right-12 w-32 h-32 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgb(var(--accent) / 0.20), transparent 65%)' }}
        />
      )}
      <div className="relative flex items-center justify-between mb-4">
        <p className="text-2xs font-medium text-ink-4 uppercase tracking-[0.08em]">{label}</p>
        {Icon && (
          <div className={`w-7 h-7 rounded-md flex items-center justify-center transition-transform duration-300 ease-apple group-hover:scale-110 ${
            accent ? 'bg-accent/10 text-accent' : 'bg-overlay text-ink-4 group-hover:text-ink-2'
          }`}>
            <Icon size={14} />
          </div>
        )}
      </div>
      <p className="relative text-3xl font-semibold text-ink font-mono tabular-nums tracking-tight leading-none">
        {value}
      </p>
      {sublabel && <p className="relative text-2xs text-ink-4 mt-2">{sublabel}</p>}
    </div>
  );
}
