import { useEffect, useState, useMemo } from 'react';
import { getOpportunities, getOpportunityFilters, type Opportunity } from '../services/api';
import OpportunityCard from '../components/OpportunityCard';
import { Loader2, Zap, ArrowUpDown, Search, SlidersHorizontal } from 'lucide-react';

type SortKey = 'opportunity_score' | 'demand_score' | 'research_gap_score' | 'trend_score' | 'feasibility_score' | 'title';

export default function Opportunities() {
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<SortKey>('opportunity_score');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [minScore, setMinScore] = useState(0);
  const [page, setPage] = useState(1);
  const [domain, setDomain] = useState('');
  const [industry, setIndustry] = useState('');
  const [technology, setTechnology] = useState('');
  const [filterOptions, setFilterOptions] = useState<{ domains: string[]; industries: string[]; technologies: string[] }>({ domains: [], industries: [], technologies: [] });
  const pageSize = 24;

  useEffect(() => {
    getOpportunities().then(setOpps).finally(() => setLoading(false));
    getOpportunityFilters().then(setFilterOptions).catch(() => {});
  }, []);

  const filtered = useMemo(() => {
    let result = [...opps];
    // ---- Phase 10.6: SRS 22 domain/industry/technology filters ----
    if (domain)     result = result.filter(o => o.domain === domain);
    if (industry)   result = result.filter(o => o.industry === industry);
    if (technology) result = result.filter(o => (o.related_technologies || []).includes(technology));
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(o =>
        o.title.toLowerCase().includes(q) ||
        (o.description || '').toLowerCase().includes(q)
      );
    }
    if (minScore > 0) result = result.filter(o => o.opportunity_score >= minScore);
    result.sort((a, b) => {
      const av = a[sortBy];
      const bv = b[sortBy];
      if (typeof av === 'string' && typeof bv === 'string') {
        return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      const an = av as number;
      const bn = bv as number;
      return sortDir === 'asc' ? an - bn : bn - an;
    });
    return result;
  }, [opps, search, sortBy, sortDir, minScore, domain, industry, technology]);

  const totalPages = Math.ceil(filtered.length / pageSize);
  const paginated = filtered.slice((page - 1) * pageSize, page * pageSize);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="animate-spin text-accent" size={32} />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-[1500px] mx-auto">

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-8 h-8 rounded-md bg-accent/10 flex items-center justify-center">
            <Zap className="text-accent" size={16} />
          </div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">Opportunities</h1>
        </div>
        <p className="text-sm text-ink-3">
          Showing{' '}
          <span className="text-ink font-medium">
            {filtered.length === 0 ? 0 : (page - 1) * pageSize + 1}–{Math.min(page * pageSize, filtered.length)}
          </span>{' '}
          of <span className="text-ink font-medium">{filtered.length}</span> ranked opportunities
        </p>
      </div>

      {/* Filter bar — row 1 (search + sort) */}
      <div className="bg-surface border border-edge rounded-lg p-3 mb-3 flex flex-col md:flex-row gap-3 items-stretch md:items-center">

        <div className="relative flex-1 md:max-w-md">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-4" size={14} />
          <input
            type="text"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search opportunities…"
            className="input pl-8 text-sm"
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value as SortKey)}
            className="input text-sm"
          >
            <option value="opportunity_score">Overall score</option>
            <option value="demand_score">Demand</option>
            <option value="research_gap_score">Research gap</option>
            <option value="trend_score">Trend</option>
            <option value="feasibility_score">Feasibility</option>
            <option value="title">Title</option>
          </select>

          <button
            onClick={() => setSortDir(d => d === 'asc' ? 'desc' : 'asc')}
            title={sortDir === 'desc' ? 'Descending' : 'Ascending'}
            className="btn-secondary text-xs flex-shrink-0"
          >
            <ArrowUpDown size={13} />
            {sortDir === 'desc' ? 'Desc' : 'Asc'}
          </button>
        </div>

        <div className="flex items-center gap-3 md:ml-auto md:pl-4 md:border-l md:border-edge">
          <SlidersHorizontal size={13} className="text-ink-4 flex-shrink-0" />
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={minScore}
            onChange={e => { setMinScore(Number(e.target.value)); setPage(1); }}
            className="flex-1 md:w-32 accent-accent"
          />
          <span className="text-xs text-ink-3 font-mono tabular-nums w-8 text-right flex-shrink-0">
            {minScore.toFixed(1)}
          </span>
        </div>

      </div>

      {/* Filter bar — row 2 (SRS 22 domain / industry / technology) */}
      <div className="bg-surface border border-edge rounded-lg p-3 mb-6 flex flex-col md:flex-row gap-3 items-stretch md:items-center">
        <select
          value={domain}
          onChange={e => { setDomain(e.target.value); setPage(1); }}
          className="input text-sm md:flex-1"
        >
          <option value="">All domains</option>
          {filterOptions.domains.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
        <select
          value={industry}
          onChange={e => { setIndustry(e.target.value); setPage(1); }}
          className="input text-sm md:flex-1"
        >
          <option value="">All industries</option>
          {filterOptions.industries.map(i => <option key={i} value={i}>{i}</option>)}
        </select>
        <select
          value={technology}
          onChange={e => { setTechnology(e.target.value); setPage(1); }}
          className="input text-sm md:flex-1"
        >
          <option value="">All technologies</option>
          {filterOptions.technologies.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        {(domain || industry || technology) && (
          <button
            onClick={() => { setDomain(''); setIndustry(''); setTechnology(''); setPage(1); }}
            className="btn-ghost text-xs whitespace-nowrap"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Results */}
      {filtered.length === 0 ? (
        <div className="bg-surface border border-edge border-dashed rounded-lg p-12 text-center">
          <Search className="text-ink-4 mx-auto mb-3" size={22} />
          <p className="text-sm text-ink-2 font-medium">No opportunities match your filters</p>
          <button
            onClick={() => { setSearch(''); setMinScore(0); setPage(1); }}
            className="btn-ghost text-xs mt-3 mx-auto"
          >
            Clear filters
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-3">
            {paginated.map(opp => <OpportunityCard key={opp.id} opp={opp} />)}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-1 mt-8">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-secondary text-xs"
              >
                Previous
              </button>

              <div className="flex items-center gap-1 mx-2">
                {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                  let pageNum: number;
                  if (totalPages <= 7) pageNum = i + 1;
                  else if (page <= 4) pageNum = i + 1;
                  else if (page >= totalPages - 3) pageNum = totalPages - 6 + i;
                  else pageNum = page - 3 + i;
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setPage(pageNum)}
                      className={`w-8 h-8 rounded-md text-xs font-mono tabular-nums transition-all ${
                        page === pageNum
                          ? 'bg-accent text-accent-fg'
                          : 'text-ink-2 hover:bg-overlay border border-edge'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>

              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="btn-secondary text-xs"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
