import { useEffect, useState } from 'react';
import {
  getOpportunities, getProblems, getResearchGaps, getTrends, getHealth,
  type Opportunity, type ProblemCluster, type ResearchGap, type Trend,
} from '../services/api';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  LineChart, Line, PieChart, Pie, Cell, Legend, ScatterChart, Scatter,
} from 'recharts';
import { Loader2, BarChart3, TrendingUp, PieChart as PieIcon, Activity } from 'lucide-react';

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899'];

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

  if (loading) return <div className="flex items-center justify-center h-screen"><Loader2 className="animate-spin text-brand-accent" size={48} /></div>;

  const scoreBuckets = [
    { range: '0.0-0.2', count: 0 },
    { range: '0.2-0.4', count: 0 },
    { range: '0.4-0.6', count: 0 },
    { range: '0.6-0.8', count: 0 },
    { range: '0.8-1.0', count: 0 },
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
  trends.forEach(t => {
    catCounts[t.category || 'general'] = (catCounts[t.category || 'general'] || 0) + 1;
  });
  const pieData = Object.entries(catCounts).map(([name, value]) => ({ name, value }));

  const gapData = [...gaps].sort((a, b) => b.gap_score - a.gap_score).slice(0, 15)
    .map((g, i) => ({ index: i + 1, score: g.gap_score }));

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <BarChart3 className="text-brand-accent" size={28} /> Analytics Dashboard
        </h1>
        <p className="text-gray-400 mt-1">Deep insights across the entire platform</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <div className="bg-brand-panel border border-brand-border rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase">Opportunities</p>
          <p className="text-2xl font-bold text-brand-accent mt-1">{opps.length}</p>
        </div>
        <div className="bg-brand-panel border border-brand-border rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase">Problems</p>
          <p className="text-2xl font-bold text-orange-400 mt-1">{problems.length}</p>
        </div>
        <div className="bg-brand-panel border border-brand-border rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase">Research Gaps</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1">{gaps.length}</p>
        </div>
        <div className="bg-brand-panel border border-brand-border rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase">Trends</p>
          <p className="text-2xl font-bold text-blue-400 mt-1">{trends.length}</p>
        </div>
        <div className="bg-brand-panel border border-brand-border rounded-xl p-4">
          <p className="text-xs text-gray-500 uppercase">Vectors</p>
          <p className="text-2xl font-bold text-purple-400 mt-1">{vectorCount}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-brand-panel border border-brand-border rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="text-brand-accent" size={18} />
            <h2 className="text-lg font-semibold text-white">Opportunity Score Distribution</h2>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={scoreBuckets}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="range" tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <Tooltip contentStyle={{ backgroundColor: '#131826', border: '1px solid #1f2937', borderRadius: 8, color: '#e5e7eb' }} />
              <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-brand-panel border border-brand-border rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <PieIcon className="text-emerald-400" size={18} />
            <h2 className="text-lg font-semibold text-white">Trend Categories</h2>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
                {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: '#131826', border: '1px solid #1f2937', borderRadius: 8, color: '#e5e7eb' }} />
              <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-brand-panel border border-brand-border rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="text-yellow-400" size={18} />
            <h2 className="text-lg font-semibold text-white">Research Gaps (Top 15)</h2>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={gapData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="index" tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <YAxis domain={[0, 1]} tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <Tooltip contentStyle={{ backgroundColor: '#131826', border: '1px solid #1f2937', borderRadius: 8, color: '#e5e7eb' }} />
              <Line type="monotone" dataKey="score" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-brand-panel border border-brand-border rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="text-purple-400" size={18} />
            <h2 className="text-lg font-semibold text-white">Demand vs Feasibility</h2>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="demand" name="Demand" domain={[0, 1]} tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <YAxis dataKey="feasibility" name="Feasibility" domain={[0, 1]} tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <Tooltip contentStyle={{ backgroundColor: '#131826', border: '1px solid #1f2937', borderRadius: 8, color: '#e5e7eb' }} />
              <Scatter data={scatterData} fill="#8b5cf6" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
