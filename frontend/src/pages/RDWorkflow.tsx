import { useState } from 'react';
import { getRDFlow } from '../services/api';
import { Loader2, Factory, Search, Cpu, BookOpen, TrendingUp, Zap } from 'lucide-react';

const INDUSTRIES = [
  '', 'Healthcare', 'Manufacturing', 'Education', 'Finance', 'Cybersecurity',
  'Transportation', 'Energy', 'Agriculture', 'Software', 'Robotics',
  'Aerospace', 'Environment', 'Defense', 'Other',
];

export default function RDWorkflow() {
  const [problem, setProblem] = useState('');
  const [industry, setIndustry] = useState('');
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try {
      const d = await getRDFlow(problem || undefined, industry || undefined, 15);
      setData(d);
    } catch { setData(null); }
    finally { setLoading(false); }
  };

  return (
    <div className="p-6 lg:p-8 max-w-[1400px] mx-auto">
      <div className="mb-6 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-warning/10 flex items-center justify-center shadow-[inset_0_1px_0_0_rgb(255_255_255/0.05)]">
          <Factory className="text-warning" size={18} />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-ink tracking-tight">R&D workflow</h1>
          <p className="text-sm text-ink-3">Industry problem → technology & research landscape → innovation opportunities.</p>
        </div>
      </div>

      <div className="card p-4 mb-6 flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-4" size={14} />
          <input
            type="text"
            value={problem}
            onChange={e => setProblem(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !loading && run()}
            placeholder="Industry problem (e.g. real-time defect detection under changing conditions)…"
            className="input pl-8 text-sm"
          />
        </div>
        <select value={industry} onChange={e => setIndustry(e.target.value)} className="input text-sm md:w-48">
          {INDUSTRIES.map(i => <option key={i} value={i}>{i || 'Any industry'}</option>)}
        </select>
        <button onClick={run} disabled={loading} className="btn-primary text-xs whitespace-nowrap">
          {loading ? <Loader2 className="animate-spin" size={13} /> : <Factory size={13} />}
          {loading ? 'Analyzing…' : 'Analyze landscape'}
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="animate-spin text-accent" size={28} />
        </div>
      )}

      {!loading && data && data.profile_count === 0 && (
        <div className="bg-surface border border-edge border-dashed rounded-lg p-12 text-center">
          <Factory className="text-ink-4 mx-auto mb-3" size={24} />
          <p className="text-sm text-ink-2 font-medium">No matching industry problems found</p>
          <p className="text-xs text-ink-4 mt-1">Try a broader query or leave the fields blank for an overview.</p>
        </div>
      )}

      {!loading && data && data.profile_count > 0 && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            {[
              { l: 'Profiles scanned', v: data.profile_count, c: 'text-ink' },
              { l: 'Technologies',     v: data.technologies?.length || 0, c: 'text-accent' },
              { l: 'Research papers',  v: data.research?.length || 0,     c: 'text-success' },
              { l: 'Opportunities',    v: data.opportunities?.length || 0, c: 'text-warning' },
            ].map(s => (
              <div key={s.l} className="card p-4">
                <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2">{s.l}</p>
                <p className={`text-2xl font-semibold font-mono tabular-nums ${s.c}`}>{s.v}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div className="card p-5">
              <div className="flex items-center gap-2 mb-4">
                <Cpu size={14} className="text-accent" />
                <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Technology landscape</h2>
              </div>
              {data.technologies?.length ? (
                <div className="flex flex-wrap gap-2">
                  {data.technologies.map((t: any) => (
                    <div key={t.name} className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-accent/[0.08] border border-accent/30">
                      <span className="text-xs text-accent font-medium">{t.name}</span>
                      <span className="text-2xs text-ink-4">{t.avg_confidence?.toFixed(2)}</span>
                      {t.stages?.length > 0 && (
                        <span className="text-2xs text-ink-4 italic">{t.stages.join('/')}</span>
                      )}
                    </div>
                  ))}
                </div>
              ) : <p className="text-xs text-ink-4 italic">No technologies linked.</p>}
            </div>

            <div className="card p-5">
              <div className="flex items-center gap-2 mb-4">
                <BookOpen size={14} className="text-success" />
                <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Research landscape</h2>
              </div>
              {data.research?.length ? (
                <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
                  {data.research.map((p: any) => (
                    <div key={p.arxiv_id} className="pb-2 border-b border-edge-subtle last:border-0 last:pb-0">
                      <div className="flex items-start justify-between gap-3">
                        <a
                          href={p.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-ink-2 leading-snug flex-1 hover:text-accent transition-colors"
                        >
                          {p.title}
                        </a>
                        <span className="text-2xs text-ink-4 font-mono flex-shrink-0">
                          {p.relevance_score?.toFixed(2)}
                        </span>
                      </div>
                      {p.results_summary && (
                        <p className="text-2xs text-ink-3 mt-1 leading-relaxed">{p.results_summary}</p>
                      )}
                      {p.research_methods?.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1.5">
                          {p.research_methods.slice(0, 4).map((m: string, k: number) => (
                            <span key={k} className="badge bg-accent/10 text-accent border border-accent/30">{m}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : <p className="text-xs text-ink-4 italic">No research papers linked.</p>}
            </div>

            <div className="card p-5">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp size={14} className="text-warning" />
                <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Emerging trends</h2>
              </div>
              {data.trends?.length ? (
                <div className="space-y-2">
                  {data.trends.map((t: any) => (
                    <div key={t.name} className="flex items-center gap-3">
                      <span className="text-xs text-ink-2 truncate flex-1">{t.name}</span>
                      <div className="w-20 h-1 bg-overlay rounded-full overflow-hidden flex-shrink-0">
                        <div className="h-full bg-warning" style={{ width: `${(t.trend_score || 0) * 100}%` }} />
                      </div>
                      <span className="text-2xs font-mono tabular-nums text-ink-4 w-8 text-right flex-shrink-0">
                        {t.trend_score?.toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : <p className="text-xs text-ink-4 italic">No matching trends.</p>}
            </div>

            <div className="card p-5">
              <div className="flex items-center gap-2 mb-4">
                <Zap size={14} className="text-warning" />
                <h2 className="text-xs font-medium text-ink uppercase tracking-wider">Innovation opportunities</h2>
              </div>
              {data.opportunities?.length ? (
                <div className="space-y-2">
                  {data.opportunities.map((o: any) => (
                    <a
                      key={o.id}
                      href={`/opportunities/${o.id}`}
                      className="flex items-start justify-between gap-3 py-2 px-2 -mx-2 rounded-md hover:bg-overlay transition-colors group"
                    >
                      <span className="text-xs text-ink-2 leading-snug flex-1 group-hover:text-accent transition-colors line-clamp-2">
                        {o.title}
                      </span>
                      <span className="text-xs font-mono text-accent flex-shrink-0">
                        {o.opportunity_score?.toFixed(2)}
                      </span>
                    </a>
                  ))}
                </div>
              ) : <p className="text-xs text-ink-4 italic">No opportunities found.</p>}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
