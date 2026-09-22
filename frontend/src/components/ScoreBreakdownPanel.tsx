import type { ScoreBreakdown } from "../types";

const LABELS: Record<string, string> = {
  skill_score: "Skill Match",
  experience_score: "Experience Match",
  semantic_score: "Semantic Relevance",
  education_score: "Education Match",
  project_score: "Project Match",
  certification_score: "Certification Match",
  preferred_score: "Preferred Requirements",
};

/** Shows exactly how the final score was computed (spec §26 - no black box). */
export default function ScoreBreakdownPanel({ scores }: { scores: ScoreBreakdown }) {
  const weights = scores.weights ?? {};
  const rows = Object.keys(LABELS).map((key) => {
    const value = (scores as unknown as Record<string, number>)[key] ?? 0;
    const weightKey = key.replace("_score", "");
    const weight = weights[weightKey] ?? null;
    return { label: LABELS[key], value, weight };
  });

  return (
    <div className="card p-5">
      <div className="mb-4 flex items-baseline justify-between">
        <h3 className="text-base font-semibold text-ink-900 dark:text-slate-100">Score breakdown</h3>
        <div className="text-right">
          <span className="text-3xl font-bold text-brand-600">
            {scores.final_score.toFixed(1)}%
          </span>
          <p className="text-xs text-ink-500 dark:text-slate-400">Final score</p>
        </div>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-ink-500 dark:text-slate-400">
            <th className="pb-2">Component</th>
            <th className="pb-2 text-right">Score</th>
            <th className="pb-2 text-right">Weight</th>
            <th className="pb-2 text-right">Contribution</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
          {rows.map((r) => (
            <tr key={r.label}>
              <td className="py-2 text-ink-700 dark:text-slate-300">{r.label}</td>
              <td className="py-2 text-right font-medium">{r.value.toFixed(1)}%</td>
              <td className="py-2 text-right text-ink-500 dark:text-slate-400">
                {r.weight != null ? `${(r.weight * 100).toFixed(0)}%` : "—"}
              </td>
              <td className="py-2 text-right">
                {r.weight != null ? `${(r.value * r.weight).toFixed(1)}` : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-3 text-xs text-ink-500 dark:text-slate-400">
        Final = Σ (component × weight). Weights are configurable per job.
      </p>
    </div>
  );
}
