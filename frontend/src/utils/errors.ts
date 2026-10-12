
export function formatApiError(e: any): string {
  if (!e) return 'Something went wrong';
  const detail = e?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: any) => {
        if (typeof d === 'string') return d;
        if (d && typeof d === 'object') {
          const loc = Array.isArray(d.loc) ? d.loc.join('.') : '';
          const msg = d.msg || JSON.stringify(d);
          return loc ? loc + ': ' + msg : msg;
        }
        return String(d);
      })
      .join('; ');
  }
  if (detail && typeof detail === 'object') return JSON.stringify(detail);
  if (typeof e?.message === 'string' && e.message) return e.message;
  return 'Something went wrong';
}
