import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import type { Job } from "../types";

type Req = { value: string; priority: "required" | "preferred"; is_hard_gate: boolean };

export default function JobCreate() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [department, setDepartment] = useState("");
  const [location, setLocation] = useState("");
  const [seniority, setSeniority] = useState("");
  const [description, setDescription] = useState("");
  const [hardGate, setHardGate] = useState(false);
  const [requirements, setRequirements] = useState<Req[]>([
    { value: "Python", priority: "required", is_hard_gate: false },
  ]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function updateReq(i: number, patch: Partial<Req>) {
    setRequirements((rs) => rs.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const { data } = await api.post<Job>("/jobs", {
        title,
        description,
        department: department || null,
        location: location || null,
        seniority: seniority || null,
        hard_gate: hardGate,
        parse_with_llm: false,
        requirements: requirements
          .filter((r) => r.value.trim())
          .map((r) => ({
            kind: "skill",
            priority: r.priority,
            value: r.value.trim(),
            is_hard_gate: r.priority === "required" ? r.is_hard_gate : false,
          })),
      });
      navigate(`/jobs/${data.id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold text-ink-900 dark:text-slate-100">Create a job</h1>
      {error && <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}

      <div className="card space-y-4 p-5">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="label">Job title</label>
            <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} required />
          </div>
          <div>
            <label className="label">Department</label>
            <input className="input" value={department} onChange={(e) => setDepartment(e.target.value)} />
          </div>
          <div>
            <label className="label">Location</label>
            <input className="input" value={location} onChange={(e) => setLocation(e.target.value)} />
          </div>
          <div>
            <label className="label">Seniority</label>
            <input className="input" value={seniority} onChange={(e) => setSeniority(e.target.value)} />
          </div>
        </div>
        <div>
          <label className="label">Job description</label>
          <textarea className="input h-40" value={description}
            onChange={(e) => setDescription(e.target.value)} required />
        </div>
        <label className="flex items-center gap-2 text-sm text-ink-700 dark:text-slate-300">
          <input type="checkbox" checked={hardGate} onChange={(e) => setHardGate(e.target.checked)} />
          Treat missing mandatory requirements as a hard eligibility gate
        </label>
      </div>

      <div className="card space-y-3 p-5">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-ink-900 dark:text-slate-100">Requirements</h2>
          <button type="button" className="btn-secondary"
            onClick={() => setRequirements((r) => [...r, { value: "", priority: "required", is_hard_gate: false }])}>
            + Add requirement
          </button>
        </div>
        {requirements.map((r, i) => (
          <div key={i} className="flex flex-wrap items-center gap-3">
            <input className="input flex-1" placeholder="e.g. FastAPI"
              value={r.value} onChange={(e) => updateReq(i, { value: e.target.value })} />
            <select className="input w-40" value={r.priority}
              onChange={(e) => updateReq(i, { priority: e.target.value as Req["priority"] })}>
              <option value="required">Mandatory</option>
              <option value="preferred">Preferred</option>
            </select>
            {r.priority === "required" && (
              <label className="flex items-center gap-1 text-sm text-ink-600 dark:text-slate-300">
                <input type="checkbox" checked={r.is_hard_gate}
                  onChange={(e) => updateReq(i, { is_hard_gate: e.target.checked })} />
                Gate
              </label>
            )}
            <button type="button" className="btn-secondary"
              onClick={() => setRequirements((rs) => rs.filter((_, idx) => idx !== i))}>
              Remove
            </button>
          </div>
        ))}
      </div>

      <div className="flex justify-end gap-3">
        <button type="button" className="btn-secondary" onClick={() => navigate(-1)}>Cancel</button>
        <button className="btn-primary" disabled={busy}>{busy ? "Creating…" : "Create job"}</button>
      </div>
    </form>
  );
}
