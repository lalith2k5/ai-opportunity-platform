import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getOpportunities, type Opportunity } from '../services/api';
import { Sparkles, ArrowRight } from 'lucide-react';

export default function AIRecommendationsPanel() {
  const [recs, setRecs] = useState<Opportunity[]>([]);

  useEffect(() => {
    getOpportunities().then(d => {
      // Top 3 by score with strong feasibility
      const top = [...d]
        .filter(o => o.feasibility_score >= 0.5)
        .sort((a, b) => b.opportunity_score - a.opportunity_score)
        .slice(0, 3);
      setRecs(top);
    }).catch(() => {});
  }, []);

  return (
    <div className="bg-brand-panel border border-brand-border rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="text-yellow-400" size={18} />
        <h3 className="text-white font-semibold text-sm">AI Recommendations</h3>
      </div>
      {recs.length === 0 ? (
        <p className="text-gray-500 text-xs text-center py-4">No recommendations yet.</p>
      ) : (
        <div className="space-y-3">
          {recs.map(o => (
            <Link
              key={o.id}
              to={`/opportunities/${o.id}`}
              className="block border border-brand-border rounded-lg p-3 hover:border-brand-accent transition-colors"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-xs text-white leading-tight flex-1">{o.title}</p>
                <span className="text-xs font-mono text-brand-accent flex-shrink-0">
                  {o.opportunity_score.toFixed(2)}
                </span>
              </div>
              <p className="text-[10px] text-gray-500 mt-1 line-clamp-2">
                {o.explanation?.slice(0, 100) || o.description?.slice(0, 100)}...
              </p>
              <div className="flex items-center gap-1 text-[10px] text-brand-accent mt-1">
                View <ArrowRight size={10} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
