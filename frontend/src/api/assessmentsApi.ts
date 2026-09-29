import { API_BASE_URL } from "./config";
import { getErrorMessage } from "./errors";

export type Assessment = {
  id: number;
  organisation_id: number;
  organisation_assessment_number: number;
  name: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  overall_combined_mean: string | null;
  overall_maturity_label: string | null;
  expected_manual_entries_employee: number;
  expected_manual_entries_manager: number;
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

export type SurveyAccess = {
  assessment_id: number;
  public_code: string;
  public_path: string;
  status: string;
};

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

export type QuestionScoreResult = {
  question_id: number;
  question_number: string;
  employee_mean: string;
  manager_mean: string;
  combined_mean: string;
  opinion_gap: string;
  maturity_level: string;
  intervention_tier: string;
};

export type DomainScoreResult = {
  domain_id: number;
  combined_mean: string;
  maturity_level: string;
};

export type AssessmentScoringResult = {
  assessment_id: number;
  questions_scored: number;
  question_scores: QuestionScoreResult[];
  domain_scores: DomainScoreResult[];
  overall_combined_mean: string | null;
  overall_maturity_label: string | null;
};

export type AssessmentCompletionResult = {
  assessment_id: number;
  status: string;
  completed_at: string;
  overall_combined_mean: string;
  overall_maturity_label: string;
  questions_scored: number;
};

export async function getAssessments(
  accessToken: string,
): Promise<Assessment[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments`,
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

  return response.json() as Promise<Assessment[]>;
}

export async function createAssessment(
  name: string,
  accessToken: string,
): Promise<Assessment> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<Assessment>;
}

export async function deleteAssessment(
  assessmentId: number,
  accessToken: string,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}`,
    {
      method: "DELETE",
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
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<Assessment>;
}

export async function updateExpectedManualEntries(
  assessmentId: number,
  expectedManualEntriesEmployee: number,
  expectedManualEntriesManager: number,
  accessToken: string,
): Promise<Assessment> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}/expected-manual-entries`,
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        expected_manual_entries_employee:
          expectedManualEntriesEmployee,
        expected_manual_entries_manager:
          expectedManualEntriesManager,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
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
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<
    AssessmentSetupQuestion[]
  >;
}

export async function getSurveyAccess(
  assessmentId: number,
  accessToken: string,
): Promise<SurveyAccess> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}/survey-access`,
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

  return response.json() as Promise<SurveyAccess>;
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
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<
    AssessmentSetupQuestion[]
  >;
}

export async function getQuestionResponses(
  assessmentId: number,
  questionId: number,
  respondentGroup: RespondentGroup,
  accessToken: string,
): Promise<QuestionResponses> {
  const encodedGroup =
    encodeURIComponent(respondentGroup);

  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}/questions/${questionId}/responses/${encodedGroup}`,
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

  return response.json() as Promise<QuestionResponses>;
}

export async function getDigitalQuestionResponses(
  assessmentId: number,
  questionId: number,
  respondentGroup: RespondentGroup,
  accessToken: string,
): Promise<QuestionResponses> {
  const encodedGroup =
    encodeURIComponent(respondentGroup);

  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}/questions/${questionId}/digital-responses/${encodedGroup}`,
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
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return response.json() as Promise<QuestionResponses>;
}

export async function calculateAssessmentScores(
  assessmentId: number,
  accessToken: string,
): Promise<AssessmentScoringResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}/calculate-scores`,
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

  return response.json() as Promise<AssessmentScoringResult>;
}

export async function completeAssessment(
  assessmentId: number,
  accessToken: string,
): Promise<AssessmentCompletionResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/assessments/${assessmentId}/complete`,
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

  return response.json() as Promise<AssessmentCompletionResult>;
}

async function downloadReportFromPath(
  path: string,
  accessToken: string,
  defaultFilename: string,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}${path}`,
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

  const pdfBlob = await response.blob();

  const downloadUrl =
    window.URL.createObjectURL(pdfBlob);

  const contentDisposition =
    response.headers.get(
      "Content-Disposition",
    );

  const filenameMatch =
    contentDisposition?.match(
      /filename="?([^"]+)"?/,
    );

  const filename =
    filenameMatch?.[1] ?? defaultFilename;

  const link =
    document.createElement("a");

  link.href = downloadUrl;
  link.download = filename;

  document.body.appendChild(link);
  link.click();
  link.remove();

  window.URL.revokeObjectURL(
    downloadUrl,
  );
}

// AI text is only added to a report when the person downloading it
// chooses to include it.
function reportQuery(
  includeAi: boolean,
): string {
  return `?include_ai=${includeAi ? "true" : "false"}`;
}

function reportFilename(
  name: string,
  assessmentId: number,
  includeAi: boolean,
): string {
  return `safeplus-${name}-${assessmentId}${
    includeAi ? "-with-ai" : ""
  }.pdf`;
}

export async function downloadAssessmentReport(
  assessmentId: number,
  includeAi: boolean,
  accessToken: string,
): Promise<void> {
  await downloadReportFromPath(
    `/api/assessments/${assessmentId}/report${reportQuery(includeAi)}`,
    accessToken,
    reportFilename("assessment", assessmentId, includeAi),
  );
}

export async function downloadBusinessLeaderReport(
  assessmentId: number,
  includeAi: boolean,
  accessToken: string,
): Promise<void> {
  await downloadReportFromPath(
    `/api/assessments/${assessmentId}/report/business-leader${reportQuery(includeAi)}`,
    accessToken,
    reportFilename("business-leader-report", assessmentId, includeAi),
  );
}

export async function downloadBoardReport(
  assessmentId: number,
  includeAi: boolean,
  accessToken: string,
): Promise<void> {
  await downloadReportFromPath(
    `/api/assessments/${assessmentId}/report/board${reportQuery(includeAi)}`,
    accessToken,
    reportFilename("board-report", assessmentId, includeAi),
  );
}

export async function downloadOperationalManagerReport(
  assessmentId: number,
  includeAi: boolean,
  accessToken: string,
): Promise<void> {
  await downloadReportFromPath(
    `/api/assessments/${assessmentId}/report/operational-manager${reportQuery(includeAi)}`,
    accessToken,
    reportFilename("operational-manager-report", assessmentId, includeAi),
  );
}