import {
  useEffect,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";

import {
  deleteAssessmentSubmission,
  getAssessmentSubmissions,
  type ManagedSubmission,
} from "../../api/submissionManagementApi";
import { useConfirm } from "../../components/useConfirm";

type SubmissionManagementPanelProps = {
  assessmentId: number;
  onChanged?: () => void;
};

function SubmissionManagementPanel({
  assessmentId,
  onChanged,
}: SubmissionManagementPanelProps) {
  const navigate = useNavigate();

  const { confirm, dialog } = useConfirm();

  const [
    submissions,
    setSubmissions,
  ] = useState<ManagedSubmission[]>([]);

  const [isLoading, setIsLoading] =
    useState(true);

  const [
    deletingSubmissionId,
    setDeletingSubmissionId,
  ] = useState<number | null>(null);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState("");

  const [
    successMessage,
    setSuccessMessage,
  ] = useState("");

  // Bumped to reload: the fetch lives in the effect, so state is
  // only set from its callbacks, never synchronously.
  const [refreshCount, setRefreshCount] =
    useState(0);

  useEffect(() => {
    const accessToken =
      localStorage.getItem(
        "safeplus_access_token",
      );

    if (!accessToken) {
      navigate("/login", {
        replace: true,
      });
      return;
    }

    let cancelled = false;

    getAssessmentSubmissions(
      assessmentId,
      accessToken,
    )
      .then((result) => {
        if (cancelled) {
          return;
        }

        setErrorMessage("");
        setSubmissions(
          result.submissions,
        );
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }

        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Unable to load submissions.",
        );
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [assessmentId, navigate, refreshCount]);

  async function handleDelete(
    submission: ManagedSubmission,
  ) {
    if (
      submission.status === "submitted"
    ) {
      return;
    }

    const confirmed = await confirm(
      "Delete this unfinished survey session? Its saved answers will also be deleted.",
    );

    if (!confirmed) {
      return;
    }

    const accessToken =
      localStorage.getItem(
        "safeplus_access_token",
      );

    if (!accessToken) {
      navigate("/login", {
        replace: true,
      });
      return;
    }

    try {
      setDeletingSubmissionId(
        submission.submission_id,
      );
      setErrorMessage("");
      setSuccessMessage("");

      const result =
        await deleteAssessmentSubmission(
          assessmentId,
          submission.submission_id,
          accessToken,
        );

      setSuccessMessage(
        result.message,
      );

      setRefreshCount(
        (count) => count + 1,
      );
      onChanged?.();
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to delete submission.",
      );
    } finally {
      setDeletingSubmissionId(null);
    }
  }

  return (
    <>
      {dialog}

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">
            Manage submissions
          </h2>

          <p className="mt-1 text-slate-600">
            Review submitted and unfinished
            respondent sessions.
          </p>
        </div>

        <button
          type="button"
          onClick={() => {
            setIsLoading(true);
            setRefreshCount(
              (count) => count + 1,
            );
          }}
          disabled={isLoading}
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50"
        >
          {isLoading
            ? "Refreshing..."
            : "Refresh sessions"}
        </button>
      </div>

      {errorMessage && (
        <div className="mt-6 rounded-lg bg-red-50 p-4 text-red-700">
          {errorMessage}
        </div>
      )}

      {successMessage && (
        <div className="mt-6 rounded-lg bg-emerald-50 p-4 text-emerald-700">
          {successMessage}
        </div>
      )}

      {isLoading ? (
        <p className="mt-6 text-slate-600">
          Loading survey sessions...
        </p>
      ) : submissions.length === 0 ? (
        <div className="mt-6 rounded-lg border border-dashed border-slate-300 p-8 text-center">
          <p className="text-slate-600">
            No survey sessions have been
            started.
          </p>
        </div>
      ) : (
        <div className="mt-6 overflow-x-auto">
          <table className="w-full border-collapse text-left">
            <thead>
              <tr className="border-b border-slate-200 text-sm text-slate-500">
                <th className="px-3 py-3">
                  Group
                </th>

                <th className="px-3 py-3">
                  Status
                </th>

                <th className="px-3 py-3">
                  Progress
                </th>

                <th className="px-3 py-3">
                  Started
                </th>

                <th className="px-3 py-3">
                  Submitted
                </th>

                <th className="px-3 py-3">
                  Action
                </th>
              </tr>
            </thead>

            <tbody>
              {submissions.map(
                (submission) => {
                  const isSubmitted =
                    submission.status ===
                    "submitted";

                  return (
                    <tr
                      key={
                        submission.submission_id
                      }
                      className="border-b border-slate-100"
                    >
                      <td className="px-3 py-4 font-semibold text-slate-900">
                        {
                          submission.respondent_group
                        }
                      </td>

                      <td className="px-3 py-4">
                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${
                            isSubmitted
                              ? "bg-emerald-100 text-emerald-700"
                              : "bg-amber-100 text-amber-700"
                          }`}
                        >
                          {isSubmitted
                            ? "Submitted"
                            : "In progress"}
                        </span>
                      </td>

                      <td className="px-3 py-4 text-slate-700">
                        {
                          submission.answered_question_count
                        }
                        /
                        {
                          submission.total_question_count
                        }
                      </td>

                      <td className="px-3 py-4 text-sm text-slate-600">
                        {new Date(
                          submission.started_at,
                        ).toLocaleString()}
                      </td>

                      <td className="px-3 py-4 text-sm text-slate-600">
                        {submission.submitted_at
                          ? new Date(
                              submission.submitted_at,
                            ).toLocaleString()
                          : "—"}
                      </td>

                      <td className="px-3 py-4">
                        {isSubmitted ? (
                          <span className="text-sm text-slate-500">
                            Protected
                          </span>
                        ) : (
                          <button
                            type="button"
                            onClick={() =>
                              handleDelete(
                                submission,
                              )
                            }
                            disabled={
                              deletingSubmissionId ===
                              submission.submission_id
                            }
                            className="rounded-lg border border-red-300 px-3 py-2 text-sm font-semibold text-red-700 disabled:opacity-50"
                          >
                            {deletingSubmissionId ===
                            submission.submission_id
                              ? "Deleting..."
                              : "Delete"}
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                },
              )}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

export default SubmissionManagementPanel;