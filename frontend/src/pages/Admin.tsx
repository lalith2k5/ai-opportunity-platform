import { useEffect, useState } from 'react';
import {
  adminGetStats, adminGetUsers, adminUpdateRole, adminDeleteUser,
  adminGetLogs, adminGetScheduler, adminTriggerScheduler,
  adminGetSettings, adminUpdateSetting,
  adminGetSyncStatus, adminTriggerSync,
} from '../services/api';
import {
  Loader2, Users, Activity, Trash2, RefreshCw, Play, Shield, FileText, Clock,
  Settings as SettingsIcon, Database, CheckCircle2, XCircle, Eye, EyeOff,
  Save, ExternalLink, Zap, Globe, AlertCircle,
} from 'lucide-react';
import { useToast } from '../context/ToastContext';
import { useConfirm } from '../context/ConfirmContext';

const ROLE_OPTIONS = ['student', 'researcher', 'entrepreneur', 'investor', 'admin'];

type Tab = 'overview' | 'users' | 'logs' | 'scheduler' | 'config' | 'sync';

function SourceStatus({ label, source, icon: Icon }: {
  label: string;
  source: { documents: number; last_collected: string | null; configured: boolean; enabled: boolean };
  icon: any;
}) {
  const last = source.last_collected ? new Date(source.last_collected).toLocaleString() : 'Never';
  return (
    <div className="bg-surface border border-edge rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon size={14} className="text-accent" />
          <p className="text-xs font-medium text-ink uppercase tracking-wider">{label}</p>
        </div>
        {source.configured
          ? <span className="badge bg-success/15 text-success border border-success/30">Connected</span>
          : <span className="badge bg-danger/15 text-danger border border-danger/30">Not configured</span>
        }
      </div>
      <p className="text-2xl font-semibold text-ink font-mono tabular-nums">{source.documents}</p>
      <p className="text-2xs text-ink-4 mt-1">documents stored</p>
      <p className="text-2xs text-ink-3 mt-2 pt-2 border-t border-edge-subtle">
        Last fetch: <span className="text-ink-2">{last}</span>
      </p>
    </div>
  );
}

