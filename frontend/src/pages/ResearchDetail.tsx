
import { useEffect, useState, type ReactNode } from 'react';
import PotentialGapNote from '../components/PotentialGapNote';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft, Loader2, AlertCircle, BookOpen, Target, Wrench,
  Award, AlertTriangle, Network, Cpu, FileText, ExternalLink,
} from 'lucide-react';
import { getResearchPaperDetail, type ResearchPaperDetail } from '../services/api';
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

function Unavailable({ label }: { label: string }) {
  return (
    <p className="text-xs text-ink-4 italic">
      {label} — not available in the source.
    </p>
  );
}

export default function ResearchDetail() {
  const { arxiv_id } = useParams<{ arxiv_id: string }>();
  const [data, setData] = useState<ResearchPaperDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!arxiv_id) return;
    setLoading(true);
    getResearchPaperDetail(arxiv_id)
      .then(setData)
      .catch((e: any) => setError(formatApiError(e)))
      .finally(() => setLoading(false));
  }, [arxiv_id]);

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
        <Link to="/research" className="btn-ghost text-xs mb-4">
          <ArrowLeft size={13} /> Back to research
        </Link>
        <div className="bg-danger/10 border border-danger/30 rounded-lg p-5">
          <AlertCircle className="text-danger mb-2" size={20} />
          <p className="text-danger text-sm">{error || 'Paper not found'}</p>
        </div>
      </div>
    );
  }

  const p = data.paper;

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto animate-fade-up">
      <Link
        to="/research"
        className="inline-flex items-center gap-1.5 text-xs text-ink-3 hover:text-accent transition-colors mb-6 group"
      >
        <ArrowLeft size={13} className="transition-transform group-hover:-translate-x-0.5" />
        Back to research
      </Link>

      {/* Hero */}
      <div className="card p-6 mb-5 relative overflow-hidden">
        <div
          className="absolute -top-32 -right-32 w-96 h-96 rounded-full pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgb(56 189 248 / 0.12), transparent 60%)' }}
        />
        <div className="flex items-start justify-between gap-6 flex-wrap relative">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-3 flex-wrap">
              {p.year ? (
                <span className="badge bg-overlay text-ink-3 border border-edge font-mono">{p.year}</span>
              ) : (
                <span className="badge bg-overlay text-ink-4 border border-edge italic">
                  year unavailable
                </span>
              )}
              {p.domain && (
                <span className="badge bg-accent/10 text-accent border border-accent/30">{p.domain}</span>
              )}
              {p.arxiv_id && (
                <span className="text-2xs text-ink-4 font-mono">arXiv:{p.arxiv_id}</span>
              )}
            </div>
            <h1 className="text-2xl lg:text-3xl font-bold text-ink tracking-tight leading-tight mb-3">
              {p.title}
            </h1>
            {p.authors.length > 0 ? (
              <p className="text-sm text-ink-2 leading-relaxed">
                {p.authors.join(', ')}
              </p>
            ) : (
              <p className="text-sm text-ink-4 italic">Authors not available.</p>
            )}
          </div>
          <div className="text-right flex-shrink-0">
            <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2">Relevance</p>
            <p className={`text-4xl font-bold font-mono tabular-nums leading-none tracking-tight ${
              p.relevance_score >= 0.7 ? 'text-success' : 'text-accent'
            }`}>
              {p.relevance_score.toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      {/* 1. Paper Overview */}
      <Section icon={BookOpen} title="Paper Overview" accent="text-sky-500">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Publication year</p>
            <p className="text-sm text-ink-2">{p.year || 'Not available'}</p>
          </div>
          <div>
            <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Published date</p>
            <p className="text-sm text-ink-2">{p.published || 'Not available'}</p>
          </div>
          <div>
            <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Domain</p>
            <p className="text-sm text-ink-2">{p.domain || 'Not available'}</p>
          </div>
          <div>
            <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">arXiv ID</p>
            <p className="text-sm text-ink-2 font-mono">{p.arxiv_id || 'Not available'}</p>
          </div>
        </div>
        <div className="pt-4 border-t border-edge-subtle">
          <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2">Abstract</p>
          {p.abstract ? (
            <p className="text-sm text-ink-2 leading-relaxed">{p.abstract}</p>
          ) : (
            <Unavailable label="Abstract" />
          )}
        </div>
      </Section>

      {/* 2. Research Objective */}
      <Section icon={Target} title="Research Objective" accent="text-warning">
        {data.research_objective ? (
          <p className="text-sm text-ink-2 leading-relaxed">{data.research_objective}</p>
        ) : (
          <Unavailable label="Research objective" />
        )}
      </Section>

      {/* 3. Methodology */}
      <Section icon={Wrench} title="Methodology" accent="text-purple-500">
        {data.methodology.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {data.methodology.map((m, i) => (
              <span key={i} className="badge bg-purple-500/10 text-purple-500 border border-purple-500/30">
                {m}
              </span>
            ))}
          </div>
        ) : (
          <Unavailable label="Methodology" />
        )}
      </Section>

      {/* 4. Key Findings */}
      <Section icon={Award} title="Key Findings" accent="text-success">
        {data.key_findings ? (
          <p className="text-sm text-ink-2 leading-relaxed">{data.key_findings}</p>
        ) : (
          <Unavailable label="Key findings" />
        )}
      </Section>

      {/* 5. Limitations */}
      <Section icon={AlertTriangle} title="Limitations" accent="text-warning">
        {data.limitations.length > 0 ? (
          <ul className="space-y-2">
            {data.limitations.map((L, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-ink-2 leading-relaxed">
                <span className="text-warning flex-shrink-0 mt-0.5">•</span>
                <span>{L}</span>
              </li>
            ))}
          </ul>
        ) : (
          <Unavailable label="Limitations" />
        )}
      </Section>

      {/* 6. Related Papers */}
      <Section icon={Network} title={`Related Papers (${data.related_papers.length})`} accent="text-accent">
        {data.related_papers.length === 0 ? (
          <Unavailable label="Related papers" />
        ) : (
          <div className="space-y-3">
            {data.related_papers.map(rp => (
              <Link
                key={rp.arxiv_id || rp.title}
                to={`/research/${encodeURIComponent(rp.arxiv_id)}`}
                className="block pb-3 border-b border-edge-subtle last:border-0 last:pb-0 hover:opacity-80 transition-opacity"
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="text-xs text-ink-2 leading-snug flex-1">{rp.title}</p>
                  <div className="text-right flex-shrink-0">
                    <p className="text-xs font-mono tabular-nums text-accent">
                      {rp.relevance_score?.toFixed(2)}
                    </p>
                    {rp.year && (
                      <p className="text-2xs text-ink-4 font-mono mt-0.5">{rp.year}</p>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </Section>

      {/* 7. Related Technologies */}
      <Section icon={Cpu} title={`Related Technologies (${data.related_technologies.length})`} accent="text-purple-500">
        {data.related_technologies.length === 0 ? (
          <Unavailable label="Related technologies" />
        ) : (
          <div className="flex flex-wrap gap-2">
            {data.related_technologies.map(t => (
              <Link
                key={t}
                to={`/technologies/${encodeURIComponent(t)}`}
                className="badge bg-purple-500/10 text-purple-500 border border-purple-500/30 hover:bg-purple-500/20 transition-colors"
              >
                {t}
              </Link>
            ))}
          </div>
        )}
      </Section>

      {/* 8. Potential Research Gaps */}
      <Section icon={FileText} title={`Potential Research Gaps (${data.potential_gaps.length})`} accent="text-warning">
        {data.potential_gaps.length === 0 ? (
          <Unavailable label="Research gaps" />
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

      {/* 9. Original Source */}
      <Section icon={ExternalLink} title="Original Source" accent="text-accent">
        {data.source.url ? (
          <a
            href={data.source.url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 text-sm text-accent hover:text-accent-hover transition-colors"
          >
            <ExternalLink size={13} />
            <span className="break-all">{data.source.url}</span>
          </a>
        ) : (
          <Unavailable label="Original source URL" />
        )}
      </Section>
    </div>
  );
}
