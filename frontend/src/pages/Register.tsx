import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [acceptPrivacy, setAcceptPrivacy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!acceptTerms || !acceptPrivacy) {
      setError("Accept the Terms of Service and Privacy Policy to continue.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await register(email, fullName, password, acceptTerms, acceptPrivacy);
      navigate("/");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <h2 className="text-xl font-semibold text-ink-900 dark:text-slate-100">Create your account</h2>
      {error && <p className="rounded-lg bg-rose-50 p-2 text-sm text-rose-700">{error}</p>}
      <div>
        <label className="label" htmlFor="name">Full name</label>
        <input id="name" className="input" value={fullName}
          onChange={(e) => setFullName(e.target.value)} required />
      </div>
      <label className="flex items-start gap-2 text-sm text-ink-700 dark:text-slate-300">
        <input type="checkbox" checked={acceptTerms} onChange={(e) => setAcceptTerms(e.target.checked)} required />
        <span>I accept the <Link className="text-brand-700 underline" to="/terms">Terms of Service</Link>.</span>
      </label>
      <label className="flex items-start gap-2 text-sm text-ink-700 dark:text-slate-300">
        <input type="checkbox" checked={acceptPrivacy} onChange={(e) => setAcceptPrivacy(e.target.checked)} required />
        <span>I have read the <Link className="text-brand-700 underline" to="/privacy">Privacy Policy</Link>.</span>
      </label>
      <div>
        <label className="label" htmlFor="email">Work email</label>
        <input id="email" className="input" type="email" value={email}
          onChange={(e) => setEmail(e.target.value)} required />
      </div>
      <div>
        <label className="label" htmlFor="password">Password (min 8 characters)</label>
        <input id="password" className="input" type="password" value={password}
          onChange={(e) => setPassword(e.target.value)} minLength={8} required />
      </div>
      <button className="btn-primary w-full" disabled={busy}>
        {busy ? "Creating…" : "Create account"}
      </button>
      <p className="text-center text-sm text-ink-500 dark:text-slate-400">
        Already registered? <Link className="text-brand-600" to="/login">Sign in</Link>
      </p>
    </form>
  );
}
