import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  calculateAssessmentScores,
  completeAssessment,
  type AssessmentCompletionResult,
  type AssessmentScoringResult,
} from "../../api/assessmentsApi";

function getDomainName(domainId: number): string {
  if (domainId === 1) {
    return "Leadership";
  }

  if (domainId === 2) {
    return "Worker Engagement";
  }

  if (domainId === 3) {
    return "Risk Management";
  }

  return `Domain ${domainId}`;
}

function getMaturityClasses(
  maturityLevel: string,
): string {
  if (maturityLevel === "Leading") {
    return "bg-emerald-100 text-emerald-800";
  }

  if (maturityLevel === "Performing") {
    return "bg-amber-100 text-amber-800";
  }

  return "bg-red-100 text-red-800";
}

function getInterventionClasses(
  interventionTier: string,
): string {
  if (interventionTier === "High") {
    return "bg-red-100 text-red-800";
  }

  if (interventionTier === "Medium") {
    return "bg-orange-100 text-orange-800";
  }

  if (interventionTier === "Low") {
    return "bg-yellow-100 text-yellow-800";
  }

  return "bg-slate-100 text-slate-700";
}

function formatScore(
  value: string | null,
): string {
  if (value === null) {
    return "Not available";
  }

  const numericValue = Number(value);

  if (Number.isNaN(numericValue)) {
    return value;
  }

  return numericValue.toFixed(2);
}

