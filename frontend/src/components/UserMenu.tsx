import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User as UserIcon, LogOut, Shield, ChevronUp } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function UserMenu() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('mousedown', onClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onClick);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  if (!user) return null;

  const handleSignOut = async () => {
    setOpen(false);
    await logout();
    navigate('/login');
  };

  return (
    <div ref={ref} className="relative">
      {open && (
        <div className="absolute bottom-full left-0 right-0 mb-2 bg-overlay border border-edge rounded-lg shadow-xl overflow-hidden animate-slide-up">
          <div className="px-3 py-2.5 border-b border-edge-subtle">
            <p className="text-2xs text-ink-4 uppercase tracking-wider mb-0.5">Signed in as</p>
            <p className="text-xs text-ink font-medium truncate">{user.email}</p>
          </div>
          <Link
            to="/profile"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2.5 px-3 py-2 text-sm text-ink-2 hover:bg-subtle hover:text-ink transition-colors"
          >
            <UserIcon size={14} />
            <span>Profile</span>
          </Link>
          {user.role === 'admin' && (
            <Link
              to="/admin"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 px-3 py-2 text-sm text-warning hover:bg-subtle transition-colors"
            >
              <Shield size={14} />
              <span>Admin</span>
            </Link>
          )}
          <button
            onClick={handleSignOut}
            className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-danger hover:bg-subtle transition-colors border-t border-edge-subtle"
          >
            <LogOut size={14} />
            <span>Sign out</span>
          </button>
        </div>
      )}

      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-2.5 px-2 py-2 rounded-md hover:bg-overlay transition-colors"
      >
        <div className="w-7 h-7 rounded-full bg-accent flex items-center justify-center flex-shrink-0 text-accent-fg">
          <UserIcon size={13} />
        </div>
        <div className="min-w-0 flex-1 text-left">
          <p className="text-sm text-ink font-medium truncate leading-tight">{user.name}</p>
          <p className="text-2xs text-ink-4 capitalize truncate leading-tight">{user.role}</p>
        </div>
        <ChevronUp
          size={13}
          className={`text-ink-4 flex-shrink-0 transition-transform duration-150 ${open ? 'rotate-180' : ''}`}
        />
      </button>
    </div>
  );
}
