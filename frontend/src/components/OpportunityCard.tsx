import { Link } from 'react-router-dom';
import { ArrowUpRight } from 'lucide-react';
import type { Opportunity } from '../services/api';

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.min(100, value * 100);
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-2xs text-ink-4">{label}</span>
        <span className="text-2xs font-mono tabular-nums text-ink-3">{value.toFixed(2)}</span>
      </div>
      <div className="h-1 bg-overlay rounded-full overflow-hidden">
        <div className={`h-full ${color} transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function OpportunityCard({
  opp,
  to,
}: {
  opp: Opportunity;
  to?: string;
}) {
  const href = to ?? `/opportunities/${opp.id}`;
  return (
    <Link
      to={href}
      className="group block bg-surface border border-edge rounded-lg p-4 hover:border-accent/40 hover:bg-overlay hover:-translate-y-[1px] hover:shadow-md transition-all duration-150"
    >
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="min-w-0 flex-1">
          <h3 className="text-ink font-medium text-sm leading-snug line-clamp-2 group-hover:text-accent transition-colors">
            {opp.title}
          </h3>
          <p className="text-xs text-ink-3 mt-1 line-clamp-2 leading-relaxed">
            {opp.description}
          </p>
        </div>
        <div className="text-right flex-shrink-0">
          <p className="text-xl font-semibold font-mono tabular-nums text-accent leading-none">
            {opp.opportunity_score.toFixed(2)}
          </p>
          <p className="text-2xs text-ink-4 mt-1 uppercase tracking-wider">Score</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-x-5 gap-y-2 mt-3 pt-3 border-t border-edge-subtle">
        <ScoreBar label="Demand"      value={opp.demand_score}       color="bg-accent" />
        <ScoreBar label="Research"    value={opp.research_gap_score} color="bg-success" />
        <ScoreBar label="Trend"       value={opp.trend_score}        color="bg-warning" />
        <ScoreBar label="Feasibility" value={opp.feasibility_score}  color="bg-sky-500" />
      </div>

      <div className="flex items-center justify-between mt-3 pt-2.5 border-t border-edge-subtle">
        <span className="text-2xs text-ink-4 uppercase tracking-wider">
          Confidence {opp.confidence_score.toFixed(2)}
        </span>
        <span className="text-2xs text-accent font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          View <ArrowUpRight size={11} />
        </span>
      </div>
    </Link>
  );
}
