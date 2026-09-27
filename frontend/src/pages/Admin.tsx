import { useEffect, useState } from 'react';
import {
  adminGetStats, adminGetUsers, adminUpdateRole, adminDeleteUser,
  adminGetLogs, adminGetScheduler, adminTriggerScheduler,
} from '../services/api';
import { Loader2, Users, Activity, AlertCircle, Trash2, RefreshCw, Play } from 'lucide-react';

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
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleRoleChange = async (id: number, role: string) => {
    try {
      await adminUpdateRole(id, role);
      await load();
    } catch (e: any) { alert(e.message); }
  };

  const handleDelete = async (id: number) => {
    if (!confirm(`Delete user #${id}?`)) return;
    try {
      await adminDeleteUser(id);
      await load();
    } catch (e: any) { alert(e.message); }
  };

  const handleTrigger = async () => {
    try {
      await adminTriggerScheduler();
      alert('Scheduler pipeline triggered — check logs in a minute.');
    } catch (e: any) { alert(e.message); }
  };

  if (loading) return <div className="flex items-center justify-center h-screen"><Loader2 className="animate-spin text-brand-accent" size={48} /></div>;

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Admin Panel</h1>
          <p className="text-gray-400 mt-1">System overview and management</p>
        </div>
        <button onClick={load} className="bg-brand-panel border border-brand-border hover:border-brand-accent text-white px-4 py-2 rounded-lg flex items-center gap-2">
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      <div className="flex gap-2 mb-6">
        {(['overview', 'users', 'logs', 'scheduler'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
              tab === t ? 'bg-brand-accent text-white' : 'bg-brand-panel border border-brand-border text-gray-300 hover:text-white'
            }`}
          >{t}</button>
        ))}
      </div>

      {tab === 'overview' && stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(stats).map(([k, v]) => (
            <div key={k} className="bg-brand-panel border border-brand-border rounded-xl p-5">
              <p className="text-xs text-gray-500 uppercase">{k.replace(/_/g, ' ')}</p>
              <p className="text-2xl font-bold text-white mt-1">{String(v)}</p>
            </div>
          ))}
        </div>
      )}

      {tab === 'users' && (
        <div className="bg-brand-panel border border-brand-border rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-brand-dark text-gray-500 text-xs uppercase">
              <tr>
                <th className="text-left px-4 py-3">ID</th>
                <th className="text-left px-4 py-3">Name</th>
                <th className="text-left px-4 py-3">Email</th>
                <th className="text-left px-4 py-3">Role</th>
                <th className="text-right px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id} className="border-t border-brand-border">
                  <td className="px-4 py-3 text-gray-400">{u.id}</td>
                  <td className="px-4 py-3 text-white">{u.name}</td>
                  <td className="px-4 py-3 text-gray-300">{u.email}</td>
                  <td className="px-4 py-3">
                    <select
                      value={u.role}
                      onChange={e => handleRoleChange(u.id, e.target.value)}
                      className="bg-brand-dark border border-brand-border rounded px-2 py-1 text-white text-xs"
                    >
                      {['student', 'researcher', 'entrepreneur', 'investor', 'admin'].map(r => (
                        <option key={r} value={r}>{r}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => handleDelete(u.id)} className="text-red-400 hover:text-red-300">
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'logs' && (
        <div className="bg-brand-panel border border-brand-border rounded-xl p-4 max-h-[600px] overflow-auto">
          {logs.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No logs</p>
          ) : logs.map(l => (
            <div key={l.id} className="border-b border-brand-border last:border-0 py-3 text-xs">
              <div className="flex items-center gap-2">
                <span className={`px-2 py-0.5 rounded ${l.status === 'success' ? 'bg-emerald-900/30 text-emerald-300' : 'bg-red-900/30 text-red-300'}`}>
                  {l.status}
                </span>
                <span className="text-brand-accent font-medium">{l.agent_name}</span>
                <span className="text-gray-400">{l.action}</span>
                <span className="text-gray-600 ml-auto">{new Date(l.created_at).toLocaleString()}</span>
              </div>
              {l.details && (
                <pre className="mt-1 text-gray-500 text-[10px]">{JSON.stringify(l.details)}</pre>
              )}
            </div>
          ))}
        </div>
      )}

      {tab === 'scheduler' && scheduler && (
        <div className="bg-brand-panel border border-brand-border rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Activity className={scheduler.running ? 'text-emerald-400' : 'text-red-400'} size={20} />
              <h2 className="text-lg font-semibold text-white">
                Scheduler: {scheduler.running ? 'Running' : 'Stopped'}
              </h2>
            </div>
            <button onClick={handleTrigger} className="bg-brand-accent hover:bg-indigo-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 text-sm">
              <Play size={14} /> Trigger Now
            </button>
          </div>
          <div className="space-y-3">
            {scheduler.jobs.map((j: any) => (
              <div key={j.id} className="border border-brand-border rounded-lg p-3 text-sm">
                <p className="text-white font-medium">{j.name}</p>
                <p className="text-xs text-gray-500 mt-1">ID: {j.id}</p>
                <p className="text-xs text-gray-500">Next run: {j.next_run || 'N/A'}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
