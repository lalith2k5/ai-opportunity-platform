import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getOpportunityDetail } from '../services/api';
import ScoreBar from '../components/ScoreBar';
import { Loader2, ArrowLeft, Lightbulb, AlertCircle, TrendingUp, FileText, CheckCircle2 } from 'lucide-react';

export default function OpportunityDetail() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    getOpportunityDetail(Number(id))
      .then(setData)
      .catch(e => setError(e?.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return <div className="flex items-center justify-center h-screen"><Loader2 className="animate-spin text-brand-accent" size={48} /></div>;
  }

  if (error || !data) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <Link to="/" className="text-brand-accent hover:underline flex items-center gap-1 mb-4">
          <ArrowLeft size={16} /> Back to dashboard
        </Link>
        <div className="bg-red-900/30 border border-red-700 rounded-xl p-6">
          <AlertCircle className="text-red-400 mb-2" size={32} />
          <p className="text-red-300">{error || 'Opportunity not found'}</p>
        </div>
      </div>
    );
  }

  const opp = data.opportunity;
  const cluster = data.problem_cluster;
  const gap = data.research_gap;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <Link to="/" className="text-brand-accent hover:underline flex items-center gap-1 mb-6 text-sm">
        <ArrowLeft size={16} /> Back to dashboard
      </Link>

      <div className="bg-brand-panel border border-brand-border rounded-xl p-6 mb-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 flex-1">
            <Lightbulb className="text-yellow-400 mt-1 flex-shrink-0" size={28} />
            <div>
              <h1 className="text-2xl font-bold text-white leading-tight">{opp.title}</h1>
              <p className="text-gray-400 mt-2">{opp.description}</p>
            </div>
          </div>
          <div className="text-right flex-shrink-0">
            <p className="text-4xl font-bold text-brand-accent">{opp.opportunity_score.toFixed(2)}</p>
            <p className="text-xs text-gray-500 mt-1">Opportunity Score</p>
            <p className="text-xs text-gray-500 mt-1">Confidence {opp.confidence_score.toFixed(2)}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-brand-panel border border-brand-border rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="text-brand-accent" size={20} /> Scoring Breakdown
          </h2>
          <ScoreBar label="Market Demand" value={opp.demand_score} />
          <ScoreBar label="Research Gap" value={opp.research_gap_score} />
          <ScoreBar label="Technology Trend" value={opp.trend_score} color="bg-emerald-500" />
          <ScoreBar label="Competition" value={opp.competition_score} color="bg-red-500" />
          <ScoreBar label="Technical Feasibility" value={opp.feasibility_score} color="bg-blue-500" />
          <ScoreBar label="Market Readiness" value={opp.market_readiness_score} color="bg-purple-500" />
        </div>

        <div className="bg-brand-panel border border-brand-border rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <CheckCircle2 className="text-emerald-400" size={20} /> AI Explanation
          </h2>
          <p className="text-sm text-gray-300 leading-relaxed">
            {opp.explanation || 'No explanation available.'}
          </p>
        </div>
      </div>

      {cluster && (
        <div className="bg-brand-panel border border-brand-border rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <AlertCircle className="text-orange-400" size={20} /> Associated Problem Cluster
          </h2>
          <p className="text-gray-300 text-sm mb-2">{cluster.description}</p>
          <p className="text-xs text-gray-500 mb-3">
            Derived from {cluster.source_count} sources
          </p>
          {cluster.keywords && cluster.keywords.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {cluster.keywords.slice(0, 10).map((kw: string) => (
                <span key={kw} className="bg-brand-border text-gray-300 text-xs px-2 py-1 rounded">
                  {kw}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {gap && (
        <div className="bg-brand-panel border border-brand-border rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <FileText className="text-emerald-400" size={20} /> Research Gap Analysis
          </h2>
          <p className="text-gray-300 text-sm mb-3">{gap.description}</p>
          <div className="flex items-center gap-4 text-xs">
            <span className="text-gray-500">Gap Score:</span>
            <span className="text-emerald-400 font-mono">{gap.gap_score.toFixed(2)}</span>
            {gap.evidence?.coverage !== undefined && (
              <>
                <span className="text-gray-500">Research Coverage:</span>
                <span className="text-gray-300 font-mono">{(gap.evidence.coverage * 100).toFixed(0)}%</span>
              </>
            )}
          </div>
        </div>
      )}

      <div className="bg-brand-panel border border-brand-border rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <FileText className="text-brand-accent" size={20} /> Recommendation Summary
        </h2>
        <ul className="text-sm text-gray-300 space-y-2">
          <li>• <strong className="text-white">Type:</strong> {opp.opportunity_score > 0.6 ? 'High-priority opportunity' : 'Moderate opportunity'}</li>
          <li>• <strong className="text-white">Best for:</strong> Researchers & entrepreneurs</li>
          <li>• <strong className="text-white">Suggested action:</strong> Validate with {cluster?.source_count || 'multiple'} real-world data points</li>
        </ul>
      </div>
    </div>
  );
}