export default function Admin() {
  const [stats, setStats] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [scheduler, setScheduler] = useState<any>(null);
  const [settings, setSettings] = useState<any[]>([]);
  const [syncStatus, setSyncStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>('overview');
  const toast = useToast();
  const { confirm } = useConfirm();

  const load = async () => {
    setLoading(true);
    try {
      const [s, u, l, sc, cfg, sy] = await Promise.all([
        adminGetStats(), adminGetUsers(), adminGetLogs(), adminGetScheduler(),
        adminGetSettings().catch(() => ({ items: [] })),
        adminGetSyncStatus().catch(() => null),
      ]);
      setStats(s); setUsers(u); setLogs(l); setScheduler(sc);
      setSettings(cfg.items || []);
      setSyncStatus(sy);
    } catch (e: any) {
      toast.error('Access denied', e?.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleRoleChange = async (id: number, role: string) => {
    try { await adminUpdateRole(id, role); await load(); toast.success('Role updated'); }
    catch (e: any) { toast.error('Update failed', e.message); }
  };

  const handleDelete = async (id: number) => {
    const ok = await confirm({
      title: `Delete user #${id}?`,
      message: 'This action cannot be undone. All associated data will be permanently removed.',
      confirmText: 'Delete user',
      danger: true,
    });
    if (!ok) return;
    try { await adminDeleteUser(id); await load(); toast.success('User deleted'); }
    catch (e: any) { toast.error('Delete failed', e.message); }
  };

  const handleTrigger = async () => {
    try {
      await adminTriggerScheduler();
      toast.success('Scheduler triggered', 'Check logs in a minute for results.');
    } catch (e: any) { toast.error('Trigger failed', e.message); }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="animate-spin text-accent" size={32} />
      </div>
    );
  }

  const tabs = [
    { id: 'overview',  label: 'Overview',  icon: FileText },
    { id: 'users',     label: 'Users',     icon: Users },
    { id: 'config',    label: 'Config',    icon: SettingsIcon },
    { id: 'sync',      label: 'Sync',      icon: Database },
    { id: 'logs',      label: 'Logs',      icon: Activity },
    { id: 'scheduler', label: 'Scheduler', icon: Clock },
  ] as const;

  return (
    <div className="p-6 lg:p-8 max-w-[1500px] mx-auto">

      <div className="mb-6 flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-warning/10 flex items-center justify-center">
            <Shield className="text-warning" size={16} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-ink tracking-tight">Admin panel</h1>
            <p className="text-sm text-ink-3">System overview and management</p>
          </div>
        </div>
        <button onClick={load} className="btn-secondary text-xs">
          <RefreshCw size={13} /> Refresh
        </button>
      </div>

      <div className="flex gap-1 mb-6 border-b border-edge overflow-x-auto">
        {tabs.map(t => {
          const Icon = t.icon;
          const active = tab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`relative flex items-center gap-2 px-3 py-2.5 text-sm whitespace-nowrap transition-colors ${
                active ? 'text-ink font-medium' : 'text-ink-3 hover:text-ink-2'
              }`}
            >
              <Icon size={14} />
              {t.label}
              {active && <span className="absolute left-0 right-0 -bottom-px h-[2px] bg-accent rounded-full" />}
            </button>
          );
        })}
      </div>

      {/* OVERVIEW */}
      {tab === 'overview' && stats && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {Object.entries(stats).map(([k, v]) => (
            <div key={k} className="bg-surface border border-edge rounded-lg p-4">
              <p className="text-2xs font-medium text-ink-4 uppercase tracking-wider mb-2">{k.replace(/_/g, ' ')}</p>
              <p className="text-2xl font-semibold text-ink font-mono tabular-nums">{String(v)}</p>
            </div>
          ))}
        </div>
      )}

      {/* USERS */}
      {tab === 'users' && (
        <div className="bg-surface border border-edge rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-edge bg-overlay">
                  <th className="text-left text-2xs font-medium text-ink-4 uppercase tracking-wider px-4 py-2.5 w-14">ID</th>
                  <th className="text-left text-2xs font-medium text-ink-4 uppercase tracking-wider px-4 py-2.5">Name</th>
                  <th className="text-left text-2xs font-medium text-ink-4 uppercase tracking-wider px-4 py-2.5">Email</th>
                  <th className="text-left text-2xs font-medium text-ink-4 uppercase tracking-wider px-4 py-2.5 w-40">Role</th>
                  <th className="text-right text-2xs font-medium text-ink-4 uppercase tracking-wider px-4 py-2.5 w-16"></th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id} className="border-b border-edge-subtle last:border-0 hover:bg-overlay/60 transition-colors">
                    <td className="px-4 py-3 text-ink-4 font-mono text-xs">{u.id}</td>
                    <td className="px-4 py-3 text-ink text-xs">{u.name}</td>
                    <td className="px-4 py-3 text-ink-2 text-xs">{u.email}</td>
                    <td className="px-4 py-3">
                      <select
                        value={u.role}
                        onChange={e => handleRoleChange(u.id, e.target.value)}
                        className="input text-xs py-1 px-2"
                      >
                        {ROLE_OPTIONS.map(r => <option key={r} value={r}>{r}</option>)}
                      </select>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleDelete(u.id)}
                        className="p-1.5 rounded-md text-ink-4 hover:text-danger hover:bg-danger/10 transition-colors"
                      >
                        <Trash2 size={13} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* CONFIG */}
      {tab === 'config' && <ConfigTab settings={settings} reload={load} />}

      {/* SYNC */}
      {tab === 'sync' && <SyncTab status={syncStatus} reload={load} />}

      {/* LOGS */}
      {tab === 'logs' && (
        <div className="bg-surface border border-edge rounded-lg p-3 max-h-[640px] overflow-y-auto">
          {logs.length === 0 ? (
            <p className="text-sm text-ink-4 text-center py-8">No logs</p>
          ) : (
            <div className="space-y-0.5">
              {logs.map(l => (
                <div key={l.id} className="flex items-center gap-3 px-2.5 py-2 rounded-md hover:bg-overlay transition-colors">
                  <span className={`badge ${
                    l.status === 'success'
                      ? 'bg-success/15 text-success border border-success/30'
                      : 'bg-danger/15 text-danger border border-danger/30'
                  }`}>
                    {l.status}
                  </span>
                  <span className="text-xs text-accent font-medium flex-shrink-0">{l.agent_name}</span>
                  <span className="text-xs text-ink-2 truncate flex-1">{l.action}</span>
                  <span className="text-2xs text-ink-4 font-mono flex-shrink-0">
                    {new Date(l.created_at).toLocaleTimeString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* SCHEDULER */}
      {tab === 'scheduler' && scheduler && (
        <div className="space-y-4">
          <div className="bg-surface border border-edge rounded-lg p-5 flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-3">
              <div className={`w-2 h-2 rounded-full ${scheduler.running ? 'bg-success animate-pulse' : 'bg-danger'}`} />
              <div>
                <h2 className="text-sm font-semibold text-ink">
                  Scheduler is {scheduler.running ? 'running' : 'stopped'}
                </h2>
                <p className="text-xs text-ink-3 mt-0.5">
                  Continuous monitoring every 6 hours · cleanup daily at 3 AM
                </p>
              </div>
            </div>
            <button onClick={handleTrigger} className="btn-primary text-xs">
              <Play size={13} /> Trigger now
            </button>
          </div>

          <div className="bg-surface border border-edge rounded-lg p-5">
            <h3 className="text-xs font-medium text-ink uppercase tracking-wider mb-4">Scheduled jobs</h3>
            <div className="space-y-2">
              {scheduler.jobs.map((j: any) => (
                <div key={j.id} className="flex items-center justify-between gap-3 py-2.5 border-b border-edge-subtle last:border-0">
                  <div>
                    <p className="text-sm text-ink font-medium">{j.name}</p>
                    <p className="text-2xs text-ink-4 font-mono mt-0.5">{j.id}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xs text-ink-4 uppercase tracking-wider">Next run</p>
                    <p className="text-xs text-ink-2 font-mono">
                      {j.next_run ? new Date(j.next_run).toLocaleString() : '—'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

/* ============================================ */
/* Config tab                                    */
/* ============================================ */
function ConfigTab({ settings, reload }: { settings: any[]; reload: () => void }) {
  const [revealed, setRevealed] = useState<Record<string, boolean>>({});
  const [editing, setEditing] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);
  const toast = useToast();

  const toggleReveal = (key: string) => {
    setRevealed(r => ({ ...r, [key]: !r[key] }));
  };

  const handleChange = (key: string, value: string) => {
    setEditing(e => ({ ...e, [key]: value }));
  };

  const handleSave = async (key: string) => {
    const value = editing[key];
    if (value === undefined) return;
    setSaving(key);
    try {
      const res = await adminUpdateSetting(key, value);
      toast.success(
        res.restart_required ? 'Saved — restart backend' : 'Saved',
        res.restart_required ? 'This setting requires a backend restart to take effect.' : undefined,
      );
      setEditing(e => { const c = { ...e }; delete c[key]; return c; });
      setRevealed(r => { const c = { ...r }; delete c[key]; return c; });
      reload();
    } catch (e: any) {
      toast.error('Save failed', e?.response?.data?.detail || e.message);
    } finally { setSaving(null); }
  };

  return (
    <div className="space-y-4">
      <div className="bg-accent/5 border border-accent/20 rounded-lg p-3.5 flex items-start gap-3">
        <AlertCircle size={14} className="text-accent flex-shrink-0 mt-0.5" />
        <p className="text-xs text-ink-2 leading-relaxed">
          These settings are written directly to <code className="font-mono text-accent">backend/.env</code>. Secrets are masked by default — click the eye to reveal, type a new value, and hit Save.
        </p>
      </div>

      <div className="bg-surface border border-edge rounded-lg overflow-hidden">
        {settings.map((item, i) => {
          const isEditing = editing[item.key] !== undefined;
          const isRevealed = revealed[item.key];
          return (
            <div key={item.key} className={`p-4 ${i > 0 ? 'border-t border-edge-subtle' : ''}`}>
              <div className="flex items-start justify-between gap-3 mb-2">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-xs font-medium text-ink">{item.label}</p>
                    <span className="badge bg-overlay text-ink-3 border border-edge font-mono">
                      {item.key}
                    </span>
                    {item.is_set
                      ? <CheckCircle2 size={12} className="text-success" />
                      : <XCircle size={12} className="text-ink-4" />
                    }
                  </div>
                  <p className="text-2xs text-ink-4 mt-0.5">{item.provider} · {item.hint}</p>
                </div>
                {item.docs_url && (
                  <a
                    href={item.docs_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-2xs text-accent hover:text-accent-hover flex items-center gap-1 flex-shrink-0"
                  >
                    Get key <ExternalLink size={10} />
                  </a>
                )}
              </div>

              <div className="flex items-center gap-2">
                <div className="relative flex-1">
                  <input
                    type={isEditing ? 'text' : 'text'}
                    value={isEditing
                      ? editing[item.key]
                      : (isRevealed ? item.masked : (item.is_set ? '•'.repeat(Math.min(32, (item.masked || '').length || 12)) : ''))
                    }
                    onChange={e => handleChange(item.key, e.target.value)}
                    onFocus={() => { if (!isEditing) setEditing(ed => ({ ...ed, [item.key]: '' })); }}
                    placeholder={item.is_set ? 'Enter new value to change…' : 'Not set — click to add'}
                    className="input text-xs font-mono pr-8"
                  />
                  {!isEditing && item.is_set && (
                    <button
                      onClick={() => toggleReveal(item.key)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded text-ink-4 hover:text-ink transition-colors"
                      title={isRevealed ? 'Hide' : 'Reveal (partial)'}
                    >
                      {isRevealed ? <EyeOff size={12} /> : <Eye size={12} />}
                    </button>
                  )}
                </div>
                <button
                  onClick={() => handleSave(item.key)}
                  disabled={!isEditing || saving === item.key}
                  className="btn-primary text-xs flex-shrink-0"
                >
                  {saving === item.key ? <Loader2 className="animate-spin" size={12} /> : <Save size={12} />}
                  Save
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ============================================ */
/* Sync tab                                      */
/* ============================================ */
function SyncTab({ status, reload }: { status: any; reload: () => void }) {
  const [topic, setTopic] = useState('');
  const [mode, setMode] = useState<'quick' | 'deep'>('quick');
  const [running, setRunning] = useState(false);
  const [lastResult, setLastResult] = useState<any>(null);
  const toast = useToast();

  const handleTrigger = async () => {
    if (!topic.trim()) {
      toast.error('Topic required', 'Enter a topic to sync.');
      return;
    }
    setRunning(true);
    setLastResult(null);
    try {
      const res = await adminTriggerSync(topic.trim(), mode);
      setLastResult(res);
      toast.success(
        'Sync complete',
        `${res.documents_count} docs · ${res.opportunities} opportunities · ${res.kg_stats?.new_nodes ?? 0} KG nodes`,
      );
      setTopic('');
      reload();
    } catch (e: any) {
      toast.error('Sync failed', e?.response?.data?.detail || e.message);
    } finally { setRunning(false); }
  };

  if (!status) {
    return <p className="text-sm text-ink-4 text-center py-12">Loading sync status…</p>;
  }

  const sourceIcons: Record<string, any> = {
    github: Globe,
    arxiv: FileText,
    news: Zap,
    reddit: Activity,
  };

  return (
    <div className="space-y-5">

      {/* Sources */}
      <div>
        <h3 className="text-xs font-medium text-ink uppercase tracking-wider mb-3">Data sources</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {status.sources.map((s: any) => (
            <SourceStatus
              key={s.source}
              label={s.source}
              source={s}
              icon={sourceIcons[s.source] || Globe}
            />
          ))}
        </div>
      </div>

      {/* DB summary */}
      <div className="bg-surface border border-edge rounded-lg p-4">
        <h3 className="text-xs font-medium text-ink uppercase tracking-wider mb-3">Database summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {Object.entries(status.database).map(([k, v]) => (
            <div key={k}>
              <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">{k.replace(/_/g, ' ')}</p>
              <p className="text-lg font-semibold text-ink font-mono tabular-nums">{String(v)}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Trigger */}
      <div className="bg-surface border border-edge rounded-lg p-5">
        <h3 className="text-xs font-medium text-ink uppercase tracking-wider mb-4">Trigger a sync</h3>
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto] gap-3">
          <input
            type="text"
            value={topic}
            onChange={e => setTopic(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !running && handleTrigger()}
            placeholder="Topic e.g. quantum computing, healthcare AI, robotics…"
            disabled={running}
            className="input text-sm"
          />
          <select
            value={mode}
            onChange={e => setMode(e.target.value as 'quick' | 'deep')}
            disabled={running}
            className="input text-sm"
          >
            <option value="quick">Quick (~8 per source)</option>
            <option value="deep">Deep (~100 per source)</option>
          </select>
          <button
            onClick={handleTrigger}
            disabled={running || !topic.trim()}
            className="btn-primary text-xs whitespace-nowrap"
          >
            {running ? <Loader2 className="animate-spin" size={13} /> : <Zap size={13} />}
            {running ? 'Running…' : 'Run sync'}
          </button>
        </div>
        <p className="text-2xs text-ink-4 mt-3 leading-relaxed">
          Quick mode finishes in ~30s. Deep mode fetches up to 100 documents per source and can take 45–90 seconds.
        </p>

        {running && (
          <div className="mt-4 bg-accent/5 border border-accent/20 rounded-md p-3 flex items-center gap-3">
            <Loader2 className="animate-spin text-accent flex-shrink-0" size={14} />
            <div>
              <p className="text-xs text-ink font-medium">Sync in progress…</p>
              <p className="text-2xs text-ink-3 mt-0.5">Fetching from sources, running AI pipeline, updating knowledge graph.</p>
            </div>
          </div>
        )}

        {lastResult && (
          <div className="mt-4 bg-success/5 border border-success/20 rounded-md p-4">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle2 size={14} className="text-success" />
              <p className="text-xs font-medium text-ink">Last sync complete</p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div>
                <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Documents</p>
                <p className="text-base font-semibold text-ink font-mono tabular-nums">{lastResult.documents_count}</p>
              </div>
              <div>
                <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Opportunities</p>
                <p className="text-base font-semibold text-ink font-mono tabular-nums">{lastResult.opportunities}</p>
              </div>
              <div>
                <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Clusters</p>
                <p className="text-base font-semibold text-ink font-mono tabular-nums">{lastResult.clusters}</p>
              </div>
              <div>
                <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">KG nodes</p>
                <p className="text-base font-semibold text-ink font-mono tabular-nums">
                  +{lastResult.kg_stats?.new_nodes ?? 0}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
