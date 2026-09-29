import { API_BASE_URL } from "./config";

export type Question = {
  id: number;
  question_number: string;
  employee_text: string;
  manager_text: string;
  is_compulsory: boolean;
  is_situation_dependent: boolean;
};

export type QuestionDomain = {
  id: number;
  name: string;
  display_order: number;
  questions: Question[];
};

export async function getQuestionDomains(): Promise<QuestionDomain[]> {
  const response = await fetch(`${API_BASE_URL}/api/questions`);

  if (!response.ok) {
    throw new Error(
      `Unable to retrieve questions. Status: ${response.status}`,
    );
  }

  return response.json() as Promise<QuestionDomain[]>;
}