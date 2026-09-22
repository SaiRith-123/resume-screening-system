import { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
}
interface State {
  error: Error | null;
}

/** Prevents a render error from blanking the whole app. */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error("Unhandled UI error:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="grid min-h-screen place-items-center bg-slate-50 dark:bg-slate-900/50 p-6 text-center dark:bg-slate-950">
          <div className="card max-w-md p-8">
            <p className="text-4xl">⚠️</p>
            <h1 className="mt-3 text-xl font-bold text-ink-900 dark:text-slate-100">
              Something went wrong
            </h1>
            <p className="mt-2 text-sm text-ink-500 dark:text-slate-400">
              {this.state.error.message || "An unexpected error occurred while rendering this page."}
            </p>
            <button
              className="btn-primary mt-6"
              onClick={() => window.location.reload()}
              aria-label="Reload the application"
            >
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
