import { useEffect, useState } from 'react';
import { getOpportunities, type Opportunity } from '../services/api';
import { Clock, TrendingUp } from 'lucide-react';

function relativeTime(iso: string): string {
  if (!iso) return 'Recently';
  const then = new Date(iso).getTime();
  const now = Date.now();
  const diffMin = Math.floor((now - then) / 60000);
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
      setOpps(sorted.slice(0, 8));
    }).catch(() => {});
  }, []);

  return (
    <div className="bg-brand-panel border border-brand-border rounded-xl p-4">
      <div className="flex items-center gap-2 mb-4">
        <Clock className="text-brand-accent" size={18} />
        <h3 className="text-white font-semibold text-sm">Innovation Timeline</h3>
      </div>
      {opps.length === 0 ? (
        <p className="text-gray-500 text-xs text-center py-4">No activity yet.</p>
      ) : (
        <div className="relative pl-4">
          <div className="absolute left-0 top-1 bottom-1 w-px bg-brand-border" />
          {opps.map((o, i) => (
            <div key={o.id} className="relative pb-4 last:pb-0">
              <div className={`absolute -left-4 top-1 w-2 h-2 rounded-full ${
                o.opportunity_score > 0.6 ? 'bg-emerald-400' : 'bg-brand-accent'
              }`} />
              <p className="text-xs text-gray-500 mb-0.5">
                {relativeTime(o.created_at || '')}
              </p>
              <p className="text-xs text-gray-300 leading-tight truncate">{o.title}</p>
              <p className="text-[10px] text-gray-500 flex items-center gap-1 mt-0.5">
                <TrendingUp size={10} /> score {o.opportunity_score.toFixed(2)}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
