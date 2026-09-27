import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { updateProfile, changePassword } from '../services/api';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

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
      setProfileMsg('Profile updated. Refresh page to see changes in sidebar.');
      // Update localStorage
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
    <div className="p-8 max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold text-white mb-1">Profile</h1>
      <p className="text-gray-400 mb-8">Manage your account settings</p>

      <div className="bg-brand-panel border border-brand-border rounded-xl p-6 mb-6">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-white">Basic Information</h2>
          <p className="text-xs text-gray-500 mt-1">Role: <span className="capitalize text-brand-accent">{user?.role}</span></p>
        </div>
        <form onSubmit={saveProfile} className="space-y-4">
          {profileMsg && <div className="bg-emerald-900/30 border border-emerald-700 rounded-lg p-3 flex gap-2"><CheckCircle2 className="text-emerald-400" size={18} /><p className="text-emerald-300 text-sm">{profileMsg}</p></div>}
          {profileErr && <div className="bg-red-900/30 border border-red-700 rounded-lg p-3 flex gap-2"><AlertCircle className="text-red-400" size={18} /><p className="text-red-300 text-sm">{profileErr}</p></div>}
          <div>
            <label className="block text-sm text-gray-400 mb-1">Name</label>
            <input type="text" value={name} onChange={e => setName(e.target.value)} required
              className="w-full bg-brand-dark border border-brand-border rounded-lg px-4 py-3 text-white" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required
              className="w-full bg-brand-dark border border-brand-border rounded-lg px-4 py-3 text-white" />
          </div>
          <button type="submit" disabled={savingProfile}
            className="bg-brand-accent hover:bg-indigo-600 disabled:opacity-50 text-white px-6 py-2 rounded-lg font-medium flex items-center gap-2">
            {savingProfile && <Loader2 className="animate-spin" size={16} />}
            {savingProfile ? 'Saving...' : 'Save changes'}
          </button>
        </form>
      </div>

      <div className="bg-brand-panel border border-brand-border rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Change Password</h2>
        <form onSubmit={savePassword} className="space-y-4">
          {pwMsg && <div className="bg-emerald-900/30 border border-emerald-700 rounded-lg p-3 flex gap-2"><CheckCircle2 className="text-emerald-400" size={18} /><p className="text-emerald-300 text-sm">{pwMsg}</p></div>}
          {pwErr && <div className="bg-red-900/30 border border-red-700 rounded-lg p-3 flex gap-2"><AlertCircle className="text-red-400" size={18} /><p className="text-red-300 text-sm">{pwErr}</p></div>}
          <div>
            <label className="block text-sm text-gray-400 mb-1">Current password</label>
            <input type="password" value={oldPw} onChange={e => setOldPw(e.target.value)} required
              className="w-full bg-brand-dark border border-brand-border rounded-lg px-4 py-3 text-white" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">New password</label>
            <input type="password" value={newPw} onChange={e => setNewPw(e.target.value)} required
              className="w-full bg-brand-dark border border-brand-border rounded-lg px-4 py-3 text-white" />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Confirm new password</label>
            <input type="password" value={confirmPw} onChange={e => setConfirmPw(e.target.value)} required
              className="w-full bg-brand-dark border border-brand-border rounded-lg px-4 py-3 text-white" />
          </div>
          <button type="submit" disabled={savingPw}
            className="bg-brand-accent hover:bg-indigo-600 disabled:opacity-50 text-white px-6 py-2 rounded-lg font-medium flex items-center gap-2">
            {savingPw && <Loader2 className="animate-spin" size={16} />}
            {savingPw ? 'Changing...' : 'Change password'}
          </button>
        </form>
      </div>
    </div>
  );
}
