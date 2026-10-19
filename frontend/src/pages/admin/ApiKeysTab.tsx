import { useEffect, useState } from 'react';
import { CheckCircle2, XCircle, Loader2, RefreshCw } from 'lucide-react';
import { api } from '../../services/api';

interface Slot {
  name: string;
  configured: boolean;
  source: 'env' | 'db' | 'none';
  preview: string;
  updated_at: string | null;
  updated_by: number | null;
}

interface TestResult {
  ok: boolean;
  message?: string;
  error?: string;
  status?: number;
}

export default function ApiKeysTab() {
  const [slots, setSlots] = useState<Slot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, TestResult>>({});
  const [llmStatus, setLlmStatus] = useState<any>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [r, l] = await Promise.all([
        api.get('/admin/keys'),
        api.get('/admin/llm/status').catch(() => null),
      ]);
      setLlmStatus(l?.data || null);
      setSlots(r.data.slots || []);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to load keys');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function save(name: string) {
    const v = input.trim();
    if (!v) return;
    setBusy(name);
    try {
      await api.post(`/admin/keys/${name}`, { value: v });
      setEditing(null);
      setInput('');
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Save failed');
    } finally {
      setBusy(null);
    }
  }

  async function test(name: string) {
    setBusy(name);
    try {
      const r = await api.post(`/admin/keys/${name}/test`);
      setResults(prev => ({ ...prev, [name]: r.data }));
    } catch (e: any) {
      setResults(prev => ({ ...prev, [name]: { ok: false, error: e?.message || 'Test failed' } }));
    } finally {
      setBusy(null);
    }
  }

  function cancelEdit() {
    setEditing(null);
    setInput('');
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-ink">API Keys</h2>
          <p className="text-sm text-ink-3 mt-1">
            Manage third-party API keys. Values are encrypted at rest and take effect within 60 seconds.
          </p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 text-sm rounded border border-line hover:bg-surface-2 disabled:opacity-50 transition-colors"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="px-4 py-3 rounded-lg bg-danger/10 text-danger text-sm border border-danger/20">
          {error}
        </div>
      )}

      {llmStatus && (
        <div className="rounded-lg border border-line p-4 bg-surface-2">
          <h3 className="text-sm font-medium text-ink mb-3">LLM Provider Status</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-ink-4 uppercase tracking-wider">Enabled</p>
              <p className="text-sm font-medium text-ink mt-0.5">{llmStatus.enabled ? 'Yes' : 'No'}</p>
            </div>
            <div>
              <p className="text-xs text-ink-4 uppercase tracking-wider">Primary</p>
              <p className="text-sm font-medium text-ink mt-0.5">{llmStatus.primary || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-ink-4 uppercase tracking-wider">Last Used</p>
              <p className="text-sm font-medium text-ink mt-0.5">{llmStatus.last_used || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-ink-4 uppercase tracking-wider">Available</p>
              <p className="text-sm font-medium text-ink mt-0.5">
                {Array.isArray(llmStatus.available) ? llmStatus.available.join(', ') : '—'}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="rounded-lg border border-line overflow-hidden bg-surface">
        <table className="w-full text-sm">
          <thead className="bg-surface-2 text-ink-3 border-b border-line">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Key</th>
              <th className="text-left px-4 py-3 font-medium">Status</th>
              <th className="text-left px-4 py-3 font-medium">Source</th>
              <th className="text-left px-4 py-3 font-medium">Value</th>
              <th className="text-right px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {slots.map(s => {
              const r = results[s.name];
              const isEditing = editing === s.name;
              return (
                <tr key={s.name} className="hover:bg-surface-2/50 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-ink">{s.name}</td>
                  <td className="px-4 py-3">
                    {s.configured ? (
                      <span className="inline-flex items-center gap-1.5 text-success text-xs font-medium">
                        <CheckCircle2 size={14} /> Configured
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 text-ink-4 text-xs">
                        <XCircle size={14} /> Not set
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-ink-3 uppercase tracking-wider">{s.source}</td>
                  <td className="px-4 py-3">
                    {isEditing ? (
                      <input
                        type="password"
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={e => {
                          if (e.key === 'Enter') save(s.name);
                          if (e.key === 'Escape') cancelEdit();
                        }}
                        placeholder="Paste new value"
                        className="w-full px-2 py-1.5 text-xs rounded border border-line bg-canvas font-mono focus:outline-none focus:ring-1 focus:ring-accent"
                        autoFocus
                      />
                    ) : (
                      <span className="text-xs text-ink-3 font-mono">{s.preview || '—'}</span>
                    )}
                    {r && (
                      <div className={`mt-1 text-[10px] font-medium ${r.ok ? 'text-success' : 'text-danger'}`}>
                        {r.ok
                          ? `✓ Test passed${r.status ? ` (${r.status})` : ''}`
                          : `✗ ${r.error || r.message || 'Failed'}`}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="inline-flex gap-2">
                      {isEditing ? (
                        <>
                          <button
                            onClick={() => save(s.name)}
                            disabled={busy === s.name || !input.trim()}
                            className="px-3 py-1.5 text-xs rounded bg-accent text-white hover:bg-accent/90 disabled:opacity-50 transition-colors"
                          >
                            {busy === s.name ? <Loader2 size={12} className="animate-spin" /> : 'Save'}
                          </button>
                          <button
                            onClick={cancelEdit}
                            className="px-3 py-1.5 text-xs rounded border border-line hover:bg-surface-2 transition-colors"
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            onClick={() => { setEditing(s.name); setInput(''); }}
                            className="px-3 py-1.5 text-xs rounded border border-line hover:bg-surface-2 transition-colors"
                          >
                            Set
                          </button>
                          <button
                            onClick={() => test(s.name)}
                            disabled={busy === s.name || !s.configured}
                            className="px-3 py-1.5 text-xs rounded border border-line hover:bg-surface-2 disabled:opacity-40 transition-colors"
                          >
                            {busy === s.name ? <Loader2 size={12} className="animate-spin" /> : 'Test'}
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {loading && slots.length === 0 && (
          <div className="p-8 text-center text-ink-3 text-sm flex items-center justify-center gap-2">
            <Loader2 size={16} className="animate-spin" /> Loading keys…
          </div>
        )}
      </div>

      <div className="rounded-lg border border-line p-4 bg-surface-2">
        <h3 className="text-sm font-medium text-ink mb-3">Where to get free keys</h3>
        <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-ink-3">
          <li><a href="https://openalex.org/action/register" className="text-accent hover:underline" target="_blank" rel="noreferrer">OpenAlex</a> — openalex.org/action/register</li>
          <li><a href="https://stackapps.com/apps/oauth/register" className="text-accent hover:underline" target="_blank" rel="noreferrer">Stack Exchange</a> — stackapps.com/apps/oauth/register</li>
          <li><a href="https://data.uspto.gov/myodp" className="text-accent hover:underline" target="_blank" rel="noreferrer">USPTO ODP</a> — data.uspto.gov/myodp</li>
          <li><a href="https://developers.epo.org" className="text-accent hover:underline" target="_blank" rel="noreferrer">EPO OPS</a> — developers.epo.org (Non-paying access)</li>
          <li><a href="https://dev.to/settings/extensions" className="text-accent hover:underline" target="_blank" rel="noreferrer">Dev.to</a> — dev.to/settings/extensions</li>
        </ul>
      </div>
    </div>
  );
}
