import { useEffect, useState } from 'react';
import {
  getOpportunities, getResearchGaps, getTrends, downloadPDFReport,
  type Opportunity, type ResearchGap, type Trend,
} from '../services/api';
import { Download, FileText, Loader2, FileDown, TrendingUp } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell, Legend,
} from 'recharts';

const COLORS = ['#5e6ad2', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export default function Reports() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [gaps, setGaps] = useState<ResearchGap[]>([]);
  const [trends, setTrends] = useState<Trend[]>([]);
  const [loading, setLoading] = useState(true);
  const [pdfLoading, setPdfLoading] = useState(false);

  useEffect(() => {
    Promise.all([getOpportunities(), getResearchGaps(), getTrends()])
      .then(([o, g, t]) => { setOpportunities(o); setGaps(g); setTrends(t); })
      .finally(() => setLoading(false));
  }, []);

  const downloadCSV = () => {
    const headers = ['Title', 'Score', 'Confidence', 'Demand', 'Research Gap', 'Trend'];
    const rows = opportunities.map(o => [
      `"${o.title.replace(/"/g, '""')}"`,
      o.opportunity_score.toFixed(3), o.confidence_score.toFixed(3),
      o.demand_score.toFixed(3), o.research_gap_score.toFixed(3), o.trend_score.toFixed(3),
    ]);
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `opportunities_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadPDF = async () => {
    setPdfLoading(true);
    try { await downloadPDFReport(); }
    catch (e: any) { alert(`PDF error: ${e.message}`); }
    finally { setPdfLoading(false); }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen"><Loader2 className="animate-spin text-accent" size={32} /></div>;
  }

  const scoreData = opportunities.slice(0, 10).map(o => ({
    name: o.title.length > 20 ? o.title.slice(0, 20) + '…' : o.title,
    score: Number(o.opportunity_score.toFixed(2)),
  }));

  const categoryCounts: Record<string, number> = {};
  trends.forEach(t => { categoryCounts[t.category || 'general'] = (categoryCounts[t.category || 'general'] || 0) + 1; });
  const pieData = Object.entries(categoryCounts).map(([name, value]) => ({ name, value }));

  const tooltipStyle = {
    backgroundColor: 'rgb(var(--bg-overlay))',
    border: '1px solid rgb(var(--border-default))',
    borderRadius: 6,
    color: 'rgb(var(--text-primary))',
    fontSize: 12,
    padding: '8px 10px',
  };

  return (
    <div className="p-6 lg:p-8 max-w-[1500px] mx-auto">

      {/* Header */}
      <div className="mb-6 flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-accent/10 flex items-center justify-center">
            <FileText className="text-accent" size={16} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-ink tracking-tight">Reports & analytics</h1>
            <p className="text-sm text-ink-3">Visual insights and downloadable reports</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={downloadCSV} disabled={opportunities.length === 0} className="btn-secondary text-xs">
            <Download size={13} /> CSV
          </button>
          <button onClick={downloadPDF} disabled={pdfLoading || opportunities.length === 0} className="btn-primary text-xs">
            {pdfLoading ? <Loader2 className="animate-spin" size={13} /> : <FileDown size={13} />}
            {pdfLoading ? 'Generating…' : 'PDF report'}
          </button>
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">

        <div className="bg-surface border border-edge rounded-lg p-5">
          <div className="flex items-center gap-2 mb-5">
            <TrendingUp size={14} className="text-accent" />
            <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Top opportunity scores</h2>
          </div>
          {scoreData.length === 0 ? (
            <p className="text-sm text-ink-4 text-center py-12">No data yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={scoreData}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgb(var(--border-subtle))" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: 'rgb(var(--text-muted))', fontSize: 10 }} angle={-35} textAnchor="end" height={70} interval={0} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: 'rgb(var(--text-muted))', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgb(var(--bg-overlay))' }} />
                <Bar dataKey="score" fill="#5e6ad2" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-surface border border-edge rounded-lg p-5">
          <div className="flex items-center gap-2 mb-5">
            <FileText size={14} className="text-success" />
            <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Trend categories</h2>
          </div>
          {pieData.length === 0 ? (
            <p className="text-sm text-ink-4 text-center py-12">No trends yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
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
          )}
        </div>
      </div>

      {/* Rankings + gaps */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

        <div className="bg-surface border border-edge rounded-lg p-5">
          <div className="flex items-center gap-2 mb-4">
            <FileText size={14} className="text-accent" />
            <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Opportunity rankings</h2>
          </div>
          <div className="max-h-96 overflow-y-auto -mr-2 pr-2">
            {opportunities.length === 0 ? (
              <p className="text-sm text-ink-4 text-center py-8">No data yet</p>
            ) : (
              <div className="space-y-0.5">
                {opportunities.map((o, i) => (
                  <div key={o.id} className="flex items-center gap-3 py-2 border-b border-edge-subtle last:border-0">
                    <span className="text-2xs text-ink-4 font-mono tabular-nums w-5 flex-shrink-0">{i + 1}</span>
                    <span className="text-xs text-ink-2 truncate flex-1">{o.title}</span>
                    <span className="text-xs font-mono tabular-nums text-accent flex-shrink-0">{o.opportunity_score.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="bg-surface border border-edge rounded-lg p-5">
          <div className="flex items-center gap-2 mb-4">
            <FileText size={14} className="text-success" />
            <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Research gaps</h2>
          </div>
          <div className="max-h-96 overflow-y-auto -mr-2 pr-2 space-y-3">
            {gaps.length === 0 ? (
              <p className="text-sm text-ink-4 text-center py-8">No data yet</p>
            ) : (
              gaps.map(g => (
                <div key={g.id} className="pb-3 border-b border-edge-subtle last:border-0">
                  <div className="flex items-start justify-between gap-3 mb-1.5">
                    <p className="text-xs text-ink-2 leading-snug flex-1">{g.title}</p>
                    <span className="text-xs font-mono tabular-nums text-success flex-shrink-0">{g.gap_score.toFixed(2)}</span>
                  </div>
                  <p className="text-2xs text-ink-4 leading-relaxed line-clamp-2">{g.description}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

    </div>
  );
}
