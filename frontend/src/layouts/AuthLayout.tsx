import { Outlet } from "react-router-dom";

export default function AuthLayout() {
  return (
    <div className="grid min-h-screen place-items-center bg-gradient-to-br from-brand-600 to-brand-900 p-4">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center text-white">
          <h1 className="text-2xl font-bold">Intelligent Resume Screening</h1>
          <p className="mt-1 text-sm text-brand-100">
            Explainable, privacy-conscious candidate ranking
          </p>
        </div>
        <div className="card p-6" role="main">
          <Outlet />
        </div>
        <p className="mt-4 text-center text-xs text-white"><a className="underline" href="/privacy">Privacy</a> · <a className="underline" href="/terms">Terms</a> · <a className="underline" href="/cookies">Cookies</a></p>
      </div>
    </div>
  );
}
