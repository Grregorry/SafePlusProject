// Shared helper that turns a failed API response into a message for the screen.
// The wording comes from the backend `detail` field. A structured `detail`
// (incomplete assessment questions) is summarised into one readable sentence.

type ApiErrorResponse = {
  detail?:
    | string
    | {
        message?: string;
        incomplete_questions?: Array<{
          question_id: number;
          question_number: string;
          missing_groups: string[];
        }>;
      };
};

export async function getErrorMessage(
  response: Response,
): Promise<string> {
  try {
    const error =
      (await response.json()) as ApiErrorResponse;

    if (typeof error.detail === "string") {
      return error.detail;
    }

    if (
      error.detail &&
      typeof error.detail === "object"
    ) {
      const message =
        error.detail.message ??
        "The request could not be completed.";

      const incompleteQuestions =
        error.detail.incomplete_questions ?? [];

      if (incompleteQuestions.length === 0) {
        return message;
      }

      const details = incompleteQuestions
        .slice(0, 10)
        .map(
          (question) =>
            `${question.question_number}: missing ${question.missing_groups.join(
              " and ",
            )}`,
        )
        .join("; ");

      const remaining =
        incompleteQuestions.length - 10;

      return remaining > 0
        ? `${message} ${details}; and ${remaining} more.`
        : `${message} ${details}.`;
    }
  } catch {
    // Response did not contain valid JSON.
  }

  return `Request failed with status ${response.status}.`;
}
