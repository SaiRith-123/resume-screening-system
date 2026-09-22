import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ScoreBreakdown } from "../types";

const LABELS: Record<string, string> = {
  skill_score: "Skills",
  experience_score: "Experience",
  semantic_score: "Semantic",
  education_score: "Education",
  project_score: "Projects",
  certification_score: "Certifications",
  preferred_score: "Preferred",
};

export default function ScoreChart({ scores }: { scores: ScoreBreakdown }) {
  const data = Object.keys(LABELS).map((key) => ({
    name: LABELS[key],
    value: Math.round((scores as unknown as Record<string, number>)[key] ?? 0),
  }));

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div className="card p-4">
        <h4 className="mb-2 text-sm font-semibold text-ink-700 dark:text-slate-300">Score breakdown</h4>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={data} outerRadius="70%">
              <PolarGrid />
              <PolarAngleAxis dataKey="name" tick={{ fontSize: 11 }} />
              <Radar dataKey="value" stroke="#4f46e5" fill="#6366f1" fillOpacity={0.4} />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="card p-4">
        <h4 className="mb-2 text-sm font-semibold text-ink-700 dark:text-slate-300">Component scores (0-100)</h4>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ left: 24 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 100]} />
              <YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {data.map((d, i) => (
                  <Cell key={i} fill={d.value >= 70 ? "#059669" : d.value >= 45 ? "#d97706" : "#e11d48"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
