import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: undefined });
    window.location.href = '/dashboard';
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-bg-primary flex flex-col items-center justify-center p-4">
          <div className="glass-panel p-8 max-w-md w-full rounded-2xl flex flex-col items-center text-center">
            <div className="w-16 h-16 bg-red-500/10 text-red-400 flex items-center justify-center rounded-2xl mb-6">
              <AlertTriangle className="w-8 h-8" />
            </div>
            <h1 className="text-2xl font-bold text-primary mb-3">Something went wrong</h1>
            <p className="text-muted text-sm mb-8">
              We encountered an unexpected error while trying to render this page.
              Our team has been notified.
            </p>
            <button
              onClick={this.handleReset}
              className="flex items-center justify-center gap-2 w-full px-4 py-3 bg-accent text-bg-primary font-semibold rounded-xl hover:bg-accent/90 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Return to Dashboard
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
