import { useEffect, useState } from "react";

const COOKIE_CONSENT_KEY = "rss_cookie_consent";

export default function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(!localStorage.getItem(COOKIE_CONSENT_KEY));
  }, []);

  if (!visible) return null;

  function choose(value: string) {
    localStorage.setItem(COOKIE_CONSENT_KEY, value);
    setVisible(false);
  }

  return (
    <aside
      className="fixed inset-x-0 bottom-0 z-40 border-t border-slate-300 bg-white p-4 shadow-lg dark:border-slate-700 dark:bg-slate-900"
      aria-label="Cookie notice"
    >
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3">
        <p className="max-w-3xl text-sm text-ink-700 dark:text-slate-200">
          This app uses necessary browser storage for sign-in, appearance, and this choice.
          It does not use advertising or analytics cookies. <a className="text-brand-700 underline" href="/cookies">Cookie Policy</a>.
        </p>
        <div className="flex gap-2">
          <button className="btn-secondary" onClick={() => choose("necessary")}>Use necessary only</button>
          <button className="btn-primary" onClick={() => choose("accepted")}>Continue</button>
        </div>
      </div>
    </aside>
  );
}