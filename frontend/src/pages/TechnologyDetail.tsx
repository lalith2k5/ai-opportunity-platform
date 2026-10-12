
import { useEffect, useState, type ReactNode } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, Loader2, AlertCircle, Cpu, TrendingUp, TrendingDown, Minus,
  BookOpen, GitBranch, Newspaper, MessageSquare, ExternalLink, Lightbulb,
  Target, FileText,
} from 'lucide-react';
import { getTechnologyDetail, type TechnologyDetailData } from '../services/api';
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

function SourceLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="flex items-start gap-2.5 px-3 py-2 rounded-md border border-edge hover:border-accent/40 hover:bg-overlay transition-colors group"
    >
      <span className="text-xs text-ink-2 leading-snug flex-1 group-hover:text-accent transition-colors line-clamp-2">
        {children}
      </span>
      <ExternalLink size={12} className="text-ink-4 group-hover:text-accent flex-shrink-0 mt-1 transition-colors" />
    </a>
  );
}

function StageBadge({ stage }: { stage: string | null }) {
  if (!stage) return null;
  const map: Record<string, string> = {
    used: 'bg-success/15 text-success border-success/30',
    proposed: 'bg-accent/15 text-accent border-accent/30',
    emerging: 'bg-warning/15 text-warning border-warning/30',
    potentially_applicable: 'bg-overlay text-ink-3 border-edge',
  };
  return (
    <span className={`badge ${map[stage] || map.potentially_applicable}`}>
      {stage.replace(/_/g, ' ')}
    </span>
  );
}

function TrendGlyph({ label }: { label: string }) {
  if (label === 'emerging' || label === 'growing') return <TrendingUp size={12} className="text-success" />;
  if (label === 'declining') return <TrendingDown size={12} className="text-danger" />;
  return <Minus size={12} className="text-ink-4" />;
}

