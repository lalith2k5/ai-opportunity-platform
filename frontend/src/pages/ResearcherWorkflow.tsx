import { useState } from 'react';
import { getResearcherFlow } from '../services/api';
import { Loader2, FlaskConical, Search, Cpu, BookOpen, AlertCircle, TrendingUp, Target } from 'lucide-react';

function Chip({ children, accent = 'bg-overlay text-ink-3 border-edge' }: any) {
  return <span className={`badge ${accent}`}>{children}</span>;
}

export default function ResearcherWorkflow() {
  const [topic, setTopic] = useState('');
  const [chains, setChains] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [ran, setRan] = useState(false);

  const run = async () => {
    setLoading(true); setRan(true);
    try {
      const data = await getResearcherFlow(topic || undefined, 10);
      setChains(data.chains || []);
    } catch { setChains([]); }
    finally { setLoading(false); }
  };

  return (
    <div className="p-6 lg:p-8 max-w-[1200px] mx-auto">
      <div className="mb-6 flex items-center gap-3">
        <div className="w-8 h-8 rounded-md bg-accent/10 flex items-center justify-center">
          <FlaskConical className="text-accent" size={16} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight">Researcher workflow</h1>
          <p className="text-sm text-ink-3">Topic → problems → research → limitations → gaps → opportunities.</p>
        </div>
      </div>

      <div className="bg-surface border border-edge rounded-lg p-4 mb-6 flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-4" size={14} />
          <input
            type="text"
            value={topic}
            onChange={e => setTopic(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !loading && run()}
            placeholder="Research topic (e.g. federated learning, graph neural networks)…"
            className="input pl-8 text-sm"
          />
        </div>
        <button onClick={run} disabled={loading} className="btn-primary text-xs whitespace-nowrap">
          {loading ? <Loader2 className="animate-spin" size={13} /> : <FlaskConical size={13} />}
          {loading ? 'Searching…' : 'Find research chains'}
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="animate-spin text-accent" size={28} />
        </div>
      )}

      {!loading && ran && chains.length === 0 && (
        <div className="bg-surface border border-edge border-dashed rounded-lg p-12 text-center">
          <FlaskConical className="text-ink-4 mx-auto mb-3" size={24} />
          <p className="text-sm text-ink-2 font-medium">No chains matched</p>
          <p className="text-xs text-ink-4 mt-1">Try a broader topic or leave the field blank to see the top-scoring clusters.</p>
        </div>
      )}

      {!loading && chains.length > 0 && (
        <div className="space-y-5">
          {chains.map((c, i) => (
            <div key={i} className="bg-surface border border-edge rounded-lg p-5">
              <div className="flex items-start justify-between gap-4 mb-4 pb-4 border-b border-edge-subtle">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Target size={13} className="text-warning" />
                    <span className="text-2xs text-ink-4 uppercase tracking-wider">Problem cluster</span>
                    <span className="text-2xs font-mono text-ink-4">#{c.cluster.id}</span>
                  </div>
                  <h2 className="text-ink font-semibold text-sm leading-snug">{c.cluster.title}</h2>
                  <p className="text-xs text-ink-3 mt-1 leading-relaxed">{c.cluster.description}</p>
                  {c.cluster.keywords?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {c.cluster.keywords.slice(0, 8).map((k: string) => <Chip key={k}>{k}</Chip>)}
                    </div>
                  )}
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="text-2xl font-bold font-mono tabular-nums text-warning leading-none">
                    {c.cluster.demand_score.toFixed(2)}
                  </p>
                  <p className="text-2xs text-ink-4 uppercase tracking-wider mt-1">Demand</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Cpu size={11} /> Technologies ({c.technologies?.length || 0})
                  </p>
                  {c.technologies?.length ? (
                    <div className="flex flex-wrap gap-1.5">
                      {c.technologies.map((t: any, j: number) => (
                        <Chip key={j} accent="bg-accent/10 text-accent border-accent/30">
                          {t.name}
                          <span className="text-2xs opacity-70 ml-1">{t.stage}</span>
                        </Chip>
                      ))}
                    </div>
                  ) : <p className="text-xs text-ink-4 italic">No technologies linked yet.</p>}

                  {c.emerging_trend && (
                    <div className="mt-4">
                      <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <TrendingUp size={11} /> Emerging trend
                      </p>
                      <Chip accent="bg-warning/15 text-warning border-warning/30">
                        {c.emerging_trend.name} ({c.emerging_trend.score?.toFixed(2)})
                      </Chip>
                    </div>
                  )}
                </div>

                <div>
                  <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <BookOpen size={11} /> Existing research ({c.papers?.length || 0})
                  </p>
                  {c.papers?.length ? (
                    <ul className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                      {c.papers.map((p: any, j: number) => (
                        <li key={j} className="text-xs text-ink-2 leading-snug">
                          <a href={p.url} target="_blank" rel="noreferrer" className="hover:text-accent transition-colors">
                            <span className="text-ink-4 font-mono mr-1.5">{p.relevance_score?.toFixed(2)}</span>
                            {p.title}
                          </a>
                        </li>
                      ))}
                    </ul>
                  ) : <p className="text-xs text-ink-4 italic">No papers linked yet.</p>}
                </div>

                {c.limitations?.length > 0 && (
                  <div className="md:col-span-2">
                    <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <AlertCircle size={11} /> Known limitations ({c.limitations.length})
                    </p>
                    <ul className="space-y-1">
                      {c.limitations.slice(0, 6).map((L: string, j: number) => (
                        <li key={j} className="text-xs text-ink-2 leading-relaxed pl-3 border-l-2 border-warning/40">
                          {L}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {c.gaps?.length > 0 && (
                  <div className="md:col-span-2">
                    <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <AlertCircle size={11} /> Potential gaps ({c.gaps.length})
                    </p>
                    <div className="space-y-2">
                      {c.gaps.map((g: any) => (
                        <div key={g.id} className="flex items-start justify-between gap-3">
                          <p className="text-xs text-ink-2 leading-snug flex-1">{g.title}</p>
                          <span className="text-xs font-mono text-success flex-shrink-0">
                            {g.gap_score?.toFixed(2)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {c.opportunities?.length > 0 && (
                  <div className="md:col-span-2 pt-3 border-t border-edge-subtle">
                    <p className="text-2xs text-ink-4 uppercase tracking-wider mb-2">Related opportunities</p>
                    <div className="space-y-1.5">
                      {c.opportunities.map((o: any) => (
                        <a
                          key={o.id}
                          href={`/opportunities/${o.id}`}
                          className="flex items-center gap-3 px-2.5 py-2 rounded-md hover:bg-overlay transition-colors group"
                        >
                          <span className="text-xs text-ink-2 leading-snug truncate flex-1 group-hover:text-accent transition-colors">
                            {o.title}
                          </span>
                          <span className="text-xs font-mono text-accent flex-shrink-0">
                            {o.opportunity_score?.toFixed(2)}
                          </span>
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
