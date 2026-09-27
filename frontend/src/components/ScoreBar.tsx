export default function ScoreBar({
  label, value, max = 1, color = 'bg-accent',
}: { label: string; value: number; max?: number; color?: string }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="mb-2">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-ink-4">{label}</span>
        <span className="text-ink-3 font-mono tabular-nums">{value.toFixed(2)}</span>
      </div>
      <div className="h-2 bg-overlay rounded-full overflow-hidden">
        <div className={`h-full ${color} transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
