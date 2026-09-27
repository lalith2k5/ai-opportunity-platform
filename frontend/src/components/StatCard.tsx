export default function StatCard({
  label, value, sublabel, color = 'text-brand-accent',
}: {
  label: string; value: string | number; sublabel?: string; color?: string;
}) {
  return (
    <div className="bg-brand-panel border border-brand-border rounded-xl p-5">
      <p className="text-sm text-gray-400 mb-1">{label}</p>
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
      {sublabel && <p className="text-xs text-gray-500 mt-1">{sublabel}</p>}
    </div>
  );
}
