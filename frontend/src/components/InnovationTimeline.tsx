import { useEffect, useState } from 'react';
import { getOpportunities, type Opportunity } from '../services/api';

function relativeTime(iso: string): string {
  if (!iso) return 'Recently';
  const diffMin = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
  if (diffMin < 1) return 'Just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 7) return `${diffDay}d ago`;
  return new Date(iso).toLocaleDateString();
}

export default function InnovationTimeline() {
  const [opps, setOpps] = useState<Opportunity[]>([]);

  useEffect(() => {
    getOpportunities().then(d => {
      const sorted = [...d].sort((a, b) => {
        const ta = a.created_at ? new Date(a.created_at).getTime() : 0;
        const tb = b.created_at ? new Date(b.created_at).getTime() : 0;
        return tb - ta;
      });
      setOpps(sorted.slice(0, 6));
    }).catch(() => {});
  }, []);

  if (opps.length === 0) {
    return <p className="text-xs text-ink-4 text-center py-4">No activity yet.</p>;
  }

  return (
    <div className="relative pl-3.5">
      <div className="absolute left-[3px] top-1.5 bottom-1.5 w-px bg-edge" />
      {opps.map((o) => (
        <div key={o.id} className="relative pb-3.5 last:pb-0">
          <div className={`absolute -left-3.5 top-1.5 w-1.5 h-1.5 rounded-full ${
            o.opportunity_score > 0.6 ? 'bg-success' : 'bg-accent'
          }`} />
          <p className="text-2xs text-ink-4 mb-0.5">{relativeTime(o.created_at || '')}</p>
          <p className="text-xs text-ink-2 leading-snug truncate">{o.title}</p>
          <p className="text-2xs font-mono tabular-nums text-ink-4 mt-0.5">
            {o.opportunity_score.toFixed(2)}
          </p>
        </div>
      ))}
    </div>
  );
}
