import { useEffect, useState } from 'react';
import { useParams, useLocation, Link } from 'react-router-dom';
import { getOpportunityDetail, getOpportunityRecommendations } from '../services/api';
import {
  Loader2, ArrowLeft, Lightbulb, AlertCircle, TrendingUp,
  FileText, CheckCircle2, ExternalLink, Sparkles, Cpu, Target,
  FlaskConical, BookOpen, Zap, Shield,
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

function Section({
  icon: Icon, title, children, accent = 'text-accent',
}: { icon: any; title: string; children: React.ReactNode; accent?: string }) {
  return (
    <div className="card p-5">
      <div className="flex items-center gap-2 mb-4">
        <Icon size={14} className={accent} />
        <h2 className="text-2xs font-semibold text-ink uppercase tracking-[0.08em]">{title}</h2>
      </div>
      {children}
    </div>
  );
}

function EmptyNote({ children }: { children: React.ReactNode }) {
  return <p className="text-xs text-ink-4 italic">{children}</p>;
}

function AiBadge() {
  return (
    <span className="badge bg-accent/10 text-accent border border-accent/30">
      <Sparkles size={10} /> AI-generated
    </span>
  );
}

export default function OpportunityDetail() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const backTo = location.pathname.startsWith('/workflows/student')
    ? '/workflows/student'
    : '/opportunities';
  const backLabel = backTo === '/workflows/student'
    ? 'Back to student workflow'
    : 'Back to opportunities';
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [recHistory, setRecHistory] = useState<any[]>([]);

  useEffect(() => {
    if (!id) return;
    getOpportunityDetail(Number(id))
      .then(setData)
      .catch(e => setError(e?.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!id) return;
    getOpportunityRecommendations(Number(id), 20)
      .then((d: any) => setRecHistory(d.recommendations || []))
      .catch(() => setRecHistory([]));
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
  const organization = data.opportunity?.organization;
  const problemProfile = data.problem_profile;
  const linkedPapers = data.linked_papers || [];
  const isHigh = opp.opportunity_score > 0.6;

  const techs: string[] = Array.isArray(opp.related_technologies) ? opp.related_technologies : [];
  const papers: string[] = Array.isArray(opp.existing_research) ? opp.existing_research : [];
  const evidence: { source: string; url: string; title: string }[] =
    Array.isArray(opp.evidence_sources) ? opp.evidence_sources : [];
  const limitations = (opp.known_limitations || '').split(' | ').map((s: string) => s.trim()).filter(Boolean);
  const hasEnrichment = Boolean(
    opp.domain || opp.industry || techs.length || papers.length ||
    opp.suggested_research_direction || opp.suggested_project_direction ||
    opp.existing_approaches || opp.known_limitations || opp.emerging_trend || evidence.length
  );

  // Group evidence by source for compact display
  const evidenceBySource: Record<string, typeof evidence> = {};
  for (const e of evidence) {
    (evidenceBySource[e.source] = evidenceBySource[e.source] || []).push(e);
  }

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto">

      {/* Back link */}
      <Link
        to={backTo}
        className="inline-flex items-center gap-1.5 text-xs text-ink-3 hover:text-accent transition-colors mb-6 group"
      >
        <ArrowLeft size={13} className="transition-transform group-hover:-translate-x-0.5" /> {backLabel}
      </Link>

      {/* Hero */}
      <div className="card p-6 mb-5 relative overflow-hidden">
        {/* Ambient glow */}
        <div
          className="absolute -top-32 -right-32 w-96 h-96 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgb(var(--accent) / 0.12), transparent 60%)' }}
        />
        <div className="flex items-start justify-between gap-6 flex-wrap">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-3 flex-wrap">
              <span className={`badge ${
                isHigh
                  ? 'bg-success/15 text-success border border-success/30'
                  : 'bg-accent/15 text-accent border border-accent/30'
              }`}>
                {isHigh ? 'High priority' : 'Moderate'}
              </span>
              {opp.domain && (
                <span className="badge bg-overlay text-ink-3 border border-edge">
                  {opp.domain}
                </span>
              )}
              {opp.industry && opp.industry !== opp.domain && (
                <span className="badge bg-overlay text-ink-3 border border-edge">
                  {opp.industry}
                </span>
              )}
              {opp.emerging_trend && (
                <span className="badge bg-warning/15 text-warning border border-warning/30">
                  <TrendingUp size={10} /> {opp.emerging_trend}
                </span>
              )}
              {organization?.name && (
                <span className="badge bg-overlay text-ink-3 border border-edge">
                  {organization.name}
                </span>
              )}
              <span className="text-2xs text-ink-4 font-mono">#{opp.id}</span>
            </div>
            <h1 className="text-3xl font-bold text-ink tracking-tight leading-tight mb-3">
              {opp.title}
            </h1>
            <p className="text-sm text-ink-2 leading-relaxed">{opp.description}</p>
          </div>

          <div className="text-right flex-shrink-0">
            <div className="flex items-baseline gap-1 justify-end">
              <span className={`text-5xl font-bold font-mono tabular-nums leading-none tracking-tight ${isHigh ? 'text-success' : 'text-accent'}`}>
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

      {/* Suggested directions (top placement — most actionable) */}
      {(opp.suggested_research_direction || opp.suggested_project_direction) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
          {opp.suggested_research_direction && (
            <div className="card p-5 border-accent/30"
              style={{ background: 'linear-gradient(135deg, rgb(var(--accent) / 0.08), rgb(var(--accent) / 0.02))' }}>
              <div className="flex items-center gap-2 mb-3">
                <FlaskConical size={14} className="text-accent" />
                <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Suggested research</h2>
                <AiBadge />
              </div>
              <p className="text-sm text-ink leading-relaxed">
                {opp.suggested_research_direction}
              </p>
            </div>
          )}
          {opp.suggested_project_direction && (
            <div className="card p-5 border-success/30"
              style={{ background: 'linear-gradient(135deg, rgb(var(--success) / 0.08), rgb(var(--success) / 0.02))' }}>
              <div className="flex items-center gap-2 mb-3">
                <Zap size={14} className="text-success" />
                <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Suggested project</h2>
                <AiBadge />
              </div>
              <p className="text-sm text-ink leading-relaxed">
                {opp.suggested_project_direction}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Two-column: scoring + explanation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        <Section icon={TrendingUp} title="Scoring breakdown">
          <div className="space-y-3.5">
            <ScoreRow label="Market demand"          value={opp.demand_score}            color="bg-accent" />
            <ScoreRow label="Research gap"           value={opp.research_gap_score}      color="bg-success" />
            <ScoreRow label="Technology trend"       value={opp.trend_score}             color="bg-warning" />
            <ScoreRow label="Innovation"             value={opp.innovation_score ?? 0}   color="bg-pink-500" />
            <ScoreRow label="Competition"            value={opp.competition_score}       color="bg-danger" />
            <ScoreRow label="Technical feasibility"  value={opp.feasibility_score}       color="bg-sky-500" />
            <ScoreRow label="Market readiness"       value={opp.market_readiness_score}  color="bg-purple-500" />
            <ScoreRow label="Technology suitability" value={opp.technology_suitability_score ?? 0} color="bg-cyan-500" />
            <ScoreRow label="Evidence strength"      value={opp.evidence_strength_score ?? 0}      color="bg-lime-500" />
            <ScoreRow label="Recency"                value={opp.recency_score ?? 0}                color="bg-orange-500" />
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

      {/* Enrichment card */}
      {hasEnrichment ? (
        <div className="card p-5 mb-5">
          <div className="flex items-center gap-2 mb-5">
            <Target size={14} className="text-accent" />
            <h2 className="text-2xs font-semibold text-ink uppercase tracking-[0.08em]">Opportunity card enrichment</h2>
            <AiBadge />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

            {techs.length > 0 && (
              <div>
                <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Cpu size={11} /> Related technologies
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {techs.map(t => (
                    <span key={t} className="badge bg-accent/10 text-accent border border-accent/30">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {papers.length > 0 && (
              <div>
                <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <BookOpen size={11} /> Existing research ({papers.length})
                </p>
                <ul className="space-y-1.5">
                  {papers.slice(0, 6).map((p, i) => (
                    <li key={i} className="text-xs text-ink-2 leading-snug">
                      <span className="text-ink-4 font-mono mr-1.5">{i + 1}.</span>
                      {p}
                    </li>
                  ))}
                  {papers.length > 6 && (
                    <li className="text-2xs text-ink-4 italic">+{papers.length - 6} more</li>
                  )}
                </ul>
              </div>
            )}

            {opp.existing_approaches && (
              <div className="md:col-span-2">
                <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <FileText size={11} /> Existing approaches
                </p>
                <p className="text-xs text-ink-2 leading-relaxed">{opp.existing_approaches}</p>
              </div>
            )}

            {limitations.length > 0 && (
              <div className="md:col-span-2">
                <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <AlertCircle size={11} /> Known limitations
                </p>
                <ul className="space-y-1.5">
                  {limitations.slice(0, 8).map((lim: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-ink-2 leading-relaxed">
                      <span className="text-warning flex-shrink-0 mt-0.5">•</span>
                      <span>{lim}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {evidence.length > 0 && (
              <div className="md:col-span-2">
                <p className="text-2xs text-ink-4 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <Shield size={11} /> Evidence sources ({evidence.length})
                </p>
                <div className="space-y-3">
                  {Object.entries(evidenceBySource).map(([src, items]) => (
                    <div key={src}>
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="badge bg-overlay text-ink-3 border border-edge uppercase">
                          {src}
                        </span>
                        <span className="text-2xs text-ink-4 font-mono">{items.length}</span>
                      </div>
                      <div className="space-y-1">
                        {items.slice(0, 4).map((e, i) => (
                          <a
                            key={i}
                            href={e.url}
                            target="_blank"
                            rel="noreferrer"
                            className="flex items-start gap-2 px-2.5 py-1.5 rounded-md border border-edge-subtle hover:border-accent/40 hover:bg-overlay transition-colors group"
                          >
                            <span className="text-xs text-ink-2 leading-snug flex-1 group-hover:text-accent transition-colors line-clamp-1">
                              {e.title || e.url}
                            </span>
                            <ExternalLink size={11} className="text-ink-4 group-hover:text-accent flex-shrink-0 mt-0.5 transition-colors" />
                          </a>
                        ))}
                        {items.length > 4 && (
                          <p className="text-2xs text-ink-4 italic pl-2.5">
                            +{items.length - 4} more from this source
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        </div>
      ) : (
        <div className="bg-surface border border-edge border-dashed rounded-lg p-5 mb-5">
          <div className="flex items-center gap-2 mb-2">
            <Target size={14} className="text-ink-4" />
            <h2 className="text-xs font-medium text-ink-3 uppercase tracking-wider">Opportunity card enrichment</h2>
          </div>
          <EmptyNote>
            No enrichment data yet. Run a fresh pipeline and this card will populate with
            technologies, papers, limitations, and suggested directions.
          </EmptyNote>
        </div>
      )}

      {/* SRS 11: rich problem profile fields */}
      {problemProfile && (problemProfile.affected_stakeholders?.length || problemProfile.evidence?.length) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
          {problemProfile.affected_stakeholders?.length > 0 && (
            <div className="bg-surface border border-edge rounded-lg p-5">
              <h2 className="text-xs font-medium text-ink uppercase tracking-wider mb-3 flex items-center gap-2">
                Affected stakeholders
              </h2>
              <ul className="space-y-1.5">
                {problemProfile.affected_stakeholders.slice(0, 8).map((s: string, i: number) => (
                  <li key={i} className="text-xs text-ink-2 leading-relaxed flex items-start gap-2">
                    <span className="text-accent flex-shrink-0 mt-0.5">•</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
              {problemProfile.confidence !== null && problemProfile.confidence !== undefined && (
                <p className="text-2xs text-ink-4 mt-3 pt-3 border-t border-edge-subtle">
                  Extraction confidence: <span className="text-ink-2 font-mono">{problemProfile.confidence.toFixed(2)}</span>
                </p>
              )}
            </div>
          )}
          {problemProfile.evidence?.length > 0 && (
            <div className="bg-surface border border-edge rounded-lg p-5">
              <h2 className="text-xs font-medium text-ink uppercase tracking-wider mb-3 flex items-center gap-2">
                Source evidence
              </h2>
              <ul className="space-y-2 max-h-64 overflow-y-auto pr-1">
                {problemProfile.evidence.slice(0, 8).map((e: string, i: number) => (
                  <li key={i} className="text-xs text-ink-2 leading-relaxed pl-3 border-l-2 border-accent/40">
                    {e}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* SRS 13: linked papers with methods/results/areas */}
      {linkedPapers.length > 0 && (
        <Section icon={BookOpen} title={`Research papers (${linkedPapers.length})`} accent="text-success">
          <div className="space-y-4">
            {linkedPapers.slice(0, 6).map((p: any) => (
              <div key={p.id} className="pb-4 border-b border-edge-subtle last:border-0 last:pb-0">
                <div className="flex items-start justify-between gap-3 mb-2">
                  <a
                    href={p.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm text-ink leading-snug flex-1 hover:text-accent transition-colors"
                  >
                    {p.title}
                    <ExternalLink size={11} className="inline ml-1 text-ink-4" />
                  </a>
                  <span className="text-xs font-mono tabular-nums text-success flex-shrink-0">
                    {p.relevance_score?.toFixed(2)}
                  </span>
                </div>
                {p.results_summary && (
                  <p className="text-xs text-ink-2 leading-relaxed mb-2">{p.results_summary}</p>
                )}
                {p.research_methods?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-1.5">
                    <span className="text-2xs text-ink-4 uppercase tracking-wider">Methods:</span>
                    {p.research_methods.slice(0, 5).map((m: string, i: number) => (
                      <span key={i} className="badge bg-accent/10 text-accent border border-accent/30">{m}</span>
                    ))}
                  </div>
                )}
                {p.research_areas?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    <span className="text-2xs text-ink-4 uppercase tracking-wider">Areas:</span>
                    {p.research_areas.slice(0, 4).map((a: string, i: number) => (
                      <span key={i} className="badge bg-overlay text-ink-3 border border-edge">{a}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

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
          {data.sources && data.sources.length > 0 && (
            <div>
              <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2">
                Original sources ({data.sources.length})
              </p>
              <div className="space-y-1.5">
                {data.sources.map((src: any) => (
                  <a
                    key={src.id}
                    href={src.url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-start gap-2.5 px-3 py-2 rounded-md border border-edge hover:border-accent/40 hover:bg-overlay transition-colors group"
                  >
                    <span className="badge bg-overlay text-ink-3 border border-edge flex-shrink-0 mt-0.5 uppercase">
                      {src.source}
                    </span>
                    <span className="text-xs text-ink-2 leading-snug flex-1 group-hover:text-accent transition-colors line-clamp-2">
                      {src.title || '(untitled)'}
                    </span>
                    <ExternalLink size={12} className="text-ink-4 group-hover:text-accent flex-shrink-0 mt-1 transition-colors" />
                  </a>
                ))}
              </div>
              <div className="mt-4 pt-4 border-t border-edge-subtle" />
            </div>
          )}

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

      {/* Recommendation history (SRS 30) */}
      {recHistory.length > 0 && (
        <div className="mt-5 bg-surface border border-edge rounded-lg p-5">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles size={14} className="text-warning" />
            <h2 className="text-xs font-medium text-ink uppercase tracking-wider">
              Recommendation history ({recHistory.length})
            </h2>
          </div>
          <div className="space-y-4">
            {recHistory.slice(0, 10).map((r: any) => (
              <div key={r.id} className="pb-4 border-b border-edge-subtle last:border-0 last:pb-0">
                <div className="flex items-center justify-between gap-3 mb-2">
                  <span className="text-2xs text-ink-4 font-mono">
                    {new Date(r.created_at).toLocaleString()}
                  </span>
                  {r.score_at_time !== null && (
                    <span className="text-2xs font-mono tabular-nums text-accent">
                      score {r.score_at_time?.toFixed(2)}
                    </span>
                  )}
                </div>
                {r.suggested_research_direction && (
                  <div className="mb-2">
                    <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Research direction</p>
                    <p className="text-xs text-ink-2 leading-relaxed">{r.suggested_research_direction}</p>
                  </div>
                )}
                {r.suggested_project_direction && (
                  <div>
                    <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Project direction</p>
                    <p className="text-xs text-ink-2 leading-relaxed">{r.suggested_project_direction}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
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
