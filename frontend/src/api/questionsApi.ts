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

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function getQuestionDomains(): Promise<QuestionDomain[]> {
  const response = await fetch(`${API_BASE_URL}/api/questions`);

  if (!response.ok) {
    throw new Error(
      `Unable to retrieve questions. Status: ${response.status}`,
    );
  }

  return response.json() as Promise<QuestionDomain[]>;
}