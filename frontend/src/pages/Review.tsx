import { useEffect, useState } from 'react';
import {
  Loader2, Shield, CheckCircle2, AlertCircle, XCircle, FileText,
} from 'lucide-react';
import {
  getReviewQueue, decideGap,
  type ReviewQueueItem,
} from '../services/api';
import GapStatusBadge from '../components/GapStatusBadge';
import { useToast } from '../context/ToastContext';

export default function Review() {
  const [items, setItems] = useState<ReviewQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [rationale, setRationale] = useState<Record<number, string>>({});
  const [error, setError] = useState('');
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const d = await getReviewQueue(100);
      setItems(d.items || []);
      setError('');
    } catch (e: any) {
      const status = e?.response?.status;
      if (status === 403) {
        setError('You need the reviewer or admin role to access this page. Ask an admin to grant it in Admin → Users.');
      } else {
        setError(e?.response?.data?.detail || e.message || 'Failed to load queue');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const submit = async (id: number, decision: 'VALIDATED' | 'REVISED' | 'REJECTED') => {
    setBusyId(id);
    try {
      await decideGap(id, decision, rationale[id] || '');
      toast.success(decision === 'VALIDATED' ? 'Gap validated' :
                    decision === 'REVISED' ? 'Gap revised' : 'Gap rejected');
      setRationale(r => { const c = { ...r }; delete c[id]; return c; });
      await load();
    } catch (e: any) {
      toast.error('Failed', e?.response?.data?.detail || e.message);
    } finally {
      setBusyId(null);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen"><Loader2 className="animate-spin text-accent" size={32} /></div>;
  }

  return (
    <div className="p-6 lg:p-8 max-w-5xl mx-auto">
      <div className="mb-6 flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center">
            <Shield size={18} className="text-accent" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-ink tracking-tight">Expert review queue</h1>
            <p className="text-sm text-ink-3 mt-1">
              Validate, revise, or reject proposed research gaps. Every decision is audited.
            </p>
          </div>
        </div>
        <button onClick={load} className="btn-secondary text-xs">Refresh</button>
      </div>

      {error ? (
        <div className="bg-danger/10 border border-danger/30 rounded-lg p-5 flex items-start gap-3">
          <AlertCircle className="text-danger flex-shrink-0 mt-0.5" size={16} />
          <p className="text-sm text-danger">{error}</p>
        </div>
      ) : items.length === 0 ? (
        <div className="bg-surface border border-edge border-dashed rounded-lg p-12 text-center">
          <CheckCircle2 className="text-success mx-auto mb-3" size={28} />
          <p className="text-sm text-ink-2 font-medium">Queue is empty</p>
          <p className="text-xs text-ink-4 mt-1">No proposed gaps awaiting review.</p>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-xs text-ink-4">{items.length} gap{items.length === 1 ? '' : 's'} awaiting review</p>
          {items.map(g => (
            <div key={g.id} className="card p-5">
              <div className="flex items-start justify-between gap-4 mb-3">
                <div className="min-w-0 flex-1">
                  <div className="mb-2 flex items-center gap-2 flex-wrap">
                    <span className="text-2xs text-ink-4 font-mono">#{g.id}</span>
                    <GapStatusBadge kind={g.kind} status={g.gap_status} />
                  </div>
                  <h3 className="text-sm font-semibold text-ink leading-snug mb-2">{g.title}</h3>
                  <p className="text-xs text-ink-3 leading-relaxed mb-3 line-clamp-3">{g.description}</p>
                  {g.supporting_limitations.length > 0 && (
                    <div className="mb-3">
                      <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Supporting limitations</p>
                      <ul className="space-y-1">
                        {g.supporting_limitations.slice(0, 3).map((lim, i) => (
                          <li key={i} className="text-2xs text-ink-3 leading-relaxed pl-3 border-l-2 border-warning/40">
                            {typeof lim === 'string' ? lim : (lim as any).snippet || JSON.stringify(lim)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="text-2xl font-bold font-mono tabular-nums text-success leading-none">
                    {g.gap_score.toFixed(2)}
                  </p>
                  <p className="text-2xs text-ink-4 mt-1">gap score</p>
                  <p className="text-2xs text-ink-3 font-mono mt-1">conf {g.gap_confidence}</p>
                </div>
              </div>

              <div className="pt-3 border-t border-edge-subtle">
                <label className="block text-2xs text-ink-4 uppercase tracking-wider mb-1.5">
                  Reviewer rationale (optional)
                </label>
                <textarea
                  value={rationale[g.id] || ''}
                  onChange={e => setRationale(r => ({ ...r, [g.id]: e.target.value }))}
                  placeholder="Why did you validate, revise, or reject this gap?"
                  className="input text-sm w-full mb-3"
                  rows={2}
                />
                <div className="flex gap-2 flex-wrap">
                  <button
                    onClick={() => submit(g.id, 'VALIDATED')}
                    disabled={busyId === g.id}
                    className="btn-primary text-xs"
                  >
                    <CheckCircle2 size={13} /> Validate
                  </button>
                  <button
                    onClick={() => submit(g.id, 'REVISED')}
                    disabled={busyId === g.id}
                    className="btn-secondary text-xs"
                  >
                    <FileText size={13} /> Revise
                  </button>
                  <button
                    onClick={() => submit(g.id, 'REJECTED')}
                    disabled={busyId === g.id}
                    className="btn text-xs bg-danger/10 text-danger hover:bg-danger/20 border border-danger/30"
                  >
                    <XCircle size={13} /> Reject
                  </button>
                  {busyId === g.id && <Loader2 className="animate-spin text-ink-4 ml-2" size={14} />}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
