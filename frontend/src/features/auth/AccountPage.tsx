import {
  useEffect,
  useMemo,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";

import {
  getAssessmentProgress,
  type AssessmentProgress,
} from "../../api/assessmentProgressApi";
import {
  createAssessment,
  deleteAssessment,
  getAssessments,
  type Assessment,
} from "../../api/assessmentsApi";
import {
  getCurrentOrganisation,
  type Organisation,
} from "../../api/authApi";
import {
  getSubmissionSummary,
  type SubmissionSummary,
} from "../../api/submissionSummaryApi";

type AssessmentDashboardData = {
  progress: AssessmentProgress | null;
  submissionSummary: SubmissionSummary | null;
  isLoading: boolean;
  errorMessage: string;
};

function getStatusClasses(
  status: string,
): string {
  switch (status) {
    case "completed":
      return "bg-emerald-100 text-emerald-800";

    case "in_progress":
      return "bg-cyan-100 text-cyan-800";

    default:
      return "bg-amber-100 text-amber-800";
  }
}

function getStatusLabel(
  status: string,
): string {
  switch (status) {
    case "completed":
      return "Completed";

    case "in_progress":
      return "In progress";

    default:
      return "Draft";
  }
}

function AccountPage() {
  const navigate = useNavigate();

  const [
    organisation,
    setOrganisation,
  ] = useState<Organisation | null>(null);

  const [
    assessments,
    setAssessments,
  ] = useState<Assessment[]>([]);

  const [
    dashboardData,
    setDashboardData,
  ] = useState<
    Record<number, AssessmentDashboardData>
  >({});

  const [
    assessmentName,
    setAssessmentName,
  ] = useState("");

  const [
    showCreateForm,
    setShowCreateForm,
  ] = useState(false);

  const [
    deletingAssessmentId,
    setDeletingAssessmentId,
  ] = useState<number | null>(null);

  const [isLoading, setIsLoading] =
    useState(true);

  const [
    isCreatingAssessment,
    setIsCreatingAssessment,
  ] = useState(false);

  const [
    isRefreshing,
    setIsRefreshing,
  ] = useState(false);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState("");

  async function loadAssessmentDashboardData(
    assessmentList: Assessment[],
    accessToken: string,
  ) {
    const loadingState =
      assessmentList.reduce<
        Record<number, AssessmentDashboardData>
      >((currentState, assessment) => {
        currentState[assessment.id] = {
          progress: null,
          submissionSummary: null,
          isLoading: true,
          errorMessage: "",
        };

        return currentState;
      }, {});

    setDashboardData(loadingState);

    await Promise.all(
      assessmentList.map(
        async (assessment) => {
          try {
            const [
              progress,
              submissionSummary,
            ] = await Promise.all([
              getAssessmentProgress(
                assessment.id,
                accessToken,
              ),
              getSubmissionSummary(
                assessment.id,
                accessToken,
              ),
            ]);

            setDashboardData(
              (currentData) => ({
                ...currentData,
                [assessment.id]: {
                  progress,
                  submissionSummary,
                  isLoading: false,
                  errorMessage: "",
                },
              }),
            );
          } catch (error) {
            setDashboardData(
              (currentData) => ({
                ...currentData,
                [assessment.id]: {
                  progress: null,
                  submissionSummary: null,
                  isLoading: false,
                  errorMessage:
                    error instanceof Error
                      ? error.message
                      : "Unable to load assessment details.",
                },
              }),
            );
          }
        },
      ),
    );
  }

  async function loadAccount(
    showRefreshState = false,
  ) {
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
      if (showRefreshState) {
        setIsRefreshing(true);
      }

      setErrorMessage("");

      const [
        account,
        existingAssessments,
      ] = await Promise.all([
        getCurrentOrganisation(
          accessToken,
        ),
        getAssessments(accessToken),
      ]);

      setOrganisation(account);
      setAssessments(
        existingAssessments,
      );

      await loadAssessmentDashboardData(
        existingAssessments,
        accessToken,
      );
    } catch (error) {
      localStorage.removeItem(
        "safeplus_access_token",
      );

      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Your session could not be verified.",
      );
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }

  useEffect(() => {
    void loadAccount();
  }, []);

  const totalSubmitted =
    useMemo(
      () =>
        Object.values(
          dashboardData,
        ).reduce(
          (total, data) =>
            total +
            (data.submissionSummary
              ?.submitted_total ?? 0),
          0,
        ),
      [dashboardData],
    );

  const totalInProgressSessions =
    useMemo(
      () =>
        Object.values(
          dashboardData,
        ).reduce(
          (total, data) =>
            total +
            (data.submissionSummary
              ?.in_progress_total ?? 0),
          0,
        ),
      [dashboardData],
    );

  const completedAssessmentCount =
    useMemo(
      () =>
        assessments.filter(
          (assessment) =>
            assessment.status ===
            "completed",
        ).length,
      [assessments],
    );

  async function handleCreateAssessment(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const cleanedName =
      assessmentName.trim();

    if (!cleanedName) {
      setErrorMessage(
        "Enter a name for the assessment.",
      );
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
      setIsCreatingAssessment(true);
      setErrorMessage("");

      const newAssessment =
        await createAssessment(
          cleanedName,
          accessToken,
        );

      setAssessments(
        (currentAssessments) => [
          newAssessment,
          ...currentAssessments,
        ],
      );

      setAssessmentName("");
      setShowCreateForm(false);

      setDashboardData(
        (currentData) => ({
          ...currentData,
          [newAssessment.id]: {
            progress: null,
            submissionSummary: null,
            isLoading: true,
            errorMessage: "",
          },
        }),
      );

      try {
        const [
          progress,
          submissionSummary,
        ] = await Promise.all([
          getAssessmentProgress(
            newAssessment.id,
            accessToken,
          ),
          getSubmissionSummary(
            newAssessment.id,
            accessToken,
          ),
        ]);

        setDashboardData(
          (currentData) => ({
            ...currentData,
            [newAssessment.id]: {
              progress,
              submissionSummary,
              isLoading: false,
              errorMessage: "",
            },
          }),
        );
      } catch (error) {
        setDashboardData(
          (currentData) => ({
            ...currentData,
            [newAssessment.id]: {
              progress: null,
              submissionSummary: null,
              isLoading: false,
              errorMessage:
                error instanceof Error
                  ? error.message
                  : "Unable to load assessment details.",
            },
          }),
        );
      }
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to create the assessment.",
      );
    } finally {
      setIsCreatingAssessment(false);
    }
  }

  async function handleDeleteAssessment(
    assessment: Assessment,
  ) {
    const confirmed = window.confirm(
      `Delete "${assessment.name}"?\n\nThis will permanently remove its survey links, responses, scores, and AI analysis. This action cannot be undone.`,
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
      setDeletingAssessmentId(
        assessment.id,
      );
      setErrorMessage("");

      await deleteAssessment(
        assessment.id,
        accessToken,
      );

      setAssessments(
        (currentAssessments) =>
          currentAssessments.filter(
            (item) =>
              item.id !== assessment.id,
          ),
      );

      setDashboardData(
        (currentData) => {
          const updatedData = {
            ...currentData,
          };

          delete updatedData[
            assessment.id
          ];

          return updatedData;
        },
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to delete the assessment.",
      );
    } finally {
      setDeletingAssessmentId(null);
    }
  }

  function handleLogout() {
    localStorage.removeItem(
      "safeplus_access_token",
    );

    navigate("/login");
  }

  if (isLoading) {
    return (
      <main className="min-h-screen bg-slate-100 p-8">
        <p className="text-slate-700">
          Loading dashboard...
        </p>
      </main>
    );
  }

  if (
    errorMessage &&
    !organisation
  ) {
    return (
      <main className="min-h-screen bg-slate-100 p-8">
        <section className="mx-auto max-w-3xl rounded-xl bg-white p-8 shadow">
          <h1 className="text-2xl font-bold text-red-700">
            Session unavailable
          </h1>

          <p className="mt-3 text-slate-700">
            {errorMessage}
          </p>

          <button
            type="button"
            onClick={() =>
              navigate("/login")
            }
            className="mt-6 rounded-lg bg-cyan-700 px-4 py-2 font-semibold text-white"
          >
            Return to login
          </button>
        </section>
      </main>
    );
  }

  if (!organisation) {
    return null;
  }

  return (
    <main className="min-h-screen bg-slate-100 px-6 py-12">
      <section className="mx-auto max-w-6xl">
        <header className="rounded-xl bg-white p-8 shadow">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
                SafePlus dashboard
              </p>

              <h1 className="mt-2 text-3xl font-bold text-slate-900">
                {organisation.name}
              </h1>

              <p className="mt-3 text-slate-600">
                Manage assessments,
                respondent participation,
                progress, and results.
              </p>
            </div>

            <div className="text-sm text-slate-600">
            <p>
              {organisation.email}
            </p>

            <p className="mt-1">
              Sector:{" "}
              <span className="font-semibold text-slate-800">
                {organisation.category}
              </span>
            </p>

            <p className="mt-1 font-semibold">
              {organisation.is_verified
                ? "Verified organisation"
                : "Organisation not verified"}
            </p>
          </div>
          </div>

          {errorMessage && (
            <div className="mt-6 rounded-lg bg-red-50 p-4 text-red-700">
              {errorMessage}
            </div>
          )}

          <div className="mt-8 flex flex-wrap gap-4">
            <button
              type="button"
              onClick={() => {
                setShowCreateForm(
                  (currentValue) =>
                    !currentValue,
                );
                setErrorMessage("");
              }}
              className="rounded-lg bg-cyan-700 px-5 py-3 font-semibold text-white"
            >
              {showCreateForm
                ? "Cancel new assessment"
                : "Start new assessment"}
            </button>

            <button
              type="button"
              onClick={() =>
                void loadAccount(true)
              }
              disabled={isRefreshing}
              className="rounded-lg border border-slate-300 px-5 py-3 font-semibold text-slate-700 disabled:opacity-60"
            >
              {isRefreshing
                ? "Refreshing..."
                : "Refresh dashboard"}
            </button>

            <button
              type="button"
              onClick={() =>
                navigate("/questions")
              }
              className="rounded-lg border border-slate-300 px-5 py-3 font-semibold text-slate-700"
            >
              View question library
            </button>

            <button
              type="button"
              onClick={handleLogout}
              className="rounded-lg border border-slate-300 px-5 py-3 font-semibold text-slate-700"
            >
              Log out
            </button>
          </div>

          {showCreateForm && (
            <form
              onSubmit={
                handleCreateAssessment
              }
              className="mt-6 rounded-xl border border-cyan-200 bg-cyan-50 p-6"
            >
              <label
                htmlFor="assessment-name"
                className="block text-sm font-semibold text-slate-900"
              >
                Assessment name
              </label>

              <p className="mt-1 text-sm text-slate-600">
                Use a clear name that helps
                identify the assessment later.
              </p>

              <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                <input
                  id="assessment-name"
                  type="text"
                  value={assessmentName}
                  onChange={(event) =>
                    setAssessmentName(
                      event.target.value,
                    )
                  }
                  maxLength={150}
                  autoFocus
                  placeholder="Example: 2026 Annual Safety Review"
                  className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
                />

                <button
                  type="submit"
                  disabled={
                    isCreatingAssessment
                  }
                  className="rounded-lg bg-cyan-700 px-5 py-3 font-semibold text-white disabled:opacity-60"
                >
                  {isCreatingAssessment
                    ? "Creating..."
                    : "Create assessment"}
                </button>
              </div>
            </form>
          )}
        </header>

        <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <article className="rounded-xl bg-white p-6 shadow">
            <p className="text-sm font-semibold text-slate-500">
              Total assessments
            </p>

            <p className="mt-2 text-3xl font-bold text-slate-900">
              {assessments.length}
            </p>
          </article>

          <article className="rounded-xl bg-white p-6 shadow">
            <p className="text-sm font-semibold text-slate-500">
              Completed assessments
            </p>

            <p className="mt-2 text-3xl font-bold text-emerald-700">
              {
                completedAssessmentCount
              }
            </p>
          </article>

          <article className="rounded-xl bg-white p-6 shadow">
            <p className="text-sm font-semibold text-slate-500">
              Submitted surveys
            </p>

            <p className="mt-2 text-3xl font-bold text-cyan-700">
              {totalSubmitted}
            </p>
          </article>

          <article className="rounded-xl bg-white p-6 shadow">
            <p className="text-sm font-semibold text-slate-500">
              Unfinished sessions
            </p>

            <p className="mt-2 text-3xl font-bold text-amber-700">
              {
                totalInProgressSessions
              }
            </p>
          </article>
        </section>

        <section className="mt-8 rounded-xl bg-white p-8 shadow">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
                Assessments
              </p>

              <h2 className="mt-1 text-2xl font-bold text-slate-900">
                Assessment dashboard
              </h2>

              <p className="mt-2 text-slate-600">
                Review progress and open the
                next action for each
                assessment.
              </p>
            </div>

            <span className="text-sm text-slate-500">
              {assessments.length} total
            </span>
          </div>

          {assessments.length === 0 ? (
            <div className="mt-8 rounded-lg border border-dashed border-slate-300 p-8 text-center">
              <h3 className="font-semibold text-slate-900">
                No assessments yet
              </h3>

              <p className="mt-2 text-slate-600">
                Start your first assessment
                to begin recording SafePlus
                results.
              </p>
            </div>
          ) : (
            <div className="mt-8 space-y-6">
              {assessments.map(
                (assessment) => {
                  const details =
                    dashboardData[
                      assessment.id
                    ];

                  const progress =
                    details?.progress;

                  const summary =
                    details
                      ?.submissionSummary;

                  const progressPercentage =
                    progress
                      ?.overall_progress_percentage ??
                    0;

                  const isDeleting =
                    deletingAssessmentId ===
                    assessment.id;

                  return (
                    <article
                      key={assessment.id}
                      className="rounded-xl border border-slate-200 p-6"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-4">
                        <div>
                          <p className="text-xl font-bold text-slate-900">
                            {assessment.name}
                          </p>

                          <p className="mt-1 text-sm font-semibold text-cyan-700">
                            Assessment{" "}
                            {
                              assessment.organisation_assessment_number
                            }
                          </p>

                          <p className="mt-1 text-sm text-slate-500">
                            Created{" "}
                            {new Date(
                              assessment.created_at,
                            ).toLocaleString()}
                          </p>
                        </div>

                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${getStatusClasses(
                            assessment.status,
                          )}`}
                        >
                          {getStatusLabel(
                            assessment.status,
                          )}
                        </span>
                      </div>

                      {details?.isLoading ? (
                        <p className="mt-6 text-sm text-slate-500">
                          Loading assessment
                          details...
                        </p>
                      ) : details?.errorMessage ? (
                        <div className="mt-6 rounded-lg bg-red-50 p-4 text-sm text-red-700">
                          {
                            details.errorMessage
                          }
                        </div>
                      ) : (
                        <>
                          <div className="mt-6">
                            <div className="flex items-center justify-between gap-4">
                              <p className="text-sm font-semibold text-slate-700">
                                Response
                                completion
                              </p>

                              <p className="text-sm font-bold text-slate-900">
                                {
                                  progressPercentage
                                }
                                %
                              </p>
                            </div>

                            <div className="mt-2 h-3 overflow-hidden rounded-full bg-slate-200">
                              <div
                                className="h-full bg-cyan-700 transition-all"
                                style={{
                                  width: `${progressPercentage}%`,
                                }}
                              />
                            </div>

                            <p className="mt-2 text-xs text-slate-500">
                              {progress
                                ?.fully_complete_count ??
                                0}{" "}
                              of{" "}
                              {progress
                                ?.active_question_count ??
                                0}{" "}
                              active questions
                              complete for both
                              groups
                            </p>
                          </div>

                          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                            <div className="rounded-lg bg-slate-50 p-4">
                              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                                Employee
                                submitted
                              </p>

                              <p className="mt-2 text-2xl font-bold text-slate-900">
                                {summary
                                  ?.employee_submitted ??
                                  0}
                              </p>
                            </div>

                            <div className="rounded-lg bg-slate-50 p-4">
                              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                                Manager
                                submitted
                              </p>

                              <p className="mt-2 text-2xl font-bold text-slate-900">
                                {summary
                                  ?.senior_manager_submitted ??
                                  0}
                              </p>
                            </div>

                            <div className="rounded-lg bg-slate-50 p-4">
                              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                                In progress
                              </p>

                              <p className="mt-2 text-2xl font-bold text-amber-700">
                                {summary
                                  ?.in_progress_total ??
                                  0}
                              </p>
                            </div>

                            <div className="rounded-lg bg-slate-50 p-4">
                              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                                Overall result
                              </p>

                              <p className="mt-2 text-lg font-bold text-slate-900">
                                {assessment
                                  .overall_maturity_label ??
                                  "Not calculated"}
                              </p>

                              {assessment.overall_combined_mean && (
                                <p className="mt-1 text-xs text-slate-500">
                                  Mean:{" "}
                                  {
                                    assessment.overall_combined_mean
                                  }
                                </p>
                              )}
                            </div>
                          </div>
                        </>
                      )}

                      <div className="mt-6 flex flex-wrap gap-3">
                        <button
                          type="button"
                          onClick={() =>
                            navigate(
                              `/assessments/${assessment.id}`,
                            )
                          }
                          disabled={isDeleting}
                          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
                        >
                          Setup and survey
                        </button>

                        <button
                          type="button"
                          onClick={() =>
                            navigate(
                              `/assessments/${assessment.id}/responses`,
                            )
                          }
                          disabled={isDeleting}
                          className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50"
                        >
                          View responses
                        </button>

                        <button
                          type="button"
                          onClick={() =>
                            navigate(
                              `/assessments/${assessment.id}/results`,
                            )
                          }
                          disabled={isDeleting}
                          className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50"
                        >
                          View results
                        </button>

                        <button
                          type="button"
                          onClick={() =>
                            void handleDeleteAssessment(
                              assessment,
                            )
                          }
                          disabled={isDeleting}
                          className="rounded-lg border border-red-300 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-50 disabled:opacity-50"
                        >
                          {isDeleting
                            ? "Deleting..."
                            : "Delete assessment"}
                        </button>
                      </div>
                    </article>
                  );
                },
              )}
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

export default AccountPage;