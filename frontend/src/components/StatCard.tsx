import { ReactNode } from "react";

export default function StatCard({
  label,
  value,
  hint,
  icon,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  icon?: ReactNode;
}) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-ink-500 dark:text-slate-400">{label}</p>
          <p className="mt-2 text-3xl font-semibold text-ink-900 dark:text-slate-100">{value}</p>
          {hint && <p className="mt-1 text-xs text-ink-500 dark:text-slate-400">{hint}</p>}
        </div>
        {icon && <div className="text-brand-500">{icon}</div>}
      </div>
    </div>
  );
}
