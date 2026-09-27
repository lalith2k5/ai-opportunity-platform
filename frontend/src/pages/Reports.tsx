import { useEffect, useState } from 'react';
import {
  getOpportunities, getResearchGaps, getTrends,
  downloadPDFReport,
  type Opportunity, type ResearchGap, type Trend,
} from '../services/api';
import { Download, FileText, Loader2, FileDown } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell, Legend,
} from 'recharts';

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

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
    const headers = ['Title', 'Opportunity Score', 'Confidence', 'Demand', 'Research Gap', 'Trend'];
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
    try {
      await downloadPDFReport();
    } catch (e: any) {
      alert(`PDF error: ${e.message}`);
    } finally {
      setPdfLoading(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen"><Loader2 className="animate-spin text-brand-accent" size={48} /></div>;
  }

  const scoreData = opportunities.slice(0, 10).map(o => ({
    name: o.title.length > 25 ? o.title.slice(0, 25) + '…' : o.title,
    score: Number(o.opportunity_score.toFixed(2)),
  }));

  const categoryCounts: Record<string, number> = {};
  trends.forEach(t => {
    const cat = t.category || 'general';
    categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
  });
  const pieData = Object.entries(categoryCounts).map(([name, value]) => ({ name, value }));

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Reports & Analytics</h1>
          <p className="text-gray-400 mt-1">Visual analytics and downloadable reports</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={downloadCSV} disabled={opportunities.length === 0}
            className="bg-brand-panel border border-brand-border hover:border-brand-accent disabled:opacity-50 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Download size={18} /> CSV
          </button>
          <button
            onClick={downloadPDF} disabled={pdfLoading || opportunities.length === 0}
            className="bg-brand-accent hover:bg-indigo-600 disabled:opacity-50 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            {pdfLoading ? <Loader2 className="animate-spin" size={18} /> : <FileDown size={18} />}
            {pdfLoading ? 'Generating…' : 'PDF Report'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-brand-panel border border-brand-border rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Top Opportunity Scores</h2>
          {scoreData.length === 0 ? (
            <p className="text-center text-gray-500 py-8">No data yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={scoreData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 10 }} angle={-30} textAnchor="end" height={70} interval={0} />
                <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#131826', border: '1px solid #1f2937', borderRadius: 8, color: '#e5e7eb' }} />
                <Bar dataKey="score" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-brand-panel border border-brand-border rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Trend Categories</h2>
          {pieData.length === 0 ? (
            <p className="text-center text-gray-500 py-8">No trends yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
                  {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#131826', border: '1px solid #1f2937', borderRadius: 8, color: '#e5e7eb' }} />
                <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-brand-panel border border-brand-border rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <FileText className="text-brand-accent" size={20} />
            <h2 className="text-lg font-semibold text-white">Opportunity Rankings</h2>
          </div>
          <div className="overflow-auto max-h-96">
            <table className="w-full text-sm">
              <thead className="text-xs text-gray-500 border-b border-brand-border">
                <tr><th className="text-left py-2">Title</th><th className="text-right py-2">Score</th></tr>
              </thead>
              <tbody>
                {opportunities.map(o => (
                  <tr key={o.id} className="border-b border-brand-border last:border-0">
                    <td className="py-3 text-gray-300 pr-2">{o.title}</td>
                    <td className="py-3 text-right font-mono text-brand-accent">{o.opportunity_score.toFixed(2)}</td>
                  </tr>
                ))}
                {opportunities.length === 0 && <tr><td colSpan={2} className="py-6 text-center text-gray-500">No data yet</td></tr>}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-brand-panel border border-brand-border rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <FileText className="text-emerald-400" size={20} />
            <h2 className="text-lg font-semibold text-white">Research Gaps</h2>
          </div>
          <div className="space-y-3 max-h-96 overflow-auto">
            {gaps.map(g => (
              <div key={g.id} className="border-b border-brand-border last:border-0 pb-3 last:pb-0">
                <div className="flex justify-between items-start gap-2">
                  <p className="text-sm text-gray-300 flex-1">{g.title}</p>
                  <span className="text-xs font-mono text-emerald-400 flex-shrink-0">{g.gap_score.toFixed(2)}</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">{g.description}</p>
              </div>
            ))}
            {gaps.length === 0 && <p className="text-center text-gray-500 py-6">No data yet</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
