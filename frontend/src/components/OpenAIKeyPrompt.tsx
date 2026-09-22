import { useState } from "react";
import { setOpenAIKey } from "../api/openaiKey";

export default function OpenAIKeyPrompt() {
  const [open, setOpen] = useState(true);
  const [key, setKey] = useState("");

  if (!open) return null;

  function save() {
    setOpenAIKey(key);
    setOpen(false);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4" role="presentation">
      <div className="card w-full max-w-md p-6 shadow-xl" role="dialog" aria-modal="true" aria-labelledby="openai-key-title">
        <h2 id="openai-key-title" className="text-xl font-semibold text-ink-900 dark:text-slate-100">Connect OpenAI</h2>
        <p className="mt-2 text-sm text-ink-600 dark:text-slate-300">
          Add your key for AI resume enrichment, explanations, and interview questions.
          It stays in this browser session and is not saved by this app.
        </p>
        <label className="label mt-4" htmlFor="openai-key">OpenAI API key</label>
        <input id="openai-key" className="input" type="password" value={key}
          onChange={(event) => setKey(event.target.value)} placeholder="sk-..." autoFocus />
        <div className="mt-5 flex justify-end gap-3">
          <button className="btn-secondary" type="button" onClick={() => setOpen(false)}>Skip</button>
          <button className="btn-primary" type="button" onClick={save} disabled={!key.trim()}>Use key</button>
        </div>
      </div>
    </div>
  );
}