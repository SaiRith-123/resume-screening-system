// Shared API types (mirror the backend Pydantic schemas).

export interface AuthUser {
  id: number;
  email: string;
  full_name: string;
  role: string;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export type MatchStatus = "MATCH" | "PARTIAL_MATCH" | "MISSING" | "UNKNOWN";
export type CandidateStatus =
  | "UPLOADED" | "PROCESSING" | "EXTRACTED" | "ANALYZED" | "SCREENED" | "FAILED";

export interface Requirement {
  id: number;
  kind: string;
  priority: "required" | "preferred";
  value: string;
  normalized_value?: string | null;
  min_years?: number | null;
  is_hard_gate: boolean;
  weight: number;
}

export interface Job {
  id: number;
  title: string;
  department?: string | null;
  seniority?: string | null;
  location?: string | null;
  employment_type?: string | null;
  description: string;
  weights: Record<string, number>;
  hard_gate: boolean;
  status: string;
  created_at: string;
  requirements: Requirement[];
}

export interface JobListItem {
  id: number;
  title: string;
  status: string;
  created_at: string;
  candidate_count: number;
  average_match: number;
  top_candidate?: string | null;
}

export interface SkillMatch {
  skill: string;
  status: MatchStatus;
  confidence: number;
  strategy: string;
  context: string;
  evidence?: string | null;
}

export interface ScoreBreakdown {
  skill_score: number;
  experience_score: number;
  semantic_score: number;
  education_score: number;
  project_score: number;
  certification_score: number;
  preferred_score: number;
  final_score: number;
  weights: Record<string, number>;
}

export interface Evidence {
  requirement: string;
  requirement_kind: string;
  status: MatchStatus;
  confidence: number;
  evidence_text?: string | null;
  source: string;
}

export interface GenAIExplanation {
  summary?: string | null;
  strengths: string[];
  weaknesses: string[];
  matched_requirements: string[];
  missing_requirements: string[];
  evidence: string[];
  confidence: number;
  available: boolean;
  note?: string | null;
}

export interface ScreeningResult {
  id: number;
  candidate_id: number;
  job_id: number;
  rank?: number | null;
  eligibility_status: string;
  recommendation: string;
  needs_review: boolean;
  missing_requirements: string[];
  matched_skills: string[];
  partial_skills: string[];
  missing_skills: string[];
  scores: ScoreBreakdown;
  evidence: Evidence[];
  explanation?: GenAIExplanation | null;
}

export interface CandidateListItem {
  id: number;
  name?: string | null;
  status: CandidateStatus;
  total_experience_years: number;
  final_score?: number | null;
  rank?: number | null;
  eligibility_status?: string | null;
  skill_score?: number | null;
  experience_score?: number | null;
  semantic_score?: number | null;
  missing_requirements: string[];
  needs_review: boolean;
}

export interface EducationItem {
  degree?: string | null;
  field_of_study?: string | null;
  institution?: string | null;
  start_year?: number | null;
  end_year?: number | null;
}

export interface ExperienceItem {
  company?: string | null;
  title?: string | null;
  description?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current: boolean;
  kind: string;
}

export interface ProjectItem {
  name?: string | null;
  description?: string | null;
  technologies: string[];
}

export interface ResumeStructured {
  candidate_name?: string | null;
  contact: { email?: string | null; phone?: string | null };
  summary?: string | null;
  skills: string[];
  technical_skills: string[];
  soft_skills: string[];
  programming_languages: string[];
  frameworks: string[];
  databases: string[];
  cloud_technologies: string[];
  tools: string[];
  education: EducationItem[];
  experience: ExperienceItem[];
  projects: ProjectItem[];
  certifications: { name?: string | null; issuer?: string | null; year?: number | null }[];
  languages: string[];
  total_experience_years: number;
}

export interface CandidateDetail {
  id: number;
  job_id: number;
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  status: CandidateStatus;
  processing_error?: string | null;
  structured: ResumeStructured;
  total_experience_years: number;
  created_at?: string | null;
  screening?: ScreeningResult | null;
}

export interface InterviewQuestions {
  candidate_id: number;
  job_id: number;
  available: boolean;
  note?: string | null;
  technical: string[];
  project: string[];
  behavioral: string[];
  role: string[];
}

export interface UploadResponse {
  accepted: { candidate_id: number; filename: string; status: string }[];
  rejected: { filename: string; reason: string }[];
  screened: number;
}
