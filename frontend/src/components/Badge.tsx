import { ReactNode } from "react";

type Tone = "neutral" | "success" | "warning" | "danger" | "info";

const TONES: Record<Tone, string> = {
  neutral: "bg-slate-100 dark:bg-slate-800 text-slate-700",
  success: "bg-emerald-100 text-emerald-700",
  warning: "bg-amber-100 text-amber-800",
  danger: "bg-rose-100 text-rose-700",
  info: "bg-brand-100 text-brand-700",
};

export default function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: Tone;
}) {
  return <span className={`badge ${TONES[tone]}`}>{children}</span>;
}

export function statusTone(status?: string | null): Tone {
  switch (status) {
    case "MATCH":
    case "MEETS_ALL_MANDATORY":
    case "SCREENED":
      return "success";
    case "PARTIAL_MATCH":
    case "MISSING_REQUIREMENTS":
      return "warning";
    case "DOES_NOT_MEET_MANDATORY":
    case "MISSING":
    case "FAILED":
      return "danger";
    default:
      return "neutral";
  }
}
