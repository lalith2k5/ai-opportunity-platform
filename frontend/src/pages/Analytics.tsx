import { useEffect, useState } from 'react';
import {
  getOpportunities, getProblems, getResearchGaps, getTrends, getHealth,
  type Opportunity, type ProblemCluster, type ResearchGap, type Trend,
} from '../services/api';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  LineChart, Line, PieChart, Pie, Cell, Legend, ScatterChart, Scatter,
} from 'recharts';
import { Loader2, BarChart3, TrendingUp, PieChart as PieIcon, Activity, Zap, FileText, Database } from 'lucide-react';

const COLORS = ['#5e6ad2', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899'];

function StatTile({ label, value, icon: Icon, accent = 'text-ink' }: {
  label: string; value: string | number; icon: any; accent?: string;
}) {
  return (
    <div className="bg-surface border border-edge rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-2xs font-medium text-ink-4 uppercase tracking-wider">{label}</p>
        <Icon size={13} className={accent} />
      </div>
      <p className={`text-2xl font-semibold font-mono tabular-nums ${accent}`}>{value}</p>
    </div>
  );
}

export default function Analytics() {
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [problems, setProblems] = useState<ProblemCluster[]>([]);
  const [gaps, setGaps] = useState<ResearchGap[]>([]);
  const [trends, setTrends] = useState<Trend[]>([]);
  const [vectorCount, setVectorCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getOpportunities(), getProblems(), getResearchGaps(), getTrends(), getHealth()])
      .then(([o, p, g, t, h]) => {
        setOpps(o); setProblems(p); setGaps(g); setTrends(t);
        setVectorCount(h.vectors_stored || 0);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-screen"><Loader2 className="animate-spin text-accent" size={32} /></div>;
  }

  const scoreBuckets = [
    { range: '0.0–0.2', count: 0 },
    { range: '0.2–0.4', count: 0 },
    { range: '0.4–0.6', count: 0 },
    { range: '0.6–0.8', count: 0 },
    { range: '0.8–1.0', count: 0 },
  ];
  opps.forEach(o => {
    const idx = Math.min(4, Math.floor(o.opportunity_score * 5));
    scoreBuckets[idx].count++;
  });

  const scatterData = opps.slice(0, 40).map(o => ({
    demand: o.demand_score,
    feasibility: o.feasibility_score,
    score: o.opportunity_score,
  }));

  const catCounts: Record<string, number> = {};
  trends.forEach(t => { catCounts[t.category || 'general'] = (catCounts[t.category || 'general'] || 0) + 1; });
  const pieData = Object.entries(catCounts).map(([name, value]) => ({ name, value }));

  const gapData = [...gaps].sort((a, b) => b.gap_score - a.gap_score).slice(0, 15)
    .map((g, i) => ({ index: i + 1, score: g.gap_score }));

  const tooltipStyle = {
    backgroundColor: 'rgb(var(--bg-overlay))',
    border: '1px solid rgb(var(--border-default))',
    borderRadius: 6,
    color: 'rgb(var(--text-primary))',
    fontSize: 12,
    padding: '8px 10px',
  };
  const tickColor = 'rgb(var(--text-muted))';

  return (
    <div className="p-6 lg:p-8 max-w-[1500px] mx-auto">

      {/* Header */}
      <div className="mb-6 flex items-center gap-3">
        <div className="w-8 h-8 rounded-md bg-accent/10 flex items-center justify-center">
          <BarChart3 className="text-accent" size={16} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">Analytics</h1>
          <p className="text-sm text-ink-3">Deep insights across the entire platform</p>
        </div>
      </div>

      {/* Stat tiles */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 mb-5">
        <StatTile label="Opportunities" value={opps.length}      icon={Zap}       accent="text-accent" />
        <StatTile label="Problems"      value={problems.length}  icon={TrendingUp} accent="text-warning" />
        <StatTile label="Research gaps" value={gaps.length}      icon={FileText}  accent="text-success" />
        <StatTile label="Trends"        value={trends.length}    icon={Activity}  accent="text-sky-500" />
        <StatTile label="Vectors"       value={vectorCount}      icon={Database}  accent="text-purple-500" />
      </div>

      {/* Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">

        <div className="bg-surface border border-edge rounded-lg p-5">
          <div className="flex items-center gap-2 mb-5">
            <BarChart3 size={14} className="text-accent" />
            <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Score distribution</h2>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={scoreBuckets}>
              <CartesianGrid strokeDasharray="2 4" stroke="rgb(var(--border-subtle))" vertical={false} />
              <XAxis dataKey="range" tick={{ fill: tickColor, fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: tickColor, fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgb(var(--bg-overlay))' }} />
              <Bar dataKey="count" fill="#5e6ad2" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-surface border border-edge rounded-lg p-5">
          <div className="flex items-center gap-2 mb-5">
            <PieIcon size={14} className="text-success" />
            <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Trend categories</h2>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={85}
                   stroke="rgb(var(--bg-surface))" strokeWidth={2}
                   label={{ fill: 'rgb(var(--text-secondary))', fontSize: 11 }}>
                {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ color: 'rgb(var(--text-secondary))', fontSize: 11 }} iconType="circle" />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

        <div className="bg-surface border border-edge rounded-lg p-5">
          <div className="flex items-center gap-2 mb-5">
            <TrendingUp size={14} className="text-warning" />
            <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Top research gaps</h2>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={gapData}>
              <CartesianGrid strokeDasharray="2 4" stroke="rgb(var(--border-subtle))" vertical={false} />
              <XAxis dataKey="index" tick={{ fill: tickColor, fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 1]} tick={{ fill: tickColor, fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={tooltipStyle} />
              <Line type="monotone" dataKey="score" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981', r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-surface border border-edge rounded-lg p-5">
          <div className="flex items-center gap-2 mb-5">
            <Activity size={14} className="text-purple-500" />
            <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Demand × feasibility</h2>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="2 4" stroke="rgb(var(--border-subtle))" />
              <XAxis dataKey="demand" name="Demand" domain={[0, 1]} tick={{ fill: tickColor, fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis dataKey="feasibility" name="Feasibility" domain={[0, 1]} tick={{ fill: tickColor, fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ strokeDasharray: '2 4' }} />
              <Scatter data={scatterData} fill="#8b5cf6" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>

    </div>
  );
}
