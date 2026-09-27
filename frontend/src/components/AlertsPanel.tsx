import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getNotifications } from '../services/api';
import { Bell, AlertCircle, TrendingUp, Lightbulb, FileWarning, Zap } from 'lucide-react';

const ICONS: Record<string, any> = {
  research_opportunity: Lightbulb,
  emerging_tech: TrendingUp,
  startup_opportunity: Zap,
  innovation_alert: Bell,
  research_gap_alert: FileWarning,
};

const COLORS: Record<string, string> = {
  success: 'text-emerald-400',
  warning: 'text-yellow-400',
  info: 'text-blue-400',
};

export default function AlertsPanel() {
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    getNotifications().then(d => setItems(d.slice(0, 5))).catch(() => {});
  }, []);

  return (
    <div className="bg-brand-panel border border-brand-border rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <AlertCircle className="text-orange-400" size={18} />
        <h3 className="text-white font-semibold text-sm">Recent Alerts</h3>
      </div>
      {items.length === 0 ? (
        <p className="text-gray-500 text-xs text-center py-4">No alerts.</p>
      ) : (
        <div className="space-y-2">
          {items.map(n => {
            const Icon = ICONS[n.type] || Bell;
            return (
              <Link
                key={n.id}
                to={n.link || '/'}
                className="block border border-brand-border rounded-lg p-2 hover:border-brand-accent transition-colors"
              >
                <div className="flex items-start gap-2">
                  <Icon size={14} className={COLORS[n.severity] || 'text-gray-400'} />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-gray-200 truncate">{n.title}</p>
                    <p className="text-[10px] text-gray-500 truncate">{n.type}</p>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