function AssessmentResultsPage() {
  const navigate = useNavigate();
  const { assessmentId } = useParams();

  const numericAssessmentId =
    Number(assessmentId);

  const [results, setResults] =
    useState<AssessmentScoringResult | null>(
      null,
    );

  const [
    completionResult,
    setCompletionResult,
  ] =
    useState<AssessmentCompletionResult | null>(
      null,
    );

  const [isCalculating, setIsCalculating] =
    useState(false);

  const [isCompleting, setIsCompleting] =
    useState(false);

  const [errorMessage, setErrorMessage] =
    useState("");

  async function handleCalculateScores() {
    const accessToken = localStorage.getItem(
      "safeplus_access_token",
    );

    if (!accessToken) {
      navigate("/login", {
        replace: true,
      });

      return;
    }

    if (
      !Number.isInteger(
        numericAssessmentId,
      ) ||
      numericAssessmentId <= 0
    ) {
      setErrorMessage(
        "Invalid assessment ID.",
      );

      return;
    }

    try {
      setIsCalculating(true);
      setErrorMessage("");

      const scoringResult =
        await calculateAssessmentScores(
          numericAssessmentId,
          accessToken,
        );

      setResults(scoringResult);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to calculate assessment scores.",
      );
    } finally {
      setIsCalculating(false);
    }
  }

  async function handleCompleteAssessment() {
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

    if (
      !Number.isInteger(
        numericAssessmentId,
      ) ||
      numericAssessmentId <= 0
    ) {
      setErrorMessage(
        "Invalid assessment ID.",
      );

      return;
    }

    const confirmed = window.confirm(
      "Complete this assessment? Responses and question selection cannot be edited afterward.",
    );

    if (!confirmed) {
      return;
    }

    try {
      setIsCompleting(true);
      setErrorMessage("");

      const completedAssessment =
        await completeAssessment(
          numericAssessmentId,
          accessToken,
        );

      setCompletionResult(
        completedAssessment,
      );

      const scoringResult =
        await calculateAssessmentScores(
          numericAssessmentId,
          accessToken,
        );

      setResults(scoringResult);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to complete the assessment.",
      );
    } finally {
      setIsCompleting(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-100 px-6 py-12">
      <section className="mx-auto max-w-6xl">
        <header className="rounded-xl bg-white p-8 shadow">
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
            Assessment #
            {numericAssessmentId}
          </p>

          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            Assessment results
          </h1>

          <p className="mt-3 text-slate-600">
            Calculate the available question,
            domain, and overall assessment scores
            from the saved response counts.
          </p>

          <div className="mt-6 flex flex-wrap gap-4">
            <button
              type="button"
              onClick={
                handleCalculateScores
              }
              disabled={
                isCalculating ||
                isCompleting
              }
              className="rounded-lg bg-cyan-700 px-5 py-3 font-semibold text-white disabled:opacity-60"
            >
              {isCalculating
                ? "Calculating scores..."
                : results
                  ? "Recalculate scores"
                  : "Calculate scores"}
            </button>

            <button
              type="button"
              onClick={
                handleCompleteAssessment
              }
              disabled={
                isCompleting ||
                isCalculating ||
                completionResult?.status ===
                  "completed"
              }
              className="rounded-lg bg-emerald-700 px-5 py-3 font-semibold text-white disabled:opacity-60"
            >
              {isCompleting
                ? "Completing assessment..."
                : completionResult?.status ===
                    "completed"
                  ? "Assessment completed"
                  : "Complete assessment"}
            </button>

            <button
              type="button"
              onClick={() =>
                navigate(
                  `/assessments/${numericAssessmentId}/responses`,
                )
              }
              disabled={
                completionResult?.status ===
                "completed"
              }
              className="rounded-lg border border-slate-300 px-5 py-3 font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Enter responses
            </button>

            <button
              type="button"
              onClick={() =>
                navigate("/account")
              }
              className="rounded-lg border border-slate-300 px-5 py-3 font-semibold text-slate-700"
            >
              Return to account
            </button>
          </div>

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
                {Number(
                  completionResult
                    .overall_combined_mean,
                ).toFixed(2)}
                {" · "}
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

        {!results ? (
          <section className="mt-8 rounded-xl bg-white p-8 text-center shadow">
            <h2 className="text-xl font-bold text-slate-900">
              Results have not been
              calculated
            </h2>

            <p className="mt-2 text-slate-600">
              Click Calculate scores to
              generate results from the
              available Employee and Senior
              Manager responses.
            </p>
          </section>
        ) : (
          <>
            <section className="mt-8 grid gap-6 md:grid-cols-3">
              <article className="rounded-xl bg-white p-6 shadow">
                <p className="text-sm font-semibold text-slate-500">
                  Questions scored
                </p>

                <p className="mt-2 text-4xl font-bold text-slate-900">
                  {
                    results.questions_scored
                  }
                </p>
              </article>

              <article className="rounded-xl bg-white p-6 shadow">
                <p className="text-sm font-semibold text-slate-500">
                  Overall combined mean
                </p>

                <p className="mt-2 text-4xl font-bold text-slate-900">
                  {formatScore(
                    results
                      .overall_combined_mean,
                  )}
                </p>
              </article>

              <article className="rounded-xl bg-white p-6 shadow">
                <p className="text-sm font-semibold text-slate-500">
                  Overall maturity
                </p>

                {results
                  .overall_maturity_label ? (
                  <span
                    className={`mt-3 inline-block rounded-full px-3 py-1 text-sm font-semibold ${getMaturityClasses(
                      results
                        .overall_maturity_label,
                    )}`}
                  >
                    {
                      results
                        .overall_maturity_label
                    }
                  </span>
                ) : (
                  <p className="mt-2 text-slate-600">
                    Not available yet
                  </p>
                )}
              </article>
            </section>

            <section className="mt-8 rounded-xl bg-white p-8 shadow">
              <h2 className="text-2xl font-bold text-slate-900">
                Domain scores
              </h2>

              {results.domain_scores
                .length === 0 ? (
                <p className="mt-4 text-slate-600">
                  No domain scores are
                  available yet.
                </p>
              ) : (
                <div className="mt-6 grid gap-4 md:grid-cols-3">
                  {results.domain_scores.map(
                    (domainScore) => (
                      <article
                        key={
                          domainScore.domain_id
                        }
                        className="rounded-lg border border-slate-200 p-5"
                      >
                        <h3 className="font-bold text-slate-900">
                          {getDomainName(
                            domainScore.domain_id,
                          )}
                        </h3>

                        <p className="mt-4 text-sm text-slate-500">
                          Combined mean
                        </p>

                        <p className="mt-1 text-3xl font-bold text-slate-900">
                          {formatScore(
                            domainScore
                              .combined_mean,
                          )}
                        </p>

                        <span
                          className={`mt-4 inline-block rounded-full px-3 py-1 text-xs font-semibold ${getMaturityClasses(
                            domainScore
                              .maturity_level,
                          )}`}
                        >
                          {
                            domainScore
                              .maturity_level
                          }
                        </span>
                      </article>
                    ),
                  )}
                </div>
              )}
            </section>

            <section className="mt-8 rounded-xl bg-white p-8 shadow">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">
                  Question scores
                </h2>

                <p className="mt-2 text-slate-600">
                  Only questions with both
                  Employee and Senior Manager
                  response data are scored.
                </p>
              </div>

              {results.question_scores
                .length === 0 ? (
                <p className="mt-6 text-slate-600">
                  No questions could be
                  scored yet.
                </p>
              ) : (
                <div className="mt-6 space-y-4">
                  {results.question_scores.map(
                    (questionScore) => (
                      <article
                        key={
                          questionScore.question_id
                        }
                        className="rounded-lg border border-slate-200 p-5"
                      >
                        <div className="flex flex-wrap items-start justify-between gap-4">
                          <div>
                            <h3 className="font-bold text-slate-900">
                              Question{" "}
                              {
                                questionScore
                                  .question_number
                              }
                            </h3>

                            <p className="mt-1 text-sm text-slate-500">
                              Question ID{" "}
                              {
                                questionScore
                                  .question_id
                              }
                            </p>
                          </div>

                          <div className="flex flex-wrap gap-2">
                            <span
                              className={`rounded-full px-3 py-1 text-xs font-semibold ${getMaturityClasses(
                                questionScore
                                  .maturity_level,
                              )}`}
                            >
                              {
                                questionScore
                                  .maturity_level
                              }
                            </span>

                            <span
                              className={`rounded-full px-3 py-1 text-xs font-semibold ${getInterventionClasses(
                                questionScore
                                  .intervention_tier,
                              )}`}
                            >
                              {
                                questionScore
                                  .intervention_tier
                              }
                            </span>
                          </div>
                        </div>

                        <div className="mt-5 grid gap-4 sm:grid-cols-4">
                          <div>
                            <p className="text-sm text-slate-500">
                              Employee mean
                            </p>

                            <p className="mt-1 text-xl font-bold text-slate-900">
                              {formatScore(
                                questionScore
                                  .employee_mean,
                              )}
                            </p>
                          </div>

                          <div>
                            <p className="text-sm text-slate-500">
                              Manager mean
                            </p>

                            <p className="mt-1 text-xl font-bold text-slate-900">
                              {formatScore(
                                questionScore
                                  .manager_mean,
                              )}
                            </p>
                          </div>

                          <div>
                            <p className="text-sm text-slate-500">
                              Combined mean
                            </p>

                            <p className="mt-1 text-xl font-bold text-slate-900">
                              {formatScore(
                                questionScore
                                  .combined_mean,
                              )}
                            </p>
                          </div>

                          <div>
                            <p className="text-sm text-slate-500">
                              Opinion gap
                            </p>

                            <p className="mt-1 text-xl font-bold text-slate-900">
                              {formatScore(
                                questionScore
                                  .opinion_gap,
                              )}
                            </p>
                          </div>
                        </div>
                      </article>
                    ),
                  )}
                </div>
              )}
            </section>
          </>
        )}
      </section>
    </main>
  );
}

export default AssessmentResultsPage;