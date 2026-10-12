
import { Info } from 'lucide-react';

export default function PotentialGapNote() {
  return (
    <div className="flex items-start gap-2 mb-4 px-3 py-2 bg-warning/5 border border-warning/20 rounded-md">
      <Info size={12} className="text-warning flex-shrink-0 mt-0.5" />
      <p className="text-2xs text-ink-2 leading-relaxed">
        These are <span className="font-semibold">potential</span> research gaps identified by comparing
        evidence across sources. Expert validation is required before acting on any gap.
      </p>
    </div>
  );
}
