import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useJob } from "../hooks/useJobs";
import { useScreening } from "../hooks/useScreening";
import { useCandidates } from "../hooks/useCandidates";
import DataTable, { Column } from "../components/DataTable";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorState from "../components/ErrorState";
import Badge, { statusTone } from "../components/Badge";
import type { ScreeningResult } from "../types";

export default function Ranking() {
  const { jobId } = useParams();
  const { job } = useJob(jobId);
  const { results, loading, error, load } = useScreening(jobId);
  const { candidates } = useCandidates(jobId);

  const [minScore, setMinScore] = useState(0);
  const [requiredSkill, setRequiredSkill] = useState("");
  const [eligibility, setEligibility] = useState("all");
  const [reviewOnly, setReviewOnly] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    void load();
  }, [load]);

  const candidateName = (r: ScreeningResult) =>
    candidates.find((candidate) => candidate.id === r.candidate_id)?.name ||
    `Candidate ${r.candidate_id}`;

  const filtered = useMemo(() => {
    return results.filter((r) => {
      if (r.scores.final_score < minScore) return false;
      if (eligibility !== "all" && r.eligibility_status !== eligibility) return false;
      if (reviewOnly && !r.needs_review) return false;
      if (requiredSkill && !r.matched_skills.some((s) =>
        s.toLowerCase().includes(requiredSkill.toLowerCase()))) return false;
      if (query && !candidateName(r).toLowerCase().includes(query.toLowerCase())) return false;
      return true;
    });
  }, [results, minScore, eligibility, reviewOnly, requiredSkill, query]);

  const columns: Column<ScreeningResult>[] = [
    { key: "rank", header: "Rank", sortValue: (r) => r.rank ?? 9999, render: (r) => `#${r.rank ?? "—"}` },
    {
      key: "candidate", header: "Candidate", sortValue: (r) => candidateName(r),
      render: (r) => (
        <Link to={`/candidates/${r.candidate_id}`} className="font-medium text-brand-700 hover:underline">
          {candidateName(r)}
        </Link>
      ),
    },
    {
      key: "score", header: "Overall", sortValue: (r) => r.scores.final_score,
      render: (r) => <span className="font-semibold">{r.scores.final_score.toFixed(1)}%</span>,
    },
    {
      key: "elig", header: "Eligibility",
      render: (r) => <Badge tone={statusTone(r.eligibility_status)}>{r.eligibility_status}</Badge>,
    },
    { key: "skill", header: "Skill", sortValue: (r) => r.scores.skill_score, render: (r) => `${r.scores.skill_score.toFixed(0)}%` },
    { key: "exp", header: "Experience", sortValue: (r) => r.scores.experience_score, render: (r) => `${r.scores.experience_score.toFixed(0)}%` },
    { key: "sem", header: "Semantic", sortValue: (r) => r.scores.semantic_score, render: (r) => `${r.scores.semantic_score.toFixed(0)}%` },
    {
      key: "missing", header: "Missing",
      render: (r) => (r.missing_skills.length ? r.missing_skills.slice(0, 3).join(", ") : "—"),
    },
    { key: "status", header: "Status", render: (r) => (r.needs_review ? "Review" : "Strong") },
  ];

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="space-y-6">
      <div>
        <Link to={`/jobs/${jobId}`} className="text-sm text-brand-600">← Job</Link>
        <h1 className="mt-1 text-2xl font-bold text-ink-900 dark:text-slate-100">
          Ranking{job ? ` · ${job.title}` : ""}
        </h1>
      </div>

      <div className="card grid gap-4 p-5 md:grid-cols-5">
        <div>
          <label className="label">Min score</label>
          <input type="number" className="input" min={0} max={100} value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))} />
        </div>
        <div>
          <label className="label">Required skill</label>
          <input className="input" value={requiredSkill}
            onChange={(e) => setRequiredSkill(e.target.value)} placeholder="e.g. Python" />
        </div>
        <div>
          <label className="label">Eligibility</label>
          <select className="input" value={eligibility} onChange={(e) => setEligibility(e.target.value)}>
            <option value="all">All</option>
            <option value="MEETS_ALL_MANDATORY">Meets all</option>
            <option value="MISSING_REQUIREMENTS">Missing requirements</option>
            <option value="DOES_NOT_MEET_MANDATORY">Does not meet mandatory</option>
          </select>
        </div>
        <div>
          <label className="label">Search</label>
          <input className="input" value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
        <label className="flex items-end gap-2 text-sm text-ink-700 dark:text-slate-300">
          <input type="checkbox" checked={reviewOnly} onChange={(e) => setReviewOnly(e.target.checked)} />
          Needs review only
        </label>
      </div>

      <DataTable columns={columns} rows={filtered} pageSize={10}
        emptyMessage="No screening results. Upload resumes first." />
    </div>
  );
}
