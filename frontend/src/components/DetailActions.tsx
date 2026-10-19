
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileDown, Sparkles } from 'lucide-react';
import { downloadContextualPdf } from '../services/api';

export type DetailKind = 'opportunity' | 'idea' | 'technology' | 'research' | 'rd';

export default function DetailActions({
  kind,
  id,
  title,
  summary,
}: {
  kind: DetailKind;
  id: string;
  title: string;
  summary?: string;
}) {
  const navigate = useNavigate();
  const [pdfLoading, setPdfLoading] = useState(false);

  const onPdf = async () => {
    setPdfLoading(true);
    try {
      await downloadContextualPdf(kind, id, title);
    } catch (e: any) {
      window.alert('PDF download failed: ' + (e?.message || 'unknown error'));
    } finally {
      setPdfLoading(false);
    }
  };

  const onAskAi = () => {
    const params = new URLSearchParams();
    params.set('kind', kind);
    params.set('id', id);
    params.set('title', title);
    if (summary) params.set('summary', summary.slice(0, 500));
    navigate('/chat?' + params.toString());
  };

  return (
    <div className="flex items-center gap-2 mb-5 flex-wrap animate-fade-up">
      <button
        type="button"
        onClick={onPdf}
        disabled={pdfLoading}
        className="btn-secondary text-xs"
      >
        <FileDown size={13} />
        {pdfLoading ? 'Generating…' : 'Download PDF report'}
      </button>
      <button
        type="button"
        onClick={onAskAi}
        className="btn-primary text-xs"
      >
        <Sparkles size={13} />
        Ask AI about this
      </button>
    </div>
  );
}
