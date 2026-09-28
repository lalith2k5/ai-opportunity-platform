import { Link } from 'react-router-dom';
import { ArrowUpRight } from 'lucide-react';
import type { Opportunity } from '../services/api';

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.min(100, value * 100);
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-2xs text-ink-4">{label}</span>
        <span className="text-2xs font-mono tabular-nums text-ink-3">{value.toFixed(2)}</span>
      </div>
      <div className="h-1 bg-overlay/70 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all duration-500 ease-smooth`}
          style={{ width: `${pct}%` }}
        />
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
  const isHigh = opp.opportunity_score > 0.6;

  return (
    <Link
      to={href}
      className="group relative block card card-hover p-5 overflow-hidden"
    >
      {/* Accent glow */}
      <div
        className="absolute -top-16 -right-16 w-40 h-40 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
        style={{
          background: isHigh
            ? 'radial-gradient(circle, rgb(var(--success) / 0.18), transparent 65%)'
            : 'radial-gradient(circle, rgb(var(--accent) / 0.18), transparent 65%)',
        }}
      />

      <div className="relative flex items-start justify-between gap-4 mb-3">
        <div className="min-w-0 flex-1">
          <h3 className="text-ink font-semibold text-sm leading-snug line-clamp-2 group-hover:text-accent transition-colors duration-200">
            {opp.title}
          </h3>
          <p className="text-xs text-ink-3 mt-1.5 line-clamp-2 leading-relaxed">
            {opp.description}
          </p>
        </div>
        <div className="text-right flex-shrink-0">
          <p className={`text-2xl font-bold font-mono tabular-nums leading-none tracking-tight ${
            isHigh ? 'text-success' : 'text-accent'
          }`}>
            {opp.opportunity_score.toFixed(2)}
          </p>
          <p className="text-2xs text-ink-4 mt-1.5 uppercase tracking-[0.08em]">Score</p>
        </div>
      </div>

      <div className="relative grid grid-cols-2 gap-x-5 gap-y-2.5 mt-4 pt-4 border-t border-edge-subtle">
        <ScoreBar label="Demand"      value={opp.demand_score}       color="bg-accent" />
        <ScoreBar label="Research"    value={opp.research_gap_score} color="bg-success" />
        <ScoreBar label="Trend"       value={opp.trend_score}        color="bg-warning" />
        <ScoreBar label="Feasibility" value={opp.feasibility_score}  color="bg-sky-500" />
      </div>

      <div className="relative flex items-center justify-between mt-4 pt-3.5 border-t border-edge-subtle">
        <span className="text-2xs text-ink-4 uppercase tracking-[0.08em]">
          Confidence {opp.confidence_score.toFixed(2)}
        </span>
        <span className="text-2xs text-accent font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all duration-200 -translate-x-1 group-hover:translate-x-0">
          View <ArrowUpRight size={11} />
        </span>
      </div>
    </Link>
  );
}
