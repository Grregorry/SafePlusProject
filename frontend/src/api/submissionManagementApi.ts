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

    if (
      typeof error.detail === "string"
    ) {
      return error.detail;
    }
  } catch {
    // Response was not valid JSON.
  }

  return `Request failed with status ${response.status}.`;
}

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