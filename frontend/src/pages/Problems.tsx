import { useEffect, useState, useMemo } from 'react';
import { getProblems, type ProblemCluster } from '../services/api';
import { Loader2, TrendingUp, ArrowUpDown } from 'lucide-react';

type SortKey = 'demand_score' | 'source_count' | 'title';

export default function Problems() {
  const [problems, setProblems] = useState<ProblemCluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<SortKey>('demand_score');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    getProblems().then(setProblems).finally(() => setLoading(false));
  }, []);

  const sorted = useMemo(() => {
    return [...problems].sort((a, b) => {
      const av = a[sortBy];
      const bv = b[sortBy];
      if (typeof av === 'string' && typeof bv === 'string') {
        return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      const an = av as number;
      const bn = bv as number;
      return sortDir === 'asc' ? an - bn : bn - an;
    });
  }, [problems, sortBy, sortDir]);

  const toggleSort = (key: SortKey) => {
    if (sortBy === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortBy(key); setSortDir('desc'); }
  };

  const avgDemand = problems.length
    ? problems.reduce((s, p) => s + p.demand_score, 0) / problems.length
    : 0;
  const totalSources = problems.reduce((s, p) => s + p.source_count, 0);

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
        <div className="flex items-center gap-3.5 mb-2">
          <div className="w-10 h-10 rounded-xl bg-warning/10 flex items-center justify-center shadow-[inset_0_1px_0_0_rgb(255_255_255/0.05)]">
            <TrendingUp className="text-warning" size={18} />
          </div>
          <h1 className="text-3xl font-bold text-ink tracking-tight">Problem rankings</h1>
        </div>
        <p className="text-sm text-ink-3">Recurring real-world problems clustered from multi-source signals</p>
      </div>

      {/* Stat row */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="card p-4">
          <p className="text-2xs font-medium text-ink-4 uppercase tracking-[0.08em] mb-2">Total clusters</p>
          <p className="text-2xl font-semibold text-ink font-mono tabular-nums">{problems.length}</p>
        </div>
        <div className="card p-4">
          <p className="text-2xs font-medium text-ink-4 uppercase tracking-[0.08em] mb-2">Avg demand</p>
          <p className="text-2xl font-semibold text-success font-mono tabular-nums">{avgDemand.toFixed(2)}</p>
        </div>
        <div className="card p-4">
          <p className="text-2xs font-medium text-ink-4 uppercase tracking-[0.08em] mb-2">Total sources</p>
          <p className="text-2xl font-semibold text-accent font-mono tabular-nums">{totalSources}</p>
        </div>
      </div>

      {/* Table */}
      <div className="bg-surface border border-edge rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-edge bg-overlay">
                <th className="text-left text-2xs font-medium text-ink-4 uppercase tracking-wider px-4 py-2.5 w-10">#</th>
                <th className="text-left px-4 py-2.5">
                  <button
                    onClick={() => toggleSort('title')}
                    className="flex items-center gap-1 text-2xs font-medium text-ink-4 uppercase tracking-wider hover:text-ink-2 transition-colors"
                  >
                    Title <ArrowUpDown size={10} />
                  </button>
                </th>
                <th className="text-right px-4 py-2.5">
                  <button
                    onClick={() => toggleSort('source_count')}
                    className="ml-auto flex items-center gap-1 text-2xs font-medium text-ink-4 uppercase tracking-wider hover:text-ink-2 transition-colors"
                  >
                    Sources <ArrowUpDown size={10} />
                  </button>
                </th>
                <th className="text-right px-4 py-2.5 w-48">
                  <button
                    onClick={() => toggleSort('demand_score')}
                    className="ml-auto flex items-center gap-1 text-2xs font-medium text-ink-4 uppercase tracking-wider hover:text-ink-2 transition-colors"
                  >
                    Demand <ArrowUpDown size={10} />
                  </button>
                </th>
                <th className="text-left px-4 py-2.5">Keywords</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((p, i) => (
                <tr key={p.id} className="border-b border-edge-subtle last:border-0 hover:bg-overlay/60 transition-colors">
                  <td className="px-4 py-3 text-ink-4 font-mono text-xs">{i + 1}</td>
                  <td className="px-4 py-3 text-ink-2 text-xs leading-snug">{p.title}</td>
                  <td className="px-4 py-3 text-right text-ink-3 font-mono tabular-nums text-xs">{p.source_count}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2.5">
                      <div className="w-24 h-1 bg-overlay rounded-full overflow-hidden">
                        <div className="h-full bg-success" style={{ width: `${Math.min(100, p.demand_score * 100)}%` }} />
                      </div>
                      <span className="text-success font-mono tabular-nums text-xs w-9 text-right">{p.demand_score.toFixed(2)}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {p.keywords?.slice(0, 4).map(k => (
                        <span key={k} className="badge bg-overlay text-ink-3 border border-edge">
                          {k}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
