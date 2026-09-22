import { Link, useLocation } from "react-router-dom";

const CONTENT = {
  "/privacy": {
    title: "Privacy Policy",
    sections: [
      ["Data we process", "Account details, job descriptions, uploaded resumes, screening results, and settings needed to provide this application."],
      ["How we use it", "We use this data to authenticate recruiters, process resumes, calculate transparent screening results, and provide exports and explanations. Resume data is not used to score protected characteristics."],
      ["Third parties", "The application has no advertising or analytics SDK. If you provide an OpenAI key, the backend may send resume and job content to OpenAI for the AI feature you request. Review OpenAI's terms and privacy documentation before using that feature."],
      ["Retention and control", "You can request deletion of your account and associated recruiter-owned data from the account controls. Backups or legal retention may follow the deployment operator's documented retention schedule."],
    ],
  },
  "/terms": {
    title: "Terms of Service",
    sections: [
      ["Use of the service", "Use this application only for lawful recruiting and evaluation workflows that you are authorized to conduct. Keep account credentials and API keys confidential."],
      ["Decision support", "Screening scores and AI outputs are recommendations, not employment decisions. Recruiters remain responsible for review, legal compliance, accommodations, and final decisions."],
      ["Uploaded content", "You confirm that you have the right to upload resumes and job descriptions and that your use complies with applicable privacy and employment laws."],
      ["Availability", "This project is provided as an application service by its operator. Features may change, and AI providers can be unavailable or return incomplete output."],
    ],
  },
  "/cookies": {
    title: "Cookie Policy",
    sections: [
      ["Necessary browser storage", "The frontend uses local browser storage for authentication state, the selected theme, and your cookie-consent choice. These values support the interface and are not advertising trackers."],
      ["No optional tracking", "This application does not install analytics, advertising, social, fingerprinting, or cross-site tracking SDKs."],
      ["Your choice", "You can clear browser storage at any time through your browser settings. Clearing it signs you out and resets preferences."],
    ],
  },
};

export default function Legal() {
  const page = CONTENT[useLocation().pathname as keyof typeof CONTENT] ?? CONTENT["/privacy"];
  return <main className="mx-auto max-w-3xl space-y-6 p-6"><Link className="text-brand-700 underline" to="/login">Back to sign in</Link><h1 className="text-3xl font-bold text-ink-900 dark:text-slate-100">{page.title}</h1><p className="text-sm text-ink-600 dark:text-slate-400">Effective September 16, 2026. This project’s operator should update these pages with its legal entity and contact details before production use.</p>{page.sections.map(([heading, text]) => <section key={heading} className="space-y-2"><h2 className="text-lg font-semibold text-ink-900 dark:text-slate-100">{heading}</h2><p className="leading-7 text-ink-700 dark:text-slate-300">{text}</p></section>)}</main>;
}