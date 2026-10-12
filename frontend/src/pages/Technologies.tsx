
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Cpu, Search, TrendingUp, TrendingDown, Minus, Loader2, ArrowUpRight,
} from 'lucide-react';
import { getTechnologies, type TechnologyListItem } from '../services/api';

function StageBadge({ stage }: { stage: string | null }) {
  if (!stage) return null;
  const map: Record<string, string> = {
    used: 'bg-success/15 text-success border-success/30',
    proposed: 'bg-accent/15 text-accent border-accent/30',
    emerging: 'bg-warning/15 text-warning border-warning/30',
    potentially_applicable: 'bg-overlay text-ink-3 border-edge',
  };
  const cls = map[stage] || map.potentially_applicable;
  return <span className={`badge ${cls}`}>{stage.replace(/_/g, ' ')}</span>;
}

function TrendGlyph({ label }: { label: string | null }) {
  if (!label) return null;
  if (label === 'emerging') return <TrendingUp size={12} className="text-warning" />;
  if (label === 'growing') return <TrendingUp size={12} className="text-success" />;
  if (label === 'declining') return <TrendingDown size={12} className="text-danger" />;
  return <Minus size={12} className="text-ink-4" />;
}

function TechCard({ tech, delay }: { tech: TechnologyListItem; delay: number }) {
  const isHigh = tech.composite_score > 0.6;
  return (
    <Link
      to={`/technologies/${encodeURIComponent(tech.name)}`}
      className="block card card-hover p-5 group animate-fade-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <StageBadge stage={tech.stage} />
            {tech.domain && (
              <span className="badge bg-overlay text-ink-3 border border-edge">
                {tech.domain}
              </span>
            )}
            {tech.trend_label && (
              <span className="inline-flex items-center gap-1 text-2xs text-ink-4 capitalize">
                <TrendGlyph label={tech.trend_label} />
                {tech.trend_label}
              </span>
            )}
          </div>
          <h3 className="text-base font-semibold text-ink tracking-tight leading-snug group-hover:text-accent transition-colors line-clamp-2">
            {tech.name}
          </h3>
          <p className="text-xs text-ink-3 mt-1.5 leading-relaxed line-clamp-2">
            {tech.description}
          </p>
        </div>
        <div className="text-right flex-shrink-0">
          <p className={`text-2xl font-bold font-mono tabular-nums leading-none tracking-tight ${
            isHigh ? 'text-success' : 'text-accent'
          }`}>
            {tech.composite_score.toFixed(2)}
          </p>
          <p className="text-2xs text-ink-4 mt-1.5 uppercase tracking-[0.08em]">Score</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 pt-3 mt-3 border-t border-edge-subtle">
        <div>
          <p className="text-2xs text-ink-4 uppercase tracking-wider">Problems</p>
          <p className="text-sm font-semibold text-ink font-mono tabular-nums">
            {tech.related_problem_count}
          </p>
        </div>
        <div>
          <p className="text-2xs text-ink-4 uppercase tracking-wider">Papers</p>
          <p className="text-sm font-semibold text-ink font-mono tabular-nums">
            {tech.related_paper_count}
          </p>
        </div>
        <div>
          <p className="text-2xs text-ink-4 uppercase tracking-wider">Signals</p>
          <p className="text-sm font-semibold text-ink font-mono tabular-nums">
            {tech.source_count}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between mt-3 pt-3 border-t border-edge-subtle">
        <span className="text-2xs text-ink-4 uppercase tracking-[0.08em]">
          Confidence {tech.confidence.toFixed(2)}
        </span>
        <span className="text-2xs text-accent font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all duration-200 -translate-x-1 group-hover:translate-x-0">
          View <ArrowUpRight size={11} />
        </span>
      </div>
    </Link>
  );
}

export default function Technologies() {
  const [items, setItems] = useState<TechnologyListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [domain, setDomain] = useState('');
  const [stage, setStage] = useState('');

  useEffect(() => {
    setLoading(true);
    const params: { q?: string; domain?: string; stage?: string; limit?: number } = { limit: 200 };
    if (search.trim()) params.q = search.trim();
    if (domain) params.domain = domain;
    if (stage) params.stage = stage;
    getTechnologies(params)
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [search, domain, stage]);

  const domains = useMemo(() => {
    const s = new Set<string>();
    items.forEach(t => { if (t.domain) s.add(t.domain); });
    return Array.from(s).sort();
  }, [items]);

  const stages = ['used', 'proposed', 'emerging', 'potentially_applicable'];
  const hasFilters = Boolean(search || domain || stage);

  return (
    <div className="p-6 lg:p-8 max-w-[1500px] mx-auto">
      <div className="mb-6">
        <div className="flex items-center gap-3.5 mb-2">
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center shadow-[inset_0_1px_0_0_rgb(255_255_255/0.05)]">
            <Cpu className="text-purple-500" size={18} />
          </div>
          <h1 className="text-3xl font-bold text-ink tracking-tight">Choose the Technology</h1>
        </div>
        <p className="text-sm text-ink-3">
          Trending technologies and the problems, research, and opportunities each one connects to.
        </p>
      </div>

      <div className="card p-3 mb-5 flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-4" size={14} />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search technology…"
            className="input pl-8 text-sm w-full"
          />
        </div>
        <select value={domain} onChange={e => setDomain(e.target.value)} className="input text-sm md:w-48">
          <option value="">All domains</option>
          {domains.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
        <select value={stage} onChange={e => setStage(e.target.value)} className="input text-sm md:w-52">
          <option value="">Any stage</option>
          {stages.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
        </select>
        {hasFilters && (
          <button
            onClick={() => { setSearch(''); setDomain(''); setStage(''); }}
            className="btn-ghost text-xs whitespace-nowrap"
          >
            Clear
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="animate-spin text-accent" size={28} />
        </div>
      ) : items.length === 0 ? (
        <div className="bg-surface border border-edge border-dashed rounded-lg p-12 text-center">
          <Cpu className="text-ink-4 mx-auto mb-3" size={24} />
          <p className="text-sm text-ink-2 font-medium">No technologies match your filters</p>
          <p className="text-xs text-ink-4 mt-1">Try a broader search or clear filters.</p>
        </div>
      ) : (
        <>
          <p className="text-xs text-ink-4 mb-4">
            {items.length} technologies · sorted by composite score
          </p>
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-3">
            {items.map((t, i) => (
              <TechCard key={t.name} tech={t} delay={Math.min(i * 30, 600)} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
