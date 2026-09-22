import { ReactNode, useMemo, useState } from "react";

export interface Column<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  sortValue?: (row: T) => string | number;
  className?: string;
}

export default function DataTable<T>({
  columns,
  rows,
  pageSize = 10,
  emptyMessage = "No records.",
  loading = false,
}: {
  columns: Column<T>[];
  rows: T[];
  pageSize?: number;
  emptyMessage?: string;
  loading?: boolean;
}) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [asc, setAsc] = useState(true);
  const [page, setPage] = useState(0);

  const sorted = useMemo(() => {
    if (!sortKey) return rows;
    const col = columns.find((c) => c.key === sortKey);
    if (!col?.sortValue) return rows;
    const copy = [...rows];
    copy.sort((a, b) => {
      const va = col.sortValue!(a);
      const vb = col.sortValue!(b);
      if (va < vb) return asc ? -1 : 1;
      if (va > vb) return asc ? 1 : -1;
      return 0;
    });
    return copy;
  }, [rows, sortKey, asc, columns]);

  const pageCount = Math.max(1, Math.ceil(sorted.length / pageSize));
  const current = sorted.slice(page * pageSize, page * pageSize + pageSize);

  function toggleSort(key: string) {
    if (sortKey === key) setAsc(!asc);
    else {
      setSortKey(key);
      setAsc(true);
    }
  }

  if (loading) {
    return (
      <div className="card overflow-hidden" aria-busy="true" role="status"
           aria-label="Loading table data">
        <div className="divide-y divide-slate-100 dark:divide-slate-800">
          {Array.from({ length: 5 }).map((_, rowIndex) => (
            <div key={rowIndex} className="flex gap-4 px-4 py-3.5">
              {columns.map((col) => (
                <div key={col.key}
                     className="h-4 flex-1 animate-pulse rounded bg-slate-200 dark:bg-slate-700"
                     style={{ maxWidth: col.key === "actions" ? 90 : undefined }} />
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (rows.length === 0) {
    return <div className="card p-8 text-center text-sm text-ink-500 dark:text-slate-400">{emptyMessage}</div>;
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-sm">
          <thead className="bg-slate-50 dark:bg-slate-900/50">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`px-4 py-3 text-left font-semibold text-ink-700 dark:text-slate-300 ${
                    col.sortValue ? "cursor-pointer select-none" : ""
                  } ${col.className ?? ""}`}
                  onClick={() => col.sortValue && toggleSort(col.key)}
                >
                  {col.header}
                  {sortKey === col.key && <span className="ml-1">{asc ? "▲" : "▼"}</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-900">
            {current.map((row, i) => (
              <tr key={i} className="hover:bg-slate-50 dark:hover:bg-slate-800 dark:bg-slate-900/50">
                {columns.map((col) => (
                  <td key={col.key} className={`px-4 py-3 ${col.className ?? ""}`}>
                    {col.render(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pageCount > 1 && (
        <div className="flex items-center justify-between border-t border-slate-200 dark:border-slate-800 px-4 py-3 text-sm">
          <span className="text-ink-500 dark:text-slate-400">
            Page {page + 1} of {pageCount}
          </span>
          <div className="flex gap-2">
            <button
              className="btn-secondary"
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
            >
              Previous
            </button>
            <button
              className="btn-secondary"
              disabled={page >= pageCount - 1}
              onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
