
export interface SegmentOption {
  value: string;
  label: string;
}

export default function SegmentedControl({
  value,
  onChange,
  options,
  size = 'md',
  className = '',
}: {
  value: string;
  onChange: (v: string) => void;
  options: SegmentOption[];
  size?: 'sm' | 'md';
  className?: string;
}) {
  const padding = size === 'sm' ? 'px-2.5 py-1 text-2xs' : 'px-3 py-1.5 text-xs';
  return (
    <div
      className={
        'inline-flex items-center p-0.5 bg-canvas border border-edge rounded-md ' + className
      }
    >
      {options.map(opt => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={
              padding +
              ' rounded font-medium transition-all duration-200 ease-smooth ' +
              (active
                ? 'bg-overlay text-ink shadow-[0_1px_2px_rgb(0_0_0/0.3)]'
                : 'text-ink-3 hover:text-ink-2')
            }
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
