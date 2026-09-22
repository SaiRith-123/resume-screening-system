import Badge from "./Badge";

export default function EligibilityBanner({
  eligibility,
  missing,
  score,
}: {
  eligibility: string;
  missing: string[];
  score?: number;
}) {
  const meets = eligibility === "MEETS_ALL_MANDATORY";
  return (
    <div
      className={`rounded-xl border p-4 ${
        meets ? "border-emerald-200 bg-emerald-50" : "border-amber-200 bg-amber-50"
      }`}
    >
      <div className="flex items-center gap-2">
        <Badge tone={meets ? "success" : "warning"}>
          Eligibility: {meets ? "Meets all mandatory requirements" : "Requires review"}
        </Badge>
        {typeof score === "number" && (
          <span className="text-sm text-ink-700 dark:text-slate-300">Overall compatibility: {score.toFixed(1)}%</span>
        )}
      </div>
      {missing.length > 0 && (
        <p className="mt-2 text-sm text-ink-700 dark:text-slate-300">
          <span className="font-medium">Missing:</span> {missing.join(", ")}
        </p>
      )}
      {!meets && (
        <p className="mt-1 text-sm font-medium text-amber-800">
          Recruiter review recommended. This candidate has not been automatically rejected.
        </p>
      )}
    </div>
  );
}
