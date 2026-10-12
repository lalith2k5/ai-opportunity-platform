
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Factory, Search, Loader2, Building2, ArrowUpRight,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Toolbar from '../components/ui/Toolbar';
import { getProblemProfiles, type ProblemProfileListItem } from '../services/api';

function SourceBadge({ source }: { source: string }) {
  const map: Record<string, string> = {
    challenge_portal: 'bg-accent/15 text-accent border-accent/30',
    sbir: 'bg-success/15 text-success border-success/30',
    arxiv: 'bg-sky-500/15 text-sky-500 border-sky-500/30',
    github_issues: 'bg-purple-500/15 text-purple-500 border-purple-500/30',
    news: 'bg-warning/15 text-warning border-warning/30',
    patents: 'bg-overlay text-ink-3 border-edge',
  };
  const cls = map[source] || 'bg-overlay text-ink-3 border-edge';
  const label = source.replace(/_/g, ' ');
  return <span className={`badge ${cls} capitalize`}>{label}</span>;
}

function SuitabilityBadge({ level }: { level: string | null }) {
  if (!level) return null;
  const map: Record<string, string> = {
    high: 'bg-success/15 text-success border-success/30',
    medium: 'bg-warning/15 text-warning border-warning/30',
    low: 'bg-overlay text-ink-3 border-edge',
  };
  return (
    <span className={`badge ${map[level] || map.medium}`}>
      {level} suitability
    </span>
  );
}

function ProblemCard({ p, delay }: { p: ProblemProfileListItem; delay: number }) {
  return (
    <Link
      to={`/rd/${p.id}`}
      className="block card card-hover p-5 group animate-fade-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <SourceBadge source={p.source} />
            {p.industry_domain && (
              <span className="badge bg-overlay text-ink-3 border border-edge">
                {p.industry_domain}
              </span>
            )}
            {p.problem_type && p.problem_type !== 'Other' && (
              <span className="badge bg-overlay text-ink-3 border border-edge">
                {p.problem_type}
              </span>
            )}
            <SuitabilityBadge level={p.student_suitability} />
          </div>
          <h3 className="text-base font-semibold text-ink tracking-tight leading-snug group-hover:text-accent transition-colors line-clamp-2">
            {p.problem_title}
          </h3>
          <div className="flex items-center gap-1.5 mt-1.5 text-2xs text-ink-4">
            <Building2 size={11} />
            <span className="truncate">{p.organization || 'Unknown organization'}</span>
          </div>
          {p.problem_description && (
            <p className="text-xs text-ink-3 mt-2 leading-relaxed line-clamp-2">
              {p.problem_description}
            </p>
          )}
        </div>
        {p.confidence !== null && p.confidence !== undefined && (
          <div className="text-right flex-shrink-0">
            <p className="text-xl font-bold font-mono tabular-nums leading-none text-accent">
              {p.confidence.toFixed(2)}
            </p>
            <p className="text-2xs text-ink-4 mt-1.5 uppercase tracking-[0.08em]">Conf.</p>
          </div>
        )}
      </div>

      {p.required_technology && p.required_technology.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-3 border-t border-edge-subtle">
          {p.required_technology.slice(0, 5).map(t => (
            <span key={t} className="badge bg-accent/10 text-accent border border-accent/30">
              {t}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between mt-3 pt-3 border-t border-edge-subtle">
        <span className="text-2xs text-ink-4 uppercase tracking-[0.08em]">
          {p.created_at ? new Date(p.created_at).toLocaleDateString() : 'No date'}
        </span>
        <span className="text-2xs text-accent font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all duration-200 -translate-x-1 group-hover:translate-x-0">
          Details <ArrowUpRight size={11} />
        </span>
      </div>
    </Link>
  );
}

export default function RD() {
  const [items, setItems] = useState<ProblemProfileListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [domain, setDomain] = useState('');
  const [source, setSource] = useState('');
  const [suitability, setSuitability] = useState('');

  useEffect(() => {
    setLoading(true);
    const params: any = { limit: 200 };
    if (search.trim()) params.search = search.trim();
    if (domain) params.domain = domain;
    if (source) params.source = source;
    if (suitability) params.student_suitability = suitability;
    getProblemProfiles(params)
      .then(d => setItems(d.items || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [search, domain, source, suitability]);

  const domains = useMemo(() => {
    const s = new Set<string>();
    items.forEach(p => { if (p.industry_domain) s.add(p.industry_domain); });
    return Array.from(s).sort();
  }, [items]);

  const sources = useMemo(() => {
    const s = new Set<string>();
    items.forEach(p => { if (p.source) s.add(p.source); });
    return Array.from(s).sort();
  }, [items]);

  const hasFilters = Boolean(search || domain || source || suitability);

  return (
    <div className="p-6 lg:p-8 max-w-[1500px] mx-auto">
      <PageHeader
        icon={Factory}
        accent="warning"
        title="R&D Intelligence"
        subtitle="Industry problems, publicly documented technical challenges, and evidence-backed innovation opportunities. Every result is traceable to its source — expert validation required."
      />

      <Toolbar>
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-4" size={14} />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search problem, description, or organization…"
            className="input pl-8 text-sm w-full"
          />
        </div>
        <select value={domain} onChange={e => setDomain(e.target.value)} className="input text-sm md:w-44">
          <option value="">All domains</option>
          {domains.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
        <select value={source} onChange={e => setSource(e.target.value)} className="input text-sm md:w-44">
          <option value="">Any source</option>
          {sources.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
        </select>
        <select value={suitability} onChange={e => setSuitability(e.target.value)} className="input text-sm md:w-44">
          <option value="">Any suitability</option>
          <option value="high">High (student-friendly)</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        {hasFilters && (
          <button
            onClick={() => { setSearch(''); setDomain(''); setSource(''); setSuitability(''); }}
            className="btn-ghost text-xs whitespace-nowrap"
          >
            Clear
          </button>
        )}
      </Toolbar>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="animate-spin text-accent" size={28} />
        </div>
      ) : items.length === 0 ? (
        <div className="bg-surface border border-edge border-dashed rounded-lg p-12 text-center">
          <Factory className="text-ink-4 mx-auto mb-3" size={24} />
          <p className="text-sm text-ink-2 font-medium">No R&D problems match your filters</p>
          <p className="text-xs text-ink-4 mt-1">
            Try a broader search, or run a fresh pipeline to populate problem profiles from public challenge portals.
          </p>
        </div>
      ) : (
        <>
          <p className="text-xs text-ink-4 mb-4">
            {items.length} problem{items.length === 1 ? '' : 's'} · newest first
          </p>
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-3">
            {items.map((p, i) => (
              <ProblemCard key={p.id} p={p} delay={Math.min(i * 25, 500)} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
