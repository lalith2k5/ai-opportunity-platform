import { useEffect, useState } from 'react';
import { CheckCircle2, XCircle, Loader2, Save, X } from 'lucide-react';
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

  async function del(name: string) {
    if (!window.confirm(`Remove ${name}? This cannot be undone.`)) return;
    setBusy(name);
    try {
      await api.delete(`/admin/keys/${name}`);
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Delete failed');
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
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-ink">API Keys</h2>
          <p className="text-sm text-ink-3">
            Manage third-party API keys. Values are encrypted at rest and take effect within 60 seconds.
          </p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="px-3 py-1.5 text-sm rounded border border-line hover:bg-surface-2 disabled:opacity-50"
        >
          {loading ? 'Loading…' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="px-3 py-2 rounded bg-danger/10 text-danger text-sm border border-danger/20">
          {error}
        </div>
      )}

      {llmStatus && (
        <div className="rounded border border-line p-3 bg-surface-2">
          <p className="text-xs font-medium text-ink-3 mb-2">LLM Provider Status</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
            {Object.entries(llmStatus).map(([k, v]) => (
              <div key={k} className="flex flex-col">
                <span className="text-ink-4">{k}</span>
                <span className="font-mono text-ink">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="rounded border border-line overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-surface-2 text-ink-3">
            <tr>
              <th className="text-left px-3 py-2 font-medium">Key</th>
              <th className="text-left px-3 py-2 font-medium">Status</th>
              <th className="text-left px-3 py-2 font-medium">Source</th>
              <th className="text-left px-3 py-2 font-medium">Value</th>
              <th className="text-right px-3 py-2 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {slots.map(s => {
              const r = results[s.name];
              const isEditing = editing === s.name;
              return (
                <tr key={s.name} className="border-t border-line">
                  <td className="px-3 py-2 font-mono text-xs">{s.name}</td>
                  <td className="px-3 py-2">
                    {s.configured ? (
                      <span className="inline-flex items-center gap-1 text-success text-xs">
                        <CheckCircle2 size={12} /> configured
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-ink-4 text-xs">
                        <XCircle size={12} /> not set
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-xs text-ink-3">{s.source}</td>
                  <td className="px-3 py-2">
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
                        className="w-full px-2 py-1 text-xs rounded border border-line bg-canvas font-mono"
                        autoFocus
                      />
                    ) : (
                      <span className="text-xs text-ink-3 font-mono">{s.preview || '—'}</span>
                    )}
                    {r && (
                      <div className={`mt-1 text-xs ${r.ok ? 'text-success' : 'text-danger'}`}>
                        {r.ok
                          ? `✓ test passed${r.status ? ` (${r.status})` : ''}`
                          : `✗ ${r.error || r.message || 'failed'}`}
                      </div>
                    )}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <div className="inline-flex gap-1">
                      {isEditing ? (
                        <>
                          <button
                            onClick={() => save(s.name)}
                            disabled={busy === s.name || !input.trim()}
                            className="px-2 py-1 text-xs rounded bg-accent text-white disabled:opacity-50"
                          >
                            {busy === s.name ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                          </button>
                          <button
                            onClick={cancelEdit}
                            className="px-2 py-1 text-xs rounded border border-line hover:bg-surface-2"
                          >
                            <X size={12} />
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            onClick={() => { setEditing(s.name); setInput(''); }}
                            className="px-2 py-1 text-xs rounded border border-line hover:bg-surface-2"
                          >
                            Set
                          </button>
                          <button
                            onClick={() => test(s.name)}
                            disabled={busy === s.name || !s.configured}
                            className="px-2 py-1 text-xs rounded border border-line hover:bg-surface-2 disabled:opacity-40"
                          >
                            {busy === s.name ? '…' : 'Test'}
                          </button>
                          {s.source === 'db' && (
                            <button
                              onClick={() => del(s.name)}
                              disabled={busy === s.name}
                              className="px-2 py-1 text-xs rounded border border-danger/40 text-danger hover:bg-danger/10 disabled:opacity-40"
                            >
                              Delete
                            </button>
                          )}
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
          <div className="p-6 text-center text-ink-3 text-sm">Loading…</div>
        )}
      </div>

      <div className="text-xs text-ink-4 space-y-1">
        <p className="font-medium text-ink-3">Where to get free keys:</p>
        <ul className="list-disc list-inside space-y-0.5">
          <li>OpenAlex: <a href="https://openalex.org/action/register" className="text-accent hover:underline" target="_blank" rel="noreferrer">openalex.org/action/register</a></li>
          <li>Stack Exchange: <a href="https://stackapps.com/apps/oauth/register" className="text-accent hover:underline" target="_blank" rel="noreferrer">stackapps.com/apps/oauth/register</a></li>
          <li>USPTO ODP: <a href="https://data.uspto.gov/myodp" className="text-accent hover:underline" target="_blank" rel="noreferrer">data.uspto.gov/myodp</a></li>
          <li>EPO OPS: <a href="https://developers.epo.org" className="text-accent hover:underline" target="_blank" rel="noreferrer">developers.epo.org</a> (Non-paying access)</li>
          <li>Dev.to: <a href="https://dev.to/settings/extensions" className="text-accent hover:underline" target="_blank" rel="noreferrer">dev.to/settings/extensions</a></li>
        </ul>
      </div>
    </div>
  );
}
