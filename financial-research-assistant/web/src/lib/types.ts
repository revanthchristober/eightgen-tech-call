export interface Citation {
  doc_id: string;
  page: number;
  quote: string;
}

export interface ChatAnswer {
  answer: string;
  citations: Citation[];
  insufficient_data: boolean;
}

export interface ComparisonRow {
  metric: string;
  company: string;
  period: string;
  value: string;
  citation: Citation;
}

export interface SubQuestionResult {
  sub_question: string;
  answer: ChatAnswer | null;
  error: string | null;
}

export interface ResearchReport {
  summary: string;
  comparison_table: ComparisonRow[];
  trends: string;
  risks: string;
  conclusion: string;
  sub_results: SubQuestionResult[];
  dropped_unverified_rows: number;
}

export type JobStatus = "pending" | "running" | "partial" | "done" | "failed";

export interface ResearchJob {
  job_id: string;
  status: JobStatus;
  brief: string;
  progress: string;
  sub_questions_total: number;
  sub_questions_done: number;
  report: ResearchReport | null;
  error: string | null;
}
