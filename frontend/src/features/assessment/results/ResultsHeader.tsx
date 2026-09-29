import {
  type Assessment,
  type AssessmentCompletionResult,
} from "../../../api/assessmentsApi";
import { type EntryTotals } from "../assessmentCompletion";
import {
  formatLongDate,
  formatScore,
} from "./resultsHelpers";

export default function ResultsHeader({
  assessment,
  completionResult,
  entryTotals,
  errorMessage,
}: {
  assessment: Assessment | null;
  completionResult: AssessmentCompletionResult | null;
  entryTotals: EntryTotals | null;
  errorMessage: string;
}) {
  return (
    <header className="rounded-xl bg-white p-8 shadow">
      <h1 className="text-3xl font-bold text-slate-900">
        {assessment?.name ??
          "Assessment results"}
      </h1>

      {assessment && (
        <p className="mt-2 text-slate-600">
          Opened{" "}
          {formatLongDate(
            assessment.created_at,
          )}
          {assessment.completed_at
            ? ` · Closed ${formatLongDate(
                assessment.completed_at,
              )}`
            : ""}
          {entryTotals
            ? ` · ${
                entryTotals.online +
                entryTotals.paper
              } ${
                entryTotals.online +
                  entryTotals.paper ===
                1
                  ? "entry"
                  : "entries"
              } (${entryTotals.online} online, ${entryTotals.paper} paper)`
            : ""}
        </p>
      )}

      {errorMessage && (
        <div className="mt-6 rounded-lg bg-red-50 p-4 text-red-700">
          {errorMessage}
        </div>
      )}

      {completionResult && (
        <div className="mt-6 rounded-lg bg-emerald-50 p-4 text-emerald-800">
          <p className="font-semibold">
            Assessment completed
            successfully.
          </p>

          <p className="mt-1 text-sm">
            Final score:{" "}
            {formatScore(
              completionResult
                .overall_combined_mean,
            )}{" "}
            ·{" "}
            {
              completionResult
                .overall_maturity_label
            }
          </p>

          <p className="mt-1 text-sm">
            Questions scored:{" "}
            {
              completionResult
                .questions_scored
            }
          </p>

          <p className="mt-1 text-sm">
            Completed:{" "}
            {new Date(
              completionResult.completed_at,
            ).toLocaleString()}
          </p>
        </div>
      )}
    </header>
  );
}
