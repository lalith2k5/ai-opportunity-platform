import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getOpportunities, type Opportunity } from '../services/api';


export default function AIRecommendationsPanel() {
  const [recs, setRecs] = useState<Opportunity[]>([]);

  useEffect(() => {
    getOpportunities().then(d => {
      const top = [...d]
        .filter(o => o.feasibility_score >= 0.5)
        .sort((a, b) => b.opportunity_score - a.opportunity_score)
        .slice(0, 3);
      setRecs(top);
    }).catch(() => {});
  }, []);

  if (recs.length === 0) {
    return <p className="text-xs text-ink-4 text-center py-4">No recommendations yet.</p>;
  }

  return (
    <div className="space-y-2">
      {recs.map(o => (
        <Link
          key={o.id}
          to={`/opportunities/${o.id}`}
          className="group block py-2 px-2 -mx-2 rounded-md hover:bg-overlay transition-colors"
        >
          <div className="flex items-start justify-between gap-3 mb-0.5">
            <p className="text-xs text-ink-2 leading-snug truncate flex-1 group-hover:text-accent transition-colors">
              {o.title}
            </p>
            <span className="text-2xs font-mono tabular-nums text-accent flex-shrink-0">
              {o.opportunity_score.toFixed(2)}
            </span>
          </div>
          <p className="text-2xs text-ink-4 leading-snug line-clamp-2">
            {o.explanation?.slice(0, 90) || o.description?.slice(0, 90)}…
          </p>
        </Link>
      ))}
    </div>
  );
}
