import { useEffect, useState } from 'react';
import { getOpportunities, getProblems, getTrends, getHealth, getSearchHistory, type Opportunity, type ProblemCluster, type Trend } from '../services/api';
import StatCard from '../components/StatCard';
import OpportunityCard from '../components/OpportunityCard';
import InnovationTimeline from '../components/InnovationTimeline';
import AlertsPanel from '../components/AlertsPanel';
import ResearchGapSummary from '../components/ResearchGapSummary';
import AIRecommendationsPanel from '../components/AIRecommendationsPanel';
import { Loader2, TrendingUp, AlertCircle, Zap, FileText, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [problems, setProblems] = useState<ProblemCluster[]>([]);
  const [trends, setTrends] = useState<Trend[]>([]);
  const [vectorCount, setVectorCount] = useState(0);
  const [searchHistory, setSearchHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getOpportunities(), getProblems(), getTrends(), getHealth(), getSearchHistory()])
      .then(([o, p, t, h, sh]) => {
        setOpportunities(o);
        setProblems(p);
        setTrends(t);
        setVectorCount(h.vectors_stored || 0);
        setSearchHistory(Array.isArray(sh) ? sh : []);
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-screen"><Loader2 className="animate-spin text-brand-accent" size={48} /></div>;
  }

  return (
    <div className="p-8 max-w-[1600px] mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 mt-1">Innovation intelligence overview</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Opportunities" value={opportunities.length} sublabel="Ranked by score" />
        <StatCard label="Problem Clusters" value={problems.length} sublabel="Recurring issues" color="text-emerald-400" />
        <StatCard label="Active Trends" value={trends.length} sublabel="Emerging technologies" color="text-blue-400" />
        <StatCard label="Vectors Stored" value={vectorCount} sublabel="Semantic index size" color="text-purple-400" />
      </div>

      {/* Main grid: 2/3 opportunities, 1/3 sidebar widgets */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left column - Opportunities (2/3 width) */}
        <div className="xl:col-span-2">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="text-yellow-400" size={20} />
            <h2 className="text-xl font-semibold text-white">Top Opportunities</h2>
            <span className="text-xs text-gray-500 ml-auto">{opportunities.length} total</span>
            <Link to="/opportunities" className="text-xs text-brand-accent hover:underline flex items-center gap-1 ml-3">
              See all <ArrowRight size={12} />
            </Link>
          </div>
          {opportunities.length === 0 ? (
            <div className="bg-brand-panel border border-brand-border rounded-xl p-8 text-center">
              <AlertCircle className="text-gray-500 mx-auto mb-2" size={32} />
              <p className="text-gray-400">No opportunities yet.</p>
              <p className="text-sm text-gray-500 mt-1">Go to Search and run the pipeline.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {opportunities.slice(0, 8).map(opp => <OpportunityCard key={opp.id} opp={opp} />)}
            </div>
          )}
        </div>

        {/* Right column - Widgets (1/3 width) */}
        <div className="xl:col-span-1 space-y-4">
          <InnovationTimeline />
          <AlertsPanel />
          <AIRecommendationsPanel />
          <ResearchGapSummary />

          <div>
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="text-emerald-400" size={18} />
              <h3 className="text-white font-semibold text-sm">Emerging Trends</h3>
            </div>
            <div className="bg-brand-panel border border-brand-border rounded-xl p-4 space-y-2 max-h-72 overflow-auto">
              {trends.length === 0 ? (
                <p className="text-gray-500 text-xs text-center py-4">No trends yet.</p>
              ) : (
                trends.slice(0, 10).map(trend => (
                  <div key={trend.id} className="flex items-center justify-between gap-2">
                    <span className="text-gray-300 text-xs truncate flex-1">{trend.name}</span>
                    <div className="w-16 h-1 bg-brand-border rounded-full overflow-hidden flex-shrink-0">
                      <div className="h-full bg-emerald-500" style={{ width: `${trend.trend_score * 100}%` }} />
                    </div>
                    <span className="text-[10px] text-gray-500 font-mono w-7 text-right flex-shrink-0">
                      {trend.trend_score.toFixed(2)}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-3">
              <FileText className="text-purple-400" size={18} />
              <h3 className="text-white font-semibold text-sm">Recent Searches</h3>
            </div>
            <div className="bg-brand-panel border border-brand-border rounded-xl p-4 space-y-2 max-h-56 overflow-auto">
              {searchHistory.length === 0 ? (
                <p className="text-gray-500 text-xs text-center py-3">No searches yet.</p>
              ) : (
                searchHistory.slice(0, 6).map((s: any) => (
                  <div key={s.id} className="flex items-center justify-between gap-2 border-b border-brand-border last:border-0 pb-2 last:pb-0">
                    <span className="text-xs text-gray-300 truncate flex-1">{s.query}</span>
                    <span className="text-[10px] text-gray-500 flex-shrink-0">{s.results_count}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
