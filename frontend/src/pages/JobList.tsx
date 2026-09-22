import { Link, useNavigate } from "react-router-dom";
import { useJobs } from "../hooks/useJobs";
import DataTable, { Column } from "../components/DataTable";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorState from "../components/ErrorState";
import type { JobListItem } from "../types";

export default function JobList() {
  const { jobs, loading, error, reload } = useJobs();
  const navigate = useNavigate();

  const columns: Column<JobListItem>[] = [
    {
      key: "title",
      header: "Job",
      sortValue: (r) => r.title,
      render: (r) => (
        <Link to={`/jobs/${r.id}`} className="font-medium text-brand-700 hover:underline">
          {r.title}
        </Link>
      ),
    },
    { key: "status", header: "Status", sortValue: (r) => r.status, render: (r) => r.status },
    {
      key: "candidates",
      header: "Candidates",
      sortValue: (r) => r.candidate_count,
      render: (r) => r.candidate_count,
    },
    {
      key: "avg",
      header: "Average match",
      sortValue: (r) => r.average_match,
      render: (r) => `${r.average_match.toFixed(1)}%`,
    },
    {
      key: "top",
      header: "Top candidate",
      render: (r) => r.top_candidate ?? "—",
    },
    {
      key: "actions",
      header: "",
      render: (r) => (
        <button className="btn-secondary" onClick={() => navigate(`/jobs/${r.id}/ranking`)}>
          Ranking
        </button>
      ),
    },
  ];

  if (error) return <ErrorState message={error} onRetry={reload} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-ink-900 dark:text-slate-100">Jobs</h1>
        <Link to="/jobs/new" className="btn-primary">+ New job</Link>
      </div>
      <DataTable columns={columns} rows={jobs} loading={loading} emptyMessage="No jobs yet." />
    </div>
  );
}
