export default function EmptyState({
  title,
  message,
  action,
}: {
  title: string;
  message?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="card flex flex-col items-center justify-center gap-3 p-12 text-center">
      <div className="grid h-12 w-12 place-items-center rounded-full bg-slate-100 dark:bg-slate-800 text-2xl">📄</div>
      <h3 className="text-lg font-semibold text-ink-900 dark:text-slate-100">{title}</h3>
      {message && <p className="max-w-md text-sm text-ink-500 dark:text-slate-400">{message}</p>}
      {action}
    </div>
  );
}
