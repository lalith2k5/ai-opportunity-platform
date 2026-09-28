import { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { getOpportunities, getRecentRecommendations, type Opportunity, type RecommendationRow } from '../services/api';
import { useAuth } from '../context/AuthContext';
import OpportunityCard from '../components/OpportunityCard';
import {
  Loader2, Sparkles, Rocket, FlaskConical, Gem, TrendingUp,
  ArrowRight, Target, Zap, Info,
} from 'lucide-react';

/* ---------- Role-aware weighting ---------- */
type RoleKey = 'student' | 'researcher' | 'entrepreneur' | 'investor' | 'admin';

const ROLE_WEIGHTS: Record<RoleKey, Partial<Record<keyof Opportunity, number>>> = {
  student:      { opportunity_score: 0.4, feasibility_score: 0.3, trend_score: 0.2, competition_score: -0.1 },
  researcher:   { opportunity_score: 0.3, research_gap_score: 0.5, trend_score: 0.1, market_readiness_score: -0.1 },
  entrepreneur: { opportunity_score: 0.4, market_readiness_score: 0.3, feasibility_score: 0.2, competition_score: -0.1 },
  investor:     { opportunity_score: 0.4, trend_score: 0.3, market_readiness_score: 0.3 },
  admin:        { opportunity_score: 1.0 },
};

const ROLE_LABELS: Record<RoleKey, { title: string; blurb: string }> = {
  student:      { title: 'Student',      blurb: 'Feasible projects, emerging technologies, and startup ideas you can actually build.' },
  researcher:   { title: 'Researcher',   blurb: 'High research-gap opportunities and under-explored areas worth a paper.' },
  entrepreneur: { title: 'Entrepreneur', blurb: 'Buildable ideas with real market demand and clear technical paths.' },
  investor:     { title: 'Investor',     blurb: 'High-growth trends and market-ready categories with strong momentum.' },
  admin:        { title: 'All roles',    blurb: 'Every opportunity ranked by overall score.' },
};

function scoreForRole(opp: Opportunity, role: RoleKey): number {
  const weights = ROLE_WEIGHTS[role] || ROLE_WEIGHTS.admin;
  let sum = 0;
  for (const [key, w] of Object.entries(weights)) {
    const v = (opp as any)[key] as number;
    if (typeof v === 'number') sum += v * (w as number);
  }
  return sum;
}

/* ---------- Shelf ---------- */
function Shelf({
  icon: Icon,
  title,
  subtitle,
  items,
  accent = 'text-accent',
  emptyText = 'Nothing here yet — run a pipeline to populate.',
}: {
  icon: any;
  title: string;
  subtitle: string;
  items: Opportunity[];
  accent?: string;
  emptyText?: string;
}) {
  return (
    <section className="mb-8">
      <div className="flex items-center gap-2 mb-1">
        <Icon size={15} className={accent} />
        <h2 className="text-ink font-semibold text-base tracking-tight">{title}</h2>
        <span className="badge bg-overlay text-ink-3 border border-edge ml-1">{items.length}</span>
      </div>
      <p className="text-xs text-ink-4 mb-4">{subtitle}</p>

      {items.length === 0 ? (
        <div className="border border-edge border-dashed rounded-lg p-6 text-center bg-surface/40">
          <p className="text-xs text-ink-4">{emptyText}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {items.map(o => <OpportunityCard key={o.id} opp={o} />)}
        </div>
      )}
    </section>
  );
}

/* ---------- Top pick hero card ---------- */
function TopPickCard({ opp, rank, reason }: { opp: Opportunity; rank: number; reason: string }) {
  return (
    <Link
      to={`/opportunities/${opp.id}`}
      className="group relative block bg-surface border border-edge rounded-lg p-5 hover:border-accent/50 hover:bg-overlay transition-all"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <span className="w-6 h-6 rounded-md bg-accent text-accent-fg flex items-center justify-center text-2xs font-bold">
            {rank}
          </span>
          <span className="badge bg-accent/10 text-accent border border-accent/30">Top pick</span>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold font-mono tabular-nums text-accent leading-none">
            {opp.opportunity_score.toFixed(2)}
          </p>
          <p className="text-2xs text-ink-4 uppercase tracking-wider mt-1">Score</p>
        </div>
      </div>

      <h3 className="text-ink font-semibold text-sm leading-snug line-clamp-2 mb-2 group-hover:text-accent transition-colors">
        {opp.title}
      </h3>
      <p className="text-xs text-ink-3 leading-relaxed line-clamp-2 mb-4">{opp.description}</p>

      <div className="flex items-start gap-2 px-3 py-2.5 bg-accent/[0.06] border border-accent/20 rounded-md mb-3">
        <Sparkles size={12} className="text-accent flex-shrink-0 mt-0.5" />
        <p className="text-2xs text-ink-2 leading-snug">{reason}</p>
      </div>

      <div className="flex items-center justify-between text-2xs">
        <span className="text-ink-4 font-mono">
          Demand {opp.demand_score.toFixed(2)} · Gap {opp.research_gap_score.toFixed(2)} · Feasibility {opp.feasibility_score.toFixed(2)}
        </span>
        <ArrowRight size={11} className="text-ink-4 group-hover:text-accent transition-colors" />
      </div>
    </Link>
  );
}

/* ---------- Page ---------- */
export default function Recommendations() {
  const { user } = useAuth();
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [recentRecs, setRecentRecs] = useState<RecommendationRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOpportunities().then(setOpps).finally(() => setLoading(false));
    getRecentRecommendations(12)
      .then(d => setRecentRecs(d.recommendations || []))
      .catch(() => setRecentRecs([]));
  }, []);

  const role = ((user?.role || 'student') as RoleKey);
  const roleInfo = ROLE_LABELS[role] || ROLE_LABELS.student;

  const {
    topPicks,
    roleMatched,
    buildable,
    researchGold,
    hiddenGems,
    risingStars,
  } = useMemo(() => {
    const sortedByRole = [...opps].sort(
      (a, b) => scoreForRole(b, role) - scoreForRole(a, role),
    );

    // Top 3 overall — plus generate a reason for each
    const top = [...opps]
      .sort((a, b) => b.opportunity_score - a.opportunity_score)
      .slice(0, 3)
      .map(o => ({
        opp: o,
        reason: (() => {
          const parts: string[] = [];
          if (o.research_gap_score > 0.5) parts.push('high research gap');
          if (o.demand_score > 0.6) parts.push('strong market demand');
          if (o.trend_score > 0.6) parts.push('rising tech trend');
          if (o.feasibility_score > 0.6) parts.push('buildable today');
          return parts.length
            ? `Standout due to ${parts.slice(0, 2).join(' and ')}.`
            : 'Highest composite score across all factors.';
        })(),
      }));

    return {
      topPicks: top,
      roleMatched: sortedByRole.filter(o => o.opportunity_score >= 0.5).slice(0, 6),
      buildable: [...opps]
        .filter(o => o.feasibility_score >= 0.6 && o.market_readiness_score >= 0.5)
        .sort((a, b) => (b.feasibility_score + b.market_readiness_score) - (a.feasibility_score + a.market_readiness_score))
        .slice(0, 6),
      researchGold: [...opps]
        .filter(o => o.research_gap_score >= 0.5)
        .sort((a, b) => b.research_gap_score - a.research_gap_score)
        .slice(0, 6),
      hiddenGems: [...opps]
        .filter(o => o.opportunity_score >= 0.55 && o.competition_score <= 0.5)
        .sort((a, b) => b.opportunity_score - a.opportunity_score)
        .slice(0, 6),
      risingStars: [...opps]
        .filter(o => o.trend_score >= 0.6)
        .sort((a, b) => b.trend_score - a.trend_score)
        .slice(0, 6),
    };
  }, [opps, role]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="animate-spin text-accent" size={32} />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-[1500px] mx-auto">

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-8 h-8 rounded-md bg-accent/10 flex items-center justify-center">
            <Sparkles className="text-accent" size={16} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-ink tracking-tight">
              Recommendations for you
            </h1>
            <p className="text-sm text-ink-3 mt-0.5">
              Curated picks tuned to your <span className="text-ink-2 font-medium capitalize">{roleInfo.title}</span> profile
            </p>
          </div>
        </div>

        <div className="mt-4 px-4 py-3 bg-accent/[0.05] border border-accent/20 rounded-lg flex items-start gap-3">
          <Info size={14} className="text-accent flex-shrink-0 mt-0.5" />
          <p className="text-xs text-ink-2 leading-relaxed">{roleInfo.blurb}</p>
        </div>
      </div>

      {recentRecs.length > 0 && (
        <section className="mb-10">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles size={15} className="text-accent" />
            <h2 className="text-ink font-semibold text-base tracking-tight">Recently generated</h2>
            <span className="badge bg-overlay text-ink-3 border border-edge ml-1">{recentRecs.length}</span>
          </div>
          <p className="text-xs text-ink-4 mb-4">
            The newest AI-generated research and project directions across the platform.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {recentRecs.slice(0, 9).map(r => (
              <Link
                key={r.id}
                to={r.opportunity_id ? `/opportunities/${r.opportunity_id}` : '#'}
                className="group block bg-surface border border-edge rounded-lg p-4 hover:border-accent/40 transition-colors"
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <p className="text-xs text-ink font-medium leading-snug line-clamp-2 flex-1 group-hover:text-accent transition-colors">
                    {r.opportunity?.title || `Opportunity #${r.opportunity_id}`}
                  </p>
                  {r.score_at_time !== null && (
                    <span className="text-2xs font-mono tabular-nums text-accent flex-shrink-0">
                      {r.score_at_time?.toFixed(2)}
                    </span>
                  )}
                </div>
                {r.suggested_research_direction && (
                  <p className="text-2xs text-ink-3 leading-relaxed line-clamp-3 mb-2">
                    {r.suggested_research_direction}
                  </p>
                )}
                {r.suggested_project_direction && (
                  <p className="text-2xs text-ink-4 leading-relaxed line-clamp-2 pt-2 border-t border-edge-subtle">
                    {r.suggested_project_direction}
                  </p>
                )}
              </Link>
            ))}
          </div>
        </section>
      )}

      {opps.length === 0 ? (
        <div className="bg-surface border border-edge border-dashed rounded-lg p-12 text-center">
          <Sparkles className="text-ink-4 mx-auto mb-3" size={24} />
          <p className="text-sm text-ink-2 font-medium">No opportunities yet</p>
          <p className="text-xs text-ink-4 mt-1">Run the pipeline a few times to populate recommendations.</p>
          <Link to="/search" className="btn-primary text-xs mt-4 inline-flex">
            Run pipeline
          </Link>
        </div>
      ) : (
        <>
          {/* Top picks hero */}
          {topPicks.length > 0 && (
            <section className="mb-10">
              <div className="flex items-center gap-2 mb-1">
                <Target size={15} className="text-warning" />
                <h2 className="text-ink font-semibold text-base tracking-tight">Today's top picks</h2>
              </div>
              <p className="text-xs text-ink-4 mb-4">
                The three highest-scoring opportunities right now, with the standout signals for each.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {topPicks.map((p, i) => (
                  <TopPickCard key={p.opp.id} opp={p.opp} rank={i + 1} reason={p.reason} />
                ))}
              </div>
            </section>
          )}

          {/* Role-matched */}
          <Shelf
            icon={Zap}
            title={`Best match for ${roleInfo.title.toLowerCase()}s`}
            subtitle="Ranked by a scoring model weighted for your role."
            items={roleMatched}
            accent="text-accent"
          />

          {/* Buildable */}
          <Shelf
            icon={Rocket}
            title="Ready to build"
            subtitle="High technical feasibility + strong market readiness. Practical starting points."
            items={buildable}
            accent="text-success"
            emptyText="No opportunities with both high feasibility and market readiness yet."
          />

          {/* Research gold */}
          <Shelf
            icon={FlaskConical}
            title="Research goldmine"
            subtitle="Large research coverage gaps — promising territory for papers and theses."
            items={researchGold}
            accent="text-purple-500"
            emptyText="No opportunities with significant research gaps detected yet."
          />

          {/* Hidden gems */}
          <Shelf
            icon={Gem}
            title="Hidden gems"
            subtitle="Strong overall scores paired with low competition. Less crowded territory."
            items={hiddenGems}
            accent="text-warning"
            emptyText="No low-competition, high-score opportunities yet."
          />

          {/* Rising stars */}
          <Shelf
            icon={TrendingUp}
            title="Rising stars"
            subtitle="Opportunities riding strong technology trend signals."
            items={risingStars}
            accent="text-sky-500"
            emptyText="No high-trend opportunities detected yet."
          />

          {/* Footer CTA */}
          <div className="mt-10 bg-surface border border-edge rounded-lg p-5 flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-start gap-3">
              <Sparkles size={16} className="text-accent flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-ink font-medium">Want personalized deep dives?</p>
                <p className="text-xs text-ink-3 mt-0.5">
                  Ask the AI assistant follow-up questions about any recommendation.
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Link to="/opportunities" className="btn-secondary text-xs">
                All opportunities
              </Link>
              <Link to="/chat" className="btn-primary text-xs">
                <Sparkles size={13} /> Ask AI
              </Link>
            </div>
          </div>
        </>
      )}

    </div>
  );
}
