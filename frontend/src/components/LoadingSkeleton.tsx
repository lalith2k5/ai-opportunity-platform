export function CardSkeleton() {
  return (
    <div className="bg-surface border border-edge rounded-lg p-4 animate-pulse">
      <div className="h-3 bg-overlay rounded w-2/3 mb-3" />
      <div className="h-2 bg-overlay rounded w-full mb-2" />
      <div className="h-2 bg-overlay rounded w-4/5 mb-4" />
      <div className="grid grid-cols-2 gap-3">
        <div className="h-1 bg-overlay rounded" />
        <div className="h-1 bg-overlay rounded" />
      </div>
    </div>
  );
}

export function StatSkeleton() {
  return (
    <div className="bg-surface border border-edge rounded-lg p-4 animate-pulse">
      <div className="h-2 bg-overlay rounded w-1/3 mb-3" />
      <div className="h-6 bg-overlay rounded w-1/2" />
    </div>
  );
}

export function RowSkeleton() {
  return (
    <div className="flex items-center gap-3 py-2.5 animate-pulse">
      <div className="h-2 bg-overlay rounded w-8" />
      <div className="h-2 bg-overlay rounded flex-1" />
      <div className="h-2 bg-overlay rounded w-12" />
    </div>
  );
}
