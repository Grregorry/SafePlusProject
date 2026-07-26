export type SafePlusGuidanceSource = {
  source_id: string;
  title: string;
  url: string;
  guidance: string[];
};

export type AIDomainSummary = {
  domain_name: string;
  score: number;
  maturity_level: string;
  summary: string;
  strengths: string[];
  improvement_areas: string[];
  source_ids: string[];
};

export type AIPriorityAction = {
  priority: number;
  title: string;
  assessment_evidence: string[];
  reason: string;
  recommended_action: string;
  related_domain: string;
  urgency: string;
  source_ids: string[];
  source_relevance: string;
};

export type AIRoadmapItem = {
  timeframe: string;
  objective: string;
  actions: string[];
  success_indicator: string;
  source_ids: string[];
};

export type AIDomainSummariesData = {
  key_strengths?: string[];
  key_risks?: string[];
  domains?: AIDomainSummary[];
  limitations?: string[];
  guidance_sources?: SafePlusGuidanceSource[];
};

export type AIAnalysis = {
  id: number;
  assessment_id: number;
  overall_summary: string | null;
  domain_summaries: AIDomainSummariesData | null;
  priority_actions: AIPriorityAction[] | null;
  roadmap: AIRoadmapItem[] | null;
  ai_provider: string;
  generated_at: string | null;
  status: string;
};

export type AIAnalysisGenerationResult =
  AIAnalysis & {
    message: string;
  };

export type AIAnalysisSourcesResult = {
  sources: SafePlusGuidanceSource[];
  count: number;
  notice: string;
};

type ApiErrorResponse = {
  detail?: string;
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  "http://127.0.0.1:8000";

async function getErrorMessage(
  response: Response,
): Promise<string> {
  try {
    const error =
      (await response.json()) as ApiErrorResponse;

    if (typeof error.detail === "string") {
      return error.detail;
    }
  } catch {
    // Response did not contain valid JSON.
  }

  return `Request failed with status ${response.status}.`;
}

export async function getAIAnalysis(
  assessmentId: number,
  accessToken: string,
): Promise<AIAnalysis | null> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}/ai-analysis`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  );

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<AIAnalysis>;
}

export async function generateAIAnalysis(
  assessmentId: number,
  accessToken: string,
): Promise<AIAnalysisGenerationResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}/ai-analysis/generate`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<AIAnalysisGenerationResult>;
}

export async function getAIAnalysisSources(
  accessToken: string,
): Promise<AIAnalysisSourcesResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments/ai-analysis/sources`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<AIAnalysisSourcesResult>;
}