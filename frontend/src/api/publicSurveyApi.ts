export type RespondentGroup =
  | "Employee"
  | "Senior Manager";

export type ResponseOption =
  | "Strongly Agree"
  | "Agree"
  | "Neither Agree nor Disagree"
  | "Disagree"
  | "Strongly Disagree"
  | "N/A";

export type PublicSurveyOverview = {
  public_code: string;
  organisation_name: string;
  assessment_status: string;
  active_question_count: number;
};

export type CreateSurveySubmissionResult = {
  submission_token: string;
  respondent_group: RespondentGroup;
  status: string;
  started_at: string;
};

export type PublicSurveyQuestion = {
  question_id: number;
  question_number: string;
  domain_name: string;
  question_text: string;
  is_situation_dependent: boolean;
  selected_response: ResponseOption | null;
};

export type SurveySubmissionDetail = {
  submission_token: string;
  public_code: string;
  organisation_name: string;
  respondent_group: RespondentGroup;
  status: string;
  started_at: string;
  submitted_at: string | null;
  answered_question_count: number;
  total_question_count: number;
  questions: PublicSurveyQuestion[];
};

export type SaveSurveyAnswerResult = {
  question_id: number;
  response_option: ResponseOption;
  answered_question_count: number;
  total_question_count: number;
};

export type SubmitSurveyResult = {
  submission_token: string;
  status: string;
  submitted_at: string;
  answered_question_count: number;
  total_question_count: number;
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

export async function getPublicSurvey(
  publicCode: string,
): Promise<PublicSurveyOverview> {
  const response = await fetch(
    `${API_BASE_URL}/api/public/surveys/${encodeURIComponent(
      publicCode,
    )}`,
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<PublicSurveyOverview>;
}

export async function createSurveySubmission(
  publicCode: string,
  respondentGroup: RespondentGroup,
): Promise<CreateSurveySubmissionResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/public/surveys/${encodeURIComponent(
      publicCode,
    )}/submissions`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        respondent_group: respondentGroup,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<CreateSurveySubmissionResult>;
}

export async function getSurveySubmission(
  submissionToken: string,
): Promise<SurveySubmissionDetail> {
  const response = await fetch(
    `${API_BASE_URL}/api/public/submissions/${encodeURIComponent(
      submissionToken,
    )}`,
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<SurveySubmissionDetail>;
}

export async function saveSurveyAnswer(
  submissionToken: string,
  questionId: number,
  responseOption: ResponseOption,
): Promise<SaveSurveyAnswerResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/public/submissions/${encodeURIComponent(
      submissionToken,
    )}/answers`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question_id: questionId,
        response_option: responseOption,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<SaveSurveyAnswerResult>;
}

export async function clearSurveyAnswer(
  submissionToken: string,
  questionId: number,
): Promise<SaveSurveyAnswerResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/public/submissions/${encodeURIComponent(
      submissionToken,
    )}/answers/${questionId}`,
    {
      method: "DELETE",
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<SaveSurveyAnswerResult>;
}

export async function submitSurvey(
  submissionToken: string,
): Promise<SubmitSurveyResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/public/submissions/${encodeURIComponent(
      submissionToken,
    )}/submit`,
    {
      method: "POST",
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<SubmitSurveyResult>;
}