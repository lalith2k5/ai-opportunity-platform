import { useState } from 'react';
import { runPipeline } from '../services/api';
import { Search as SearchIcon, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

export default function Search() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const handleRun = async () => {
    if (!query.trim()) return;
    setLoading(true); setError(''); setResult(null);
    try {
      const data = await runPipeline(query);
      setResult(data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || 'Pipeline failed');
    } finally { setLoading(false); }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Run Intelligence Pipeline</h1>
        <p className="text-gray-400 mt-1">Enter a topic to collect data from GitHub, arXiv, and News, then run AI analysis.</p>
      </div>

      <div className="bg-brand-panel border border-brand-border rounded-xl p-6 mb-6">
        <div className="flex gap-3">
          <input
            type="text" value={query} onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleRun()}
            placeholder="e.g. artificial intelligence healthcare"
            className="flex-1 bg-brand-dark border border-brand-border rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-brand-accent"
          />
          <button
            onClick={handleRun} disabled={loading || !query.trim()}
            className="bg-brand-accent hover:bg-indigo-600 disabled:opacity-50 text-white px-6 py-3 rounded-lg font-medium flex items-center gap-2 transition-colors"
          >
            {loading ? <Loader2 className="animate-spin" size={18} /> : <SearchIcon size={18} />}
            {loading ? 'Running...' : 'Run Pipeline'}
          </button>
        </div>
        {loading && <p className="text-sm text-gray-400 mt-3">This takes 30–90 seconds.</p>}
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 mb-6 flex items-start gap-3">
          <AlertCircle className="text-red-400 mt-0.5" size={20} />
          <div><p className="text-red-300 font-medium">Pipeline Error</p><p className="text-red-200/70 text-sm mt-1">{error}</p></div>
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <div className="bg-emerald-900/30 border border-emerald-700 rounded-xl p-4 flex items-start gap-3">
            <CheckCircle2 className="text-emerald-400 mt-0.5" size={20} />
            <div><p className="text-emerald-300 font-medium">Pipeline Complete</p>
              <p className="text-emerald-200/70 text-sm mt-1">{result.documents_count} documents processed</p></div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-brand-panel border border-brand-border rounded-lg p-4">
              <p className="text-xs text-gray-500 mb-1">Clusters</p>
              <p className="text-2xl font-bold text-white">{result.clusters?.length || 0}</p>
            </div>
            <div className="bg-brand-panel border border-brand-border rounded-lg p-4">
              <p className="text-xs text-gray-500 mb-1">Research Gaps</p>
              <p className="text-2xl font-bold text-white">{result.research_gaps?.length || 0}</p>
            </div>
            <div className="bg-brand-panel border border-brand-border rounded-lg p-4">
              <p className="text-xs text-gray-500 mb-1">Trends</p>
              <p className="text-2xl font-bold text-white">{result.trends?.length || 0}</p>
            </div>
            <div className="bg-brand-panel border border-brand-border rounded-lg p-4">
              <p className="text-xs text-gray-500 mb-1">Opportunities</p>
              <p className="text-2xl font-bold text-white">{result.opportunities?.length || 0}</p>
            </div>
          </div>
          <div className="bg-brand-panel border border-brand-border rounded-xl p-4">
            <p className="text-sm text-gray-400">
              Navigate to <span className="text-brand-accent font-medium">Dashboard</span> to see new opportunities.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
