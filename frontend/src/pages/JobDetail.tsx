import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useJob } from "../hooks/useJobs";
import { useCandidates } from "../hooks/useCandidates";
import { useScreening } from "../hooks/useScreening";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorState from "../components/ErrorState";
import UploadDropzone from "../components/UploadDropzone";
import ProgressTracker from "../components/ProgressTracker";
import Badge, { statusTone } from "../components/Badge";
import type { UploadResponse } from "../types";

export default function JobDetail() {
  const { jobId } = useParams();
  const { job, loading, error, reload } = useJob(jobId);
  const { candidates, reload: reloadCandidates } = useCandidates(jobId);
  const { upload, run, loading: screening } = useScreening(jobId);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!job) return <ErrorState message="Job not found" />;

  async function handleUpload(files: File[]) {
    const result = await upload(files);
    setUploadResult(result);
    await reloadCandidates();
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link to="/jobs" className="text-sm text-brand-600">← Jobs</Link>
          <h1 className="mt-1 text-2xl font-bold text-ink-900 dark:text-slate-100">{job.title}</h1>
          <p className="text-sm text-ink-500 dark:text-slate-400">
            {[job.department, job.location, job.seniority].filter(Boolean).join(" · ")}
          </p>
        </div>
        <div className="flex gap-3">
          <button className="btn-secondary" disabled={screening} onClick={() => run()}>
            {screening ? "Screening…" : "Re-run screening"}
          </button>
          <Link className="btn-primary" to={`/jobs/${job.id}/ranking`}>View ranking</Link>
        </div>
      </div>

      {notice && <p className="rounded-lg bg-brand-50 p-3 text-sm text-brand-700">{notice}</p>}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="card p-5 lg:col-span-2">
          <h2 className="mb-3 font-semibold text-ink-900 dark:text-slate-100">Upload resumes</h2>
          <UploadDropzone onUpload={handleUpload} />
          {uploadResult && (
            <div className="mt-4 space-y-2 text-sm">
              <p className="text-emerald-700">{uploadResult.accepted.length} accepted, {uploadResult.screened} screened.</p>
              {uploadResult.rejected.length > 0 && (
                <ul className="list-inside list-disc text-rose-600">
                  {uploadResult.rejected.map((r, i) => (
                    <li key={i}>{r.filename}: {r.reason}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        <div className="card p-5">
          <h2 className="mb-3 font-semibold text-ink-900 dark:text-slate-100">Requirements</h2>
          <ul className="space-y-2 text-sm">
            {job.requirements.map((r) => (
              <li key={r.id} className="flex items-center gap-2">
                <Badge tone={r.priority === "required" ? "danger" : "info"}>{r.priority}</Badge>
                <span className="text-ink-800 dark:text-slate-200">{r.value}</span>
                {r.is_hard_gate && <Badge tone="warning">gate</Badge>}
              </li>
            ))}
            {job.requirements.length === 0 && <li className="text-ink-500 dark:text-slate-400">No requirements</li>}
          </ul>
        </div>
      </div>

      <div className="card p-5">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold text-ink-900 dark:text-slate-100">Candidates ({candidates.length})</h2>
          <div className="flex gap-2">
            <a className="btn-secondary" href={`${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api"}/jobs/${job.id}/export?fmt=csv`}>Export CSV</a>
            <a className="btn-secondary" href={`${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api"}/jobs/${job.id}/export?fmt=xlsx`}>Export Excel</a>
            <a className="btn-secondary" href={`${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api"}/jobs/${job.id}/export?fmt=pdf`}>Export PDF</a>
          </div>
        </div>
        <ul className="divide-y divide-slate-100 dark:divide-slate-800">
          {candidates.map((c) => (
            <li key={c.id} className="py-3">
              <div className="flex items-center justify-between">
                <Link to={`/candidates/${c.id}`} className="font-medium text-brand-700 hover:underline">
                  {c.name ?? `Candidate ${c.id}`}
                </Link>
                <div className="flex items-center gap-3 text-sm">
                  <Badge tone={statusTone(c.status)}>{c.status}</Badge>
                  <span className="font-semibold">
                    {c.final_score != null ? `${c.final_score.toFixed(1)}%` : "—"}
                  </span>
                </div>
              </div>
              <div className="mt-2"><ProgressTracker status={c.status} /></div>
            </li>
          ))}
          {candidates.length === 0 && <li className="py-4 text-sm text-ink-500 dark:text-slate-400">No candidates yet.</li>}
        </ul>
      </div>
    </div>
  );
}
