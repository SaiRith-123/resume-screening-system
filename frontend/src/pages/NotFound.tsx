import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="grid min-h-screen place-items-center p-6 text-center">
      <div>
        <p className="text-6xl">🔍</p>
        <h1 className="mt-4 text-2xl font-bold text-ink-900 dark:text-slate-100">Page not found</h1>
        <p className="mt-2 text-sm text-ink-500 dark:text-slate-400">The page you are looking for does not exist.</p>
        <Link to="/" className="btn-primary mt-6 inline-flex">Back to dashboard</Link>
      </div>
    </div>
  );
}
