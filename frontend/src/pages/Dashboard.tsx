import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  getOpportunities, getProblems, getTrends, getHealth, getSearchHistory,
  type Opportunity, type ProblemCluster, type Trend,
} from '../services/api';
import StatCard from '../components/StatCard';
import OpportunityCard from '../components/OpportunityCard';
import InnovationTimeline from '../components/InnovationTimeline';
import AlertsPanel from '../components/AlertsPanel';
import ResearchGapSummary from '../components/ResearchGapSummary';
import AIRecommendationsPanel from '../components/AIRecommendationsPanel';
import { useAuth } from '../context/AuthContext';
import {
  Loader2, Zap, TrendingUp, FileText, Database, Search as SearchIcon,
  ArrowRight, Sparkles, Clock, Bell,
} from 'lucide-react';

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 18) return 'Good afternoon';
  return 'Good evening';
}

function Panel({
  icon: Icon,
  title,
  action,
  accent = 'text-accent',
  children,
}: {
  icon: any;
  title: string;
  action?: React.ReactNode;
  accent?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="card p-4 flex flex-col">
      <div className="flex items-center justify-between mb-3 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Icon size={13} className={accent} />
          <h3 className="text-ink font-semibold text-2xs uppercase tracking-[0.08em]">{title}</h3>
        </div>
        {action}
      </div>
      <div className="flex-1 min-h-0">{children}</div>
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
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
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="animate-spin text-accent" size={32} />
      </div>
    );
  }

  const firstName = user?.name?.split(' ')[0] || 'there';

  return (
    <div className="p-6 lg:p-8 max-w-[1500px] mx-auto">

      {/* Header */}
      <div className="flex items-start justify-between gap-6 mb-8 flex-wrap">
        <div>
          <h1 className="text-4xl font-bold text-ink tracking-tight leading-tight">
            {greeting()}, <span className="bg-gradient-to-r from-accent to-sky-300 bg-clip-text text-transparent">{firstName}</span>.
          </h1>
          <p className="text-base text-ink-3 mt-2.5 leading-relaxed">
            Here's what's happening in your innovation workspace.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/chat" className="btn-secondary text-xs">
            <Sparkles size={13} /> Ask AI
          </Link>
          <Link to="/search" className="btn-primary text-xs">
            <SearchIcon size={13} /> Run pipeline
          </Link>
        </div>
      </div>

      {/* Stat row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <StatCard label="Opportunities"   value={opportunities.length} sublabel="Ranked by score"    icon={Zap}        accent />
        <StatCard label="Problem clusters" value={problems.length}    sublabel="Recurring signals"  icon={TrendingUp} />
        <StatCard label="Active trends"   value={trends.length}       sublabel="Emerging tech"      icon={FileText} />
        <StatCard label="Vectors stored"  value={vectorCount}         sublabel="Semantic index"     icon={Database} />
      </div>

      {/* Top row: Opportunities (2/3) + AI Picks & Gaps (1/3) */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5 mb-5">

        {/* LEFT — Top opportunities */}
        <div className="xl:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Zap className="text-accent" size={15} />
              <h2 className="text-ink font-bold text-lg tracking-tight">Top opportunities</h2>
              <span className="badge bg-overlay text-ink-3 border border-edge">{opportunities.length}</span>
            </div>
            <Link
              to="/opportunities"
              className="text-xs text-accent hover:text-accent-hover font-medium flex items-center gap-1"
            >
              See all <ArrowRight size={12} />
            </Link>
          </div>

          {opportunities.length === 0 ? (
            <div className="bg-surface border border-edge border-dashed rounded-lg p-10 text-center">
              <Zap className="text-ink-4 mx-auto mb-3" size={24} />
              <p className="text-sm text-ink-2 font-medium">No opportunities yet</p>
              <p className="text-xs text-ink-4 mt-1">Run the pipeline to discover your first set.</p>
              <Link to="/search" className="btn-primary text-xs mt-4 inline-flex">
                Run pipeline
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {opportunities.slice(0, 6).map(opp => (
                <OpportunityCard key={opp.id} opp={opp} />
              ))}
            </div>
          )}
        </div>

        {/* RIGHT — AI Picks + Research Gaps stacked */}
        <div className="xl:col-span-1 space-y-5">
          <Panel icon={Sparkles} title="AI picks" accent="text-warning">
            <AIRecommendationsPanel />
          </Panel>

          <Panel icon={FileText} title="Research gaps" accent="text-success">
            <ResearchGapSummary />
          </Panel>
        </div>
      </div>

      {/* Bottom row: 4 even widgets */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">

        <Panel icon={Clock} title="Timeline">
          <InnovationTimeline />
        </Panel>

        <Panel icon={Bell} title="Alerts" accent="text-warning">
          <AlertsPanel />
        </Panel>

        <Panel
          icon={TrendingUp}
          title="Emerging trends"
          accent="text-success"
          action={
            <Link to="/reports" className="text-2xs text-accent hover:text-accent-hover font-medium">
              View all
            </Link>
          }
        >
          <div className="space-y-2.5">
            {trends.length === 0 ? (
              <p className="text-xs text-ink-4 text-center py-4">No trends yet.</p>
            ) : (
              trends.slice(0, 6).map(trend => {
                const growth = trend.growth_rate ?? 0;
                const arrow = trend.label === 'emerging' ? '⚡'
                            : trend.label === 'rising' ? '↑'
                            : trend.label === 'declining' ? '↓'
                            : trend.label === 'new' ? '★'
                            : '·';
                const arrowColor = trend.label === 'emerging' ? 'text-warning'
                                 : trend.label === 'rising' ? 'text-success'
                                 : trend.label === 'declining' ? 'text-danger'
                                 : trend.label === 'new' ? 'text-accent'
                                 : 'text-ink-4';
                return (
                  <div key={trend.id} className="flex items-center gap-3">
                    <span className="text-xs text-ink-2 truncate flex-1">{trend.name}</span>
                    <span className={`text-xs font-mono ${arrowColor} w-3 text-center flex-shrink-0`} title={
                      trend.label === 'emerging' ? 'Emerging (fast growth)'
                      : trend.label === 'new' ? 'New this week'
                      : trend.label === 'rising' ? `Rising (${(growth*100).toFixed(0)}%)`
                      : trend.label === 'declining' ? `Declining (${(growth*100).toFixed(0)}%)`
                      : 'Stable'
                    }>
                      {arrow}
                    </span>
                    <div className="w-14 h-1 bg-overlay rounded-full overflow-hidden flex-shrink-0">
                      <div className="h-full bg-success" style={{ width: `${trend.trend_score * 100}%` }} />
                    </div>
                    <span className="text-2xs font-mono tabular-nums text-ink-4 w-8 text-right flex-shrink-0">
                      {trend.trend_score.toFixed(2)}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </Panel>

        <Panel icon={SearchIcon} title="Recent searches" accent="text-ink-3">
          <div className="space-y-2">
            {searchHistory.length === 0 ? (
              <p className="text-xs text-ink-4 text-center py-3">No searches yet.</p>
            ) : (
              searchHistory.slice(0, 6).map((s: any) => (
                <div key={s.id} className="flex items-center justify-between gap-3 py-1.5 border-b border-edge-subtle last:border-0">
                  <span className="text-xs text-ink-2 truncate flex-1">{s.query}</span>
                  <span className="text-2xs font-mono text-ink-4 flex-shrink-0">{s.results_count}</span>
                </div>
              ))
            )}
          </div>
        </Panel>

      </div>
    </div>
  );
}
