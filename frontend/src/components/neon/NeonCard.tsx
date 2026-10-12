
import type { ReactNode } from 'react';

export default function NeonCard({
  children,
  className = '',
  onClick,
  accent = 'blue',
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
  accent?: 'blue' | 'purple' | 'cyan' | 'orange';
  delay?: number;
}) {
  const accentMap: Record<string, string> = {
    blue: 'shadow-[0_0_24px_-4px_rgba(0,212,255,0.4)]',
    purple: 'shadow-[0_0_24px_-4px_rgba(168,85,247,0.4)]',
    cyan: 'shadow-[0_0_24px_-4px_rgba(34,211,238,0.4)]',
    orange: 'shadow-[0_0_24px_-4px_rgba(255,140,66,0.4)]',
  };

  return (
    <div
      onClick={onClick}
      className={`neon-card neon-fade-up ${accentMap[accent] || ''} ${className}`}
      style={{ animationDelay: `${delay}ms` }}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {children}
    </div>
  );
}
