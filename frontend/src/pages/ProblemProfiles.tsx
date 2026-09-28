import { useEffect, useState } from 'react';
import { Loader2, Target, Building2, ExternalLink, Filter, Search } from 'lucide-react';
import { api } from '../services/api';

interface ProblemProfile {
  id: number;
  organization: string;
  problem_title: string;
  problem_description: string;
  industry_domain: string;
  problem_type: string;
  technology_stage: 'used' | 'exploring' | 'potential';
  required_technology: string[];
  current_approach: string;
  known_limitations: string;
  expected_outcome: string;
  source: string;
  source_url: string;
  keywords: string[];
  problem_status: string;
  student_suitability: 'high' | 'medium' | 'low';
  extracted_by: string;
  affected_stakeholders?: string[];
  evidence?: string[];
  confidence?: number | null;
  created_at: string;
}

interface Stats {
  total: number;
  by_domain: Record<string, number>;
  by_suitability: Record<string, number>;
  by_source: Record<string, number>;
}

const STAGE_COLORS: Record<string, string> = {
  used: 'bg-success/15 text-success border-success/30',
  exploring: 'bg-warning/15 text-warning border-warning/30',
  potential: 'bg-accent/15 text-accent border-accent/30',
};

const SUITABILITY_COLORS: Record<string, string> = {
  high: 'bg-success/15 text-success border-success/30',
  medium: 'bg-warning/15 text-warning border-warning/30',
  low: 'bg-ink-4/15 text-ink-3 border-edge',
};

export default function ProblemProfiles() {
  const [items, setItems] = useState<ProblemProfile[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [domain, setDomain] = useState('');
  const [suitability, setSuitability] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const params: any = { limit: 100 };
      if (domain) params.domain = domain;
      if (suitability) params.student_suitability = suitability;
      if (search) params.search = search;
      const [listRes, statsRes] = await Promise.all([
        api.get('/problem-profiles', { params }),
        api.get('/problem-profiles/stats'),
      ]);
      setItems(listRes.data.items || []);
      setStats(statsRes.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [domain, suitability]);

  const submitSearch = (e: React.FormEvent) => {
    e.preventDefault();
    load();
  };

  const domains = stats ? Object.keys(stats.by_domain).sort() : [];

  return (
    <div className="p-6 lg:p-8 max-w-[1400px] mx-auto">

      {/* Header */}
      <div className="mb-6 flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-8 h-8 rounded-md bg-accent/10 flex items-center justify-center">
              <Target className="text-accent" size={16} />
            </div>
            <h1 className="text-2xl font-bold text-ink tracking-tight">Problem Profiles</h1>
          </div>
          <p className="text-sm text-ink-3">
            Structured industry & government R&D problems — extracted from SBIR, challenge.gov and other public portals.
          </p>
        </div>
        {stats && (
          <div className="flex items-center gap-2 text-xs text-ink-3">
            <span>Total: <span className="text-ink font-mono">{stats.total}</span></span>
          </div>
        )}
      </div>

      {/* Filters */}
      <form onSubmit={submitSearch} className="bg-surface border border-edge rounded-lg p-3 mb-5 flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-4" size={14} />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search title, description, organization…"
            className="input pl-8 text-sm w-full"
          />
        </div>
        <select value={domain} onChange={e => setDomain(e.target.value)} className="input text-sm">
          <option value="">All domains</option>
          {domains.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
        <select value={suitability} onChange={e => setSuitability(e.target.value)} className="input text-sm">
          <option value="">Any suitability</option>
          <option value="high">High (student-friendly)</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <button type="submit" className="btn-primary text-xs">
          <Filter size={13} /> Apply
        </button>
      </form>

      {/* Body */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="animate-spin text-accent" size={28} />
        </div>
      ) : items.length === 0 ? (
        <div className="bg-surface border border-edge border-dashed rounded-lg p-12 text-center">
          <Target className="text-ink-4 mx-auto mb-3" size={24} />
          <p className="text-sm text-ink-2 font-medium">No problem profiles yet</p>
          <p className="text-xs text-ink-4 mt-1 max-w-md mx-auto">
            Run the pipeline — problem profiles are extracted automatically from SBIR solicitations and challenge.gov feeds.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map(p => (
            <div key={p.id} className="bg-surface border border-edge rounded-lg p-5 hover:border-accent/40 transition-colors">
              <div className="flex items-start justify-between gap-4 mb-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                    <span className={`badge ${STAGE_COLORS[p.technology_stage] || STAGE_COLORS.potential}`}>
                      {p.technology_stage}
                    </span>
                    <span className={`badge ${SUITABILITY_COLORS[p.student_suitability] || SUITABILITY_COLORS.medium}`}>
                      {p.student_suitability} suitability
                    </span>
                    <span className="badge bg-overlay text-ink-3 border border-edge">
                      {p.industry_domain}
                    </span>
                    <span className="badge bg-overlay text-ink-3 border border-edge">
                      {p.problem_type}
                    </span>
                  </div>
                  <h3 className="text-ink font-semibold text-base leading-snug">{p.problem_title}</h3>
                  <div className="flex items-center gap-1.5 mt-1 text-2xs text-ink-4">
                    <Building2 size={11} />
                    <span>{p.organization || 'Unknown org'}</span>
                    <span className="mx-1">·</span>
                    <span>{p.source}</span>
                  </div>
                </div>
                {p.source_url && (
                  <a
                    href={p.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-accent hover:text-accent-hover flex items-center gap-1 text-xs flex-shrink-0"
                  >
                    Source <ExternalLink size={11} />
                  </a>
                )}
              </div>

              <p className="text-sm text-ink-2 leading-relaxed mb-3">{p.problem_description}</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                {p.current_approach && (
                  <div>
                    <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Current approach</p>
                    <p className="text-xs text-ink-2 leading-relaxed">{p.current_approach}</p>
                  </div>
                )}
                {p.known_limitations && (
                  <div>
                    <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Known limitations</p>
                    <p className="text-xs text-ink-2 leading-relaxed">{p.known_limitations}</p>
                  </div>
                )}
              </div>

              {p.expected_outcome && (
                <div className="mb-3">
                  <p className="text-2xs text-ink-4 uppercase tracking-wider mb-1">Expected outcome</p>
                  <p className="text-xs text-ink-2 leading-relaxed">{p.expected_outcome}</p>
                </div>
              )}

              {p.required_technology?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-3 border-t border-edge-subtle">
                  {p.required_technology.map(t => (
                    <span key={t} className="badge bg-accent/10 text-accent border border-accent/30">
                      {t}
                    </span>
                  ))}
                </div>
              )}

              {p.affected_stakeholders && p.affected_stakeholders.length > 0 && (
                <div className="pt-3 mt-3 border-t border-edge-subtle">
                  <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2">Affected stakeholders</p>
                  <div className="flex flex-wrap gap-1.5">
                    {p.affected_stakeholders.slice(0, 8).map((s, i) => (
                      <span key={i} className="badge bg-overlay text-ink-3 border border-edge">{s}</span>
                    ))}
                  </div>
                </div>
              )}

              {p.evidence && p.evidence.length > 0 && (
                <div className="pt-3 mt-3 border-t border-edge-subtle">
                  <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2">Source evidence ({p.evidence.length})</p>
                  <ul className="space-y-1.5">
                    {p.evidence.slice(0, 4).map((e, i) => (
                      <li key={i} className="text-xs text-ink-2 leading-relaxed pl-3 border-l-2 border-accent/40">
                        {e}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
