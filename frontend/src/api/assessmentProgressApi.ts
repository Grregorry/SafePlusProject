import { API_BASE_URL } from "./config";
import { getErrorMessage } from "./errors";

export type QuestionProgress = {
  question_id: number;
  question_number: string;
  employee_complete: boolean;
  manager_complete: boolean;
  employee_manual_entries_recorded: number;
  manager_manual_entries_recorded: number;
  fully_complete: boolean;
};

export type AssessmentProgress = {
  assessment_id: number;
  active_question_count: number;
  employee_complete_count: number;
  manager_complete_count: number;
  fully_complete_count: number;
  overall_progress_percentage: number;
  expected_manual_entries_employee: number;
  expected_manual_entries_manager: number;
  digital_employee_complete_count: number;
  digital_manager_complete_count: number;
  manual_employee_complete_count: number;
  manual_manager_complete_count: number;
  questions: QuestionProgress[];
};

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