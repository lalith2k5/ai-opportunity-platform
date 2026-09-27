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
    <div className="p-6 lg:p-8 max-w-4xl mx-auto">

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-8 h-8 rounded-md bg-accent/10 flex items-center justify-center">
            <SearchIcon className="text-accent" size={16} />
          </div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">Run intelligence pipeline</h1>
        </div>
        <p className="text-sm text-ink-3">
          Enter a topic to collect data from GitHub, arXiv, and News, then run the AI analysis.
        </p>
      </div>

      {/* Input card */}
      <div className="bg-surface border border-edge rounded-lg p-5 mb-6">
        <div className="flex flex-col md:flex-row gap-3">
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleRun()}
            placeholder="e.g. artificial intelligence healthcare"
            className="input flex-1"
          />
          <button
            onClick={handleRun}
            disabled={loading || !query.trim()}
            className="btn-primary whitespace-nowrap"
          >
            {loading ? <Loader2 className="animate-spin" size={15} /> : <SearchIcon size={15} />}
            {loading ? 'Running…' : 'Run pipeline'}
          </button>
        </div>
        {loading && (
          <p className="text-xs text-ink-4 mt-3">
            This takes 30–90 seconds depending on mode.
          </p>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="bg-danger/10 border border-danger/30 rounded-lg p-4 mb-6 flex items-start gap-3">
          <AlertCircle className="text-danger flex-shrink-0 mt-0.5" size={16} />
          <div>
            <p className="text-sm text-danger font-medium">Pipeline error</p>
            <p className="text-xs text-danger/80 mt-1 leading-relaxed">{error}</p>
          </div>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="space-y-4">
          <div className="bg-success/10 border border-success/30 rounded-lg p-4 flex items-start gap-3">
            <CheckCircle2 className="text-success flex-shrink-0 mt-0.5" size={16} />
            <div>
              <p className="text-sm text-success font-medium">Pipeline complete</p>
              <p className="text-xs text-success/80 mt-1">
                {result.documents_count} documents processed
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'Clusters',      value: result.clusters?.length || 0,       accent: 'text-accent' },
              { label: 'Research gaps', value: result.research_gaps?.length || 0,  accent: 'text-success' },
              { label: 'Trends',        value: result.trends?.length || 0,         accent: 'text-warning' },
              { label: 'Opportunities', value: result.opportunities?.length || 0,  accent: 'text-accent' },
            ].map(s => (
              <div key={s.label} className="bg-surface border border-edge rounded-lg p-4">
                <p className="text-2xs font-medium text-ink-4 uppercase tracking-wider mb-2">{s.label}</p>
                <p className={`text-2xl font-semibold font-mono tabular-nums ${s.accent}`}>{s.value}</p>
              </div>
            ))}
          </div>

          <div className="bg-surface border border-edge rounded-lg p-4 flex items-start gap-3">
            <SearchIcon size={14} className="text-accent flex-shrink-0 mt-0.5" />
            <p className="text-xs text-ink-2 leading-relaxed">
              New opportunities are ready. Open the <span className="text-ink font-medium">Dashboard</span> or{' '}
              <span className="text-ink font-medium">Opportunities</span> page to see them.
            </p>
          </div>
        </div>
      )}

    </div>
  );
}
