export type Assessment = {
  id: number;
  organisation_id: number;
  status: string;
  created_at: string;
  completed_at: string | null;
  overall_combined_mean: string | null;
  overall_maturity_label: string | null;
};

type ApiErrorResponse = {
  detail?: string;
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function getErrorMessage(response: Response): Promise<string> {
  try {
    const error = (await response.json()) as ApiErrorResponse;

    if (typeof error.detail === "string") {
      return error.detail;
    }
  } catch {
    // The response did not contain valid JSON.
  }

  return `Request failed with status ${response.status}.`;
}

export async function getAssessments(
  accessToken: string,
): Promise<Assessment[]> {
  const response = await fetch(`${API_BASE_URL}/api/assessments`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json() as Promise<Assessment[]>;
}

export async function createAssessment(
  accessToken: string,
): Promise<Assessment> {
  const response = await fetch(`${API_BASE_URL}/api/assessments`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json() as Promise<Assessment>;
}