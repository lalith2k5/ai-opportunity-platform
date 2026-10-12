
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpen, Search, Loader2, ArrowUpRight,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Toolbar from '../components/ui/Toolbar';
import { getResearchPapers, type ResearchPaperListItem } from '../services/api';

type SortKey = 'relevance' | 'year' | 'title';

function PaperCard({ p, delay }: { p: ResearchPaperListItem; delay: number }) {
  const canDrillDown = Boolean(p.arxiv_id) && !p.arxiv_id.startsWith('paper:');
  const inner = (
    <div
      className={`card card-hover p-5 group animate-fade-up ${canDrillDown ? '' : 'cursor-default'}`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            {p.year ? (
              <span className="badge bg-overlay text-ink-3 border border-edge font-mono">
                {p.year}
              </span>
            ) : (
              <span className="badge bg-overlay text-ink-4 border border-edge italic">
                year unavailable
              </span>
            )}
            {p.domain && (
              <span className="badge bg-accent/10 text-accent border border-accent/30">
                {p.domain}
              </span>
            )}
            {p.limitations_count > 0 && (
              <span className="badge bg-warning/10 text-warning border border-warning/30">
                {p.limitations_count} limitation{p.limitations_count === 1 ? '' : 's'}
              </span>
            )}
          </div>
          <h3 className="text-base font-semibold text-ink tracking-tight leading-snug group-hover:text-accent transition-colors line-clamp-2">
            {p.title}
          </h3>
          {p.authors.length > 0 && (
            <p className="text-xs text-ink-3 mt-1.5 leading-relaxed line-clamp-1">
              {p.authors.slice(0, 4).join(', ')}
              {p.authors.length > 4 ? ` +${p.authors.length - 4} more` : ''}
            </p>
          )}
        </div>
        <div className="text-right flex-shrink-0">
          <p className={`text-2xl font-bold font-mono tabular-nums leading-none tracking-tight ${
            p.relevance_score >= 0.7 ? 'text-success' : 'text-accent'
          }`}>
            {p.relevance_score.toFixed(2)}
          </p>
          <p className="text-2xs text-ink-4 mt-1.5 uppercase tracking-[0.08em]">Relevance</p>
        </div>
      </div>

      {p.abstract_snippet && (
        <p className="text-xs text-ink-3 leading-relaxed line-clamp-3 mb-3">
          {p.abstract_snippet}
        </p>
      )}

      {p.methods.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-3 border-t border-edge-subtle">
          {p.methods.slice(0, 5).map((m, i) => (
            <span key={i} className="badge bg-accent/10 text-accent border border-accent/30">
              {m}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between mt-3 pt-3 border-t border-edge-subtle">
        <span className="text-2xs text-ink-4 uppercase tracking-[0.08em] font-mono truncate">
          {p.arxiv_id || 'no id'}
        </span>
        {canDrillDown && (
          <span className="text-2xs text-accent font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all duration-200 -translate-x-1 group-hover:translate-x-0">
            View <ArrowUpRight size={11} />
          </span>
        )}
      </div>
    </div>
  );

  if (!canDrillDown) return inner;
  return (
    <Link to={`/research/${encodeURIComponent(p.arxiv_id)}`} className="block">
      {inner}
    </Link>
  );
}

export default function Research() {
  const [items, setItems] = useState<ResearchPaperListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [domain, setDomain] = useState('');
  const [year, setYear] = useState('');
  const [minRelevance, setMinRelevance] = useState(0);
  const [sortBy, setSortBy] = useState<SortKey>('relevance');

  useEffect(() => {
    setLoading(true);
    const params: { q?: string; domain?: string; year?: number; min_relevance?: number; limit?: number } = { limit: 300 };
    if (search.trim()) params.q = search.trim();
    if (domain) params.domain = domain;
    if (year) params.year = Number(year);
    if (minRelevance > 0) params.min_relevance = minRelevance;
    getResearchPapers(params)
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [search, domain, year, minRelevance]);

  const domains = useMemo(() => {
    const s = new Set<string>();
    items.forEach(p => { if (p.domain) s.add(p.domain); });
    return Array.from(s).sort();
  }, [items]);

  const years = useMemo(() => {
    const s = new Set<number>();
    items.forEach(p => { if (p.year) s.add(p.year); });
    return Array.from(s).sort((a, b) => b - a);
  }, [items]);

  const sorted = useMemo(() => {
    const list = [...items];
    if (sortBy === 'relevance') list.sort((a, b) => b.relevance_score - a.relevance_score);
    else if (sortBy === 'year') list.sort((a, b) => (b.year || 0) - (a.year || 0));
    else list.sort((a, b) => a.title.localeCompare(b.title));
    return list;
  }, [items, sortBy]);

  const hasFilters = Boolean(search || domain || year || minRelevance > 0);

  return (
    <div className="p-6 lg:p-8 max-w-[1500px] mx-auto">
      <PageHeader
        icon={BookOpen}
        accent="sky"
        title="Research Analysis"
        subtitle="Search, compare, and drill into papers — objective, methodology, findings, limitations, related work, and potential gaps."
      />

      {/* Filter bar */}
      <Toolbar className="mb-3">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-4" size={14} />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search title or abstract…"
            className="input pl-8 text-sm w-full"
          />
        </div>
        <select value={domain} onChange={e => setDomain(e.target.value)} className="input text-sm md:w-48">
          <option value="">All domains</option>
          {domains.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
        <select value={year} onChange={e => setYear(e.target.value)} className="input text-sm md:w-32">
          <option value="">Any year</option>
          {years.map(y => <option key={y} value={y}>{y}</option>)}
        </select>
        <select value={sortBy} onChange={e => setSortBy(e.target.value as SortKey)} className="input text-sm md:w-44">
          <option value="relevance">Sort: relevance</option>
          <option value="year">Sort: year (newest)</option>
          <option value="title">Sort: title (A-Z)</option>
        </select>
      </Toolbar>

      <div className="card p-3 mb-5 flex flex-col md:flex-row gap-4 items-center">
        <div className="flex items-center gap-3 flex-1">
          <span className="text-2xs text-ink-4 uppercase tracking-wider whitespace-nowrap">
            Min relevance
          </span>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={minRelevance}
            onChange={e => setMinRelevance(Number(e.target.value))}
            className="flex-1 accent-accent"
          />
          <span className="text-xs text-ink-3 font-mono tabular-nums w-8 text-right">
            {minRelevance.toFixed(1)}
          </span>
        </div>
        {hasFilters && (
          <button
            onClick={() => { setSearch(''); setDomain(''); setYear(''); setMinRelevance(0); }}
            className="btn-ghost text-xs whitespace-nowrap"
          >
            Clear filters
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="animate-spin text-accent" size={28} />
        </div>
      ) : sorted.length === 0 ? (
        <div className="bg-surface border border-edge border-dashed rounded-lg p-12 text-center">
          <BookOpen className="text-ink-4 mx-auto mb-3" size={24} />
          <p className="text-sm text-ink-2 font-medium">No papers match your filters</p>
          <p className="text-xs text-ink-4 mt-1">Try a broader search or clear filters.</p>
        </div>
      ) : (
        <>
          <p className="text-xs text-ink-4 mb-4">
            {sorted.length} paper{sorted.length === 1 ? '' : 's'} · sorted by {sortBy}
          </p>
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-3">
            {sorted.slice(0, 120).map((p, i) => (
              <PaperCard key={p.arxiv_id || i} p={p} delay={Math.min(i * 25, 500)} />
            ))}
          </div>
          {sorted.length > 120 && (
            <p className="text-xs text-ink-4 text-center mt-6">
              Showing first 120 results — narrow with filters above to see more.
            </p>
          )}
        </>
      )}
    </div>
  );
}
