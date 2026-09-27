import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getResearchGaps, type ResearchGap } from '../services/api';
import { FileWarning, ArrowRight } from 'lucide-react';

export default function ResearchGapSummary() {
  const [gaps, setGaps] = useState<ResearchGap[]>([]);

  useEffect(() => {
    getResearchGaps().then(d => {
      const sorted = [...d].sort((a, b) => b.gap_score - a.gap_score);
      setGaps(sorted.slice(0, 5));
    }).catch(() => {});
  }, []);

  return (
    <div className="bg-brand-panel border border-brand-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <FileWarning className="text-emerald-400" size={18} />
          <h3 className="text-white font-semibold text-sm">Research Gap Summary</h3>
        </div>
        <Link to="/reports" className="text-xs text-brand-accent hover:underline flex items-center gap-1">
          All <ArrowRight size={10} />
        </Link>
      </div>
      {gaps.length === 0 ? (
        <p className="text-gray-500 text-xs text-center py-4">No gaps detected yet.</p>
      ) : (
        <div className="space-y-2">
          {gaps.map(g => (
            <div key={g.id} className="border-b border-brand-border last:border-0 pb-2 last:pb-0">
              <div className="flex items-start justify-between gap-2">
                <p className="text-xs text-gray-300 flex-1 truncate">{g.title}</p>
                <span className="text-xs font-mono text-emerald-400 flex-shrink-0">
                  {g.gap_score.toFixed(2)}
                </span>
              </div>
              <div className="w-full h-1 bg-brand-border rounded-full overflow-hidden mt-1">
                <div className="h-full bg-emerald-500" style={{ width: `${g.gap_score * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
