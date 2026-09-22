import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import api from "../api/client";

export default function DataDeletion() {
  const { logout } = useAuth();
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  async function deleteData() {
    if (!confirmed) return;
    setBusy(true);
    try {
      await api.post("/auth/data-deletion-request");
      setDone(true);
      logout();
    } finally {
      setBusy(false);
    }
  }
  return <main className="mx-auto max-w-2xl space-y-5 p-6"><h1 className="text-2xl font-bold text-ink-900 dark:text-slate-100">Delete account and data</h1><p className="text-ink-700 dark:text-slate-300">This permanently deletes your account, jobs, uploaded resumes, candidate records, and screening results owned by this account.</p>{done ? <p className="rounded-lg bg-emerald-50 p-3 text-emerald-800">Your deletion request was completed.</p> : <><label className="flex items-start gap-2 text-sm text-ink-700 dark:text-slate-300"><input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} /><span>I understand this action cannot be undone.</span></label><button className="btn-danger" disabled={busy || !confirmed} onClick={deleteData}>{busy ? "Deleting…" : "Delete my account and data"}</button></>}</main>;
}