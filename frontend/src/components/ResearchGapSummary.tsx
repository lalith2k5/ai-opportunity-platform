import { useEffect, useState } from 'react';
import { getResearchGaps, type ResearchGap } from '../services/api';

export default function ResearchGapSummary() {
  const [gaps, setGaps] = useState<ResearchGap[]>([]);

  useEffect(() => {
    getResearchGaps().then(d => {
      const sorted = [...d].sort((a, b) => b.gap_score - a.gap_score);
      setGaps(sorted.slice(0, 4));
    }).catch(() => {});
  }, []);

  if (gaps.length === 0) {
    return <p className="text-xs text-ink-4 text-center py-4">No gaps detected yet.</p>;
  }

  return (
    <div className="space-y-2.5">
      {gaps.map(g => (
        <div key={g.id}>
          <div className="flex items-start justify-between gap-2 mb-1">
            <p className="text-xs text-ink-2 leading-snug truncate flex-1">{g.title}</p>
            <span className="text-2xs font-mono tabular-nums text-success flex-shrink-0">
              {g.gap_score.toFixed(2)}
            </span>
          </div>
          <div className="w-full h-1 bg-overlay rounded-full overflow-hidden">
            <div className="h-full bg-success" style={{ width: `${g.gap_score * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}
