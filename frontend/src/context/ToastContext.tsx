import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

type ToastType = 'success' | 'error' | 'info';
interface Toast { id: string; type: ToastType; title: string; message?: string; }

interface ToastContextValue {
  success: (title: string, message?: string) => void;
  error:   (title: string, message?: string) => void;
  info:    (title: string, message?: string) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

const ICONS = {
  success: CheckCircle2,
  error:   AlertCircle,
  info:    Info,
};
const COLORS = {
  success: 'text-success',
  error:   'text-danger',
  info:    'text-accent',
};
const BG = {
  success: 'border-success/30',
  error:   'border-danger/30',
  info:    'border-accent/30',
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const remove = useCallback((id: string) => {
    setToasts(t => t.filter(x => x.id !== id));
  }, []);

  const push = useCallback((type: ToastType, title: string, message?: string) => {
    const id = Math.random().toString(36).slice(2);
    setToasts(t => [...t, { id, type, title, message }]);
    setTimeout(() => remove(id), 4500);
  }, [remove]);

  const api: ToastContextValue = {
    success: (t, m) => push('success', t, m),
    error:   (t, m) => push('error', t, m),
    info:    (t, m) => push('info', t, m),
  };

  return (
    <ToastContext.Provider value={api}>
      {children}
      {createPortal(
        <div className="fixed bottom-4 right-4 z-[200] flex flex-col gap-2 w-[360px] max-w-[calc(100vw-2rem)] pointer-events-none">
          {toasts.map(t => {
            const Icon = ICONS[t.type];
            return (
              <div
                key={t.id}
                className={`pointer-events-auto bg-overlay border ${BG[t.type]} rounded-lg shadow-xl p-3.5 flex items-start gap-3 animate-slide-up backdrop-blur-sm`}
              >
                <Icon size={15} className={`${COLORS[t.type]} flex-shrink-0 mt-0.5`} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-ink leading-tight">{t.title}</p>
                  {t.message && (
                    <p className="text-2xs text-ink-3 mt-0.5 leading-relaxed">{t.message}</p>
                  )}
                </div>
                <button
                  onClick={() => remove(t.id)}
                  className="p-0.5 -mr-1 -mt-1 rounded text-ink-4 hover:text-ink hover:bg-subtle transition-colors flex-shrink-0"
                >
                  <X size={12} />
                </button>
              </div>
            );
          })}
        </div>,
        document.body
      )}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside ToastProvider');
  return ctx;
}
