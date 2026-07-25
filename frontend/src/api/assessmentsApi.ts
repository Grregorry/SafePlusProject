export type Assessment = {
  id: number;
  organisation_id: number;
  status: string;
  created_at: string;
  completed_at: string | null;
  overall_combined_mean: string | null;
  overall_maturity_label: string | null;
};

export type AssessmentSetupQuestion = {
  question_id: number;
  question_number: string;
  domain_name: string;
  employee_text: string;
  manager_text: string;
  is_compulsory: boolean;
  is_situation_dependent: boolean;
  is_active: boolean;
};

export type RespondentGroup = "Employee" | "Senior Manager";

export type ResponseOption =
  | "Strongly Agree"
  | "Agree"
  | "Neither Agree nor Disagree"
  | "Disagree"
  | "Strongly Disagree"
  | "N/A";

export type ResponseCount = {
  response_option: ResponseOption;
  count: number;
};

export type QuestionResponses = {
  assessment_id: number;
  question_id: number;
  respondent_group: RespondentGroup;
  responses: ResponseCount[];
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

export async function getAssessment(
  assessmentId: number,
  accessToken: string,
): Promise<Assessment> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  );

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json() as Promise<Assessment>;
}

export async function getAssessmentQuestions(
  assessmentId: number,
  accessToken: string,
): Promise<AssessmentSetupQuestion[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}/questions`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  );

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json() as Promise<AssessmentSetupQuestion[]>;
}

export async function updateQuestionSelection(
  assessmentId: number,
  questionIds: number[],
  accessToken: string,
): Promise<AssessmentSetupQuestion[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}/question-selection`,
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question_ids: questionIds,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json() as Promise<AssessmentSetupQuestion[]>;
}

export async function getQuestionResponses(
  assessmentId: number,
  questionId: number,
  respondentGroup: RespondentGroup,
  accessToken: string,
): Promise<QuestionResponses> {
  const encodedGroup = encodeURIComponent(respondentGroup);

  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}/questions/${questionId}/responses/${encodedGroup}`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  );

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json() as Promise<QuestionResponses>;
}

export async function updateQuestionResponses(
  assessmentId: number,
  questionId: number,
  respondentGroup: RespondentGroup,
  responses: ResponseCount[],
  accessToken: string,
): Promise<QuestionResponses> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}/questions/${questionId}/responses`,
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        respondent_group: respondentGroup,
        responses,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }

  return response.json() as Promise<QuestionResponses>;
}