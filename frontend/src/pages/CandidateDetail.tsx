import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useCandidate } from "../hooks/useCandidates";
import { fetchExplanation, fetchInterviewQuestions } from "../hooks/useScreening";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorState from "../components/ErrorState";
import ScoreChart from "../components/ScoreChart";
import ScoreBreakdownPanel from "../components/ScoreBreakdownPanel";
import EvidencePanel from "../components/EvidencePanel";
import EligibilityBanner from "../components/EligibilityBanner";
import Badge, { statusTone } from "../components/Badge";
import type { GenAIExplanation, InterviewQuestions } from "../types";

const API = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export default function CandidateDetail() {
  const { candidateId } = useParams();
  const { candidate, loading, error, reload } = useCandidate(candidateId);
  const [explanation, setExplanation] = useState<GenAIExplanation | null>(null);
  const [questions, setQuestions] = useState<InterviewQuestions | null>(null);
  const [busy, setBusy] = useState(false);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!candidate) return <ErrorState message="Candidate not found" />;

  const s = candidate.structured;
  const screening = candidate.screening;

  async function loadExplanation() {
    setBusy(true);
    try {
      setExplanation(await fetchExplanation(candidate!.id));
    } finally {
      setBusy(false);
    }
  }

  async function loadQuestions() {
    setBusy(true);
    try {
      setQuestions(await fetchInterviewQuestions(candidate!.id));
    } finally {
      setBusy(false);
    }
  }

  const skills = [
    ...(s.programming_languages ?? []),
    ...(s.frameworks ?? []),
    ...(s.databases ?? []),
    ...(s.cloud_technologies ?? []),
    ...(s.technical_skills ?? []),
    ...(s.tools ?? []),
  ];
  const uniqueSkills = Array.from(new Set(skills));

  function skillStatus(skill: string): string {
    if (!screening) return "UNKNOWN";
    if (screening.matched_skills.includes(skill)) return "MATCH";
    if (screening.partial_skills.includes(skill)) return "PARTIAL_MATCH";
    if (screening.missing_skills.includes(skill)) return "MISSING";
    return "UNKNOWN";
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link to={`/jobs/${candidate.job_id}/ranking`} className="text-sm text-brand-600">← Ranking</Link>
          <h1 className="mt-1 text-2xl font-bold text-ink-900 dark:text-slate-100">{candidate.name ?? `Candidate ${candidate.id}`}</h1>
          <p className="text-sm text-ink-500 dark:text-slate-400">
            {s.contact?.email ?? candidate.email ?? "—"} · {candidate.total_experience_years} yrs experience
          </p>
        </div>
        <div className="flex gap-3">
          <a className="btn-secondary" href={`${API}/candidates/${candidate.id}/resume`}>Download resume</a>
          <button className="btn-secondary" onClick={loadQuestions} disabled={busy}>Generate interview questions</button>
          <button className="btn-primary" onClick={loadExplanation} disabled={busy}>Generate AI explanation</button>
        </div>
      </div>

      {screening && (
        <EligibilityBanner eligibility={screening.eligibility_status}
          missing={screening.missing_requirements} score={screening.scores.final_score} />
      )}

      {screening && <ScoreChart scores={screening.scores} />}

      <div className="grid gap-6 lg:grid-cols-2">
        {screening && <ScoreBreakdownPanel scores={screening.scores} />}
        <div className="card p-5">
          <h3 className="mb-3 font-semibold text-ink-900 dark:text-slate-100">Candidate overview</h3>
          <p className="text-sm text-ink-700 dark:text-slate-300">{s.summary ?? "No summary extracted."}</p>
          <div className="mt-4">
            <h4 className="text-sm font-semibold text-ink-700 dark:text-slate-300">Skills</h4>
            <div className="mt-2 flex flex-wrap gap-2">
              {uniqueSkills.map((skill) => (
                <span key={skill} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 dark:border-slate-800 px-2.5 py-1 text-xs">
                  {skill}
                  <Badge tone={statusTone(skillStatus(skill))}>{skillStatus(skill)}</Badge>
                </span>
              ))}
              {uniqueSkills.length === 0 && <span className="text-sm text-ink-500 dark:text-slate-400">No skills extracted.</span>}
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card p-5">
          <h3 className="mb-3 font-semibold text-ink-900 dark:text-slate-100">Experience</h3>
          <ol className="relative space-y-4 border-l border-slate-200 dark:border-slate-800 pl-4">
            {(s.experience ?? []).map((e, i) => (
              <li key={i}>
                <p className="font-medium text-ink-800 dark:text-slate-200">{e.title ?? "Role"}</p>
                <p className="text-xs text-ink-500 dark:text-slate-400">
                  {e.company ?? ""} · {e.start_date ?? "?"} – {e.is_current ? "Present" : e.end_date ?? "?"} · {e.kind}
                </p>
                {e.description && <p className="mt-1 text-sm text-ink-700 dark:text-slate-300">{e.description}</p>}
              </li>
            ))}
            {(s.experience ?? []).length === 0 && <li className="text-sm text-ink-500 dark:text-slate-400">None extracted.</li>}
          </ol>
        </div>

        <div className="card p-5">
          <h3 className="mb-3 font-semibold text-ink-900 dark:text-slate-100">Education & certifications</h3>
          <ul className="space-y-2 text-sm">
            {(s.education ?? []).map((e, i) => (
              <li key={i} className="text-ink-800 dark:text-slate-200">
                {[e.degree, e.field_of_study, e.institution].filter(Boolean).join(", ")}
                {e.end_year ? ` (${e.end_year})` : ""}
              </li>
            ))}
            {(s.certifications ?? []).map((c, i) => (
              <li key={`c${i}`} className="text-ink-600 dark:text-slate-300">🎓 {c.name}{c.year ? ` (${c.year})` : ""}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className="card p-5">
        <h3 className="mb-3 font-semibold text-ink-900 dark:text-slate-100">Projects</h3>
        <div className="grid gap-4 md:grid-cols-2">
          {(s.projects ?? []).map((p, i) => (
            <div key={i} className="rounded-lg border border-slate-200 dark:border-slate-800 p-3">
              <p className="font-medium text-ink-800 dark:text-slate-200">{p.name ?? "Project"}</p>
              <p className="mt-1 text-sm text-ink-600 dark:text-slate-300">{p.description}</p>
              <div className="mt-2 flex flex-wrap gap-1">
                {(p.technologies ?? []).map((t) => (
                  <span key={t} className="badge bg-slate-100 dark:bg-slate-800 text-slate-600">{t}</span>
                ))}
              </div>
            </div>
          ))}
          {(s.projects ?? []).length === 0 && <p className="text-sm text-ink-500 dark:text-slate-400">None extracted.</p>}
        </div>
      </div>

      {screening && <EvidencePanel evidence={screening.evidence} />}

      {(explanation || screening?.explanation) && (
        <div className="card p-5">
          <h3 className="mb-2 font-semibold text-ink-900 dark:text-slate-100">AI screening explanation</h3>
          {(explanation ?? screening?.explanation)?.available === false && (
            <p className="mb-2 text-sm text-amber-700">
              {(explanation ?? screening?.explanation)?.note}
            </p>
          )}
          <p className="text-sm text-ink-700 dark:text-slate-300">{(explanation ?? screening?.explanation)?.summary}</p>
          <div className="mt-3 grid gap-4 md:grid-cols-2">
            <div>
              <h4 className="text-sm font-semibold text-emerald-700">Strengths</h4>
              <ul className="list-inside list-disc text-sm text-ink-700 dark:text-slate-300">
                {(explanation ?? screening?.explanation)?.strengths?.map((x, i) => <li key={i}>{x}</li>)}
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-rose-700">Weaknesses</h4>
              <ul className="list-inside list-disc text-sm text-ink-700 dark:text-slate-300">
                {(explanation ?? screening?.explanation)?.weaknesses?.map((x, i) => <li key={i}>{x}</li>)}
              </ul>
            </div>
          </div>
        </div>
      )}

      {questions && (
        <div className="card p-5">
          <h3 className="mb-2 font-semibold text-ink-900 dark:text-slate-100">Interview questions</h3>
          {!questions.available && <p className="mb-2 text-sm text-amber-700">{questions.note}</p>}
          {(["technical", "project", "behavioral", "role"] as const).map((kind) => (
            <div key={kind} className="mt-3">
              <h4 className="text-sm font-semibold capitalize text-ink-700 dark:text-slate-300">{kind}</h4>
              <ul className="list-inside list-disc text-sm text-ink-700 dark:text-slate-300">
                {questions[kind].map((q, i) => <li key={i}>{q}</li>)}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
