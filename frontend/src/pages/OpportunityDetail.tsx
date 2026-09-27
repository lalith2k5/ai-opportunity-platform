import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getOpportunityDetail } from '../services/api';
import {
  Loader2, ArrowLeft, Lightbulb, AlertCircle, TrendingUp,
  FileText, CheckCircle2, ExternalLink, Sparkles,
} from 'lucide-react';

function ScoreRow({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs text-ink-3">{label}</span>
        <span className="text-xs font-mono tabular-nums text-ink font-medium">{value.toFixed(2)}</span>
      </div>
      <div className="h-1.5 bg-overlay rounded-full overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${Math.min(100, value * 100)}%` }} />
      </div>
    </div>
  );
}

function Section({ icon: Icon, title, children, accent = 'text-accent' }: {
  icon: any; title: string; children: React.ReactNode; accent?: string;
}) {
  return (
    <div className="bg-surface border border-edge rounded-lg p-5">
      <div className="flex items-center gap-2 mb-4">
        <Icon size={14} className={accent} />
        <h2 className="text-xs font-medium text-ink uppercase tracking-wider">{title}</h2>
      </div>
      {children}
    </div>
  );
}

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
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="animate-spin text-accent" size={32} />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 max-w-3xl mx-auto">
        <Link to="/opportunities" className="btn-ghost text-xs mb-4">
          <ArrowLeft size={13} /> Back to opportunities
        </Link>
        <div className="bg-danger/10 border border-danger/30 rounded-lg p-5">
          <AlertCircle className="text-danger mb-2" size={20} />
          <p className="text-danger text-sm">{error || 'Opportunity not found'}</p>
        </div>
      </div>
    );
  }

  const opp = data.opportunity;
  const cluster = data.problem_cluster;
  const gap = data.research_gap;
  const isHigh = opp.opportunity_score > 0.6;

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto">

      {/* Back link */}
      <Link
        to="/opportunities"
        className="inline-flex items-center gap-1 text-xs text-ink-3 hover:text-ink transition-colors mb-6"
      >
        <ArrowLeft size={13} /> Back to opportunities
      </Link>

      {/* Hero */}
      <div className="bg-surface border border-edge rounded-lg p-6 mb-5">
        <div className="flex items-start justify-between gap-6 flex-wrap">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-3">
              <span className={`badge ${
                isHigh
                  ? 'bg-success/15 text-success border border-success/30'
                  : 'bg-accent/15 text-accent border border-accent/30'
              }`}>
                {isHigh ? 'High priority' : 'Moderate'}
              </span>
              <span className="text-2xs text-ink-4 font-mono">#{opp.id}</span>
            </div>
            <h1 className="text-2xl font-bold text-ink tracking-tight leading-tight mb-2">
              {opp.title}
            </h1>
            <p className="text-sm text-ink-2 leading-relaxed">{opp.description}</p>
          </div>

          <div className="text-right flex-shrink-0">
            <div className="flex items-baseline gap-1 justify-end">
              <span className="text-4xl font-bold text-accent font-mono tabular-nums leading-none tracking-tight">
                {opp.opportunity_score.toFixed(2)}
              </span>
              <span className="text-sm text-ink-4 font-mono">/1.00</span>
            </div>
            <p className="text-2xs text-ink-4 uppercase tracking-wider mt-2">Opportunity score</p>
            <p className="text-xs text-ink-3 mt-1 font-mono tabular-nums">
              Confidence {opp.confidence_score.toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      {/* Two-column: breakdown + explanation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">

        <Section icon={TrendingUp} title="Scoring breakdown">
          <div className="space-y-3.5">
            <ScoreRow label="Market demand"       value={opp.demand_score}            color="bg-accent" />
            <ScoreRow label="Research gap"        value={opp.research_gap_score}      color="bg-success" />
            <ScoreRow label="Technology trend"    value={opp.trend_score}             color="bg-warning" />
            <ScoreRow label="Competition"         value={opp.competition_score}       color="bg-danger" />
            <ScoreRow label="Technical feasibility" value={opp.feasibility_score}     color="bg-sky-500" />
            <ScoreRow label="Market readiness"    value={opp.market_readiness_score}  color="bg-purple-500" />
          </div>
        </Section>

        <Section icon={Sparkles} title="AI explanation" accent="text-warning">
          <p className="text-sm text-ink-2 leading-relaxed">
            {opp.explanation || 'No explanation available.'}
          </p>
          <div className="mt-4 pt-4 border-t border-edge-subtle">
            <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2">Best suited for</p>
            <p className="text-xs text-ink-2">
              {isHigh ? 'Researchers, entrepreneurs, and investors' : 'Students and early-stage researchers'}
            </p>
          </div>
        </Section>

      </div>

      {/* Problem cluster */}
      {cluster && (
        <div className="bg-surface border border-edge rounded-lg p-5 mb-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <AlertCircle size={14} className="text-warning" />
              <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Associated problem cluster</h2>
            </div>
            <span className="text-2xs text-ink-4 font-mono">{cluster.source_count} sources</span>
          </div>
          <p className="text-sm text-ink-2 leading-relaxed mb-3">{cluster.description}</p>
          {cluster.keywords?.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {cluster.keywords.slice(0, 12).map((kw: string) => (
                <span key={kw} className="badge bg-overlay text-ink-3 border border-edge">{kw}</span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Research gap */}
      {gap && (
        <div className="bg-surface border border-edge rounded-lg p-5 mb-5">
          <div className="flex items-center gap-2 mb-4">
            <FileText size={14} className="text-success" />
            <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Research gap analysis</h2>
          </div>
          <p className="text-sm text-ink-2 leading-relaxed mb-4">{gap.description}</p>

          <div className="grid grid-cols-2 gap-4 mb-4 pb-4 border-b border-edge-subtle">
            <div>
              <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Gap score</p>
              <p className="text-lg font-semibold text-success font-mono tabular-nums">
                {gap.gap_score.toFixed(2)}
              </p>
            </div>
            {gap.evidence?.coverage !== undefined && (
              <div>
                <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Coverage</p>
                <p className="text-lg font-semibold text-ink font-mono tabular-nums">
                  {(gap.evidence.coverage * 100).toFixed(0)}%
                </p>
              </div>
            )}
          </div>

          {gap.evidence?.future_work_snippets?.length > 0 && (
            <div>
              <p className="text-2xs text-ink-4 uppercase tracking-wider mb-3">Future-work signals from arXiv</p>
              <div className="space-y-3">
                {gap.evidence.future_work_snippets.slice(0, 3).map((fws: any, i: number) => (
                  <div key={i} className="pl-3 border-l-2 border-edge-strong">
                    <p className="text-xs text-ink-3 italic leading-relaxed">"{fws.snippet?.slice(0, 200)}…"</p>
                    <p className="text-2xs text-ink-4 mt-1">{fws.paper?.slice(0, 70)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Source references */}
      <Section icon={FileText} title="Source references">
        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle2 size={14} className="text-success flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-xs text-ink font-medium mb-0.5">Cluster keywords</p>
              <p className="text-xs text-ink-3">
                {cluster?.keywords?.slice(0, 8).join(' · ') || 'N/A'}
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <CheckCircle2 size={14} className="text-success flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-xs text-ink font-medium mb-0.5">Cluster size</p>
              <p className="text-xs text-ink-3">{cluster?.source_count || 0} sources analyzed</p>
            </div>
          </div>
          {gap && (
            <div className="flex items-start gap-3">
              <CheckCircle2 size={14} className="text-success flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-xs text-ink font-medium mb-0.5">Research coverage</p>
                <p className="text-xs text-ink-3">
                  {((gap.evidence?.coverage || 0) * 100).toFixed(0)}% of key terms appear in recent papers
                </p>
              </div>
            </div>
          )}
        </div>
      </Section>

      {/* Recommendation CTA */}
      <div className="mt-5 bg-surface border border-edge rounded-lg p-5 flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-start gap-3">
          <Lightbulb size={18} className="text-warning flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-ink font-medium">Recommended next step</p>
            <p className="text-xs text-ink-3 mt-0.5">
              Validate this opportunity with {cluster?.source_count || 'multiple'} real-world data points and run the AI chat for follow-up questions.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/chat" className="btn-secondary text-xs">
            <Sparkles size={13} /> Ask AI
          </Link>
          <Link to="/reports" className="btn-primary text-xs">
            <ExternalLink size={13} /> Add to report
          </Link>
        </div>
      </div>

    </div>
  );
}
