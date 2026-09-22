import Badge, { statusTone } from "./Badge";

export default function SkillBadge({
  skill,
  status,
  confidence,
}: {
  skill: string;
  status: string;
  confidence?: number;
}) {
  const label =
    status === "MATCH"
      ? "Strong"
      : status === "PARTIAL_MATCH"
      ? "Partial"
      : status === "MISSING"
      ? "Missing"
      : "Unknown";
  return (
    <span className="inline-flex items-center gap-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-1.5 text-sm">
      <span className="font-medium text-ink-800 dark:text-slate-200">{skill}</span>
      <Badge tone={statusTone(status)}>{label}</Badge>
      {typeof confidence === "number" && (
        <span className="text-xs text-ink-500 dark:text-slate-400">{Math.round(confidence * 100)}%</span>
      )}
    </span>
  );
}
