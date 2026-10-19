
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Lightbulb, Search, TrendingUp, TrendingDown, Minus, ArrowUpRight,
} from 'lucide-react';
import { getIdeas, type IdeaListItem } from '../services/api';
import PageHeader from '../components/ui/PageHeader';
import { CardSkeleton } from '../components/LoadingSkeleton';
import Toolbar from '../components/ui/Toolbar';

function TrendGlyph({ label }: { label: string | null }) {
  if (!label) return null;
  if (label === 'emerging' || label === 'growing') return <TrendingUp size={12} className="text-success" />;
  if (label === 'declining') return <TrendingDown size={12} className="text-danger" />;
  return <Minus size={12} className="text-ink-4" />;
}

function IdeaCard({ idea, delay }: { idea: IdeaListItem; delay: number }) {
  const isHigh = idea.composite_score > 0.6;
  return (
    <Link
      to={`/ideas/${idea.id}`}
      className="block card card-hover p-5 lg:p-6 group animate-fade-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between gap-6 mb-4 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap min-w-0 flex-1">
          <span className="text-2xs font-mono text-ink-4">#{idea.id}</span>
          {idea.domain && (
            <span className="badge bg-overlay text-ink-3 border border-edge">
              {idea.domain}
            </span>
          )}
          {idea.trend_name && (
            <span className="inline-flex items-center gap-1 text-2xs text-ink-4 capitalize">
              <TrendGlyph label={idea.trend_name} />
              {idea.trend_name}
            </span>
          )}
        </div>
        <div className="text-right flex-shrink-0">
          <div className="flex items-baseline gap-1.5 justify-end">
            <span className={`text-3xl lg:text-4xl font-bold font-mono tabular-nums leading-none tracking-tight ${
              isHigh ? 'text-success' : 'text-accent'
            }`}>
              {idea.composite_score.toFixed(2)}
            </span>
            <span className="text-xs text-ink-4 font-mono">/1.00</span>
          </div>
          <p className="text-2xs text-ink-4 mt-1.5 uppercase tracking-[0.08em]">Composite score</p>
        </div>
      </div>

      <h3 className="text-xl lg:text-2xl font-semibold text-ink tracking-tight leading-tight mb-3 group-hover:text-accent transition-colors">
        {idea.title}
      </h3>

      {idea.description && (
        <p className="text-sm text-ink-2 leading-relaxed mb-4">
          {idea.description}
        </p>
      )}

      {idea.keywords.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {idea.keywords.slice(0, 10).map(k => (
            <span key={k} className="badge bg-overlay text-ink-3 border border-edge">
              {k}
            </span>
          ))}
        </div>
      )}

      <div className="grid grid-cols-3 gap-6 pt-4 border-t border-edge-subtle">
        <div>
          <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1.5">Sources</p>
          <p className="text-lg font-semibold text-ink font-mono tabular-nums">
            {idea.source_count}
          </p>
        </div>
        <div>
          <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1.5">Demand</p>
          <p className="text-lg font-semibold text-success font-mono tabular-nums">
            {idea.demand_score.toFixed(2)}
          </p>
        </div>
        <div>
          <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1.5">Opportunities</p>
          <p className="text-lg font-semibold text-accent font-mono tabular-nums">
            {idea.opportunity_count}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between mt-4 pt-4 border-t border-edge-subtle">
        <span className="text-2xs text-ink-4 uppercase tracking-[0.08em]">
          Trend {idea.trend_score.toFixed(2)}
        </span>
        <span className="text-2xs text-accent font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all duration-200 -translate-x-1 group-hover:translate-x-0">
          Open details <ArrowUpRight size={11} />
        </span>
      </div>
    </Link>
  );
}

export default function Ideas() {
  const [items, setItems] = useState<IdeaListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [domain, setDomain] = useState('');

  useEffect(() => {
    setLoading(true);
    const params: { q?: string; domain?: string; limit?: number } = { limit: 100 };
    if (search.trim()) params.q = search.trim();
    if (domain) params.domain = domain;
    getIdeas(params)
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [search, domain]);

  const domains = useMemo(() => {
    const s = new Set<string>();
    items.forEach(i => { if (i.domain) s.add(i.domain); });
    return Array.from(s).sort();
  }, [items]);

  const hasFilters = Boolean(search || domain);

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto">
      <PageHeader
        icon={Lightbulb}
        accent="accent"
        title="Find the Real-Time Ideas"
        subtitle="Trending real-world problems ranked by evidence and momentum, with a full drill-down across sources."
      />

      <Toolbar>
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-4" size={14} />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search problem, idea, or topic…"
            className="input pl-8 text-sm w-full"
          />
        </div>
        <select value={domain} onChange={e => setDomain(e.target.value)} className="input text-sm md:w-48">
          <option value="">All domains</option>
          {domains.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
        {hasFilters && (
          <button
            onClick={() => { setSearch(''); setDomain(''); }}
            className="btn-ghost text-xs whitespace-nowrap"
          >
            Clear
          </button>
        )}
      </Toolbar>

      {loading ? (
        <div className="space-y-4">
          {[1,2,3].map(i => <CardSkeleton key={i} />)}
        </div>
      ) : items.length === 0 ? (
        <div className="bg-surface border border-edge border-dashed rounded-lg p-12 text-center">
          <Lightbulb className="text-ink-4 mx-auto mb-3" size={24} />
          <p className="text-sm text-ink-2 font-medium">No ideas match your filters</p>
          <p className="text-xs text-ink-4 mt-1">Try a broader search, or run a fresh pipeline.</p>
        </div>
      ) : (
        <>
          <p className="text-xs text-ink-4 mb-4">
            {items.length} idea{items.length === 1 ? '' : 's'} · sorted by composite score
          </p>
          <div
            key={search + '|' + domain}
            className="space-y-4 animate-fade-in"
          >
            {items.map((idea, i) => (
              <IdeaCard key={idea.id} idea={idea} delay={Math.min(i * 40, 400)} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
