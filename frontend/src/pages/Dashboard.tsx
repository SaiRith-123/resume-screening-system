import { Link } from "react-router-dom";
import { useJobs } from "../hooks/useJobs";
import StatCard from "../components/StatCard";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";

export default function Dashboard() {
  const { jobs, loading, error, reload } = useJobs();

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorState message={error} onRetry={reload} />;

  const totalCandidates = jobs.reduce((s, j) => s + j.candidate_count, 0);
  const avg = jobs.length
    ? jobs.reduce((s, j) => s + (j.average_match || 0), 0) / jobs.length
    : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ink-900 dark:text-slate-100">Dashboard</h1>
          <p className="text-sm text-ink-500 dark:text-slate-400">Screening overview across all your jobs</p>
        </div>
        <Link to="/jobs/new" className="btn-primary">+ New job</Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total jobs" value={jobs.length} />
        <StatCard label="Total candidates" value={totalCandidates} />
        <StatCard label="Average match" value={`${avg.toFixed(1)}%`} />
        <StatCard label="Jobs needing attention"
          value={jobs.filter((j) => j.candidate_count > 0 && (j.average_match || 0) < 60).length} />
      </div>

      <div>
        <h2 className="mb-3 text-lg font-semibold text-ink-900 dark:text-slate-100">Your jobs</h2>
        {jobs.length === 0 ? (
          <EmptyState title="No jobs yet"
            message="Create your first job posting to start screening candidates."
            action={<Link to="/jobs/new" className="btn-primary">Create a job</Link>} />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {jobs.map((job) => (
              <Link key={job.id} to={`/jobs/${job.id}`} className="card p-5 hover:shadow-md">
                <h3 className="font-semibold text-ink-900 dark:text-slate-100">{job.title}</h3>
                <p className="mt-1 text-xs text-ink-500 dark:text-slate-400">{job.status}</p>
                <div className="mt-4 flex items-center justify-between text-sm">
                  <span className="text-ink-500 dark:text-slate-400">{job.candidate_count} candidates</span>
                  <span className="font-semibold text-brand-600">
                    {job.average_match.toFixed(1)}% avg
                  </span>
                </div>
                {job.top_candidate && (
                  <p className="mt-2 text-xs text-ink-500 dark:text-slate-400">Top: {job.top_candidate}</p>
                )}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
