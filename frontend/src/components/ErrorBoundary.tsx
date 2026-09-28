import { Component, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props { children: ReactNode; }
interface State { hasError: boolean; error: Error | null; }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: any) {
    console.error('[ErrorBoundary]', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-canvas flex items-center justify-center p-6">
          <div className="max-w-md w-full bg-surface border border-edge rounded-lg p-6 text-center">
            <div className="w-12 h-12 rounded-lg bg-danger/10 flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="text-danger" size={22} />
            </div>
            <h1 className="text-lg font-semibold text-ink tracking-tight mb-2">
              Something went wrong
            </h1>
            <p className="text-sm text-ink-3 mb-5">
              {this.state.error?.message || 'An unexpected error occurred.'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="btn-primary text-xs mx-auto"
            >
              <RefreshCw size={13} /> Reload page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
