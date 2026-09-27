import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';

export default function EmptyState({
  icon: Icon,
  title,
  message,
  action,
}: {
  icon: LucideIcon;
  title: string;
  message?: string;
  action?: ReactNode;
}) {
  return (
    <div className="border border-edge border-dashed rounded-lg p-10 text-center bg-surface/40">
      <div className="w-10 h-10 rounded-lg bg-overlay border border-edge flex items-center justify-center mx-auto mb-3">
        <Icon size={16} className="text-ink-4" />
      </div>
      <p className="text-sm text-ink-2 font-medium">{title}</p>
      {message && <p className="text-xs text-ink-4 mt-1 max-w-sm mx-auto leading-relaxed">{message}</p>}
      {action && <div className="mt-4 flex justify-center">{action}</div>}
    </div>
  );
}
