import { getAssessmentProgress } from "../../api/assessmentProgressApi";
import { getSubmissionSummary } from "../../api/submissionSummaryApi";

// Fewest responses (online plus paper, both groups together) for an
// assessment to be completed and compared with other assessments.
// Matches MINIMUM_RESPONSES_TO_COMPLETE in the backend.
export const MINIMUM_RESPONSES = 5;

export type EntryTotals = {
  online: number;
  paper: number;
};

// Online entries are submitted surveys. Paper totals are entered one
// question at a time, so the most entries recorded for any question is
// the number of paper surveys for that group.
export async function fetchEntryTotals(
  assessmentId: number,
  accessToken: string,
): Promise<EntryTotals> {
  const [summary, progress] = await Promise.all([
    getSubmissionSummary(
      assessmentId,
      accessToken,
    ),
    getAssessmentProgress(
      assessmentId,
      accessToken,
    ),
  ]);

  const most = (values: number[]) =>
    Math.max(0, ...values);

  return {
    online: summary.submitted_total,
    paper:
      most(
        progress.questions.map(
          (question) =>
            question.employee_manual_entries_recorded,
        ),
      ) +
      most(
        progress.questions.map(
          (question) =>
            question.manager_manual_entries_recorded,
        ),
      ),
  };
}

export function tooFewResponsesMessage(
  totals: EntryTotals,
): string {
  const total = totals.online + totals.paper;

  return `This assessment can't be completed yet.\n\nIt needs at least ${MINIMUM_RESPONSES} responses in total from employees and senior managers to count as a valid assessment that can be compared with future and other assessments.\n\nIt has ${total} so far (${totals.online} online, ${totals.paper} paper). You can keep it open to collect more responses, or delete it.`;
}

export function completeConfirmMessage(
  totals: EntryTotals,
): string {
  const total = totals.online + totals.paper;

  return `Complete this assessment? It has ${total} responses (${totals.online} online, ${totals.paper} paper).\n\nResponses and question selection cannot be edited afterward.`;
}

export function deleteConfirmMessage(
  assessmentName: string | undefined,
): string {
  return `Delete "${assessmentName ?? "this assessment"}"?\n\nThis permanently removes its survey link and all responses. This can't be undone.`;
}
