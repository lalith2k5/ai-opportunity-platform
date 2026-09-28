import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { getOpportunities, getProblemProfileStats, type Opportunity } from '../services/api';
import OpportunityCard from '../components/OpportunityCard';
import { Loader2, GraduationCap, Search, Rocket, Sparkles } from 'lucide-react';

const DOMAINS = [
  'Healthcare', 'Education', 'Cybersecurity', 'Manufacturing',
  'Energy', 'Transportation', 'Environment', 'Software',
  'Robotics', 'Agriculture', 'Finance', 'Other',
];

export default function StudentWorkflow() {
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [stats, setStats] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [domain, setDomain] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    Promise.all([
      getOpportunities(),
      getProblemProfileStats().catch(() => ({ by_domain: {} })),
    ]).then(([o, s]: [Opportunity[], any]) => {
      setOpps(o);
      setStats(s.by_domain || {});
    }).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    let list = [...opps];
    if (domain) {
      const d = domain.toLowerCase();
      list = list.filter(o =>
        (o.domain || '').toLowerCase().includes(d) ||
        (o.industry || '').toLowerCase().includes(d) ||
        (o.related_technologies || []).some(t => t.toLowerCase().includes(d)) ||
        (o.title || '').toLowerCase().includes(d) ||
        (o.description || '').toLowerCase().includes(d)
      );
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(o =>
        (o.title || '').toLowerCase().includes(q) ||
        (o.description || '').toLowerCase().includes(q)
      );
    }
    return list.sort((a, b) => b.feasibility_score - a.feasibility_score).slice(0, 18);
  }, [opps, domain, search]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="animate-spin text-accent" size={32} />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-[1500px] mx-auto">
      <div className="mb-8 flex items-center gap-3">
        <div className="w-8 h-8 rounded-md bg-accent/10 flex items-center justify-center">
          <GraduationCap className="text-accent" size={16} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">Student workflow</h1>
          <p className="text-sm text-ink-3">Pick a domain, see buildable opportunities and project directions.</p>
        </div>
      </div>

      <div className="bg-surface border border-edge rounded-lg p-5 mb-6">
        <p className="text-2xs text-ink-4 uppercase tracking-wider mb-3">Step 1 — choose a domain</p>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setDomain('')}
            className={`px-3 py-1.5 text-xs rounded-md border transition-all ${
              domain === ''
                ? 'bg-accent/10 border-accent/50 text-ink font-medium'
                : 'bg-canvas border-edge text-ink-2 hover:border-edge-strong'
            }`}
          >
            All domains
          </button>
          {DOMAINS.map(d => (
            <button
              key={d}
              onClick={() => setDomain(d)}
              className={`px-3 py-1.5 text-xs rounded-md border transition-all ${
                domain === d
                  ? 'bg-accent/10 border-accent/50 text-ink font-medium'
                  : 'bg-canvas border-edge text-ink-2 hover:border-edge-strong'
              }`}
            >
              {d}
              {stats[d] ? <span className="ml-1.5 text-ink-4 font-mono">{stats[d]}</span> : null}
            </button>
          ))}
        </div>

        <div className="mt-4 relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-4" size={14} />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Or search by keyword…"
            className="input pl-8 text-sm"
          />
        </div>
      </div>

      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Rocket size={15} className="text-success" />
          <h2 className="text-ink font-semibold text-base tracking-tight">
            Buildable opportunities
          </h2>
          <span className="badge bg-overlay text-ink-3 border border-edge">
            {filtered.length}
          </span>
        </div>
        {domain && (
          <p className="text-xs text-ink-4">Ranked by feasibility · filtered to <span className="text-ink-2">{domain}</span></p>
        )}
      </div>

      {filtered.length === 0 ? (
        <div className="bg-surface border border-edge border-dashed rounded-lg p-12 text-center">
          <GraduationCap className="text-ink-4 mx-auto mb-3" size={24} />
          <p className="text-sm text-ink-2 font-medium">No opportunities match your filter</p>
          <p className="text-xs text-ink-4 mt-1">Try a different domain or run a fresh pipeline to populate this pool.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 mb-8">
            {filtered.slice(0, 9).map(o => <OpportunityCard key={o.id} opp={o} />)}
          </div>

          <div className="flex items-center gap-2 mb-4">
            <Sparkles size={15} className="text-accent" />
            <h2 className="text-ink font-semibold text-base tracking-tight">
              Suggested project directions
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {filtered.filter(o => o.suggested_project_direction).slice(0, 6).map(o => (
              <Link
                key={o.id}
                to={`/opportunities/${o.id}`}
                className="group block bg-surface border border-edge hover:border-accent/40 rounded-lg p-4 transition-colors"
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <p className="text-xs text-ink-2 font-medium leading-snug line-clamp-2 flex-1 group-hover:text-accent transition-colors">
                    {o.title}
                  </p>
                  <span className="text-xs font-mono tabular-nums text-accent flex-shrink-0">
                    {o.feasibility_score.toFixed(2)}
                  </span>
                </div>
                <p className="text-xs text-ink-3 leading-relaxed line-clamp-3">
                  {o.suggested_project_direction}
                </p>
              </Link>
            ))}
            {filtered.filter(o => o.suggested_project_direction).length === 0 && (
              <p className="text-xs text-ink-4 italic md:col-span-2">
                No project directions yet — run a fresh pipeline to enrich the newest opportunities.
              </p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
