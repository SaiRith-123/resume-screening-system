import Badge, { statusTone } from "./Badge";
import type { Evidence } from "../types";

export default function EvidencePanel({ evidence }: { evidence: Evidence[] }) {
  const grounded = evidence.filter((e) => e.evidence_text);
  const rest = evidence.filter((e) => !e.evidence_text);
  return (
    <div className="card p-5">
      <h3 className="mb-3 text-base font-semibold text-ink-900 dark:text-slate-100">Evidence</h3>
      {grounded.length === 0 && rest.length === 0 && (
        <p className="text-sm text-ink-500 dark:text-slate-400">No evidence captured.</p>
      )}
      <ul className="space-y-3">
        {[...grounded, ...rest].map((e, i) => (
          <li key={i} className="rounded-lg border border-slate-200 dark:border-slate-800 p-3">
            <div className="flex items-center gap-2">
              <span className="font-medium text-ink-800 dark:text-slate-200">{e.requirement}</span>
              <Badge tone={statusTone(e.status)}>{e.status}</Badge>
              <span className="ml-auto text-xs text-ink-500 dark:text-slate-400">
                {Math.round((e.confidence ?? 0) * 100)}% confidence
              </span>
            </div>
            {e.evidence_text && (
              <p className="mt-2 border-l-2 border-brand-300 pl-3 text-sm italic text-ink-700 dark:text-slate-300">
                “{e.evidence_text}”
              </p>
            )}
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-ink-500 dark:text-slate-400">
        Evidence is quoted verbatim from the resume. The system never fabricates experience.
      </p>
    </div>
  );
}
