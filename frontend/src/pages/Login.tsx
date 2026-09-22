import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { firebaseConfigured } from "../api/firebase";

export default function Login() {
  const { login, loginWithGoogle } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("demo@recruiter.io");
  const [password, setPassword] = useState("demo12345");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [acceptPrivacy, setAcceptPrivacy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function onGoogleSignIn() {
    setBusy(true);
    setError(null);
    try {
      await loginWithGoogle(acceptTerms, acceptPrivacy);
      navigate("/");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <h2 className="text-xl font-semibold text-ink-900 dark:text-slate-100">Sign in</h2>
      {error && <p className="rounded-lg bg-rose-50 p-2 text-sm text-rose-700">{error}</p>}
      {firebaseConfigured && (
        <>
          <label className="flex items-start gap-2 text-sm text-ink-700 dark:text-slate-300">
            <input type="checkbox" checked={acceptTerms} onChange={(e) => setAcceptTerms(e.target.checked)} required />
            <span>I accept the <Link className="text-brand-600 underline" to="/terms">Terms of Service</Link>.</span>
          </label>
          <label className="flex items-start gap-2 text-sm text-ink-700 dark:text-slate-300">
            <input type="checkbox" checked={acceptPrivacy} onChange={(e) => setAcceptPrivacy(e.target.checked)} required />
            <span>I accept the <Link className="text-brand-600 underline" to="/privacy">Privacy Policy</Link>.</span>
          </label>
          <button type="button" className="btn-secondary w-full" onClick={onGoogleSignIn} disabled={busy || !acceptTerms || !acceptPrivacy}>
            {busy ? "Connecting…" : "Continue with Google"}
          </button>
          <div className="flex items-center gap-3 text-xs text-ink-400"><span className="h-px flex-1 bg-ink-200" />or<span className="h-px flex-1 bg-ink-200" /></div>
        </>
      )}
      <div>
        <label className="label" htmlFor="email">Email</label>
        <input id="email" className="input" type="email" value={email}
          onChange={(e) => setEmail(e.target.value)} required />
      </div>
      <div>
        <label className="label" htmlFor="password">Password</label>
        <input id="password" className="input" type="password" value={password}
          onChange={(e) => setPassword(e.target.value)} required />
      </div>
      <button className="btn-primary w-full" disabled={busy}>
        {busy ? "Signing in…" : "Sign in"}
      </button>
      <p className="text-center text-sm text-ink-500 dark:text-slate-400">
        No account? <Link className="text-brand-600" to="/register">Register</Link>
      </p>
    </form>
  );
}
