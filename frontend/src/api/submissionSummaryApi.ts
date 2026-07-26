export type SubmissionSummary = {
  assessment_id: number;
  employee_submitted: number;
  senior_manager_submitted: number;
  submitted_total: number;
  employee_in_progress: number;
  senior_manager_in_progress: number;
  in_progress_total: number;
  started_total: number;
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

export async function getSubmissionSummary(
  assessmentId: number,
  accessToken: string,
): Promise<SubmissionSummary> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}/submission-summary`,
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

  return response.json() as Promise<SubmissionSummary>;
}