export default function TechnologyDetail() {
  const { name } = useParams<{ name: string }>();
  const [data, setData] = useState<TechnologyDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!name) return;
    setLoading(true);
    getTechnologyDetail(name)
      .then(setData)
      .catch((e: any) => setError(formatApiError(e)))
      .finally(() => setLoading(false));
  }, [name]);

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
        <Link to="/technologies" className="btn-ghost text-xs mb-4">
          <ArrowLeft size={13} /> Back to technologies
        </Link>
        <div className="bg-danger/10 border border-danger/30 rounded-lg p-5">
          <AlertCircle className="text-danger mb-2" size={20} />
          <p className="text-danger text-sm">{error || 'Technology not found'}</p>
        </div>
      </div>
    );
  }

  const tech = data.technology;
  const trend = data.trend;

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto animate-fade-up">
      <Link
        to="/technologies"
        className="inline-flex items-center gap-1.5 text-xs text-ink-3 hover:text-accent transition-colors mb-6 group"
      >
        <ArrowLeft size={13} className="transition-transform group-hover:-translate-x-0.5" />
        Back to technologies
      </Link>

      {/* Hero */}
      <div className="card p-6 mb-5 relative overflow-hidden">
        <div
          className="absolute -top-32 -right-32 w-96 h-96 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgb(168 85 247 / 0.12), transparent 60%)' }}
        />
        <div className="flex items-start justify-between gap-6 flex-wrap relative">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-3 flex-wrap">
              <StageBadge stage={tech.stage} />
              {tech.domain && (
                <span className="badge bg-overlay text-ink-3 border border-edge">{tech.domain}</span>
              )}
              {tech.domains.length > 1 && (
                <span className="text-2xs text-ink-4">+{tech.domains.length - 1} more domains</span>
              )}
            </div>
            <h1 className="text-3xl font-bold text-ink tracking-tight leading-tight mb-3">
              {tech.name}
            </h1>
            <p className="text-sm text-ink-2 leading-relaxed">{tech.description}</p>
          </div>
          <div className="text-right flex-shrink-0">
            <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2">Confidence</p>
            <p className="text-4xl font-bold font-mono tabular-nums text-accent leading-none tracking-tight">
              {tech.confidence.toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      {/* Counts strip */}
      <div className="grid grid-cols-3 gap-3 mb-5">
        <div className="card p-4">
          <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Problems</p>
          <p className="text-2xl font-semibold text-ink font-mono tabular-nums">
            {tech.related_problem_count}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Papers</p>
          <p className="text-2xl font-semibold text-success font-mono tabular-nums">
            {tech.related_paper_count}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Signals</p>
          <p className="text-2xl font-semibold text-accent font-mono tabular-nums">
            {tech.source_count}
          </p>
        </div>
      </div>

      {/* Overview / trend side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        <Section icon={Cpu} title="Technology Overview" accent="text-purple-500">
          <p className="text-sm text-ink-2 leading-relaxed mb-3">{tech.description}</p>
          <div className="grid grid-cols-2 gap-3 pt-3 border-t border-edge-subtle">
            <div>
              <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Primary domain</p>
              <p className="text-xs text-ink-2">{tech.domain || '—'}</p>
            </div>
            <div>
              <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Stage</p>
              <p className="text-xs text-ink-2 capitalize">{tech.stage ? tech.stage.replace(/_/g, ' ') : '—'}</p>
            </div>
          </div>
          {tech.domains.length > 1 && (
            <div className="mt-3 pt-3 border-t border-edge-subtle">
              <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2">All domains</p>
              <div className="flex flex-wrap gap-1.5">
                {tech.domains.map(d => (
                  <span key={d} className="badge bg-overlay text-ink-3 border border-edge">{d}</span>
                ))}
              </div>
            </div>
          )}
        </Section>

        <Section icon={TrendingUp} title="Trend Analysis" accent="text-success">
          {!trend ? (
            <EmptyNote>No trend data available for this technology yet.</EmptyNote>
          ) : (
            <div>
              <div className="flex items-center gap-3 mb-4">
                <span className="text-3xl font-bold font-mono tabular-nums text-success leading-none">
                  {trend.trend_score.toFixed(2)}
                </span>
                <div className="inline-flex items-center gap-1.5 text-xs">
                  <TrendGlyph label={trend.label} />
                  <span className="text-ink-2 capitalize">{trend.label.replace(/_/g, ' ')}</span>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3 pt-3 border-t border-edge-subtle">
                <div>
                  <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Growth</p>
                  <p className="text-xs text-ink font-mono">{(trend.growth_rate * 100).toFixed(0)}%</p>
                </div>
                <div>
                  <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Recent avg</p>
                  <p className="text-xs text-ink font-mono">{trend.recent_avg.toFixed(1)}</p>
                </div>
                <div>
                  <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Prior avg</p>
                  <p className="text-xs text-ink font-mono">{trend.prior_avg.toFixed(1)}</p>
                </div>
              </div>
              {trend.category && (
                <div className="mt-3 pt-3 border-t border-edge-subtle">
                  <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Category</p>
                  <p className="text-xs text-ink-2 capitalize">{trend.category.replace(/_/g, ' ')}</p>
                </div>
              )}
            </div>
          )}
        </Section>
      </div>

      {/* Related Problems */}
      <Section icon={AlertCircle} title={`Related Problems (${data.related_problems.length})`} accent="text-warning">
        {data.related_problems.length === 0 ? (
          <EmptyNote>No linked problem profiles yet.</EmptyNote>
        ) : (
          <div className="space-y-3">
            {data.related_problems.slice(0, 10).map(p => (
              <div key={p.id} className="pb-3 border-b border-edge-subtle last:border-0 last:pb-0">
                <div className="flex items-start justify-between gap-3 mb-1">
                  <p className="text-sm text-ink font-medium leading-snug flex-1">
                    {p.problem_title}
                  </p>
                  {p.source_url && (
                    <a
                      href={p.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-accent hover:text-accent-hover flex-shrink-0"
                    >
                      <ExternalLink size={12} />
                    </a>
                  )}
                </div>
                <p className="text-xs text-ink-3 leading-relaxed line-clamp-2 mb-1.5">
                  {p.problem_description}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {p.industry_domain && (
                    <span className="badge bg-overlay text-ink-3 border border-edge">
                      {p.industry_domain}
                    </span>
                  )}
                  {p.problem_type && (
                    <span className="badge bg-overlay text-ink-3 border border-edge">
                      {p.problem_type}
                    </span>
                  )}
                  {p.organization && p.organization !== 'Unknown' && (
                    <span className="badge bg-accent/10 text-accent border border-accent/30">
                      {p.organization}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* Related Papers */}
      <Section icon={BookOpen} title={`Related Papers (${data.related_papers.length})`} accent="text-success">
        {data.related_papers.length === 0 ? (
          <EmptyNote>No papers linked yet.</EmptyNote>
        ) : (
          <div className="space-y-4">
            {data.related_papers.slice(0, 8).map(p => (
              <div key={p.id} className="pb-4 border-b border-edge-subtle last:border-0 last:pb-0">
                <div className="flex items-start justify-between gap-3 mb-1.5">
                  <a
                    href={p.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm text-ink hover:text-accent transition-colors leading-snug flex-1"
                  >
                    {p.title}
                    <ExternalLink size={11} className="inline ml-1 text-ink-4" />
                  </a>
                  <span className="text-xs font-mono tabular-nums text-success flex-shrink-0">
                    {p.relevance_score?.toFixed(2)}
                  </span>
                </div>
                {p.results_summary && (
                  <p className="text-xs text-ink-3 leading-relaxed mb-1.5">{p.results_summary}</p>
                )}
                {p.research_methods && p.research_methods.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {p.research_methods.slice(0, 5).map((m, i) => (
                      <span key={i} className="badge bg-accent/10 text-accent border border-accent/30">
                        {m}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* GitHub */}
      <Section icon={GitBranch} title={`GitHub Repositories (${data.github_repositories.length})`}>
        {data.github_repositories.length === 0 ? (
          <EmptyNote>No matching repositories in the current corpus.</EmptyNote>
        ) : (
          <div className="space-y-1.5">
            {data.github_repositories.map(r => (
              <SourceLink key={r.id} href={r.url}>{r.title}</SourceLink>
            ))}
          </div>
        )}
      </Section>

      {/* News */}
      <Section icon={Newspaper} title={`News & Industry (${data.news_articles.length})`} accent="text-warning">
        {data.news_articles.length === 0 ? (
          <EmptyNote>No matching news articles.</EmptyNote>
        ) : (
          <div className="space-y-1.5">
            {data.news_articles.map(n => (
              <SourceLink key={n.id} href={n.url}>{n.title}</SourceLink>
            ))}
          </div>
        )}
      </Section>

      {/* Reddit */}
      <Section icon={MessageSquare} title={`Reddit Discussions (${data.reddit_discussions.length})`} accent="text-orange-500">
        {data.reddit_discussions.length === 0 ? (
          <EmptyNote>
            No matching Reddit discussions. Reddit is not configured — add credentials in Admin → Config to enable this source.
          </EmptyNote>
        ) : (
          <div className="space-y-1.5">
            {data.reddit_discussions.map(r => (
              <SourceLink key={r.id} href={r.url}>{r.title}</SourceLink>
            ))}
          </div>
        )}
      </Section>

      {/* Potential Gaps */}
      <Section icon={FileText} title={`Potential Research Gaps (${data.potential_gaps.length})`} accent="text-warning">
        {data.potential_gaps.length === 0 ? (
          <EmptyNote>No research gaps identified for this technology yet.</EmptyNote>
        ) : (
          <div className="space-y-3">
            {data.potential_gaps.slice(0, 6).map(g => (
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
        )}
      </Section>

      {/* Opportunities */}
      <Section icon={Lightbulb} title={`Opportunities (${data.opportunities.length})`} accent="text-accent">
        {data.opportunities.length === 0 ? (
          <EmptyNote>No linked opportunities yet.</EmptyNote>
        ) : (
          <div className="space-y-2">
            {data.opportunities.map(o => (
              <Link
                key={o.id}
                to={`/opportunities/${o.id}`}
                className="flex items-start justify-between gap-3 py-2 px-2 -mx-2 rounded-md hover:bg-overlay transition-colors group"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-ink-2 leading-snug group-hover:text-accent transition-colors line-clamp-2">
                    {o.title}
                  </p>
                  <div className="flex gap-1.5 mt-1">
                    {o.domain && (
                      <span className="text-2xs text-ink-4">{o.domain}</span>
                    )}
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

      {/* Sources */}
      <Section icon={Target} title="Source References">
        {data.sources.length === 0 ? (
          <EmptyNote>No source links available.</EmptyNote>
        ) : (
          <div className="space-y-1.5">
            {data.sources.map((s, i) => (
              <div key={i} className="flex items-center gap-2.5 text-xs">
                <span className="badge bg-overlay text-ink-3 border border-edge uppercase flex-shrink-0">
                  {s.source}
                </span>
                <a
                  href={s.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-ink-2 hover:text-accent transition-colors truncate flex-1"
                >
                  {s.title || s.url}
                </a>
              </div>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}
