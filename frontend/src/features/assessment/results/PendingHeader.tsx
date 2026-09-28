import {
  Link,
  useNavigate,
} from "react-router-dom";
import { type Assessment } from "../../../api/assessmentsApi";
import { formatLongDate } from "./resultsHelpers";

export default function PendingHeader({
  assessment,
  errorMessage,
  handleCompleteAssessment,
  isCompleting,
  numericAssessmentId,
  organisationName,
}: {
  assessment: Assessment | null;
  errorMessage: string;
  handleCompleteAssessment: () => void | Promise<void>;
  isCompleting: boolean;
  numericAssessmentId: number;
  organisationName: string;
}) {
  const navigate = useNavigate();

  return (
    <header>
      <Link
        to="/account"
        className="text-sm font-semibold text-cyan-700 underline hover:text-cyan-900"
      >
        {organisationName ||
          "Company dashboard"}
      </Link>

      <div className="mt-2 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            {assessment
              ? `${assessment.name} assessment`
              : "Assessment"}
          </h1>

          {assessment && (
            <p className="mt-2 text-slate-600">
              {assessment.status === "draft"
                ? "Draft. Created"
                : "In progress. Opened"}{" "}
              {formatLongDate(
                assessment.created_at,
              )}
            </p>
          )}
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() =>
              navigate(
                `/assessments/${numericAssessmentId}/responses`,
              )
            }
            className="rounded-lg border border-slate-300 bg-white px-5 py-3 font-semibold text-slate-700 hover:bg-slate-50"
          >
            Manual entry
          </button>

          <button
            type="button"
            onClick={
              handleCompleteAssessment
            }
            disabled={isCompleting}
            className="rounded-lg border border-cyan-700 bg-white px-5 py-3 font-semibold text-cyan-800 hover:bg-cyan-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isCompleting
              ? "Completing assessment..."
              : "Complete assessment"}
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="mt-6 rounded-lg bg-red-50 p-4 text-red-700">
          {errorMessage}
        </div>
      )}
    </header>
  );
}
