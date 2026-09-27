import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getNotifications } from '../services/api';
import { Bell, TrendingUp, Lightbulb, FileWarning, Zap } from 'lucide-react';

const ICONS: Record<string, any> = {
  research_opportunity: Lightbulb,
  emerging_tech: TrendingUp,
  startup_opportunity: Zap,
  innovation_alert: Bell,
  research_gap_alert: FileWarning,
};

const COLORS: Record<string, string> = {
  success: 'text-success',
  warning: 'text-warning',
  info: 'text-accent',
};

export default function AlertsPanel() {
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    getNotifications().then(d => setItems(d.slice(0, 4))).catch(() => {});
  }, []);

  if (items.length === 0) {
    return <p className="text-xs text-ink-4 text-center py-4">No alerts.</p>;
  }

  return (
    <div className="space-y-1.5">
      {items.map(n => {
        const Icon = ICONS[n.type] || Bell;
        return (
          <Link
            key={n.id}
            to={n.link || '/'}
            className="flex items-start gap-2.5 py-2 px-2 -mx-2 rounded-md hover:bg-overlay transition-colors"
          >
            <Icon size={13} className={`${COLORS[n.severity] || 'text-ink-4'} mt-0.5 flex-shrink-0`} />
            <div className="min-w-0 flex-1">
              <p className="text-xs text-ink-2 leading-snug truncate">{n.title}</p>
              <p className="text-2xs text-ink-4 mt-0.5 capitalize">{n.type.replace(/_/g, ' ')}</p>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
