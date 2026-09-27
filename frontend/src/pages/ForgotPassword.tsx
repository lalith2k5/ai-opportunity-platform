import { useState } from 'react';
import { Link } from 'react-router-dom';
import { forgotPassword } from '../services/api';
import { Activity, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [resetLink, setResetLink] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError(''); setResetLink('');
    try {
      const res = await forgotPassword(email);
      if (res.reset_url) setResetLink(res.reset_url);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-brand-dark flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Activity className="mx-auto text-brand-accent mb-3" size={40} />
          <h1 className="text-2xl font-bold text-white">Reset your password</h1>
          <p className="text-gray-400 mt-1 text-sm">We'll send you a reset link</p>
        </div>
        <form onSubmit={submit} className="bg-brand-panel border border-brand-border rounded-xl p-6 space-y-4">
          {error && (
            <div className="bg-red-900/30 border border-red-700 rounded-lg p-3 flex gap-2">
              <AlertCircle className="text-red-400 flex-shrink-0" size={18} />
              <p className="text-red-300 text-sm">{error}</p>
            </div>
          )}
          {resetLink && (
            <div className="bg-emerald-900/30 border border-emerald-700 rounded-lg p-3">
              <div className="flex gap-2 mb-2">
                <CheckCircle2 className="text-emerald-400 flex-shrink-0" size={18} />
                <p className="text-emerald-300 text-sm">Reset link generated (dev mode)</p>
              </div>
              <Link to={resetLink.replace('http://localhost:5173', '')} className="text-brand-accent hover:underline text-xs break-all">
                {resetLink}
              </Link>
            </div>
          )}
          <div>
            <label className="block text-sm text-gray-400 mb-1">Email</label>
            <input
              type="email" value={email} onChange={e => setEmail(e.target.value)} required
              className="w-full bg-brand-dark border border-brand-border rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-brand-accent"
              placeholder="you@example.com"
            />
          </div>
          <button
            type="submit" disabled={loading}
            className="w-full bg-brand-accent hover:bg-indigo-600 disabled:opacity-50 text-white py-3 rounded-lg font-medium flex items-center justify-center gap-2"
          >
            {loading && <Loader2 className="animate-spin" size={18} />}
            {loading ? 'Sending...' : 'Send reset link'}
          </button>
          <p className="text-center text-sm text-gray-400 pt-2">
            Remembered? <Link to="/login" className="text-brand-accent hover:underline">Sign in</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
