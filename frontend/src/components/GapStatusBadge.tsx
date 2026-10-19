type GapKind = 'CAPABILITY' | 'COVERAGE' | undefined;
type GapStatus = 'PROPOSED' | 'UNDER_REVIEW' | 'VALIDATED' | 'REVISED' | 'REJECTED' | undefined;

const KIND_CLS: Record<string, string> = {
  CAPABILITY: 'bg-accent/10 text-accent border-accent/30',
  COVERAGE: 'bg-warning/10 text-warning border-warning/30',
};

const STATUS_CLS: Record<string, string> = {
  PROPOSED: 'bg-ink-4/10 text-ink-3 border-edge',
  UNDER_REVIEW: 'bg-sky-500/10 text-sky-500 border-sky-500/30',
  VALIDATED: 'bg-success/10 text-success border-success/30',
  REVISED: 'bg-accent/10 text-accent border-accent/30',
  REJECTED: 'bg-danger/10 text-danger border-danger/30',
};

const STATUS_LABEL: Record<string, string> = {
  PROPOSED: 'proposed',
  UNDER_REVIEW: 'under review',
  VALIDATED: 'validated',
  REVISED: 'revised',
  REJECTED: 'rejected',
};

export default function GapStatusBadge({
  kind,
  status,
  compact = false,
}: {
  kind?: GapKind | string;
  status?: GapStatus | string;
  compact?: boolean;
}) {
  const k = kind || 'COVERAGE';
  const s = status || 'PROPOSED';
  const kCls = KIND_CLS[k] || KIND_CLS.COVERAGE;
  const sCls = STATUS_CLS[s] || STATUS_CLS.PROPOSED;
  const sLabel = STATUS_LABEL[s] || s.toLowerCase().replace(/_/g, ' ');
  const sizeCls = compact ? 'text-2xs px-1.5 py-0.5' : 'text-2xs px-2 py-0.5';
  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      <span className={'badge border ' + kCls + ' ' + sizeCls}>{k.toLowerCase()}</span>
      <span className={'badge border ' + sCls + ' ' + sizeCls}>{sLabel}</span>
      {s === 'PROPOSED' && (
        <span className="text-2xs text-warning italic">not yet expert-validated</span>
      )}
    </div>
  );
}
