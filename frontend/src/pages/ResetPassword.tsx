import { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { resetPassword } from '../services/api';
import AuthShell from '../components/AuthShell';
import { Field, Alert } from '../components/Field';
import { Loader2 } from 'lucide-react';

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
    <AuthShell
      title="Set a new password"
      subtitle={done ? 'Redirecting you to sign in…' : 'Choose a strong password you haven\'t used before.'}
      footer={
        <Link to="/login" className="text-accent hover:text-accent-hover font-medium">
          Back to sign in
        </Link>
      }
    >
      <form onSubmit={submit} className="space-y-4">
        {!token && <Alert type="error">Missing reset token. Request a new link from the sign-in page.</Alert>}
        {error && <Alert type="error">{error}</Alert>}
        {done && <Alert type="success">Password reset! Taking you to sign in…</Alert>}

        <Field label="New password" htmlFor="password" hint="Minimum 6 characters">
          <input id="password" type="password" autoComplete="new-password" required
            value={password} onChange={e => setPassword(e.target.value)}
            placeholder="••••••••" className="input" />
        </Field>

        <Field label="Confirm password" htmlFor="confirm">
          <input id="confirm" type="password" autoComplete="new-password" required
            value={confirm} onChange={e => setConfirm(e.target.value)}
            placeholder="••••••••" className="input" />
        </Field>

        <button type="submit" disabled={loading || !token || done} className="btn-primary w-full py-2.5">
          {loading ? <Loader2 className="animate-spin" size={15} /> : null}
          {loading ? 'Resetting…' : done ? 'Done' : 'Reset password'}
        </button>
      </form>
    </AuthShell>
  );
}
