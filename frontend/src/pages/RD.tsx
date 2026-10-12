import { Factory, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function RD() {
  return (
    <div className="p-6 lg:p-10 max-w-4xl mx-auto">
      <div className="mb-8 animate-fade-up">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent/10 border border-accent/20 mb-5">
          <span className="text-2xs font-medium text-accent uppercase tracking-[0.08em]">
            Module
          </span>
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold text-ink tracking-tight leading-tight">
          R&D
        </h1>
        <p className="text-base text-ink-3 mt-3 max-w-2xl leading-relaxed">
          Industry problems to technology landscape, research landscape, evidence aggregation, and evidence-backed innovation opportunities.
        </p>
      </div>

      <div className="card p-8 text-center animate-fade-up" style={{ animationDelay: '200ms' }}>
        <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center mx-auto mb-4">
          <Factory size={20} className="text-accent" />
        </div>
        <p className="text-sm text-ink-2 font-medium">Coming in Phase N.8</p>
        <p className="text-xs text-ink-4 mt-2">
          Backend endpoints are already live — the UI arrives shortly.
        </p>
        <Link to="/entrance" className="btn-secondary text-xs mt-6 inline-flex">
          Back to entrance <ArrowRight size={12} />
        </Link>
      </div>
    </div>
  );
}
