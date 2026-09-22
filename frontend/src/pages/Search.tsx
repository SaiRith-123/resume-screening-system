import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";

interface SearchResult {
  candidate_id: number;
  job_id: number;
  name?: string | null;
  final_score?: number | null;
  semantic_score?: number;
  eligibility_status?: string | null;
  total_experience_years: number;
}

export default function Search() {
  const [q, setQ] = useState("");
  const [minScore, setMinScore] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [mode, setMode] = useState("keyword");
  const [busy, setBusy] = useState(false);
  const [searched, setSearched] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      if (minScore) params.set("min_score", minScore);
      const { data } = await api.get(`/search/candidates?${params.toString()}`);
      setResults(data.results);
      setMode(data.mode);
      setSearched(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-ink-900 dark:text-slate-100">Candidate search</h1>
      <form onSubmit={onSubmit} className="card flex flex-wrap items-end gap-4 p-5">
        <div className="flex-1">
          <label className="label">Search</label>
          <input className="input" value={q} onChange={(e) => setQ(e.target.value)}
            placeholder='e.g. "strong backend engineering with Python API development"' />
        </div>
        <div className="w-40">
          <label className="label">Min score</label>
          <input className="input" type="number" value={minScore}
            onChange={(e) => setMinScore(e.target.value)} />
        </div>
        <button className="btn-primary" disabled={busy}>{busy ? "Searching…" : "Search"}</button>
      </form>

      {searched && (
        <>
          <p className="text-sm text-ink-500 dark:text-slate-400">
            Mode: <span className="font-medium">{mode}</span> · {results.length} result(s)
          </p>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {results.map((r) => (
              <Link key={`${r.job_id}-${r.candidate_id}`} to={`/candidates/${r.candidate_id}`}
                className="card p-4 hover:shadow-md">
                <p className="font-medium text-ink-900 dark:text-slate-100">{r.name ?? `Candidate ${r.candidate_id}`}</p>
                <p className="text-xs text-ink-500 dark:text-slate-400">Job #{r.job_id} · {r.total_experience_years} yrs</p>
                <div className="mt-2 flex items-center justify-between text-sm">
                  <span className="text-ink-500 dark:text-slate-400">{r.eligibility_status ?? "—"}</span>
                  <span className="font-semibold text-brand-600">
                    {r.semantic_score != null
                      ? `${r.semantic_score.toFixed(0)}% sim`
                      : r.final_score != null
                      ? `${r.final_score.toFixed(1)}%`
                      : "—"}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
