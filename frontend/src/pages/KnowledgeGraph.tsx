import { useEffect, useMemo, useRef, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import {
  getKGNodes,
  getKGEdgesList,
  getKGEntityTypes,
  getKGSemanticChain,
} from '../services/api';
import {
  Loader2,
  Network,
  Filter,
  X,
  ExternalLink,
  Info,
} from 'lucide-react';

/* ---------- Colors per entity type ---------- */
const TYPE_COLORS: Record<string, string> = {
  Technology:         '#5e6ad2',
  Problem:            '#f59e0b',
  ResearchPaper:      '#10b981',
  Author:             '#8b5cf6',
  Repository:         '#06b6d4',
  Industry:           '#ec4899',
  Article:            '#f472b6',
  ResearchGap:        '#ef4444',
  StartupOpportunity: '#22c55e',
  RDLab:              '#a855f7',
  Document:           '#94a3b8',
  Keyword:            '#64748b',
  unknown:            '#6b7280',
};

const colorForType = (t: string) => TYPE_COLORS[t] || TYPE_COLORS.unknown;

const ALL_TYPES = Object.keys(TYPE_COLORS).filter(t => t !== 'unknown');

/* ---------- Types ---------- */
interface KGNode {
  id: number;
  name: string;
  type: string;
  metadata?: Record<string, any>;
}

interface KGEdge {
  source: string;
  target: string;
  relation: string;
}

interface GraphNode {
  id: string;
  name: string;
  type: string;
  metadata: Record<string, any>;
  degree: number;
  x?: number;
  y?: number;
}

interface GraphLink {
  source: string;
  target: string;
  relation: string;
}

interface ChainNeighbor {
  name: string;
  type: string;
}

/* ---------- Component ---------- */
export default function KnowledgeGraph() {
  const [loading, setLoading] = useState(true);
  const [nodes, setNodes] = useState<KGNode[]>([]);
  const [edges, setEdges] = useState<KGEdge[]>([]);
  const [typeCounts, setTypeCounts] = useState<Record<string, number>>({});
  const [activeTypes, setActiveTypes] = useState<Set<string>>(new Set(ALL_TYPES));
  const [nodeLimit, setNodeLimit] = useState(400);
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const [neighbors, setNeighbors] = useState<ChainNeighbor[]>([]);
  const [loadingNeighbors, setLoadingNeighbors] = useState(false);
  const [showFilters, setShowFilters] = useState(true);

  const fgRef = useRef<any>(null);

  /* ---------- Initial load ---------- */
  useEffect(() => {
    setLoading(true);
    Promise.all([
      getKGNodes({ limit: nodeLimit }),
      getKGEdgesList({ limit: nodeLimit * 2 }),
      getKGEntityTypes(),
    ])
      .then(([n, e, t]) => {
        setNodes(n);
        setEdges(e);
        const counts: Record<string, number> = {};
        for (const row of t) {
          counts[row.type] = row.count;
        }
        setTypeCounts(counts);
        // Default-enable all types that actually have nodes
        setActiveTypes(new Set(Object.keys(counts).filter(k => counts[k] > 0)));
      })
      .catch(err => console.error('KG load error:', err))
      .finally(() => setLoading(false));
  }, [nodeLimit]);

  /* ---------- Build graph data (filtered) ---------- */
  const graphData = useMemo(() => {
    const filteredNodes = nodes.filter(n => activeTypes.has(n.type));
    const validNames = new Set(filteredNodes.map(n => n.name));

    // Compute degree from full edge list
    const degree: Record<string, number> = {};
    for (const e of edges) {
      degree[e.source] = (degree[e.source] || 0) + 1;
      degree[e.target] = (degree[e.target] || 0) + 1;
    }

    const graphNodes: GraphNode[] = filteredNodes.map(n => ({
      id: n.name,       // force-graph links reference name
      name: n.name,
      type: n.type,
      metadata: n.metadata || {},
      degree: degree[n.name] || 0,
    }));

    const graphLinks: GraphLink[] = edges
      .filter(e => validNames.has(e.source) && validNames.has(e.target))
      .map(e => ({
        source: e.source,
        target: e.target,
        relation: e.relation,
      }));

    return { nodes: graphNodes, links: graphLinks };
  }, [nodes, edges, activeTypes]);

  /* ---------- Fetch neighbors when a node is selected ---------- */
  useEffect(() => {
    if (!selected) {
      setNeighbors([]);
      return;
    }
    setLoadingNeighbors(true);
    getKGSemanticChain(selected.name, 1)
      .then((data: any) => {
        setNeighbors(data.nodes || []);
      })
      .catch(() => setNeighbors([]))
      .finally(() => setLoadingNeighbors(false));
  }, [selected]);

  /* ---------- Zoom controls ---------- */
  const zoomIn = () => {
    if (!fgRef.current) return;
    const g = fgRef.current;
    g.zoom(g.zoom() * 1.4, 300);
  };
  const zoomOut = () => {
    if (!fgRef.current) return;
    const g = fgRef.current;
    g.zoom(g.zoom() / 1.4, 300);
  };
  const resetView = () => {
    if (!fgRef.current) return;
    fgRef.current.zoomToFit(500);
  };

  /* ---------- Filter toggle ---------- */
  const toggleType = (t: string) => {
    setActiveTypes(prev => {
      const next = new Set(prev);
      if (next.has(t)) next.delete(t);
      else next.add(t);
      return next;
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="animate-spin text-accent" size={32} />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">

      {/* Header */}
      <div className="border-b border-edge/60 glass px-6 py-4 flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center shadow-[inset_0_1px_0_0_rgb(255_255_255/0.05)]">
            <Network className="text-accent" size={18} />
          </div>
          <div>
            <h1 className="text-lg font-bold text-ink tracking-tight">Knowledge Graph</h1>
            <p className="text-2xs text-ink-4">
              {graphData.nodes.length} nodes · {graphData.links.length} edges shown
              {' · '}
              <span className="text-ink-3">
                {nodes.length} total loaded
              </span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={nodeLimit}
            onChange={e => setNodeLimit(Number(e.target.value))}
            className="input text-xs py-1.5"
            title="How many nodes to load"
          >
            <option value={200}>200 nodes</option>
            <option value={400}>400 nodes</option>
            <option value={800}>800 nodes</option>
            <option value={1500}>1500 nodes</option>
          </select>

          <button
            onClick={() => setShowFilters(s => !s)}
            className="btn-secondary text-xs"
          >
            <Filter size={13} />
            {showFilters ? 'Hide filters' : 'Show filters'}
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 flex min-h-0 relative">

        {/* Left: filter panel */}
        {showFilters && (
          <aside className="w-64 border-r border-edge/60 glass flex-shrink-0 overflow-y-auto">
            <div className="px-4 py-3 border-b border-edge-subtle">
              <p className="text-2xs font-medium text-ink-4 uppercase tracking-wider">
                Entity types
              </p>
            </div>

            <div className="p-2">
              {ALL_TYPES.map(t => {
                const count = typeCounts[t] || 0;
                if (count === 0) return null;
                const active = activeTypes.has(t);
                return (
                  <button
                    key={t}
                    onClick={() => toggleType(t)}
                    className={`w-full flex items-center justify-between gap-2 px-2.5 py-2 rounded-md text-xs transition-colors ${
                      active ? 'bg-overlay text-ink' : 'text-ink-4 hover:bg-subtle'
                    }`}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span
                        className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                        style={{ backgroundColor: colorForType(t), opacity: active ? 1 : 0.4 }}
                      />
                      <span className="truncate">{t}</span>
                    </div>
                    <span className="font-mono tabular-nums text-2xs flex-shrink-0">
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>

            <div className="border-t border-edge-subtle p-3 flex items-center gap-2">
              <button
                onClick={() => setActiveTypes(new Set(ALL_TYPES))}
                className="btn-ghost text-2xs flex-1"
              >
                All
              </button>
              <button
                onClick={() => setActiveTypes(new Set())}
                className="btn-ghost text-2xs flex-1"
              >
                None
              </button>
            </div>

            {/* Zoom controls */}
            <div className="border-t border-edge-subtle p-3">
              <p className="text-2xs font-medium text-ink-4 uppercase tracking-wider mb-2">
                View
              </p>
              <div className="flex items-center gap-1.5">
                <button onClick={zoomIn}  className="btn-secondary text-xs flex-1">+</button>
                <button onClick={zoomOut} className="btn-secondary text-xs flex-1">−</button>
                <button onClick={resetView} className="btn-secondary text-xs flex-1">Fit</button>
              </div>
            </div>
          </aside>
        )}

        {/* Center: graph canvas */}
        <div className="flex-1 relative bg-canvas overflow-hidden">
          {graphData.nodes.length === 0 ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <Network className="text-ink-4 mx-auto mb-3" size={32} />
                <p className="text-sm text-ink-3">No nodes match your filters</p>
                <button
                  onClick={() => setActiveTypes(new Set(ALL_TYPES))}
                  className="btn-primary text-xs mt-3"
                >
                  Reset filters
                </button>
              </div>
            </div>
          ) : (
            <ForceGraph2D
              ref={fgRef}
              graphData={graphData}
              backgroundColor="rgba(0,0,0,0)"
              nodeLabel={(n: GraphNode) => `${n.name} (${n.type})`}
              nodeColor={(n: GraphNode) => colorForType(n.type)}
              nodeVal={(n: GraphNode) => Math.max(1, Math.sqrt(n.degree) * 1.5)}
              nodeRelSize={4}
              linkColor={() => 'rgba(148, 163, 184, 0.25)'}
              linkWidth={0.5}
              linkDirectionalArrowLength={2.5}
              linkDirectionalArrowRelPos={1}
              linkLabel={(l: GraphLink) => l.relation}
              onNodeClick={(n: GraphNode) => setSelected(n)}
              onBackgroundClick={() => setSelected(null)}
              cooldownTicks={80}
              warmupTicks={20}
              d3AlphaDecay={0.03}
              d3VelocityDecay={0.3}
              enableNodeDrag={true}
              enableZoomInteraction={true}
              enablePanInteraction={true}
            />
          )}
        </div>

        {/* Right: node detail panel */}
        {selected && (
          <aside className="w-80 border-l border-edge/60 glass flex-shrink-0 flex flex-col overflow-hidden">
            <div className="px-4 py-3 border-b border-edge flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: colorForType(selected.type) }}
                  />
                  <span className="text-2xs text-ink-4 uppercase tracking-wider">
                    {selected.type}
                  </span>
                </div>
                <p className="text-sm font-semibold text-ink leading-tight break-words">
                  {selected.name}
                </p>
              </div>
              <button
                onClick={() => setSelected(null)}
                className="p-1.5 rounded-md text-ink-4 hover:text-ink hover:bg-overlay transition-colors flex-shrink-0"
              >
                <X size={14} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">

              {/* Metadata */}
              {Object.keys(selected.metadata).length > 0 && (
                <div>
                  <p className="text-2xs font-medium text-ink-4 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Info size={11} /> Metadata
                  </p>
                  <div className="space-y-1.5">
                    {Object.entries(selected.metadata).map(([k, v]) => (
                      <div key={k} className="flex items-start justify-between gap-2">
                        <span className="text-2xs text-ink-4 font-mono">{k}</span>
                        <span className="text-2xs text-ink-2 text-right break-all flex-1">
                          {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* External link if URL present */}
              {selected.metadata?.url && (
                <a
                  href={selected.metadata.url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-2 px-3 py-2 rounded-md border border-edge hover:border-accent/40 hover:bg-overlay transition-colors text-xs text-ink-2 group"
                >
                  <ExternalLink size={12} className="text-ink-4 group-hover:text-accent" />
                  <span className="truncate">{selected.metadata.url}</span>
                </a>
              )}

              {/* Neighbors */}
              <div>
                <p className="text-2xs font-medium text-ink-4 uppercase tracking-wider mb-2">
                  Neighbors {loadingNeighbors ? '…' : `(${neighbors.length})`}
                </p>
                {loadingNeighbors ? (
                  <Loader2 className="animate-spin text-ink-4" size={14} />
                ) : neighbors.length === 0 ? (
                  <p className="text-2xs text-ink-4 italic">No connected nodes</p>
                ) : (
                  <div className="space-y-0.5">
                    {neighbors
                      .filter(n => n.name !== selected.name)
                      .slice(0, 30)
                      .map(n => {
                        const nodeObj = graphData.nodes.find(
                          gn => gn.name === n.name
                        );
                        return (
                          <button
                            key={n.name}
                            onClick={() => {
                              if (nodeObj) {
                                setSelected(nodeObj);
                                if (fgRef.current) {
                                  fgRef.current.centerAt(
                                    nodeObj.x,
                                    nodeObj.y,
                                    400
                                  );
                                }
                              }
                            }}
                            className="w-full text-left flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-overlay transition-colors group"
                          >
                            <span
                              className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                              style={{ backgroundColor: colorForType(n.type) }}
                            />
                            <span className="text-2xs text-ink-2 truncate flex-1 group-hover:text-accent transition-colors">
                              {n.name}
                            </span>
                          </button>
                        );
                      })}
                  </div>
                )}
              </div>

            </div>
          </aside>
        )}
      </div>
    </div>
  );
}
