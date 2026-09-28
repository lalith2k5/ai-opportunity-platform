import { useEffect, useState } from 'react';
import { getOrganizations, type Organization } from '../services/api';
import { Loader2, Building2, Users } from 'lucide-react';

export default function Organizations() {
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    getOrganizations().then(setOrgs).finally(() => setLoading(false));
  }, []);

  const filtered = orgs.filter(o =>
    !search.trim() || o.name.toLowerCase().includes(search.toLowerCase())
  ).sort((a, b) => b.profile_count - a.profile_count || a.name.localeCompare(b.name));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="animate-spin text-accent" size={32} />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-[1200px] mx-auto">
      <div className="mb-6 flex items-center gap-3.5">
        <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center shadow-[inset_0_1px_0_0_rgb(255_255_255/0.05)]">
          <Building2 className="text-accent" size={18} />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-ink tracking-tight">Organizations</h1>
          <p className="text-sm text-ink-3 mt-1">Source organizations behind problem profiles</p>
        </div>
      </div>

      <div className="card p-3 mb-6">
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search organizations…"
          className="input text-sm"
        />
      </div>

      {filtered.length === 0 ? (
        <div className="bg-surface border border-edge border-dashed rounded-lg p-12 text-center">
          <Building2 className="text-ink-4 mx-auto mb-3" size={24} />
          <p className="text-sm text-ink-2 font-medium">No organizations</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {filtered.map(o => (
            <div key={o.id} className="card card-hover p-5">
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="min-w-0 flex-1">
                  <h3 className="text-ink font-medium text-sm leading-snug">{o.name}</h3>
                  {o.industry_domain && (
                    <span className="badge bg-overlay text-ink-3 border border-edge mt-1.5">
                      {o.industry_domain}
                    </span>
                  )}
                </div>
                <span className="text-lg font-semibold font-mono tabular-nums text-accent flex-shrink-0">
                  {o.profile_count}
                </span>
              </div>
              <div className="flex items-center justify-between text-2xs pt-3 border-t border-edge-subtle">
                <span className="text-ink-4 flex items-center gap-1">
                  <Users size={10} /> {o.profile_count} profiles
                </span>
                {o.source && (
                  <span className="text-ink-4 font-mono">{o.source}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
