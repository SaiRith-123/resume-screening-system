const STEPS = ["UPLOADED", "PROCESSING", "EXTRACTED", "ANALYZED", "SCREENED"] as const;

export default function ProgressTracker({ status }: { status: string }) {
  const failed = status === "FAILED";
  const index = STEPS.indexOf(status as (typeof STEPS)[number]);
  return (
    <div className="flex items-center gap-1">
      {STEPS.map((step, i) => {
        const done = index >= i && !failed;
        const active = index === i && !failed;
        return (
          <div key={step} className="flex flex-1 flex-col items-center">
            <div
              className={`h-2 w-full rounded-full ${
                failed
                  ? "bg-rose-300"
                  : done
                  ? "bg-brand-500"
                  : active
                  ? "bg-brand-300"
                  : "bg-slate-200 dark:bg-slate-700"
              }`}
            />
            <span className="mt-1 text-[10px] uppercase tracking-wide text-ink-500 dark:text-slate-400">{step}</span>
          </div>
        );
      })}
      {failed && <span className="ml-2 text-xs font-medium text-rose-600">FAILED</span>}
    </div>
  );
}
