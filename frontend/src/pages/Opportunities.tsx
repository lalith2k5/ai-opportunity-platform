import { useEffect, useState, useMemo } from 'react';
import { getOpportunities, type Opportunity } from '../services/api';
import OpportunityCard from '../components/OpportunityCard';
import { Loader2, Zap, ArrowUpDown, Search, Filter } from 'lucide-react';

type SortKey = 'opportunity_score' | 'demand_score' | 'research_gap_score' | 'trend_score' | 'feasibility_score' | 'title';

export default function Opportunities() {
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<SortKey>('opportunity_score');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [minScore, setMinScore] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 12;

  useEffect(() => {
    getOpportunities().then(setOpps).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    let result = [...opps];

    // Search
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(o =>
        o.title.toLowerCase().includes(q) ||
        (o.description || '').toLowerCase().includes(q)
      );
    }

    // Min score filter
    if (minScore > 0) {
      result = result.filter(o => o.opportunity_score >= minScore);
    }

    // Sort
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
  }, [opps, search, sortBy, sortDir, minScore]);

  const totalPages = Math.ceil(filtered.length / pageSize);
  const paginated = filtered.slice((page - 1) * pageSize, page * pageSize);

  const toggleSort = (key: SortKey) => {
    if (sortBy === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortBy(key); setSortDir('desc'); }
  };

  if (loading) return <div className="flex items-center justify-center h-screen"><Loader2 className="animate-spin text-brand-accent" size={48} /></div>;

  return (
    <div className="p-8 max-w-[1600px] mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <Zap className="text-yellow-400" size={28} /> All Opportunities
        </h1>
        <p className="text-gray-400 mt-1">
          Showing {paginated.length} of {filtered.length} opportunities
          {filtered.length < opps.length && ` (${opps.length} total)`}
        </p>
      </div>

      {/* Filters Bar */}
      <div className="bg-brand-panel border border-brand-border rounded-xl p-4 mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
          <input
            type="text"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search title or description..."
            className="w-full bg-brand-dark border border-brand-border rounded-lg pl-9 pr-3 py-2 text-white placeholder-gray-500 text-sm focus:outline-none focus:border-brand-accent"
          />
        </div>

        <select
          value={sortBy}
          onChange={e => setSortBy(e.target.value as SortKey)}
          className="bg-brand-dark border border-brand-border rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-brand-accent"
        >
          <option value="opportunity_score">Sort by Overall Score</option>
          <option value="demand_score">Sort by Demand</option>
          <option value="research_gap_score">Sort by Research Gap</option>
          <option value="trend_score">Sort by Trend</option>
          <option value="feasibility_score">Sort by Feasibility</option>
          <option value="title">Sort by Title</option>
        </select>

        <button
          onClick={() => setSortDir(d => d === 'asc' ? 'desc' : 'asc')}
          className="bg-brand-dark border border-brand-border rounded-lg px-3 py-2 text-white text-sm flex items-center justify-center gap-2 hover:border-brand-accent transition-colors"
        >
          <ArrowUpDown size={14} /> {sortDir === 'desc' ? 'Descending' : 'Ascending'}
        </button>

        <div className="flex items-center gap-3">
          <Filter className="text-gray-500 flex-shrink-0" size={16} />
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={minScore}
            onChange={e => { setMinScore(Number(e.target.value)); setPage(1); }}
            className="flex-1 accent-brand-accent"
          />
          <span className="text-xs text-gray-400 font-mono w-8 text-right">{minScore.toFixed(1)}</span>
        </div>
      </div>

      {/* Results */}
      {filtered.length === 0 ? (
        <div className="bg-brand-panel border border-brand-border rounded-xl p-12 text-center">
          <p className="text-gray-400">No opportunities match your filters.</p>
          <button
            onClick={() => { setSearch(''); setMinScore(0); setPage(1); }}
            className="mt-3 text-brand-accent hover:underline text-sm"
          >
            Clear filters
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {paginated.map(opp => <OpportunityCard key={opp.id} opp={opp} />)}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="bg-brand-panel border border-brand-border hover:border-brand-accent disabled:opacity-50 disabled:hover:border-brand-border text-white px-4 py-2 rounded-lg text-sm transition-colors"
              >
                Previous
              </button>
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                  let pageNum: number;
                  if (totalPages <= 7) {
                    pageNum = i + 1;
                  } else if (page <= 4) {
                    pageNum = i + 1;
                  } else if (page >= totalPages - 3) {
                    pageNum = totalPages - 6 + i;
                  } else {
                    pageNum = page - 3 + i;
                  }
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setPage(pageNum)}
                      className={`w-9 h-9 rounded-lg text-sm transition-colors ${
                        page === pageNum
                          ? 'bg-brand-accent text-white'
                          : 'bg-brand-panel border border-brand-border text-gray-300 hover:border-brand-accent'
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
                className="bg-brand-panel border border-brand-border hover:border-brand-accent disabled:opacity-50 disabled:hover:border-brand-border text-white px-4 py-2 rounded-lg text-sm transition-colors"
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
