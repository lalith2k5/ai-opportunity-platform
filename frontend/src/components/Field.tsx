import type { ReactNode } from 'react';

export function Field({
  label,
  htmlFor,
  hint,
  action,
  children,
}: {
  label: string;
  htmlFor?: string;
  hint?: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <label htmlFor={htmlFor} className="text-xs font-medium text-ink-2">
          {label}
        </label>
        {action}
      </div>
      {children}
      {hint && <p className="text-2xs text-ink-4 mt-1.5">{hint}</p>}
    </div>
  );
}

export function Alert({
  type,
  children,
}: {
  type: 'error' | 'success' | 'info';
  children: ReactNode;
}) {
  const styles = {
    error:   'bg-danger/10 border-danger/30 text-danger',
    success: 'bg-success/10 border-success/30 text-success',
    info:    'bg-accent/10 border-accent/30 text-ink-2',
  }[type];
  return (
    <div className={`text-xs border rounded-md px-3 py-2.5 animate-slide-up ${styles}`}>
      {children}
    </div>
  );
}
