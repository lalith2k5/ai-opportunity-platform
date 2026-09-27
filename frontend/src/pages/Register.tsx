import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Activity, Loader2, AlertCircle } from 'lucide-react';

const ROLES = [
  { value: 'student', label: 'Student' },
  { value: 'researcher', label: 'Researcher' },
  { value: 'entrepreneur', label: 'Entrepreneur' },
  { value: 'investor', label: 'Investor' },
];

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [role, setRole] = useState('student');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (password !== confirm) { setError('Passwords do not match'); return; }
    if (password.length < 6) { setError('Password must be at least 6 characters'); return; }
    setLoading(true);
    try {
      await register(name, email, password, role);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-brand-dark flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Activity className="mx-auto text-brand-accent mb-3" size={40} />
          <h1 className="text-2xl font-bold text-white">Create your account</h1>
          <p className="text-gray-400 mt-1 text-sm">Join the opportunity discovery platform</p>
        </div>

        <form onSubmit={submit} className="bg-brand-panel border border-brand-border rounded-xl p-6 space-y-4">
          {error && (
            <div className="bg-red-900/30 border border-red-700 rounded-lg p-3 flex items-start gap-2">
              <AlertCircle className="text-red-400 mt-0.5 flex-shrink-0" size={18} />
              <p className="text-red-300 text-sm">{error}</p>
            </div>
          )}

          <div>
            <label className="block text-sm text-gray-400 mb-1">Full name</label>
            <input
              type="text" value={name} onChange={e => setName(e.target.value)} required
              className="w-full bg-brand-dark border border-brand-border rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-brand-accent"
              placeholder="Jane Doe"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Email</label>
            <input
              type="email" value={email} onChange={e => setEmail(e.target.value)} required
              className="w-full bg-brand-dark border border-brand-border rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-brand-accent"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">I am a…</label>
            <select
              value={role} onChange={e => setRole(e.target.value)}
              className="w-full bg-brand-dark border border-brand-border rounded-lg px-4 py-3 text-white focus:outline-none focus:border-brand-accent"
            >
              {ROLES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Password</label>
            <input
              type="password" value={password} onChange={e => setPassword(e.target.value)} required
              className="w-full bg-brand-dark border border-brand-border rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-brand-accent"
              placeholder="At least 6 characters"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Confirm password</label>
            <input
              type="password" value={confirm} onChange={e => setConfirm(e.target.value)} required
              className="w-full bg-brand-dark border border-brand-border rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-brand-accent"
              placeholder="Repeat password"
            />
          </div>

          <button
            type="submit" disabled={loading}
            className="w-full bg-brand-accent hover:bg-indigo-600 disabled:opacity-50 text-white py-3 rounded-lg font-medium flex items-center justify-center gap-2 transition-colors"
          >
            {loading ? <Loader2 className="animate-spin" size={18} /> : null}
            {loading ? 'Creating account...' : 'Create account'}
          </button>

          <p className="text-center text-sm text-gray-400 pt-2">
            Already have an account?{' '}
            <Link to="/login" className="text-brand-accent hover:underline">Sign in</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
