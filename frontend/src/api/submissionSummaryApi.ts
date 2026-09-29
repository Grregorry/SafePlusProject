import { API_BASE_URL } from "./config";
import { getErrorMessage } from "./errors";

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