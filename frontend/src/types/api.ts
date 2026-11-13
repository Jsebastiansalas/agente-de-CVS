// Tipos TypeScript en estricta sincronía con los esquemas Pydantic del backend

export type SeniorityLevel =
  | 'INTERN'
  | 'JUNIOR'
  | 'MID'
  | 'SENIOR'
  | 'LEAD'
  | 'OPERATIONAL'
  | 'NO_ESPECIFICADO';

export interface LanguageRequirement {
  language: string;
  min_level: string;
}

export interface VacancySchema {
  vacancy_id: string;
  title: string;
  seniority: SeniorityLevel;
  min_years_experience: number;
  knockout_requirements: string[];
  must_have_skills: string[];
  nice_to_have_skills: string[];
  required_languages: LanguageRequirement[];
  required_education: string | null;
  responsibilities: string[];
}

export type Verdict = 'ACEPTABLE' | 'ACEPTABLE_CON_RESERVAS' | 'NO_ACEPTABLE';

export type KnockoutStatus = 'CUMPLIDO' | 'NO_CUMPLIDO' | 'NO_MENCIONADO_EN_CV';

export type SkillMatchLevel =
  | 'EXACTO'
  | 'PARCIAL_EQUIVALENTE'
  | 'SOLO_LISTADO'
  | 'NO_EVIDENCIADO';

export type SkillType = 'MUST_HAVE' | 'NICE_TO_HAVE';

export interface KnockoutEvaluation {
  requirement: string;
  status: KnockoutStatus;
  calculated_months?: number | null;
  evidence?: string | null;
  notes?: string | null;
}

export interface SkillEvaluation {
  skill: string;
  skill_type: SkillType;
  match_level: SkillMatchLevel;
  proven_in_work_experience: boolean;
  evidence?: string | null;
  explanation: string;
}

export interface CategoryScore {
  score: number;
  weight: number;
  weighted: number;
  justification: string;
}

export interface CategoryScores {
  relevant_experience: CategoryScore;
  must_have_skills: CategoryScore;
  nice_to_have_skills: CategoryScore;
  education_and_languages: CategoryScore;
}

export interface SecurityFlags {
  prompt_injection_detected: boolean;
  inconsistent_dates_warning: boolean;
  details: string[];
}

export interface EvaluationResultSchema {
  evaluation_id: string;
  vacancy_title: string;
  candidate_id: string;
  verdict: Verdict;
  overall_score: number;
  category_scores: CategoryScores;
  knockout_requirements: KnockoutEvaluation[];
  skills_matrix: SkillEvaluation[];
  executive_summary: string;
  detected_gaps: string[];
  suggested_interview_questions: string[];
  security_flags?: SecurityFlags;
}

export interface CandidateContactPII {
  candidate_id: string;
  full_name?: string | null;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
}

export interface FeedbackRecord {
  id?: number | null;
  evaluation_id: string;
  agrees_with_agent: boolean;
  human_verdict: Verdict;
  comment: string;
  created_at: string;
}

export interface StoredEvaluation {
  evaluation: EvaluationResultSchema;
  contact_pii: CandidateContactPII;
  source_file?: string | null;
  created_at: string;
  latest_feedback?: FeedbackRecord | null;
}

export interface RankedCandidateItem {
  rank: number;
  source_file: string;
  evaluation: EvaluationResultSchema;
  contact_pii: CandidateContactPII;
  duration_seconds: number;
}

export interface UsageSummary {
  total_calls?: number;
  total_prompt_tokens?: number;
  total_output_tokens?: number;
  total_cached_tokens?: number;
  total_tokens?: number;
  total_latency_ms?: number;
  avg_latency_ms?: number;
  total_estimated_cost_usd?: number;
}

export interface BatchEvaluationResult {
  vacancy: VacancySchema;
  ranked_candidates: RankedCandidateItem[];
  errors: Array<{ source_file: string; error: string }>;
  total_duration_seconds: number;
  usage_summary: UsageSummary;
}

export interface SingleEvaluationResponse {
  source_file: string;
  evaluation: EvaluationResultSchema;
  contact_pii: CandidateContactPII;
}
