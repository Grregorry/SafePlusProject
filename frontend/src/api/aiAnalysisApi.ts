import { API_BASE_URL } from "./config";
import { getErrorMessage } from "./errors";

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
  included_in_report: boolean;
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

export async function setAIAnalysisInclusion(
  assessmentId: number,
  includedInReport: boolean,
  accessToken: string,
): Promise<AIAnalysis> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}/ai-analysis/inclusion`,
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        included_in_report:
          includedInReport,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<AIAnalysis>;
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