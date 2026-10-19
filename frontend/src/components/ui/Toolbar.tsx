
import type { ReactNode } from 'react';

export default function Toolbar({
  children,
  className = '',
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={
        'card p-3 mb-5 flex flex-col md:flex-row md:items-center gap-3 ' + className
      }
    >
      {children}
    </div>
  );
}

export function ToolbarSearch({
  value,
  onChange,
  placeholder = 'Search…',
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <input
      type="text"
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      className="input text-sm w-full md:flex-1 md:min-w-[240px]"
    />
  );
}

export function ToolbarSpacer() {
  return <div className="md:flex-1" />;
}
