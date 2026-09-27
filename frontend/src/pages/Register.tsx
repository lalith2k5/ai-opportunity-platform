import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AuthShell from '../components/AuthShell';
import { Field, Alert } from '../components/Field';
import { Loader2 } from 'lucide-react';

const ROLES = [
  { value: 'student',      label: 'Student',       hint: 'Project ideas, topics' },
  { value: 'researcher',   label: 'Researcher',    hint: 'Gaps, papers, trends' },
  { value: 'entrepreneur', label: 'Entrepreneur',  hint: 'Startup opportunities' },
  { value: 'investor',     label: 'Investor',      hint: 'Market signals' },
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
    } finally { setLoading(false); }
  };

  return (
    <AuthShell
      title="Create your account"
      subtitle="Start discovering opportunities in under a minute."
      footer={
        <>
          Already have an account?{' '}
          <Link to="/login" className="text-accent hover:text-accent-hover font-medium">Sign in</Link>
        </>
      }
    >
      <form onSubmit={submit} className="space-y-4">
        {error && <Alert type="error">{error}</Alert>}

        <Field label="Full name" htmlFor="name">
          <input id="name" type="text" required value={name}
            onChange={e => setName(e.target.value)} placeholder="Jane Doe" className="input" />
        </Field>

        <Field label="Email" htmlFor="email">
          <input id="email" type="email" autoComplete="email" required value={email}
            onChange={e => setEmail(e.target.value)} placeholder="you@example.com" className="input" />
        </Field>

        <Field label="I am a…" hint={ROLES.find(r => r.value === role)?.hint}>
          <div className="grid grid-cols-2 gap-2">
            {ROLES.map(r => (
              <button
                key={r.value}
                type="button"
                onClick={() => setRole(r.value)}
                className={`px-3 py-2 text-sm rounded-md border text-left transition-all ${
                  role === r.value
                    ? 'bg-accent/10 border-accent/50 text-ink font-medium'
                    : 'bg-canvas border-edge text-ink-2 hover:border-edge-strong'
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
        </Field>

        <Field label="Password" htmlFor="password" hint="Minimum 6 characters">
          <input id="password" type="password" autoComplete="new-password" required
            value={password} onChange={e => setPassword(e.target.value)}
            placeholder="••••••••" className="input" />
        </Field>

        <Field label="Confirm password" htmlFor="confirm">
          <input id="confirm" type="password" autoComplete="new-password" required
            value={confirm} onChange={e => setConfirm(e.target.value)}
            placeholder="••••••••" className="input" />
        </Field>

        <button type="submit" disabled={loading} className="btn-primary w-full py-2.5">
          {loading ? <Loader2 className="animate-spin" size={15} /> : null}
          {loading ? 'Creating account…' : 'Create account'}
        </button>
      </form>
    </AuthShell>
  );
}
