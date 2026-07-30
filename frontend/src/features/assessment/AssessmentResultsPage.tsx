import {
  useEffect,
  useState,
} from "react";
import {
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import {
  generateAIAnalysis,
  getAIAnalysis,
  type AIAnalysis,
  type SafePlusGuidanceSource,
} from "../../api/aiAnalysisApi";
import {
  calculateAssessmentScores,
  completeAssessment,
  getAssessment,
  type Assessment,
  type AssessmentCompletionResult,
  type AssessmentScoringResult,
} from "../../api/assessmentsApi";

function getDomainName(
  domainId: number,
): string {
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



function isHighOverride(
  opinionGap: string | number,
): boolean {
  return Number(opinionGap) >= 3;
}

function getQuestionStatusLabel(
  interventionTier: string,
  opinionGap: string | number,
): string {
  if (isHighOverride(opinionGap)) {
    return "High Override";
  }

  return interventionTier;
}

function getInterventionClasses(
  interventionTier: string,
  opinionGap?: string | number,
): string {
  if (
    opinionGap !== undefined &&
    isHighOverride(opinionGap)
  ) {
    return "bg-red-700 text-white";
  }

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

function getUrgencyClasses(
  urgency: string,
): string {
  const normalisedUrgency =
    urgency.toLowerCase();

  if (
    normalisedUrgency.includes("high") ||
    normalisedUrgency.includes("urgent") ||
    normalisedUrgency.includes("immediate")
  ) {
    return "bg-red-100 text-red-800";
  }

  if (
    normalisedUrgency.includes("medium") ||
    normalisedUrgency.includes("moderate")
  ) {
    return "bg-orange-100 text-orange-800";
  }

  return "bg-emerald-100 text-emerald-800";
}

function formatScore(
  value: string | number | null,
): string {
  if (value === null) {
    return "Not available";
  }

  const numericValue = Number(value);

  if (Number.isNaN(numericValue)) {
    return String(value);
  }

  return numericValue.toFixed(2);
}

function getSourceById(
  sourceId: string,
  sources: SafePlusGuidanceSource[],
): SafePlusGuidanceSource | undefined {
  return sources.find(
    (source) =>
      source.source_id === sourceId,
  );
}

function SourceLinks({
  sourceIds,
  sources,
}: {
  sourceIds: string[];
  sources: SafePlusGuidanceSource[];
}) {
  if (sourceIds.length === 0) {
    return null;
  }

  return (
    <div className="mt-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        WorkSafe sources
      </p>

      <div className="mt-2 flex flex-wrap gap-2">
        {sourceIds.map((sourceId) => {
          const source = getSourceById(
            sourceId,
            sources,
          );

          if (!source) {
            return (
              <span
                key={sourceId}
                className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600"
              >
                {sourceId}
              </span>
            );
          }

          return (
            <a
              key={sourceId}
              href={source.url}
              target="_blank"
              rel="noreferrer"
              className="rounded-full bg-cyan-50 px-3 py-1 text-xs font-semibold text-cyan-800 hover:bg-cyan-100"
            >
              {source.title}
            </a>
          );
        })}
      </div>
    </div>
  );
}

function AssessmentResultsPage() {
  const navigate = useNavigate();
  const { assessmentId } = useParams();

  const numericAssessmentId =
    Number(assessmentId);

  const [
    assessment,
    setAssessment,
  ] = useState<Assessment | null>(
    null,
  );

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

  const [
    aiAnalysis,
    setAIAnalysis,
  ] = useState<AIAnalysis | null>(
    null,
  );

  const [
    isLoadingPage,
    setIsLoadingPage,
  ] = useState(true);

  const [
    isCalculating,
    setIsCalculating,
  ] = useState(false);

  const [
    isCompleting,
    setIsCompleting,
  ] = useState(false);

  const [
    isGeneratingAnalysis,
    setIsGeneratingAnalysis,
  ] = useState(false);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState("");

  const [
    analysisMessage,
    setAnalysisMessage,
  ] = useState("");

  const isAssessmentCompleted =
    assessment?.status === "completed" ||
    completionResult?.status ===
      "completed";

  const domainData =
    aiAnalysis?.domain_summaries;

  const keyStrengths =
    domainData?.key_strengths ?? [];

  const keyRisks =
    domainData?.key_risks ?? [];

  const aiDomainSummaries =
    domainData?.domains ?? [];

  const guidanceSources =
    domainData?.guidance_sources ?? [];

  const limitations =
    domainData?.limitations ?? [];

  const priorityActions =
    aiAnalysis?.priority_actions ?? [];

  const roadmap =
    aiAnalysis?.roadmap ?? [];

  const radarData =
    results?.domain_scores.map(
      (domainScore) => ({
        domain: getDomainName(
          domainScore.domain_id,
        ),
        score: Number(
          domainScore.combined_mean,
        ),
        fullMark: 5,
      }),
    ) ?? [];

  useEffect(() => {
    async function loadPage() {
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

        setIsLoadingPage(false);
        return;
      }

      try {
        setErrorMessage("");

        const [
          assessmentResult,
          scoringResult,
          savedAnalysis,
        ] = await Promise.all([
          getAssessment(
            numericAssessmentId,
            accessToken,
          ),
          calculateAssessmentScores(
            numericAssessmentId,
            accessToken,
          ),
          getAIAnalysis(
            numericAssessmentId,
            accessToken,
          ),
        ]);

        setAssessment(
          assessmentResult,
        );

        setResults(scoringResult);
        setAIAnalysis(savedAnalysis);
      } catch (error) {
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Unable to load assessment results.",
        );
      } finally {
        setIsLoadingPage(false);
      }
    }

    void loadPage();
  }, [
    navigate,
    numericAssessmentId,
  ]);

  async function handleCalculateScores() {
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
      setIsCalculating(true);
      setErrorMessage("");
      setAnalysisMessage("");

      const scoringResult =
        await calculateAssessmentScores(
          numericAssessmentId,
          accessToken,
        );

      setResults(scoringResult);

      const updatedAssessment =
        await getAssessment(
          numericAssessmentId,
          accessToken,
        );

      setAssessment(
        updatedAssessment,
      );
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

    const confirmed = window.confirm(
      "Complete this assessment? Responses and question selection cannot be edited afterward.",
    );

    if (!confirmed) {
      return;
    }

    try {
      setIsCompleting(true);
      setErrorMessage("");
      setAnalysisMessage("");

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

      const updatedAssessment =
        await getAssessment(
          numericAssessmentId,
          accessToken,
        );

      setAssessment(
        updatedAssessment,
      );
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

  async function handleGenerateAIAnalysis() {
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

    if (!isAssessmentCompleted) {
      setErrorMessage(
        "Complete the assessment before generating AI analysis.",
      );

      return;
    }

    const confirmed = window.confirm(
      aiAnalysis
        ? "Regenerate the AI analysis? The existing saved analysis will be replaced."
        : "Generate an AI analysis using the assessment results and curated WorkSafe SafePlus guidance?",
    );

    if (!confirmed) {
      return;
    }

    try {
      setIsGeneratingAnalysis(true);
      setErrorMessage("");
      setAnalysisMessage("");

      const generatedAnalysis =
        await generateAIAnalysis(
          numericAssessmentId,
          accessToken,
        );

      setAIAnalysis(
        generatedAnalysis,
      );

      setAnalysisMessage(
        generatedAnalysis.message,
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to generate AI analysis.",
      );
    } finally {
      setIsGeneratingAnalysis(false);
    }
  }

  if (isLoadingPage) {
    return (
      <main className="min-h-screen bg-slate-100 p-8">
        <p className="text-slate-700">
          Loading assessment results...
        </p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-100 px-6 py-12">
      <section className="mx-auto max-w-6xl">
        <header className="rounded-xl bg-white p-8 shadow">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
                {assessment
                  ? `Assessment ${assessment.organisation_assessment_number}`
                  : `Assessment ${numericAssessmentId}`}
              </p>

              <h1 className="mt-2 text-3xl font-bold text-slate-900">
                {assessment?.name ??
                  "Assessment results"}
              </h1>

              <p className="mt-3 max-w-3xl text-slate-600">
                Review calculated SafePlus
                scores and generate a
                source-grounded AI analysis
                using official WorkSafe
                SafePlus guidance.
              </p>
            </div>

            {assessment && (
              <span
                className={`rounded-full px-3 py-1 text-sm font-semibold ${
                  isAssessmentCompleted
                    ? "bg-emerald-100 text-emerald-800"
                    : "bg-amber-100 text-amber-800"
                }`}
              >
                {isAssessmentCompleted
                  ? "Completed"
                  : assessment.status.replace(
                      "_",
                      " ",
                    )}
              </span>
            )}
          </div>

          <div className="mt-6 flex flex-wrap gap-4">
            <button
              type="button"
              onClick={
                handleCalculateScores
              }
              disabled={
                isCalculating ||
                isCompleting ||
                isGeneratingAnalysis
              }
              className="rounded-lg bg-cyan-700 px-5 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
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
                isAssessmentCompleted ||
                isCompleting ||
                isCalculating ||
                isGeneratingAnalysis
              }
              className="rounded-lg bg-emerald-700 px-5 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isCompleting
                ? "Completing assessment..."
                : isAssessmentCompleted
                  ? "Assessment completed"
                  : "Complete assessment"}
            </button>

            <button
              type="button"
              onClick={
                handleGenerateAIAnalysis
              }
              disabled={
                !isAssessmentCompleted ||
                isGeneratingAnalysis ||
                isCompleting ||
                isCalculating
              }
              className="rounded-lg bg-violet-700 px-5 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isGeneratingAnalysis
                ? "Generating AI analysis..."
                : aiAnalysis
                  ? "Regenerate AI analysis"
                  : "Generate AI analysis"}
            </button>

            <button
              type="button"
              onClick={() =>
                navigate(
                  `/assessments/${numericAssessmentId}/responses`,
                )
              }
              disabled={
                isAssessmentCompleted
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

          {!isAssessmentCompleted && (
            <div className="mt-6 rounded-lg bg-violet-50 p-4 text-sm text-violet-800">
              Complete the assessment before
              generating the WorkSafe-grounded
              AI analysis.
            </div>
          )}

          {errorMessage && (
            <div className="mt-6 rounded-lg bg-red-50 p-4 text-red-700">
              {errorMessage}
            </div>
          )}

          {analysisMessage && (
            <div className="mt-6 rounded-lg bg-emerald-50 p-4 text-emerald-800">
              {analysisMessage}
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

        {!results ? (
          <section className="mt-8 rounded-xl bg-white p-8 text-center shadow">
            <h2 className="text-xl font-bold text-slate-900">
              Results have not been
              calculated
            </h2>

            <p className="mt-2 text-slate-600">
              Click Calculate scores to
              generate the available
              assessment results.
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
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-bold text-slate-900">
                    SafePlus domain profile
                  </h2>

                  <p className="mt-2 max-w-3xl text-slate-600">
                    The radar chart compares the
                    combined score for Leadership,
                    Worker Engagement, and Risk
                    Management on the 1 to 5
                    SafePlus scale.
                  </p>
                </div>

                <div className="rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-600">
                  <p>
                    1 = lower maturity
                  </p>

                  <p className="mt-1">
                    5 = higher maturity
                  </p>
                </div>
              </div>

              {radarData.length === 0 ? (
                <p className="mt-6 text-slate-600">
                  No domain data is available
                  for the radar chart.
                </p>
              ) : (
                <div className="mt-6 h-[420px] w-full">
                  <ResponsiveContainer
                    width="100%"
                    height="100%"
                  >
                    <RadarChart
                      data={radarData}
                      outerRadius="72%"
                    >
                      <PolarGrid />

                      <PolarAngleAxis
                        dataKey="domain"
                        tick={{
                          fill: "#334155",
                          fontSize: 13,
                        }}
                      />

                      <PolarRadiusAxis
                        angle={90}
                        domain={[0, 5]}
                        tickCount={6}
                        allowDecimals={false}
                      />

                      <Tooltip
                        formatter={(value) => [
                          Number(value).toFixed(2),
                          "Domain score",
                        ]}
                      />

                      <Radar
                        name="Domain score"
                        dataKey="score"
                        stroke="#0e7490"
                        fill="#0891b2"
                        fillOpacity={0.3}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </section>

            <section className="mt-8 rounded-xl bg-white p-8 shadow">
              <h2 className="text-2xl font-bold text-slate-900">
                Question results
              </h2>

              <p className="mt-2 max-w-3xl text-slate-600">
                Compare Employee and Senior
                Manager perceptions directly.
                Combined means are shown when
                the groups are reasonably aligned.
                When the opinion gap is 3.00
                points or greater, the combined
                mean is hidden because it could
                mask opposing perceptions.
              </p>

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

                          <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold ${getInterventionClasses(
                              questionScore
                                .intervention_tier,
                              questionScore
                                .opinion_gap,
                            )}`}
                          >
                            {getQuestionStatusLabel(
                              questionScore
                                .intervention_tier,
                              questionScore
                                .opinion_gap,
                            )}
                          </span>
                        </div>

                        <div
                            className={`mt-5 grid gap-4 ${
                              isHighOverride(
                                questionScore.opinion_gap,
                              )
                                ? "sm:grid-cols-3"
                                : "sm:grid-cols-4"
                            }`}
                          >
                            <div>
                              <p className="text-sm text-slate-500">
                                Employee mean
                              </p>

                              <p className="mt-1 text-xl font-bold text-slate-900">
                                {formatScore(
                                  questionScore.employee_mean,
                                )}
                              </p>
                            </div>

                            <div>
                              <p className="text-sm text-slate-500">
                                Senior Manager mean
                              </p>

                              <p className="mt-1 text-xl font-bold text-slate-900">
                                {formatScore(
                                  questionScore.manager_mean,
                                )}
                              </p>
                            </div>

                            {!isHighOverride(
                              questionScore.opinion_gap,
                            ) && (
                              <div>
                                <p className="text-sm text-slate-500">
                                  Combined mean
                                </p>

                                <p className="mt-1 text-xl font-bold text-slate-900">
                                  {formatScore(
                                    questionScore.combined_mean,
                                  )}
                                </p>
                              </div>
                            )}

                            <div>
                              <p className="text-sm text-slate-500">
                                Opinion gap
                              </p>

                              <p
                                className={`mt-1 text-xl font-bold ${
                                  isHighOverride(
                                    questionScore.opinion_gap,
                                  )
                                    ? "text-red-700"
                                    : "text-slate-900"
                                }`}
                              >
                                {formatScore(
                                  questionScore.opinion_gap,
                                )}
                              </p>
                            </div>
                          </div>

                        {isHighOverride(
                          questionScore
                            .opinion_gap,
                        ) && (
                          <div className="mt-5 rounded-lg border border-red-200 bg-red-50 p-4">
                            <p className="font-semibold text-red-900">
                              Extreme perception
                              difference
                            </p>

                            <p className="mt-1 text-sm leading-6 text-red-800">
                              The Employee and
                              Senior Manager scores
                              differ by 3.00 points
                              or more. The combined
                              average is not shown
                              because it could hide
                              the opposing
                              perceptions.
                            </p>
                          </div>
                        )}
                      </article>
                    ),
                  )}
                </div>
              )}
            </section>
          </>
        )}

        <section className="mt-8 rounded-xl bg-white p-8 shadow">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-violet-700">
                Gemini analysis
              </p>

              <h2 className="mt-1 text-2xl font-bold text-slate-900">
                WorkSafe-grounded improvement
                analysis
              </h2>

              <p className="mt-2 max-w-3xl text-slate-600">
                Recommendations use the
                assessment evidence together
                with curated official WorkSafe
                SafePlus guidance.
              </p>
            </div>

            {aiAnalysis && (
              <div className="text-right text-sm text-slate-500">
                <p className="font-semibold text-slate-700">
                  {aiAnalysis.ai_provider}
                </p>

                {aiAnalysis.generated_at && (
                  <p className="mt-1">
                    Generated{" "}
                    {new Date(
                      aiAnalysis.generated_at,
                    ).toLocaleString()}
                  </p>
                )}
              </div>
            )}
          </div>

          {!aiAnalysis ? (
            <div className="mt-8 rounded-lg border border-dashed border-slate-300 p-8 text-center">
              <h3 className="font-bold text-slate-900">
                AI analysis has not been
                generated
              </h3>

              <p className="mt-2 text-slate-600">
                Complete the assessment and
                click Generate AI analysis.
              </p>
            </div>
          ) : aiAnalysis.status !==
            "completed" ? (
            <div className="mt-8 rounded-lg bg-amber-50 p-5 text-amber-800">
              AI analysis status:{" "}
              <span className="font-semibold capitalize">
                {aiAnalysis.status}
              </span>
            </div>
          ) : (
            <div className="mt-8 space-y-8">
              <article className="rounded-xl bg-violet-50 p-6">
                <h3 className="text-xl font-bold text-violet-950">
                  Overall summary
                </h3>

                <p className="mt-4 whitespace-pre-line leading-7 text-slate-700">
                  {aiAnalysis.overall_summary}
                </p>
              </article>

              <div className="grid gap-6 lg:grid-cols-2">
                <article className="rounded-xl border border-emerald-200 bg-emerald-50 p-6">
                  <h3 className="text-xl font-bold text-emerald-900">
                    Key strengths
                  </h3>

                  {keyStrengths.length ===
                  0 ? (
                    <p className="mt-3 text-emerald-800">
                      No strengths were
                      returned.
                    </p>
                  ) : (
                    <ul className="mt-4 space-y-3">
                      {keyStrengths.map(
                        (strength, index) => (
                          <li
                            key={`${strength}-${index}`}
                            className="flex gap-3 text-slate-700"
                          >
                            <span className="font-bold text-emerald-700">
                              ✓
                            </span>

                            <span>
                              {strength}
                            </span>
                          </li>
                        ),
                      )}
                    </ul>
                  )}
                </article>

                <article className="rounded-xl border border-red-200 bg-red-50 p-6">
                  <h3 className="text-xl font-bold text-red-900">
                    Key risks
                  </h3>

                  {keyRisks.length === 0 ? (
                    <p className="mt-3 text-red-800">
                      No risks were returned.
                    </p>
                  ) : (
                    <ul className="mt-4 space-y-3">
                      {keyRisks.map(
                        (risk, index) => (
                          <li
                            key={`${risk}-${index}`}
                            className="flex gap-3 text-slate-700"
                          >
                            <span className="font-bold text-red-700">
                              !
                            </span>

                            <span>{risk}</span>
                          </li>
                        ),
                      )}
                    </ul>
                  )}
                </article>
              </div>

              <section>
                <h3 className="text-2xl font-bold text-slate-900">
                  Domain analysis
                </h3>

                <div className="mt-5 grid gap-5 lg:grid-cols-3">
                  {aiDomainSummaries.map(
                    (domainSummary) => (
                      <article
                        key={
                          domainSummary.domain_name
                        }
                        className="rounded-xl border border-slate-200 p-6"
                      >
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <h4 className="font-bold text-slate-900">
                            {
                              domainSummary.domain_name
                            }
                          </h4>

                          <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold ${getMaturityClasses(
                              domainSummary.maturity_level,
                            )}`}
                          >
                            {
                              domainSummary.maturity_level
                            }
                          </span>
                        </div>

                        <p className="mt-3 text-3xl font-bold text-slate-900">
                          {formatScore(
                            domainSummary.score,
                          )}
                        </p>

                        <p className="mt-4 leading-7 text-slate-700">
                          {
                            domainSummary.summary
                          }
                        </p>

                        {domainSummary
                          .strengths.length >
                          0 && (
                          <div className="mt-5">
                            <p className="text-sm font-bold text-emerald-800">
                              Strengths
                            </p>

                            <ul className="mt-2 space-y-2 text-sm text-slate-700">
                              {domainSummary.strengths.map(
                                (
                                  strength,
                                  index,
                                ) => (
                                  <li
                                    key={`${strength}-${index}`}
                                  >
                                    • {strength}
                                  </li>
                                ),
                              )}
                            </ul>
                          </div>
                        )}

                        {domainSummary
                          .improvement_areas
                          .length > 0 && (
                          <div className="mt-5">
                            <p className="text-sm font-bold text-orange-800">
                              Improvement areas
                            </p>

                            <ul className="mt-2 space-y-2 text-sm text-slate-700">
                              {domainSummary.improvement_areas.map(
                                (
                                  improvement,
                                  index,
                                ) => (
                                  <li
                                    key={`${improvement}-${index}`}
                                  >
                                    •{" "}
                                    {improvement}
                                  </li>
                                ),
                              )}
                            </ul>
                          </div>
                        )}

                        <SourceLinks
                          sourceIds={
                            domainSummary.source_ids
                          }
                          sources={
                            guidanceSources
                          }
                        />
                      </article>
                    ),
                  )}
                </div>
              </section>

              <section>
                <h3 className="text-2xl font-bold text-slate-900">
                  Priority actions
                </h3>

                <div className="mt-5 space-y-5">
                  {priorityActions.map(
                    (action) => (
                      <article
                        key={`${action.priority}-${action.title}`}
                        className="rounded-xl border border-slate-200 p-6"
                      >
                        <div className="flex flex-wrap items-start justify-between gap-4">
                          <div>
                            <p className="text-sm font-semibold uppercase tracking-wide text-violet-700">
                              Priority{" "}
                              {action.priority}
                            </p>

                            <h4 className="mt-1 text-xl font-bold text-slate-900">
                              {action.title}
                            </h4>

                            <p className="mt-1 text-sm text-slate-500">
                              {
                                action.related_domain
                              }
                            </p>
                          </div>

                          <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold ${getUrgencyClasses(
                              action.urgency,
                            )}`}
                          >
                            {action.urgency}
                          </span>
                        </div>

                        <div className="mt-5 grid gap-5 lg:grid-cols-2">
                          <div>
                            <p className="font-bold text-slate-900">
                              Assessment
                              evidence
                            </p>

                            <ul className="mt-2 space-y-2 text-slate-700">
                              {action.assessment_evidence.map(
                                (
                                  evidence,
                                  index,
                                ) => (
                                  <li
                                    key={`${evidence}-${index}`}
                                  >
                                    • {evidence}
                                  </li>
                                ),
                              )}
                            </ul>
                          </div>

                          <div>
                            <p className="font-bold text-slate-900">
                              Why this matters
                            </p>

                            <p className="mt-2 leading-7 text-slate-700">
                              {action.reason}
                            </p>
                          </div>
                        </div>

                        <div className="mt-5 rounded-lg bg-slate-50 p-5">
                          <p className="font-bold text-slate-900">
                            Recommended action
                          </p>

                          <p className="mt-2 leading-7 text-slate-700">
                            {
                              action.recommended_action
                            }
                          </p>
                        </div>

                        <p className="mt-4 text-sm text-slate-600">
                          <span className="font-semibold">
                            Source relevance:
                          </span>{" "}
                          {
                            action.source_relevance
                          }
                        </p>

                        <SourceLinks
                          sourceIds={
                            action.source_ids
                          }
                          sources={
                            guidanceSources
                          }
                        />
                      </article>
                    ),
                  )}
                </div>
              </section>

              <section>
                <h3 className="text-2xl font-bold text-slate-900">
                  Improvement roadmap
                </h3>

                <div className="mt-5 space-y-4">
                  {roadmap.map(
                    (item, index) => (
                      <article
                        key={`${item.timeframe}-${index}`}
                        className="rounded-xl border border-slate-200 p-6"
                      >
                        <div className="flex flex-wrap items-start justify-between gap-4">
                          <div>
                            <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
                              {item.timeframe}
                            </p>

                            <h4 className="mt-1 text-lg font-bold text-slate-900">
                              {item.objective}
                            </h4>
                          </div>

                          <span className="rounded-full bg-cyan-50 px-3 py-1 text-xs font-semibold text-cyan-800">
                            Step {index + 1}
                          </span>
                        </div>

                        <div className="mt-5">
                          <p className="font-bold text-slate-900">
                            Actions
                          </p>

                          <ul className="mt-2 space-y-2 text-slate-700">
                            {item.actions.map(
                              (
                                roadmapAction,
                                actionIndex,
                              ) => (
                                <li
                                  key={`${roadmapAction}-${actionIndex}`}
                                >
                                  •{" "}
                                  {roadmapAction}
                                </li>
                              ),
                            )}
                          </ul>
                        </div>

                        <div className="mt-5 rounded-lg bg-emerald-50 p-4">
                          <p className="text-sm font-bold text-emerald-900">
                            Success indicator
                          </p>

                          <p className="mt-1 text-sm text-emerald-800">
                            {
                              item.success_indicator
                            }
                          </p>
                        </div>

                        <SourceLinks
                          sourceIds={
                            item.source_ids
                          }
                          sources={
                            guidanceSources
                          }
                        />
                      </article>
                    ),
                  )}
                </div>
              </section>

              {guidanceSources.length > 0 && (
                <section className="rounded-xl bg-slate-50 p-6">
                  <h3 className="text-xl font-bold text-slate-900">
                    Official guidance sources
                  </h3>

                  <p className="mt-2 text-sm text-slate-600">
                    The AI was limited to
                    curated summaries of these
                    official WorkSafe SafePlus
                    resources.
                  </p>

                  <div className="mt-5 grid gap-4 md:grid-cols-2">
                    {guidanceSources.map(
                      (source) => (
                        <a
                          key={source.source_id}
                          href={source.url}
                          target="_blank"
                          rel="noreferrer"
                          className="rounded-lg border border-slate-200 bg-white p-4 hover:border-cyan-400"
                        >
                          <p className="font-bold text-cyan-800">
                            {source.title}
                          </p>

                          <p className="mt-1 text-xs text-slate-500">
                            {source.source_id}
                          </p>
                        </a>
                      ),
                    )}
                  </div>
                </section>
              )}

              {limitations.length > 0 && (
                <section className="rounded-xl border border-amber-200 bg-amber-50 p-6">
                  <h3 className="text-xl font-bold text-amber-900">
                    Important limitations
                  </h3>

                  <ul className="mt-4 space-y-3 text-amber-900">
                    {limitations.map(
                      (
                        limitation,
                        index,
                      ) => (
                        <li
                          key={`${limitation}-${index}`}
                        >
                          • {limitation}
                        </li>
                      ),
                    )}
                  </ul>
                </section>
              )}
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

export default AssessmentResultsPage;