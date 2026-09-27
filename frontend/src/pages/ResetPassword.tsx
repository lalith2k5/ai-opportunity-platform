import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { resetPassword } from '../services/api';
import { Activity, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function ResetPassword() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);
  const token = params.get('token') || '';

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (password !== confirm) { setError('Passwords do not match'); return; }
    if (password.length < 6) { setError('Password must be at least 6 characters'); return; }
    setLoading(true);
    try {
      await resetPassword(token, password);
      setDone(true);
      setTimeout(() => navigate('/login'), 2000);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-brand-dark flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Activity className="mx-auto text-brand-accent mb-3" size={40} />
          <h1 className="text-2xl font-bold text-white">Set a new password</h1>
        </div>
        <form onSubmit={submit} className="bg-brand-panel border border-brand-border rounded-xl p-6 space-y-4">
          {!token && (
            <div className="bg-red-900/30 border border-red-700 rounded-lg p-3">
              <p className="text-red-300 text-sm">Missing reset token. Request a new link.</p>
            </div>
          )}
          {error && (
            <div className="bg-red-900/30 border border-red-700 rounded-lg p-3 flex gap-2">
              <AlertCircle className="text-red-400" size={18} />
              <p className="text-red-300 text-sm">{error}</p>
            </div>
          )}
          {done && (
            <div className="bg-emerald-900/30 border border-emerald-700 rounded-lg p-3 flex gap-2">
              <CheckCircle2 className="text-emerald-400" size={18} />
              <p className="text-emerald-300 text-sm">Password reset! Redirecting to login...</p>
            </div>
          )}
          <div>
            <label className="block text-sm text-gray-400 mb-1">New password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required
              className="w-full bg-brand-dark border border-brand-border rounded-lg px-4 py-3 text-white" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Confirm</label>
            <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} required
              className="w-full bg-brand-dark border border-brand-border rounded-lg px-4 py-3 text-white" />
          </div>
          <button type="submit" disabled={loading || !token}
            className="w-full bg-brand-accent hover:bg-indigo-600 disabled:opacity-50 text-white py-3 rounded-lg font-medium flex items-center justify-center gap-2">
            {loading && <Loader2 className="animate-spin" size={18} />}
            {loading ? 'Resetting...' : 'Reset password'}
          </button>
          <p className="text-center text-sm text-gray-400 pt-2">
            <Link to="/login" className="text-brand-accent hover:underline">Back to login</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
