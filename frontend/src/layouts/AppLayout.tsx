import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useTheme } from "../hooks/useTheme";
import Disclaimer from "../components/Disclaimer";

const NAV = [
  { to: "/", label: "Dashboard", icon: "📊" },
  { to: "/jobs", label: "Jobs", icon: "💼" },
  { to: "/search", label: "Search", icon: "🔍" },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const { theme, toggle } = useTheme();
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-64 flex-col border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 md:flex">
        <div className="mb-8 flex items-center gap-2 px-2">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-brand-600 text-white">
            RS
          </div>
          <div>
            <p className="text-sm font-semibold text-ink-900 dark:text-slate-100">ResumeScreening</p>
            <p className="text-xs text-ink-500 dark:text-slate-400">AI recruiting console</p>
          </div>
        </div>
        <nav className="flex-1 space-y-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium ${
                  isActive ? "bg-brand-50 text-brand-700" : "text-ink-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 dark:bg-slate-900/50"
                }`
              }
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-4 border-t border-slate-200 dark:border-slate-800 pt-4">
          <button
            className="btn-secondary mb-2 w-full"
            onClick={toggle}
            aria-label="Toggle dark mode"
            title="Toggle dark mode"
          >
            {theme === "dark" ? "Light mode" : "Dark mode"}
          </button>
          <p className="truncate text-sm font-medium text-ink-800 dark:text-slate-200">{user?.full_name}</p>
          <p className="truncate text-xs text-ink-500 dark:text-slate-400">{user?.email}</p>
          <a className="mt-2 block text-xs text-brand-700 underline" href="/account/delete">Delete account and data</a>
          <button
            className="btn-secondary mt-3 w-full"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-6 py-3 md:hidden">
          <span className="font-semibold">ResumeScreening</span>
          <div className="flex gap-2">
            <button className="btn-secondary" onClick={toggle} aria-label="Toggle dark mode">
              {theme === "dark" ? "Light" : "Dark"}
            </button>
            <button className="btn-secondary" onClick={() => { logout(); navigate("/login"); }}>
              Sign out
            </button>
          </div>
        </header>
        <main className="flex-1 p-6">
          <Outlet />
        </main>
        <footer className="px-6 pb-6">
          <Disclaimer />
          <p className="mt-3 text-xs text-ink-600 dark:text-slate-400"><a className="underline" href="/privacy">Privacy</a> · <a className="underline" href="/terms">Terms</a> · <a className="underline" href="/cookies">Cookies</a></p>
        </footer>
      </div>
    </div>
  );
}
