import { useEffect, useState } from 'react';
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

  const sorted = [...problems].sort((a, b) => {
    const av = a[sortBy];
    const bv = b[sortBy];
    if (typeof av === 'string' && typeof bv === 'string') {
      return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
    }
    const an = av as number;
    const bn = bv as number;
    return sortDir === 'asc' ? an - bn : bn - an;
  });

  const toggleSort = (key: SortKey) => {
    if (sortBy === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(key);
      setSortDir('desc');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen"><Loader2 className="animate-spin text-brand-accent" size={48} /></div>;
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <TrendingUp className="text-orange-400" size={28} /> Problem Rankings
        </h1>
        <p className="text-gray-400 mt-1">Recurring real-world problems ranked by demand</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-brand-panel border border-brand-border rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase">Total Problems</p>
          <p className="text-2xl font-bold text-white mt-1">{problems.length}</p>
        </div>
        <div className="bg-brand-panel border border-brand-border rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase">Avg Demand</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1">
            {problems.length ? (problems.reduce((s, p) => s + p.demand_score, 0) / problems.length).toFixed(2) : '0.00'}
          </p>
        </div>
        <div className="bg-brand-panel border border-brand-border rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase">Total Sources</p>
          <p className="text-2xl font-bold text-brand-accent mt-1">
            {problems.reduce((s, p) => s + p.source_count, 0)}
          </p>
        </div>
      </div>

      <div className="bg-brand-panel border border-brand-border rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-brand-dark text-xs text-gray-500 uppercase">
            <tr>
              <th className="text-left px-4 py-3 w-12">#</th>
              <th className="text-left px-4 py-3">
                <button onClick={() => toggleSort('title')} className="flex items-center gap-1 hover:text-white">
                  Title <ArrowUpDown size={12} />
                </button>
              </th>
              <th className="text-right px-4 py-3">
                <button onClick={() => toggleSort('source_count')} className="flex items-center gap-1 hover:text-white ml-auto">
                  Sources <ArrowUpDown size={12} />
                </button>
              </th>
              <th className="text-right px-4 py-3">
                <button onClick={() => toggleSort('demand_score')} className="flex items-center gap-1 hover:text-white ml-auto">
                  Demand <ArrowUpDown size={12} />
                </button>
              </th>
              <th className="text-left px-4 py-3">Keywords</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((p, i) => (
              <tr key={p.id} className="border-t border-brand-border hover:bg-brand-border/20">
                <td className="px-4 py-3 text-gray-500 font-mono">{i + 1}</td>
                <td className="px-4 py-3 text-gray-200">{p.title}</td>
                <td className="px-4 py-3 text-right text-gray-400 font-mono">{p.source_count}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <div className="w-24 h-1.5 bg-brand-border rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500" style={{ width: `${Math.min(100, p.demand_score * 100)}%` }} />
                    </div>
                    <span className="text-emerald-400 font-mono w-10 text-right">{p.demand_score.toFixed(2)}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {p.keywords?.slice(0, 4).map(k => (
                      <span key={k} className="bg-brand-border text-gray-400 text-[10px] px-1.5 py-0.5 rounded">
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
  );
}
