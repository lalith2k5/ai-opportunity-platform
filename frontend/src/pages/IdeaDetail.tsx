
import { useEffect, useState, type ReactNode } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, Loader2, AlertCircle, Lightbulb, Cpu, Newspaper,
  MessageSquare, GitBranch, BookOpen, Target, FileText, Sparkles,
  ExternalLink, ArrowUpRight,
} from 'lucide-react';
import { getIdeaDetail, type IdeaDetailData } from '../services/api';

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

function SourceRow({ source, href, children }: { source?: string; href: string; children: ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="flex items-start gap-2.5 px-3 py-2 rounded-md border border-edge hover:border-accent/40 hover:bg-overlay transition-colors group"
    >
      {source && (
        <span className="badge bg-overlay text-ink-3 border border-edge uppercase flex-shrink-0 mt-0.5">
          {source}
        </span>
      )}
      <span className="text-xs text-ink-2 leading-snug flex-1 group-hover:text-accent transition-colors line-clamp-2">
        {children}
      </span>
      <ExternalLink size={12} className="text-ink-4 group-hover:text-accent flex-shrink-0 mt-1 transition-colors" />
    </a>
  );
}

export default function IdeaDetail() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<IdeaDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getIdeaDetail(Number(id))
      .then(setData)
      .catch((e: any) => setError(e?.response?.data?.detail || e.message))
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
        <Link to="/ideas" className="btn-ghost text-xs mb-4">
          <ArrowLeft size={13} /> Back to ideas
        </Link>
        <div className="bg-danger/10 border border-danger/30 rounded-lg p-5">
          <AlertCircle className="text-danger mb-2" size={20} />
          <p className="text-danger text-sm">{error || 'Idea not found'}</p>
        </div>
      </div>
    );
  }

  const idea = data.idea;

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto">
      <Link
        to="/ideas"
        className="inline-flex items-center gap-1.5 text-xs text-ink-3 hover:text-accent transition-colors mb-6 group"
      >
        <ArrowLeft size={13} className="transition-transform group-hover:-translate-x-0.5" />
        Back to ideas
      </Link>

      {/* Hero */}
      <div className="card p-6 mb-5 relative overflow-hidden">
        <div
          className="absolute -top-32 -right-32 w-96 h-96 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgb(24 119 242 / 0.12), transparent 60%)' }}
        />
        <div className="flex items-start justify-between gap-6 flex-wrap relative">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-3 flex-wrap">
              {idea.domain && (
                <span className="badge bg-overlay text-ink-3 border border-edge">{idea.domain}</span>
              )}
              {idea.problem_type && (
                <span className="badge bg-accent/10 text-accent border border-accent/30">
                  {idea.problem_type}
                </span>
              )}
              <span className="text-2xs text-ink-4 font-mono">#{idea.id}</span>
            </div>
            <h1 className="text-3xl font-bold text-ink tracking-tight leading-tight mb-3">
              {idea.title}
            </h1>
            <p className="text-sm text-ink-2 leading-relaxed">{idea.description}</p>
          </div>
          <div className="text-right flex-shrink-0">
            <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2">Demand</p>
            <p className="text-4xl font-bold font-mono tabular-nums text-success leading-none tracking-tight">
              {idea.demand_score.toFixed(2)}
            </p>
            <p className="text-2xs text-ink-4 mt-2 font-mono">
              {idea.source_count} sources
            </p>
          </div>
        </div>
        {idea.keywords.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-4 pt-4 border-t border-edge-subtle">
            {idea.keywords.map(k => (
              <span key={k} className="badge bg-overlay text-ink-3 border border-edge">
                {k}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Suggested directions (top placement -- most actionable) */}
      {data.suggested_directions.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
          {data.suggested_directions.map((s, i) => (
            <div
              key={i}
              className={`card p-5 border-accent/30`}
              style={{ background: 'linear-gradient(135deg, rgb(var(--accent) / 0.08), rgb(var(--accent) / 0.02))' }}
            >
              <div className="flex items-center gap-2 mb-3">
                <Sparkles size={14} className="text-accent" />
                <h2 className="text-xs font-medium text-ink uppercase tracking-wider">
                  Suggested {s.kind === 'project' ? 'project' : 'research'} direction
                </h2>
              </div>
              <p className="text-sm text-ink leading-relaxed">{s.text}</p>
            </div>
          ))}
        </div>
      )}

      {/* 1. Problem Overview */}
      <Section icon={Lightbulb} title="Problem Overview" accent="text-accent">
        <p className="text-sm text-ink-2 leading-relaxed mb-3">{idea.description}</p>
        <div className="grid grid-cols-2 gap-3 pt-3 border-t border-edge-subtle">
          <div>
            <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Domain</p>
            <p className="text-xs text-ink-2">{idea.domain || 'Not classified'}</p>
          </div>
          <div>
            <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Problem type</p>
            <p className="text-xs text-ink-2">{idea.problem_type || 'Not classified'}</p>
          </div>
        </div>
      </Section>

      {/* 2. Related Technologies */}
      <Section icon={Cpu} title={`Related Technologies (${data.related_technologies.length})`} accent="text-purple-500">
        {data.related_technologies.length === 0 ? (
          <EmptyNote>No technologies linked to this cluster yet.</EmptyNote>
        ) : (
          <div className="flex flex-wrap gap-2">
            {data.related_technologies.map(t => (
              <Link
                key={t.name}
                to={`/technologies/${encodeURIComponent(t.name)}`}
                className="badge bg-purple-500/10 text-purple-500 border border-purple-500/30 hover:bg-purple-500/20 transition-colors"
              >
                {t.name}
                {t.stage && <span className="ml-1 opacity-70 text-2xs">{t.stage}</span>}
              </Link>
            ))}
          </div>
        )}
      </Section>

      {/* 3. Related News */}
      <Section icon={Newspaper} title={`Related News (${data.related_news.length})`} accent="text-warning">
        {data.related_news.length === 0 ? (
          <EmptyNote>No matching news in the current corpus.</EmptyNote>
        ) : (
          <div className="space-y-1.5">
            {data.related_news.map(n => (
              <SourceRow key={n.id} source="news" href={n.url}>{n.title}</SourceRow>
            ))}
          </div>
        )}
      </Section>

      {/* 4. Reddit Discussions */}
      <Section icon={MessageSquare} title={`Reddit Discussions (${data.reddit_discussions.length})`} accent="text-orange-500">
        {data.reddit_discussions.length === 0 ? (
          <EmptyNote>
            Reddit is not configured — add credentials in Admin → Config to enable this source.
          </EmptyNote>
        ) : (
          <div className="space-y-1.5">
            {data.reddit_discussions.map(r => (
              <SourceRow key={r.id} source="reddit" href={r.url}>{r.title}</SourceRow>
            ))}
          </div>
        )}
      </Section>

      {/* 5. GitHub Repositories */}
      <Section icon={GitBranch} title={`GitHub Repositories (${data.github_repositories.length})`}>
        {data.github_repositories.length === 0 ? (
          <EmptyNote>No matching repositories in the current corpus.</EmptyNote>
        ) : (
          <div className="space-y-1.5">
            {data.github_repositories.map(g => (
              <SourceRow key={g.id} source={g.source} href={g.url}>{g.title}</SourceRow>
            ))}
          </div>
        )}
      </Section>

      {/* 6. Research Papers */}
      <Section icon={BookOpen} title={`Research Papers (${data.research_papers.length})`} accent="text-success">
        {data.research_papers.length === 0 ? (
          <EmptyNote>No linked papers found.</EmptyNote>
        ) : (
          <div className="space-y-4">
            {data.research_papers.slice(0, 10).map((p: any, i: number) => (
              <div key={p.id || i} className="pb-4 border-b border-edge-subtle last:border-0 last:pb-0">
                <div className="flex items-start justify-between gap-3 mb-1.5">
                  {p.arxiv_id ? (
                    <Link
                      to={`/research/${encodeURIComponent(p.arxiv_id)}`}
                      className="text-sm text-ink hover:text-accent transition-colors leading-snug flex-1"
                    >
                      {p.title}
                      <ArrowUpRight size={11} className="inline ml-1 text-ink-4" />
                    </Link>
                  ) : p.url ? (
                    <a
                      href={p.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm text-ink hover:text-accent transition-colors leading-snug flex-1"
                    >
                      {p.title}
                      <ExternalLink size={11} className="inline ml-1 text-ink-4" />
                    </a>
                  ) : (
                    <span className="text-sm text-ink leading-snug flex-1">{p.title}</span>
                  )}
                  {p.relevance_score !== undefined && p.relevance_score !== null && (
                    <span className="text-xs font-mono tabular-nums text-success flex-shrink-0">
                      {p.relevance_score.toFixed(2)}
                    </span>
                  )}
                </div>
                {p.authors && p.authors.length > 0 && (
                  <p className="text-2xs text-ink-3 mb-1.5 line-clamp-1">
                    {p.authors.slice(0, 4).join(', ')}
                    {p.authors.length > 4 ? ` +${p.authors.length - 4}` : ''}
                  </p>
                )}
                {p.results_summary && (
                  <p className="text-xs text-ink-3 leading-relaxed mb-1.5">{p.results_summary}</p>
                )}
                {p.research_methods && p.research_methods.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {p.research_methods.slice(0, 4).map((m: string, k: number) => (
                      <span key={k} className="badge bg-accent/10 text-accent border border-accent/30">
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

      {/* 7. Evidence and Sources */}
      <Section icon={Target} title={`Evidence & Sources (${data.evidence.length})`} accent="text-accent">
        {data.evidence.length === 0 ? (
          <EmptyNote>No aggregated evidence rows for this idea yet.</EmptyNote>
        ) : (
          <div className="space-y-1.5">
            {data.evidence.map((e, i) => (
              <SourceRow key={i} source={e.source} href={e.url}>{e.title || e.url}</SourceRow>
            ))}
          </div>
        )}
      </Section>

      {/* 8. Potential Research Gaps */}
      <Section icon={FileText} title={`Potential Research Gaps (${data.potential_gaps.length})`} accent="text-warning">
        {data.potential_gaps.length === 0 ? (
          <EmptyNote>No potential gaps identified for this idea yet.</EmptyNote>
        ) : (
          <>
            <p className="text-2xs text-ink-4 italic mb-3">
              These are potential gaps identified from available evidence. Expert validation required.
            </p>
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

      {/* 9. Related Opportunities */}
      <Section icon={Sparkles} title={`Related Opportunities (${data.opportunities.length})`} accent="text-accent">
        {data.opportunities.length === 0 ? (
          <EmptyNote>No opportunities linked to this idea yet.</EmptyNote>
        ) : (
          <div className="space-y-2">
            {data.opportunities.map(o => (
              <Link
                key={o.id}
                to={`/opportunities/${o.id}`}
                className="flex items-start justify-between gap-3 py-2 px-2 -mx-2 rounded-md hover:bg-overlay transition-colors group"
              >
                <p className="text-xs text-ink-2 leading-snug flex-1 group-hover:text-accent transition-colors line-clamp-2">
                  {o.title}
                </p>
                <span className="text-xs font-mono tabular-nums text-accent flex-shrink-0">
                  {o.opportunity_score.toFixed(2)}
                </span>
              </Link>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}
