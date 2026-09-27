import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { Bell, Check, X } from 'lucide-react';
import { Link } from 'react-router-dom';
import {
  getNotifications, getUnreadCount,
  markNotificationRead, markAllNotificationsRead,
} from '../services/api';

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [count, setCount] = useState(0);
  const [coords, setCoords] = useState<{ top: number; left: number }>({ top: 0, left: 0 });

  const load = async () => {
    try {
      const [n, c] = await Promise.all([getNotifications(), getUnreadCount()]);
      setNotifications(n);
      setCount(c.count);
    } catch {}
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, []);

  const handleToggle = (e: React.MouseEvent<HTMLButtonElement>) => {
    const rect = (e.currentTarget as HTMLButtonElement).getBoundingClientRect();
    const PANEL_WIDTH = 320;
    const MARGIN = 8;

    // Prefer left-aligning panel to the right edge of the button.
    // If that would overflow the viewport, right-align instead.
    let left = rect.right + MARGIN;
    if (left + PANEL_WIDTH > window.innerWidth - MARGIN) {
      left = Math.max(MARGIN, window.innerWidth - PANEL_WIDTH - MARGIN);
    }

    setCoords({ top: rect.bottom + MARGIN, left });
    setOpen(o => !o);
  };

  const handleRead = async (id: number) => {
    await markNotificationRead(id);
    await load();
  };

  const handleAll = async () => {
    await markAllNotificationsRead();
    await load();
  };

  const severityDot = (s: string) => ({
    success: 'bg-success',
    warning: 'bg-warning',
    info:    'bg-accent',
  }[s] || 'bg-ink-4');

  const dropdown = open ? createPortal(
    <>
      <div className="fixed inset-0 z-[90]" onClick={() => setOpen(false)} />
      <div
        className="fixed z-[100] w-80 max-w-[calc(100vw-1rem)] bg-overlay border border-edge rounded-lg shadow-xl overflow-hidden animate-slide-up"
        style={{ top: coords.top, left: coords.left }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-3.5 py-3 border-b border-edge-subtle bg-overlay">
          <div className="flex items-center gap-2">
            <h3 className="text-xs font-medium text-ink uppercase tracking-wider">Notifications</h3>
            {count > 0 && (
              <span className="badge bg-accent/15 text-accent border border-accent/30">
                {count}
              </span>
            )}
          </div>
          <div className="flex items-center gap-0.5">
            {count > 0 && (
              <button
                onClick={handleAll}
                title="Mark all as read"
                className="p-1.5 rounded-md text-ink-4 hover:text-ink hover:bg-subtle transition-colors"
              >
                <Check size={13} />
              </button>
            )}
            <button
              onClick={() => setOpen(false)}
              className="p-1.5 rounded-md text-ink-4 hover:text-ink hover:bg-subtle transition-colors"
            >
              <X size={13} />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="max-h-[440px] overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="px-6 py-10 text-center">
              <Bell className="text-ink-4 mx-auto mb-3" size={20} />
              <p className="text-xs text-ink-3 font-medium">You're all caught up</p>
              <p className="text-2xs text-ink-4 mt-1">No notifications yet</p>
            </div>
          ) : (
            notifications.slice(0, 15).map(n => (
              <Link
                key={n.id}
                to={n.link || '/'}
                onClick={() => { if (!n.read) handleRead(n.id); setOpen(false); }}
                className={`block px-3.5 py-3 border-b border-edge-subtle last:border-0 hover:bg-subtle/60 transition-colors ${
                  !n.read ? 'bg-accent/[0.04]' : ''
                }`}
              >
                <div className="flex items-start gap-2.5">
                  <span className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${severityDot(n.severity)}`} />
                  <div className="flex-1 min-w-0">
                    <p className={`text-xs truncate ${!n.read ? 'text-ink font-medium' : 'text-ink-2'}`}>
                      {n.title}
                    </p>
                    <p className="text-2xs text-ink-3 mt-0.5 line-clamp-2 leading-relaxed">{n.message}</p>
                    <p className="text-2xs text-ink-4 mt-1.5">
                      {new Date(n.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </>,
    document.body
  ) : null;

  return (
    <>
      <button
        onClick={handleToggle}
        aria-label="Notifications"
        className="relative p-2 rounded-md text-ink-3 hover:text-ink hover:bg-overlay transition-colors"
      >
        <Bell size={16} />
        {count > 0 && (
          <span className="absolute top-0.5 right-0.5 min-w-[16px] h-[16px] px-1 bg-danger text-white text-[9px] font-bold rounded-full flex items-center justify-center leading-none">
            {count > 9 ? '9+' : count}
          </span>
        )}
      </button>
      {dropdown}
    </>
  );
}
