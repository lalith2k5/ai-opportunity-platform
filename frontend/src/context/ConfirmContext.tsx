import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { AlertTriangle, X } from 'lucide-react';

interface ConfirmOptions {
  title: string;
  message?: string;
  confirmText?: string;
  cancelText?: string;
  danger?: boolean;
}

interface ConfirmState extends ConfirmOptions {
  resolve: (v: boolean) => void;
}

interface ConfirmContextValue {
  confirm: (opts: ConfirmOptions) => Promise<boolean>;
}

const ConfirmContext = createContext<ConfirmContextValue | undefined>(undefined);

export function ConfirmProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<ConfirmState | null>(null);

  const confirm = useCallback((opts: ConfirmOptions): Promise<boolean> => {
    return new Promise(resolve => {
      setState({ ...opts, resolve });
    });
  }, []);

  const close = (v: boolean) => {
    if (state) {
      state.resolve(v);
      setState(null);
    }
  };

  return (
    <ConfirmContext.Provider value={{ confirm }}>
      {children}
      {state && createPortal(
        <>
          <div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[200] animate-fade-in"
            onClick={() => close(false)}
          />
          <div className="fixed inset-0 z-[201] flex items-center justify-center p-4 pointer-events-none">
            <div className="bg-overlay border border-edge rounded-lg shadow-xl w-full max-w-md pointer-events-auto animate-slide-up">
              <div className="flex items-start justify-between gap-4 px-5 pt-5 pb-3">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <div className={`w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0 ${
                    state.danger ? 'bg-danger/10' : 'bg-accent/10'
                  }`}>
                    <AlertTriangle size={15} className={state.danger ? 'text-danger' : 'text-accent'} />
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-sm font-semibold text-ink leading-tight">{state.title}</h3>
                    {state.message && (
                      <p className="text-xs text-ink-3 mt-1.5 leading-relaxed">{state.message}</p>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => close(false)}
                  className="p-1 rounded text-ink-4 hover:text-ink hover:bg-subtle transition-colors flex-shrink-0"
                >
                  <X size={14} />
                </button>
              </div>
              <div className="flex items-center justify-end gap-2 px-5 pb-5 pt-2">
                <button onClick={() => close(false)} className="btn-secondary text-xs">
                  {state.cancelText || 'Cancel'}
                </button>
                <button
                  onClick={() => close(true)}
                  className={`btn text-xs ${
                    state.danger
                      ? 'bg-danger text-white hover:bg-danger/90 active:scale-[0.98] shadow-sm'
                      : 'bg-accent text-accent-fg hover:bg-accent-hover active:scale-[0.98] shadow-sm'
                  }`}
                >
                  {state.confirmText || 'Confirm'}
                </button>
              </div>
            </div>
          </div>
        </>,
        document.body
      )}
    </ConfirmContext.Provider>
  );
}

export function useConfirm() {
  const ctx = useContext(ConfirmContext);
  if (!ctx) throw new Error('useConfirm must be used inside ConfirmProvider');
  return ctx;
}
