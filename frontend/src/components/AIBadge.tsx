
import { Sparkles } from 'lucide-react';

export default function AIBadge({ label = 'AI-generated' }: { label?: string }) {
  return (
    <span className="badge bg-accent/10 text-accent border border-accent/30">
      <Sparkles size={10} /> {label}
    </span>
  );
}
