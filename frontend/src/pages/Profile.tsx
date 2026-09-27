import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { updateProfile, changePassword } from '../services/api';
import { Loader2, CheckCircle2, User as UserIcon, Lock, Shield } from 'lucide-react';

function Alert({ type, children }: { type: 'success' | 'error'; children: React.ReactNode }) {
  const cls = type === 'success'
    ? 'bg-success/10 border-success/30 text-success'
    : 'bg-danger/10 border-danger/30 text-danger';
  return (
    <div className={`text-xs border rounded-md px-3 py-2.5 flex items-center gap-2 ${cls}`}>
      <CheckCircle2 size={13} className="flex-shrink-0" />
      <span>{children}</span>
    </div>
  );
}

export default function Profile() {
  const { user } = useAuth();
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileMsg, setProfileMsg] = useState('');
  const [profileErr, setProfileErr] = useState('');

  const [oldPw, setOldPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [savingPw, setSavingPw] = useState(false);
  const [pwMsg, setPwMsg] = useState('');
  const [pwErr, setPwErr] = useState('');

  const saveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true); setProfileMsg(''); setProfileErr('');
    try {
      await updateProfile({ name, email });
      setProfileMsg('Profile updated successfully');
      localStorage.setItem('aod_user', JSON.stringify({ ...user, name, email }));
    } catch (e: any) {
      setProfileErr(e?.response?.data?.detail || e.message);
    } finally { setSavingProfile(false); }
  };

  const savePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwMsg(''); setPwErr('');
    if (newPw !== confirmPw) { setPwErr('Passwords do not match'); return; }
    setSavingPw(true);
    try {
      await changePassword(oldPw, newPw);
      setPwMsg('Password changed successfully');
      setOldPw(''); setNewPw(''); setConfirmPw('');
    } catch (e: any) {
      setPwErr(e?.response?.data?.detail || e.message);
    } finally { setSavingPw(false); }
  };

  return (
    <div className="p-6 lg:p-8 max-w-3xl mx-auto">

      {/* Header */}
      <div className="mb-6 flex items-center gap-4">
        <div className="w-14 h-14 rounded-xl bg-accent flex items-center justify-center text-accent-fg">
          <UserIcon size={24} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">{user?.name}</h1>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-sm text-ink-3">{user?.email}</span>
            <span className="badge bg-accent/10 text-accent border border-accent/30 capitalize">
              {user?.role}
            </span>
          </div>
        </div>
      </div>

      {/* Basic info */}
      <form onSubmit={saveProfile} className="bg-surface border border-edge rounded-lg p-6 mb-5">
        <div className="flex items-center gap-2 mb-5">
          <UserIcon size={14} className="text-accent" />
          <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Basic information</h2>
        </div>

        <div className="space-y-4">
          {profileMsg && <Alert type="success">{profileMsg}</Alert>}
          {profileErr && <Alert type="error">{profileErr}</Alert>}

          <div>
            <label className="block text-xs font-medium text-ink-2 mb-1.5">Name</label>
            <input type="text" value={name} onChange={e => setName(e.target.value)} required className="input" />
          </div>

          <div>
            <label className="block text-xs font-medium text-ink-2 mb-1.5">Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required className="input" />
          </div>

          <div className="flex justify-end pt-2">
            <button type="submit" disabled={savingProfile} className="btn-primary text-xs">
              {savingProfile && <Loader2 className="animate-spin" size={12} />}
              {savingProfile ? 'Saving…' : 'Save changes'}
            </button>
          </div>
        </div>
      </form>

      {/* Password */}
      <form onSubmit={savePassword} className="bg-surface border border-edge rounded-lg p-6">
        <div className="flex items-center gap-2 mb-5">
          <Lock size={14} className="text-warning" />
          <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Change password</h2>
        </div>

        <div className="space-y-4">
          {pwMsg && <Alert type="success">{pwMsg}</Alert>}
          {pwErr && <Alert type="error">{pwErr}</Alert>}

          <div>
            <label className="block text-xs font-medium text-ink-2 mb-1.5">Current password</label>
            <input type="password" value={oldPw} onChange={e => setOldPw(e.target.value)} required className="input" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-ink-2 mb-1.5">New password</label>
              <input type="password" value={newPw} onChange={e => setNewPw(e.target.value)} required className="input" />
            </div>
            <div>
              <label className="block text-xs font-medium text-ink-2 mb-1.5">Confirm new password</label>
              <input type="password" value={confirmPw} onChange={e => setConfirmPw(e.target.value)} required className="input" />
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button type="submit" disabled={savingPw} className="btn-primary text-xs">
              {savingPw && <Loader2 className="animate-spin" size={12} />}
              {savingPw ? 'Changing…' : 'Change password'}
            </button>
          </div>
        </div>
      </form>

      {/* Security note */}
      <div className="mt-5 flex items-start gap-3 px-1">
        <Shield size={14} className="text-ink-4 flex-shrink-0 mt-0.5" />
        <p className="text-2xs text-ink-4 leading-relaxed">
          Your password is protected with bcrypt hashing. Changing it will sign you out of all other devices automatically.
        </p>
      </div>

    </div>
  );
}
