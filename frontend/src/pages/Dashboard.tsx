import { useEffect, useState } from 'react';
import { getOpportunities, getProblems, getTrends, getHealth, getSearchHistory, type Opportunity, type ProblemCluster, type Trend } from '../services/api';
import StatCard from '../components/StatCard';
import OpportunityCard from '../components/OpportunityCard';
import InnovationTimeline from '../components/InnovationTimeline';
import AlertsPanel from '../components/AlertsPanel';
import ResearchGapSummary from '../components/ResearchGapSummary';
import AIRecommendationsPanel from '../components/AIRecommendationsPanel';
import { Loader2, TrendingUp, AlertCircle, Zap, FileText } from 'lucide-react';

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
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 mt-1">Innovation intelligence overview</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Opportunities" value={opportunities.length} sublabel="Ranked by score" />
        <StatCard label="Problem Clusters" value={problems.length} sublabel="Recurring issues" color="text-emerald-400" />
        <StatCard label="Active Trends" value={trends.length} sublabel="Emerging technologies" color="text-blue-400" />
        <StatCard label="Vectors Stored" value={vectorCount} sublabel="Semantic index size" color="text-purple-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="flex items-center gap-2 mb-4">
            <Zap className="text-yellow-400" size={20} />
            <h2 className="text-xl font-semibold text-white">Top Opportunities</h2>
          </div>
          {opportunities.length === 0 ? (
            <div className="bg-brand-panel border border-brand-border rounded-xl p-8 text-center">
              <AlertCircle className="text-gray-500 mx-auto mb-2" size={32} />
              <p className="text-gray-400">No opportunities yet.</p>
              <p className="text-sm text-gray-500 mt-1">Go to Search and run the pipeline.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {opportunities.map(opp => <OpportunityCard key={opp.id} opp={opp} />)}
            </div>
          )}
        </div>

        <div>
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="text-emerald-400" size={20} />
            <h2 className="text-xl font-semibold text-white">Emerging Trends</h2>
          </div>
          <div className="bg-brand-panel border border-brand-border rounded-xl p-4 space-y-3">
            {trends.length === 0 ? (
              <p className="text-gray-500 text-sm text-center py-4">No trends yet.</p>
            ) : (
              trends.slice(0, 10).map(trend => (
                <div key={trend.id} className="flex items-center justify-between">
                  <span className="text-gray-300 text-sm truncate pr-2">{trend.name}</span>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <div className="w-16 h-1.5 bg-brand-border rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500" style={{ width: `${trend.trend_score * 100}%` }} />
                    </div>
                    <span className="text-xs text-gray-500 font-mono w-8 text-right">{trend.trend_score.toFixed(2)}</span>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="flex items-center gap-2 mb-4 mt-8">
            <AlertCircle className="text-orange-400" size={20} />
            <h2 className="text-xl font-semibold text-white">Problem Clusters</h2>
          </div>
          <div className="bg-brand-panel border border-brand-border rounded-xl p-4 space-y-3">
            {problems.length === 0 ? (
              <p className="text-gray-500 text-sm text-center py-4">No problems yet.</p>
            ) : (
              problems.slice(0, 5).map(p => (
                <div key={p.id} className="border-b border-brand-border last:border-0 pb-3 last:pb-0">
                  <p className="text-sm text-gray-300 truncate">{p.title}</p>
                  <p className="text-xs text-gray-500 mt-1">{p.source_count} sources · demand {p.demand_score.toFixed(2)}</p>
                </div>
              ))
            )}
          </div>

          <div className="mt-8">
            <InnovationTimeline />
          </div>

          <div className="mt-6">
            <AlertsPanel />
          </div>

          <div className="mt-6">
            <AIRecommendationsPanel />
          </div>

          <div className="mt-6">
            <ResearchGapSummary />
          </div>

          <div className="flex items-center gap-2 mb-4 mt-8">
            <FileText className="text-purple-400" size={20} />
            <h2 className="text-xl font-semibold text-white">Recent Searches</h2>
          </div>
          <div className="bg-brand-panel border border-brand-border rounded-xl p-4 space-y-2">
            {searchHistory.length === 0 ? (
              <p className="text-gray-500 text-sm text-center py-4">No searches yet.</p>
            ) : (
              searchHistory.slice(0, 5).map((s: any) => (
                <div key={s.id} className="flex items-center justify-between border-b border-brand-border last:border-0 pb-2 last:pb-0">
                  <span className="text-xs text-gray-300 truncate pr-2">{s.query}</span>
                  <span className="text-xs text-gray-500 flex-shrink-0">{s.results_count} results</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
