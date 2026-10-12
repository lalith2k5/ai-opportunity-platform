
import { useEffect, useState, type ReactNode } from 'react';
import PotentialGapNote from '../components/PotentialGapNote';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, Loader2, AlertCircle, Building2, Factory, Cpu, BarChart3,
  BookOpen, TrendingUp, Database, Network, FileText, Lightbulb,
  Compass, ExternalLink, ShieldAlert, Sparkles,
} from 'lucide-react';
import { getRDProblemDetail, type RDProblemDetail } from '../services/api';
import { formatApiError } from '../utils/errors';

function Section({
  icon: Icon,
  title,
  accent = 'text-accent',
  children,
}: {
  icon: any;
  title: string;
  accent?: string;
  children: ReactNode;
}) {
  return (
    <div className="card p-5 mb-5">
      <div className="flex items-center gap-2 mb-4">
        <Icon size={14} className={accent} />
        <h2 className="text-2xs font-semibold text-ink uppercase tracking-[0.08em]">{title}</h2>
      </div>
      {children}
    </div>
  );
}

function EmptyNote({ children }: { children: ReactNode }) {
  return <p className="text-xs text-ink-4 italic">{children}</p>;
}

function ScoreRow({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="mb-3">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs text-ink-3">{label}</span>
        <span className="text-xs font-mono tabular-nums text-ink font-medium">
          {value.toFixed(2)}
        </span>
      </div>
      <div className="h-1.5 bg-overlay rounded-full overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${Math.min(100, value * 100)}%` }} />
      </div>
    </div>
  );
}

function classifyChallengeSource(source: string): { label: string; tone: string; blurb: string } {
  const s = (source || '').toLowerCase();
  if (s === 'sbir' || s === 'challenge_portal' || s === 'challenge_gov') {
    return {
      label: 'Public challenge',
      tone: 'bg-success/10 border-success/30 text-success',
      blurb: 'This problem was published through a public challenge portal and is directly supported by the source.',
    };
  }
  if (s === 'arxiv') {
    return {
      label: 'Research-derived problem',
      tone: 'bg-sky-500/10 border-sky-500/30 text-sky-500',
      blurb: 'This problem was inferred from academic research. Treat as a potential industry problem.',
    };
  }
  if (s === 'github_issues') {
    return {
      label: 'Developer-reported problem',
      tone: 'bg-purple-500/10 border-purple-500/30 text-purple-500',
      blurb: 'This problem was derived from public issue trackers. Treat as a developer pain point.',
    };
  }
  if (s === 'news') {
    return {
      label: 'Industry-inferred problem',
      tone: 'bg-warning/10 border-warning/30 text-warning',
      blurb: 'This problem was inferred from news coverage. Company affiliation is sectoral, not a formal announcement.',
    };
  }
  return {
    label: 'Industry problem',
    tone: 'bg-accent/10 border-accent/30 text-accent',
    blurb: 'This problem was extracted from available public sources. Not an officially announced challenge unless the source states so.',
  };
}

