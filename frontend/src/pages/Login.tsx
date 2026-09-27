import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Activity, Loader2, AlertCircle } from 'lucide-react';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-brand-dark flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Activity className="mx-auto text-brand-accent mb-3" size={40} />
          <h1 className="text-2xl font-bold text-white">Welcome back</h1>
          <p className="text-gray-400 mt-1 text-sm">Sign in to your opportunity platform</p>
        </div>

        <form onSubmit={submit} className="bg-brand-panel border border-brand-border rounded-xl p-6 space-y-4">
          {error && (
            <div className="bg-red-900/30 border border-red-700 rounded-lg p-3 flex items-start gap-2">
              <AlertCircle className="text-red-400 mt-0.5 flex-shrink-0" size={18} />
              <p className="text-red-300 text-sm">{error}</p>
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

          <div>
            <div className="flex items-center justify-between mb-1">
            <label className="text-sm text-gray-400">Password</label>
            <Link to="/forgot-password" className="text-xs text-brand-accent hover:underline">Forgot?</Link>
          </div>
            <input
              type="password" value={password} onChange={e => setPassword(e.target.value)} required
              className="w-full bg-brand-dark border border-brand-border rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-brand-accent"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit" disabled={loading}
            className="w-full bg-brand-accent hover:bg-indigo-600 disabled:opacity-50 text-white py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-colors"
          >
            {loading ? <Loader2 className="animate-spin" size={18} /> : null}
            {loading ? 'Signing in...' : 'Sign in'}
          </button>

          <p className="text-center text-sm text-gray-400 pt-2">
            Don't have an account?{' '}
            <Link to="/register" className="text-brand-accent hover:underline">Register</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
