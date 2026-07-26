export type QuestionProgress = {
  question_id: number;
  question_number: string;
  employee_complete: boolean;
  manager_complete: boolean;
  fully_complete: boolean;
};

export type AssessmentProgress = {
  assessment_id: number;
  active_question_count: number;
  employee_complete_count: number;
  manager_complete_count: number;
  fully_complete_count: number;
  overall_progress_percentage: number;
  questions: QuestionProgress[];
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
    // The response did not contain valid JSON.
  }

  return `Request failed with status ${response.status}.`;
}

export async function getAssessmentProgress(
  assessmentId: number,
  accessToken: string,
): Promise<AssessmentProgress> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}/progress`,
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

  return response.json() as Promise<AssessmentProgress>;
}