export default function RDProblemDetail() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<RDProblemDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getRDProblemDetail(Number(id))
      .then(setData)
      .catch((e: any) => setError(formatApiError(e)))
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
        <Link to="/rd" className="btn-ghost text-xs mb-4">
          <ArrowLeft size={13} /> Back to R&D
        </Link>
        <div className="bg-danger/10 border border-danger/30 rounded-lg p-5">
          <AlertCircle className="text-danger mb-2" size={20} />
          <p className="text-danger text-sm">{error || 'Problem not found'}</p>
        </div>
      </div>
    );
  }

  const p = data.problem;
  const org = data.organization;
  const scoring = data.opportunity_scoring;
  const kg = data.knowledge_graph;
  const classified = classifyChallengeSource(p.source);
  const evidenceGroups = Object.entries(data.evidence_aggregation || {});

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto">
      <Link
        to="/rd"
        className="inline-flex items-center gap-1.5 text-xs text-ink-3 hover:text-accent transition-colors mb-6 group"
      >
        <ArrowLeft size={13} className="transition-transform group-hover:-translate-x-0.5" />
        Back to R&D
      </Link>

      {/* Hero */}
      <div className="card p-6 mb-5 relative overflow-hidden">
        <div
          className="absolute -top-32 -right-32 w-96 h-96 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgb(255 179 64 / 0.12), transparent 60%)' }}
        />
        <div className="flex items-start justify-between gap-6 flex-wrap relative">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-3 flex-wrap">
              {p.industry_domain && (
                <span className="badge bg-overlay text-ink-3 border border-edge">
                  {p.industry_domain}
                </span>
              )}
              {p.problem_type && p.problem_type !== 'Other' && (
                <span className="badge bg-accent/10 text-accent border border-accent/30">
                  {p.problem_type}
                </span>
              )}
              {p.problem_status && p.problem_status !== 'unknown' && (
                <span className="badge bg-overlay text-ink-3 border border-edge capitalize">
                  {p.problem_status}
                </span>
              )}
              <span className="text-2xs text-ink-4 font-mono">#{p.id}</span>
            </div>
            <h1 className="text-3xl font-bold text-ink tracking-tight leading-tight mb-3">
              {p.problem_title}
            </h1>
            <p className="text-sm text-ink-2 leading-relaxed">
              {p.problem_description || 'No description provided.'}
            </p>
          </div>
          {p.confidence !== null && p.confidence !== undefined && (
            <div className="text-right flex-shrink-0">
              <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2">Confidence</p>
              <p className="text-4xl font-bold font-mono tabular-nums text-accent leading-none tracking-tight">
                {p.confidence.toFixed(2)}
              </p>
            </div>
          )}
        </div>
        {p.keywords && p.keywords.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-4 pt-4 border-t border-edge-subtle">
            {p.keywords.map(k => (
              <span key={k} className="badge bg-overlay text-ink-3 border border-edge">{k}</span>
            ))}
          </div>
        )}
      </div>

      {/* Source disclaimer banner (SRS: distinguish challenge types) */}
      <div className={`mb-5 border rounded-lg p-4 flex items-start gap-3 ${classified.tone}`}>
        <ShieldAlert size={16} className="flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold uppercase tracking-[0.08em] mb-1">
            {classified.label}
          </p>
          <p className="text-xs leading-relaxed opacity-90">
            {classified.blurb}
          </p>
        </div>
      </div>

      {/* 1. Industry Problem */}
      <Section icon={Factory} title="Industry Problem" accent="text-warning">
        <p className="text-sm text-ink-2 leading-relaxed mb-3">
          {p.problem_description || 'Not available.'}
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-edge-subtle">
          <div>
            <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Current approach</p>
            <p className="text-xs text-ink-2 leading-relaxed">
              {p.current_approach || 'Not available'}
            </p>
          </div>
          <div>
            <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Known limitations</p>
            <p className="text-xs text-ink-2 leading-relaxed">
              {p.known_limitations || 'Not available'}
            </p>
          </div>
        </div>
        {p.source_url && (
          <div className="mt-3 pt-3 border-t border-edge-subtle">
            <a
              href={p.source_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-accent hover:text-accent-hover transition-colors"
            >
              <ExternalLink size={11} />
              View original source
            </a>
          </div>
        )}
      </Section>

      {/* 2. Related Organizations */}
      <Section icon={Building2} title="Related Organizations" accent="text-accent">
        {!org || !org.name ? (
          <EmptyNote>No specific organization identified from available sources.</EmptyNote>
        ) : (
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
              <Building2 size={16} className="text-accent" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-ink">{org.name}</p>
              <div className="flex flex-wrap gap-1.5 mt-1.5">
                {org.industry_domain && (
                  <span className="badge bg-overlay text-ink-3 border border-edge">
                    {org.industry_domain}
                  </span>
                )}
                {org.source && (
                  <span className="badge bg-overlay text-ink-4 border border-edge">
                    via {org.source.replace(/_/g, ' ')}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </Section>

      {/* 3. Related Technologies */}
      <Section icon={Cpu} title={`Related Technologies (${data.related_technologies.length})`} accent="text-purple-500">
        {data.related_technologies.length === 0 ? (
          <EmptyNote>No technologies linked to this problem yet.</EmptyNote>
        ) : (
          <div className="flex flex-wrap gap-2">
            {data.related_technologies.map((t, i) => (
              <Link
                key={i}
                to={`/technologies/${encodeURIComponent(t.name)}`}
                className="badge bg-purple-500/10 text-purple-500 border border-purple-500/30 hover:bg-purple-500/20 transition-colors"
              >
                {t.name}
                {t.stage && <span className="ml-1 opacity-70 text-2xs">{t.stage}</span>}
                {t.confidence !== undefined && (
                  <span className="ml-1 opacity-60 text-2xs">{t.confidence.toFixed(2)}</span>
                )}
              </Link>
            ))}
          </div>
        )}
      </Section>

      {/* 4. Technology Landscape */}
      <Section icon={BarChart3} title="Technology Landscape" accent="text-purple-500">
        {data.technology_landscape.count === 0 ? (
          <EmptyNote>No technology landscape signals available.</EmptyNote>
        ) : (
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Technologies</p>
              <p className="text-2xl font-semibold text-ink font-mono tabular-nums">
                {data.technology_landscape.count}
              </p>
            </div>
            <div>
              <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Avg confidence</p>
              <p className="text-2xl font-semibold text-accent font-mono tabular-nums">
                {data.technology_landscape.average_confidence.toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Stages</p>
              <div className="flex flex-wrap gap-1">
                {data.technology_landscape.stages.length > 0 ? (
                  data.technology_landscape.stages.map(s => (
                    <span key={s} className="text-2xs text-ink-3 capitalize">
                      {s.replace(/_/g, ' ')}
                    </span>
                  ))
                ) : (
                  <span className="text-2xs text-ink-4 italic">none</span>
                )}
              </div>
            </div>
          </div>
        )}
      </Section>

      {/* 5. Research Landscape */}
      <Section icon={BookOpen} title={`Research Landscape (${data.research_landscape.length})`} accent="text-success">
        {data.research_landscape.length === 0 ? (
          <EmptyNote>No linked research papers yet.</EmptyNote>
        ) : (
          <div className="space-y-3">
            {data.research_landscape.slice(0, 10).map(rp => (
              <div key={rp.id} className="pb-3 border-b border-edge-subtle last:border-0 last:pb-0">
                <div className="flex items-start justify-between gap-3 mb-1">
                  {rp.arxiv_id && !rp.arxiv_id.startsWith('paper:') ? (
                    <Link
                      to={`/research/${encodeURIComponent(rp.arxiv_id)}`}
                      className="text-sm text-ink hover:text-accent transition-colors leading-snug flex-1"
                    >
                      {rp.title}
                    </Link>
                  ) : rp.url ? (
                    <a
                      href={rp.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm text-ink hover:text-accent transition-colors leading-snug flex-1"
                    >
                      {rp.title}
                      <ExternalLink size={11} className="inline ml-1 text-ink-4" />
                    </a>
                  ) : (
                    <span className="text-sm text-ink leading-snug flex-1">{rp.title}</span>
                  )}
                  <span className="text-xs font-mono tabular-nums text-success flex-shrink-0">
                    {rp.relevance_score?.toFixed(2)}
                  </span>
                </div>
                {rp.results_summary && (
                  <p className="text-xs text-ink-3 leading-relaxed">{rp.results_summary}</p>
                )}
                {rp.research_methods && rp.research_methods.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {rp.research_methods.slice(0, 4).map((m, k) => (
                      <span key={k} className="badge bg-accent/10 text-accent border border-accent/30">{m}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* 6. Emerging Trends */}
      <Section icon={TrendingUp} title={`Emerging Trends (${data.emerging_trends.length})`} accent="text-warning">
        {data.emerging_trends.length === 0 ? (
          <EmptyNote>No matching trends detected.</EmptyNote>
        ) : (
          <div className="space-y-2">
            {data.emerging_trends.map(t => (
              <div key={t.name} className="flex items-center gap-3">
                <span className="text-xs text-ink-2 truncate flex-1">{t.name}</span>
                {t.category && (
                  <span className="text-2xs text-ink-4 capitalize">{t.category.replace(/_/g, ' ')}</span>
                )}
                <div className="w-20 h-1.5 bg-overlay rounded-full overflow-hidden flex-shrink-0">
                  <div className="h-full bg-warning" style={{ width: `${(t.trend_score || 0) * 100}%` }} />
                </div>
                <span className="text-2xs font-mono tabular-nums text-ink-3 w-8 text-right flex-shrink-0">
                  {t.trend_score?.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* 7. Evidence Aggregation */}
      <Section icon={Database} title="Evidence Aggregation" accent="text-accent">
        {evidenceGroups.every(([, arr]) => !Array.isArray(arr) || arr.length === 0) ? (
          <EmptyNote>No supporting evidence rows found across sources.</EmptyNote>
        ) : (
          <div className="space-y-4">
            {evidenceGroups.map(([src, arr]) => {
              if (!Array.isArray(arr) || arr.length === 0) return null;
              return (
                <div key={src}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="badge bg-overlay text-ink-3 border border-edge uppercase">
                      {src.replace(/_/g, ' ')}
                    </span>
                    <span className="text-2xs text-ink-4 font-mono">{arr.length}</span>
                  </div>
                  <div className="space-y-1">
                    {arr.slice(0, 6).map((r: any, i: number) => (
                      <a
                        key={i}
                        href={r.url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-start gap-2 px-2.5 py-1.5 rounded-md border border-edge-subtle hover:border-accent/40 hover:bg-overlay transition-colors group"
                      >
                        <span className="text-xs text-ink-2 leading-snug flex-1 group-hover:text-accent transition-colors line-clamp-1">
                          {r.title || r.url}
                        </span>
                        <ExternalLink size={11} className="text-ink-4 group-hover:text-accent flex-shrink-0 mt-0.5 transition-colors" />
                      </a>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Section>

      {/* 8. Knowledge Graph Connections */}
      <Section icon={Network} title="Knowledge Graph Connections" accent="text-sky-500">
        {(!kg || kg.edges.length === 0) ? (
          <EmptyNote>No KG connections found for this problem.</EmptyNote>
        ) : (
          <div className="space-y-2">
            <p className="text-2xs text-ink-4 mb-3">
              Node: <span className="text-ink-2 font-medium">{kg.node}</span>
              {' · '}
              {kg.edges.length} edge{kg.edges.length === 1 ? '' : 's'}
            </p>
            {kg.edges.slice(0, 20).map((e, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span className="text-ink-2 truncate max-w-[30%]">{e.source}</span>
                <span className="text-accent font-mono text-2xs flex-shrink-0">{e.relation}</span>
                <span className="text-ink-2 truncate flex-1">{e.target}</span>
              </div>
            ))}
            {kg.edges.length > 20 && (
              <p className="text-2xs text-ink-4 italic pt-2">+{kg.edges.length - 20} more connections</p>
            )}
          </div>
        )}
      </Section>

      {/* 9. Potential Research Gaps */}
      <Section icon={FileText} title={`Potential Research Gaps (${data.potential_gaps.length})`} accent="text-warning">
        {data.potential_gaps.length === 0 ? (
          <EmptyNote>No potential gaps identified from current evidence.</EmptyNote>
        ) : (
          <>
            <PotentialGapNote />
            <div className="space-y-3">
              {data.potential_gaps.map(g => (
                <div key={g.id} className="pb-3 border-b border-edge-subtle last:border-0 last:pb-0">
                  <div className="flex items-start justify-between gap-3 mb-1">
                    <p className="text-xs text-ink font-medium leading-snug flex-1">{g.title}</p>
                    <span className="text-xs font-mono tabular-nums text-success flex-shrink-0">
                      {g.gap_score.toFixed(2)}
                    </span>
                  </div>
                  <p className="text-2xs text-ink-3 leading-relaxed line-clamp-2">{g.description}</p>
                </div>
              ))}
            </div>
          </>
        )}
      </Section>

      {/* 10. Innovation Opportunities */}
      <Section icon={Lightbulb} title={`Innovation Opportunities (${data.innovation_opportunities.length})`} accent="text-accent">
        {data.innovation_opportunities.length === 0 ? (
          <EmptyNote>No opportunities linked yet.</EmptyNote>
        ) : (
          <div className="space-y-2">
            {data.innovation_opportunities.map(o => (
              <Link
                key={o.id}
                to={`/opportunities/${o.id}`}
                className="flex items-start justify-between gap-3 py-2 px-2 -mx-2 rounded-md hover:bg-overlay transition-colors group"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-ink-2 leading-snug group-hover:text-accent transition-colors line-clamp-2">
                    {o.title}
                  </p>
                  <div className="flex gap-2 mt-1">
                    {o.domain && <span className="text-2xs text-ink-4">{o.domain}</span>}
                    {o.industry && o.industry !== o.domain && (
                      <span className="text-2xs text-ink-4">· {o.industry}</span>
                    )}
                  </div>
                </div>
                <span className="text-xs font-mono tabular-nums text-accent flex-shrink-0">
                  {o.opportunity_score.toFixed(2)}
                </span>
              </Link>
            ))}
          </div>
        )}
      </Section>

      {/* 11. Opportunity Scoring */}
      <Section icon={BarChart3} title="Opportunity Scoring" accent="text-accent">
        {!scoring ? (
          <EmptyNote>No scoring data — opportunity has not been scored yet.</EmptyNote>
        ) : (
          <>
            <div className="flex items-start justify-between gap-4 mb-5 pb-4 border-b border-edge-subtle">
              <div className="min-w-0 flex-1">
                <p className="text-xs text-ink-4 uppercase tracking-wider mb-1">Top opportunity</p>
                <Link
                  to={`/opportunities/${scoring.opportunity_id}`}
                  className="text-sm font-medium text-ink hover:text-accent transition-colors"
                >
                  {scoring.title}
                </Link>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-3xl font-bold font-mono tabular-nums text-success leading-none">
                  {scoring.opportunity_score.toFixed(2)}
                </p>
                <p className="text-2xs text-ink-4 mt-1 uppercase tracking-wider">Overall</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
              <div>
                <ScoreRow label="Demand" value={scoring.demand} color="bg-accent" />
                <ScoreRow label="Research gap" value={scoring.research_gap} color="bg-success" />
                <ScoreRow label="Trend" value={scoring.trend} color="bg-warning" />
                <ScoreRow label="Feasibility" value={scoring.feasibility} color="bg-sky-500" />
                <ScoreRow label="Market readiness" value={scoring.market_readiness} color="bg-purple-500" />
              </div>
              <div>
                <ScoreRow label="Technology suitability" value={scoring.technology_suitability} color="bg-cyan-500" />
                <ScoreRow label="Evidence strength" value={scoring.evidence_strength} color="bg-lime-500" />
                <ScoreRow label="Recency" value={scoring.recency} color="bg-orange-500" />
                <ScoreRow label="Confidence" value={scoring.confidence} color="bg-pink-500" />
              </div>
            </div>
            {scoring.explanation && (
              <div className="mt-4 pt-4 border-t border-edge-subtle">
                <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Sparkles size={10} className="text-warning" />
                  AI explanation
                </p>
                <p className="text-xs text-ink-2 leading-relaxed">{scoring.explanation}</p>
              </div>
            )}
          </>
        )}
      </Section>

      {/* 12. Recommended Next Steps */}
      <Section icon={Compass} title="Recommended Next Steps" accent="text-success">
        {data.recommended_next_steps.length === 0 ? (
          <EmptyNote>No next steps generated yet.</EmptyNote>
        ) : (
          <div className="space-y-3">
            {data.recommended_next_steps.map((s, i) => (
              <div key={i} className="flex items-start gap-3 pb-3 border-b border-edge-subtle last:border-0 last:pb-0">
                <div className={`w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0 ${
                  s.kind === 'project' ? 'bg-success/10' : 'bg-accent/10'
                }`}>
                  {s.kind === 'project' ? (
                    <Lightbulb size={13} className="text-success" />
                  ) : (
                    <BookOpen size={13} className="text-accent" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">
                    {s.kind === 'project' ? 'Project direction' : 'Research direction'}
                  </p>
                  <p className="text-xs text-ink-2 leading-relaxed">{s.text}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}
