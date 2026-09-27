import { Lightbulb, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import ScoreBar from './ScoreBar';
import type { Opportunity } from '../services/api';

export default function OpportunityCard({ opp }: { opp: Opportunity }) {
  return (
    <Link to={`/opportunities/${opp.id}`} className="block bg-brand-panel border border-brand-border rounded-xl p-5 hover:border-brand-accent transition-colors cursor-pointer">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start gap-3 flex-1">
          <Lightbulb className="text-yellow-400 mt-1 flex-shrink-0" size={20} />
          <div className="flex-1">
            <h3 className="text-white font-semibold leading-tight">{opp.title}</h3>
            <p className="text-sm text-gray-400 mt-1">{opp.description}</p>
          </div>
        </div>
        <div className="text-right ml-4">
          <p className="text-2xl font-bold text-brand-accent">{opp.opportunity_score.toFixed(2)}</p>
          <p className="text-xs text-gray-500">Score</p>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-x-6 gap-y-1 mt-3">
        <ScoreBar label="Demand" value={opp.demand_score} />
        <ScoreBar label="Research Gap" value={opp.research_gap_score} />
        <ScoreBar label="Trend" value={opp.trend_score} color="bg-emerald-500" />
        <ScoreBar label="Feasibility" value={opp.feasibility_score} color="bg-blue-500" />
      </div>
      {opp.explanation && (
        <p className="mt-3 text-xs text-gray-400 italic border-t border-brand-border pt-3">
          {opp.explanation}
        </p>
      )}
      <div className="mt-3 text-xs text-brand-accent flex items-center gap-1">
        View details <ArrowRight size={12} />
      </div>
    </Link>
  );
}
