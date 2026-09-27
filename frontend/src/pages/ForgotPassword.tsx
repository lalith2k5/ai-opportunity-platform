import { useState } from 'react';
import { Link } from 'react-router-dom';
import { forgotPassword } from '../services/api';
import AuthShell from '../components/AuthShell';
import { Field, Alert } from '../components/Field';
import { Loader2, ArrowRight } from 'lucide-react';

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
    <AuthShell
      title="Reset your password"
      subtitle="Enter your email and we'll generate a reset link."
      footer={
        <Link to="/login" className="text-accent hover:text-accent-hover font-medium">
          Back to sign in
        </Link>
      }
    >
      <form onSubmit={submit} className="space-y-4">
        {error && <Alert type="error">{error}</Alert>}

        {resetLink ? (
          <>
            <Alert type="success">
              Reset link generated (dev mode).
            </Alert>
            <Link
              to={resetLink.replace('http://localhost:5173', '')}
              className="btn-primary w-full py-2.5"
            >
              Open reset link <ArrowRight size={15} />
            </Link>
            <button
              type="button"
              onClick={() => setResetLink('')}
              className="btn-ghost w-full text-xs"
            >
              Send to a different email
            </button>
          </>
        ) : (
          <>
            <Field label="Email" htmlFor="email">
              <input id="email" type="email" required value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com" className="input" />
            </Field>
            <button type="submit" disabled={loading} className="btn-primary w-full py-2.5">
              {loading ? <Loader2 className="animate-spin" size={15} /> : null}
              {loading ? 'Sending…' : 'Send reset link'}
            </button>
          </>
        )}
      </form>
    </AuthShell>
  );
}
