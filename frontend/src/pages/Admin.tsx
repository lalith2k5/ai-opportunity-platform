import { useEffect, useState } from 'react';
import {
  adminGetStats, adminGetUsers, adminUpdateRole, adminDeleteUser,
  adminGetLogs, adminGetScheduler, adminTriggerScheduler,
} from '../services/api';
import {
  Loader2, Users, Activity, Trash2, RefreshCw, Play, Shield, FileText, Clock,
} from 'lucide-react';

const ROLE_OPTIONS = ['student', 'researcher', 'entrepreneur', 'investor', 'admin'];

export default function Admin() {
  const [stats, setStats] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [scheduler, setScheduler] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'overview' | 'users' | 'logs' | 'scheduler'>('overview');

  const load = async () => {
    setLoading(true);
    try {
      const [s, u, l, sc] = await Promise.all([
        adminGetStats(), adminGetUsers(), adminGetLogs(), adminGetScheduler(),
      ]);
      setStats(s); setUsers(u); setLogs(l); setScheduler(sc);
    } catch (e: any) {
      alert(`Admin access error: ${e?.response?.data?.detail || e.message}`);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleRoleChange = async (id: number, role: string) => {
    try { await adminUpdateRole(id, role); await load(); }
    catch (e: any) { alert(e.message); }
  };

  const handleDelete = async (id: number) => {
    if (!confirm(`Delete user #${id}? This cannot be undone.`)) return;
    try { await adminDeleteUser(id); await load(); }
    catch (e: any) { alert(e.message); }
  };

  const handleTrigger = async () => {
    try {
      await adminTriggerScheduler();
      alert('Scheduler pipeline triggered — check logs in a minute.');
    } catch (e: any) { alert(e.message); }
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
    { id: 'logs',      label: 'Logs',      icon: Activity },
    { id: 'scheduler', label: 'Scheduler', icon: Clock },
  ] as const;

  return (
    <div className="p-6 lg:p-8 max-w-[1500px] mx-auto">

      {/* Header */}
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

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-edge">
        {tabs.map(t => {
          const Icon = t.icon;
          const active = tab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`relative flex items-center gap-2 px-3 py-2.5 text-sm transition-colors ${
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

      {/* Overview */}
      {tab === 'overview' && stats && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {Object.entries(stats).map(([k, v]) => (
            <div key={k} className="bg-surface border border-edge rounded-lg p-4">
              <p className="text-2xs font-medium text-ink-4 uppercase tracking-wider mb-2">
                {k.replace(/_/g, ' ')}
              </p>
              <p className="text-2xl font-semibold text-ink font-mono tabular-nums">{String(v)}</p>
            </div>
          ))}
        </div>
      )}

      {/* Users */}
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

      {/* Logs */}
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

      {/* Scheduler */}
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
