import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { Bell } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getNotifications, getUnreadCount, markNotificationRead, markAllNotificationsRead } from '../services/api';

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [count, setCount] = useState(0);
  const [coords, setCoords] = useState({ top: 0, left: 0 });

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
    setCoords({
      top: rect.bottom + 8,
      left: rect.right + 12,
    });
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

  const severityColor = (s: string) => ({
    success: 'text-emerald-400',
    warning: 'text-yellow-400',
    info: 'text-blue-400',
  }[s] || 'text-gray-400');

  const dropdown = open ? createPortal(
    <>
      <div className="fixed inset-0 z-[90]" onClick={() => setOpen(false)} />
      <div
        className="fixed z-[100] w-80 bg-brand-panel border border-brand-border rounded-xl shadow-2xl max-h-[500px] overflow-auto"
        style={{ top: coords.top, left: coords.left }}
      >
        <div className="p-3 border-b border-brand-border flex items-center justify-between sticky top-0 bg-brand-panel z-10">
          <h3 className="text-white font-semibold text-sm">Notifications</h3>
          {count > 0 && (
            <button onClick={handleAll} className="text-xs text-brand-accent hover:underline">
              Mark all read
            </button>
          )}
        </div>
        {notifications.length === 0 ? (
          <p className="p-6 text-center text-gray-500 text-sm">No notifications</p>
        ) : (
          notifications.slice(0, 15).map(n => (
            <Link
              key={n.id}
              to={n.link || '/'}
              onClick={() => { if (!n.read) handleRead(n.id); setOpen(false); }}
              className={`block p-3 border-b border-brand-border last:border-0 hover:bg-brand-border/30 ${!n.read ? 'bg-brand-border/20' : ''}`}
            >
              <div className="flex items-start gap-2">
                <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${severityColor(n.severity)}`} style={{ backgroundColor: 'currentColor' }} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-white truncate">{n.title}</p>
                  <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{n.message}</p>
                  <p className="text-[10px] text-gray-600 mt-1">{new Date(n.created_at).toLocaleString()}</p>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </>,
    document.body
  ) : null;

  return (
    <>
      <button
        onClick={handleToggle}
        className="relative p-2 rounded-lg text-gray-400 hover:text-white hover:bg-brand-border transition-colors"
      >
        <Bell size={20} />
        {count > 0 && (
          <span className="absolute top-0 right-0 w-4 h-4 bg-red-500 text-white text-[10px] rounded-full flex items-center justify-center">
            {count > 9 ? '9+' : count}
          </span>
        )}
      </button>
      {dropdown}
    </>
  );
}
