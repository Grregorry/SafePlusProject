import { API_BASE_URL } from "./config";
import { getErrorMessage } from "./errors";

export type ManagedSubmission = {
  submission_id: number;
  respondent_group:
    | "Employee"
    | "Senior Manager";
  status: "in_progress" | "submitted";
  answered_question_count: number;
  total_question_count: number;
  started_at: string;
  submitted_at: string | null;
};

export type SubmissionListResponse = {
  assessment_id: number;
  submissions: ManagedSubmission[];
};

export type DeleteSubmissionResponse = {
  submission_id: number;
  deleted: boolean;
  message: string;
};

export async function getAssessmentSubmissions(
  assessmentId: number,
  accessToken: string,
): Promise<SubmissionListResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}/submissions`,
    {
      headers: {
        Authorization:
          `Bearer ${accessToken}`,
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<
    SubmissionListResponse
  >;
}

export async function deleteAssessmentSubmission(
  assessmentId: number,
  submissionId: number,
  accessToken: string,
): Promise<DeleteSubmissionResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}/submissions/${submissionId}`,
    {
      method: "DELETE",
      headers: {
        Authorization:
          `Bearer ${accessToken}`,
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<
    DeleteSubmissionResponse
  >;
}