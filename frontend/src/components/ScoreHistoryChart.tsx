import { useEffect, useState } from 'react';
import { getOpportunityHistory } from '../services/api';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { TrendingUp } from 'lucide-react';

export default function ScoreHistoryChart({ oppId }: { oppId: number }) {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOpportunityHistory(oppId, 30)
      .then((d: any) => setHistory(d.history || []))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, [oppId]);

  if (loading || history.length < 2) return null;

  const data = history.map(h => ({
    t: new Date(h.recorded_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    score: Number(h.score?.toFixed(3) || 0),
    rank: h.rank,
  }));

  return (
    <div className="bg-surface border border-edge rounded-lg p-5">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp size={14} className="text-accent" />
        <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Score history (last 30 days)</h2>
        <span className="text-2xs text-ink-4 font-mono ml-auto">{history.length} snapshots</span>
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="2 4" stroke="rgb(var(--border-subtle))" vertical={false} />
          <XAxis dataKey="t" tick={{ fill: 'rgb(var(--text-muted))', fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis domain={[0, 1]} tick={{ fill: 'rgb(var(--text-muted))', fontSize: 10 }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgb(var(--bg-overlay))',
              border: '1px solid rgb(var(--border-default))',
              borderRadius: 6,
              color: 'rgb(var(--text-primary))',
              fontSize: 12,
            }}
          />
          <Line type="monotone" dataKey="score" stroke="#5e6ad2" strokeWidth={2} dot={{ fill: '#5e6ad2', r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
