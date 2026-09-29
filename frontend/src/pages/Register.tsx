import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function Register() {
  const { register, loginWithGoogle } = useAuth();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
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
  setSuccess(null);

  try {
    await register(email, fullName, password, acceptTerms, acceptPrivacy);

    setSuccess(
      "Account created. Please check your email and verify your email address before signing in."
    );
  } catch (err) {
    setError((err as Error).message);
  } finally {
    setBusy(false);
  }
}
async function onGoogleSignUp() {
  if (!acceptTerms || !acceptPrivacy) {
    setError("Accept the Terms of Service and Privacy Policy to continue.");
    return;
  }

  setBusy(true);
  setError(null);
  setSuccess(null);

  try {
    await loginWithGoogle(acceptTerms, acceptPrivacy);
    window.location.href = "/";
  } catch (err) {
    setError((err as Error).message);
  } finally {
    setBusy(false);
  }
}

  const hasValidLength = password.length >= 8 && password.length <= 20;
  const hasUppercase = /[A-Z]/.test(password);
  const hasLowercase = /[a-z]/.test(password);
  const hasNumber = /\d/.test(password);
  const hasSpecial = /[^A-Za-z\d]/.test(password);

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <h2 className="text-xl font-semibold text-ink-900 dark:text-slate-100">
        Create your account
      </h2>

      {error && (
        <p className="rounded-lg bg-rose-50 p-2 text-sm text-rose-700">
          {error}
        </p>
      )}  
      {success && (
        <p className="rounded-lg bg-green-50 p-2 text-sm text-green-700">
          {success}
        </p>
      )}


      <div>
        <label className="label" htmlFor="name">
          Full name
        </label>
        <input
          id="name"
          className="input"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          required
        />
      </div>

      <div>
        <label className="label" htmlFor="email">
          Work email
        </label>
        <input
          id="email"
          className="input"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>

      <div>
        <label className="label" htmlFor="password">
          Password
        </label>

        <input
          id="password"
          className="input"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          minLength={8}
          maxLength={20}
          pattern="^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,20}$"
          title="Password must be 8–20 characters and contain at least one uppercase letter, one lowercase letter, one number, and one special character."
          required
        />

        <div className="mt-2 space-y-1 text-sm">
          <p className={hasValidLength ? "text-green-600" : "text-ink-500"}>
            {hasValidLength ? "☑" : "☐"} 8–20 characters
          </p>

          <p className={hasUppercase ? "text-green-600" : "text-ink-500"}>
            {hasUppercase ? "☑" : "☐"} One capital letter
          </p>

          <p className={hasLowercase ? "text-green-600" : "text-ink-500"}>
            {hasLowercase ? "☑" : "☐"} One small letter
          </p>

          <p className={hasNumber ? "text-green-600" : "text-ink-500"}>
            {hasNumber ? "☑" : "☐"} One number
          </p>

          <p className={hasSpecial ? "text-green-600" : "text-ink-500"}>
            {hasSpecial ? "☑" : "☐"} One special character
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 text-xs text-ink-400 dark:text-slate-500">
        <span className="h-px flex-1 bg-ink-200 dark:bg-slate-700" />
        or
        <span className="h-px flex-1 bg-ink-200 dark:bg-slate-700" />
      </div>

      <button
        type="button"
        onClick={onGoogleSignUp}
        disabled={busy}
        className="btn-secondary w-full"
      >
        {busy ? "Connecting…" : "Continue with Google"}
      </button>

      <label className="flex items-start gap-2 text-sm text-ink-700 dark:text-slate-300">
        <input
          type="checkbox"
          checked={acceptTerms}
          onChange={(e) => setAcceptTerms(e.target.checked)}
        />
        <span>
          I accept the{" "}
          <Link className="text-brand-700 underline" to="/terms">
            Terms of Service
          </Link>
          .
        </span>
      </label>

      <label className="flex items-start gap-2 text-sm text-ink-700 dark:text-slate-300">
        <input
          type="checkbox"
          checked={acceptPrivacy}
          onChange={(e) => setAcceptPrivacy(e.target.checked)}
        />
        <span>
          I have read the{" "}
          <Link className="text-brand-700 underline" to="/privacy">
            Privacy Policy
          </Link>
          .
        </span>
      </label>

      <button className="btn-primary w-full" disabled={busy}>
        {busy ? "Creating…" : "Create account"}
      </button>

      <p className="text-center text-sm text-ink-500 dark:text-slate-400">
        Already registered?{" "}
        <Link className="text-brand-600" to="/login">
          Sign in
        </Link>
      </p>
    </form>
  );
}