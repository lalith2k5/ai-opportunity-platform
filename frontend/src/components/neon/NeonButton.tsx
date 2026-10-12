
import type { ReactNode } from 'react';

export default function NeonButton({
  children,
  onClick,
  type = 'button',
  disabled = false,
  className = '',
}: {
  children: ReactNode;
  onClick?: () => void;
  type?: 'button' | 'submit';
  disabled?: boolean;
  className?: string;
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`neon-btn ${className}`}
    >
      {children}
    </button>
  );
}
