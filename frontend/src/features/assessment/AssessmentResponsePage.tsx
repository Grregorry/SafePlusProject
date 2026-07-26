import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  getAssessmentQuestions,
  getQuestionResponses,
  updateQuestionResponses,
  type AssessmentSetupQuestion,
  type RespondentGroup,
  type ResponseCount,
  type ResponseOption,
} from "../../api/assessmentsApi";

import {
  getAssessmentProgress,
  type AssessmentProgress,
} from "../../api/assessmentProgressApi";

const standardResponseOptions: ResponseOption[] = [
  "Strongly Agree",
  "Agree",
  "Neither Agree nor Disagree",
  "Disagree",
  "Strongly Disagree",
];

type ResponseValues =
  Record<ResponseOption, number>;

function createEmptyResponseValues(): ResponseValues {
  return {
    "Strongly Agree": 0,
    Agree: 0,
    "Neither Agree nor Disagree": 0,
    Disagree: 0,
    "Strongly Disagree": 0,
    "N/A": 0,
  };
}

function convertResponsesToValues(
  responses: ResponseCount[],
): ResponseValues {
  const values = createEmptyResponseValues();

  for (const response of responses) {
    values[response.response_option] =
      response.count;
  }

  return values;
}

function AssessmentResponsePage() {
  const navigate = useNavigate();
  const { assessmentId } = useParams();

  const numericAssessmentId =
    Number(assessmentId);

  const [questions, setQuestions] =
    useState<AssessmentSetupQuestion[]>([]);

  const [
    selectedQuestionId,
    setSelectedQuestionId,
  ] = useState<number | null>(null);

  const [
    respondentGroup,
    setRespondentGroup,
  ] = useState<RespondentGroup>(
    "Employee",
  );

  const [
    responseValues,
    setResponseValues,
  ] = useState<ResponseValues>(
    createEmptyResponseValues(),
  );

  const [progress, setProgress] =
    useState<AssessmentProgress | null>(
      null,
    );

  const [
    isLoadingQuestions,
    setIsLoadingQuestions,
  ] = useState(true);

  const [
    isLoadingResponses,
    setIsLoadingResponses,
  ] = useState(false);

  const [
    isLoadingProgress,
    setIsLoadingProgress,
  ] = useState(true);

  const [isSaving, setIsSaving] =
    useState(false);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState("");

  const [
    successMessage,
    setSuccessMessage,
  ] = useState("");

  const loadProgress = useCallback(
    async (
      accessToken: string,
    ): Promise<void> => {
      try {
        setIsLoadingProgress(true);

        const loadedProgress =
          await getAssessmentProgress(
            numericAssessmentId,
            accessToken,
          );

        setProgress(loadedProgress);
      } catch (error) {
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Unable to load assessment progress.",
        );
      } finally {
        setIsLoadingProgress(false);
      }
    },
    [numericAssessmentId],
  );

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

        setIsLoadingQuestions(false);
        setIsLoadingProgress(false);

        return;
      }

      try {
        setErrorMessage("");

        const loadedQuestions =
          await getAssessmentQuestions(
            numericAssessmentId,
            accessToken,
          );

        const activeQuestions =
          loadedQuestions.filter(
            (question) =>
              question.is_active,
          );

        setQuestions(activeQuestions);

        if (activeQuestions.length > 0) {
          setSelectedQuestionId(
            activeQuestions[0].question_id,
          );
        }

        await loadProgress(accessToken);
      } catch (error) {
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Unable to load assessment questions.",
        );
      } finally {
        setIsLoadingQuestions(false);
      }
    }

    void loadPage();
  }, [
    loadProgress,
    navigate,
    numericAssessmentId,
  ]);

  useEffect(() => {
    async function loadResponses() {
      if (selectedQuestionId === null) {
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
        setIsLoadingResponses(true);
        setErrorMessage("");
        setSuccessMessage("");

        const response =
          await getQuestionResponses(
            numericAssessmentId,
            selectedQuestionId,
            respondentGroup,
            accessToken,
          );

        setResponseValues(
          convertResponsesToValues(
            response.responses,
          ),
        );
      } catch (error) {
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Unable to load saved responses.",
        );

        setResponseValues(
          createEmptyResponseValues(),
        );
      } finally {
        setIsLoadingResponses(false);
      }
    }

    void loadResponses();
  }, [
    navigate,
    numericAssessmentId,
    respondentGroup,
    selectedQuestionId,
  ]);

  const selectedQuestion = useMemo(
    () =>
      questions.find(
        (question) =>
          question.question_id ===
          selectedQuestionId,
      ) ?? null,
    [questions, selectedQuestionId],
  );

  const selectedQuestionProgress =
    useMemo(
      () =>
        progress?.questions.find(
          (question) =>
            question.question_id ===
            selectedQuestionId,
        ) ?? null,
      [progress, selectedQuestionId],
    );

  const availableResponseOptions =
    useMemo(() => {
      if (
        respondentGroup === "Employee" &&
        selectedQuestion
          ?.is_situation_dependent
      ) {
        return [
          ...standardResponseOptions,
          "N/A" as ResponseOption,
        ];
      }

      return standardResponseOptions;
    }, [
      respondentGroup,
      selectedQuestion,
    ]);

  const totalResponses = useMemo(
    () =>
      availableResponseOptions.reduce(
        (total, option) =>
          total + responseValues[option],
        0,
      ),
    [
      availableResponseOptions,
      responseValues,
    ],
  );

  function handleResponseChange(
    option: ResponseOption,
    value: string,
  ) {
    const numericValue = Number(value);

    setSuccessMessage("");

    setResponseValues(
      (currentValues) => ({
        ...currentValues,
        [option]:
          Number.isInteger(numericValue) &&
          numericValue >= 0
            ? numericValue
            : 0,
      }),
    );
  }

  async function handleSaveResponses() {
    if (selectedQuestionId === null) {
      setErrorMessage(
        "Please select a question.",
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

    const responses: ResponseCount[] =
      availableResponseOptions.map(
        (option) => ({
          response_option: option,
          count:
            responseValues[option],
        }),
      );

    try {
      setIsSaving(true);
      setErrorMessage("");
      setSuccessMessage("");

      const savedResponse =
        await updateQuestionResponses(
          numericAssessmentId,
          selectedQuestionId,
          respondentGroup,
          responses,
          accessToken,
        );

      setResponseValues(
        convertResponsesToValues(
          savedResponse.responses,
        ),
      );

      await loadProgress(accessToken);

      setSuccessMessage(
        "Responses saved successfully.",
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to save responses.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoadingQuestions) {
    return (
      <main className="min-h-screen bg-slate-100 p-8">
        <p className="text-slate-700">
          Loading assessment questions...
        </p>
      </main>
    );
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
            Enter response counts
          </h1>

          <p className="mt-3 text-slate-600">
            Enter the aggregated survey response
            totals for every active question.
          </p>

          <div className="mt-6 flex flex-wrap gap-4">
            <button
              type="button"
              onClick={() =>
                navigate(
                  `/assessments/${numericAssessmentId}`,
                )
              }
              className="rounded-lg border border-slate-300 px-4 py-2 font-semibold text-slate-700"
            >
              Question setup
            </button>

            <button
              type="button"
              onClick={() =>
                navigate(
                  `/assessments/${numericAssessmentId}/results`,
                )
              }
              className="rounded-lg bg-slate-900 px-4 py-2 font-semibold text-white"
            >
              View results
            </button>

            <button
              type="button"
              onClick={() =>
                navigate("/account")
              }
              className="rounded-lg border border-slate-300 px-4 py-2 font-semibold text-slate-700"
            >
              Return to account
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
        </header>

        <section className="mt-8 rounded-xl bg-white p-8 shadow">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
                Assessment progress
              </p>

              <h2 className="mt-1 text-2xl font-bold text-slate-900">
                Response completion
              </h2>
            </div>

            <p className="text-3xl font-bold text-slate-900">
              {progress?.overall_progress_percentage ??
                0}
              %
            </p>
          </div>

          {isLoadingProgress ? (
            <p className="mt-6 text-slate-600">
              Loading progress...
            </p>
          ) : (
            <>
              <div className="mt-6 h-3 overflow-hidden rounded-full bg-slate-200">
                <div
                  className="h-full bg-cyan-700 transition-all"
                  style={{
                    width: `${
                      progress
                        ?.overall_progress_percentage ??
                      0
                    }%`,
                  }}
                />
              </div>

              <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <article className="rounded-lg bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">
                    Active questions
                  </p>

                  <p className="mt-1 text-2xl font-bold text-slate-900">
                    {progress
                      ?.active_question_count ??
                      0}
                  </p>
                </article>

                <article className="rounded-lg bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">
                    Employee complete
                  </p>

                  <p className="mt-1 text-2xl font-bold text-slate-900">
                    {progress
                      ?.employee_complete_count ??
                      0}
                    {" / "}
                    {progress
                      ?.active_question_count ??
                      0}
                  </p>
                </article>

                <article className="rounded-lg bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">
                    Manager complete
                  </p>

                  <p className="mt-1 text-2xl font-bold text-slate-900">
                    {progress
                      ?.manager_complete_count ??
                      0}
                    {" / "}
                    {progress
                      ?.active_question_count ??
                      0}
                  </p>
                </article>

                <article className="rounded-lg bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">
                    Fully answered
                  </p>

                  <p className="mt-1 text-2xl font-bold text-slate-900">
                    {progress
                      ?.fully_complete_count ??
                      0}
                    {" / "}
                    {progress
                      ?.active_question_count ??
                      0}
                  </p>
                </article>
              </div>
            </>
          )}
        </section>

        {questions.length === 0 ? (
          <section className="mt-8 rounded-xl bg-white p-8 shadow">
            <p className="text-slate-700">
              This assessment does not have
              any active questions.
            </p>
          </section>
        ) : (
          <div className="mt-8 grid gap-8 lg:grid-cols-[320px_1fr]">
            <aside className="rounded-xl bg-white p-6 shadow">
              <h2 className="text-lg font-bold text-slate-900">
                Active questions
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                {questions.length} questions
              </p>

              <div className="mt-6 max-h-[650px] space-y-2 overflow-y-auto">
                {questions.map(
                  (question) => {
                    const isSelected =
                      question.question_id ===
                      selectedQuestionId;

                    const questionProgress =
                      progress?.questions.find(
                        (item) =>
                          item.question_id ===
                          question.question_id,
                      );

                    return (
                      <button
                        key={
                          question.question_id
                        }
                        type="button"
                        onClick={() =>
                          setSelectedQuestionId(
                            question.question_id,
                          )
                        }
                        className={`w-full rounded-lg border p-4 text-left ${
                          isSelected
                            ? "border-cyan-700 bg-cyan-50"
                            : "border-slate-200 bg-white"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <span className="font-semibold text-slate-900">
                            {
                              question.question_number
                            }
                          </span>

                          <span
                            className={`rounded-full px-2 py-1 text-xs font-semibold ${
                              questionProgress
                                ?.fully_complete
                                ? "bg-emerald-100 text-emerald-800"
                                : "bg-amber-100 text-amber-800"
                            }`}
                          >
                            {questionProgress
                              ?.fully_complete
                              ? "Complete"
                              : "Incomplete"}
                          </span>
                        </div>

                        <span className="mt-1 block text-sm text-slate-500">
                          {
                            question.domain_name
                          }
                        </span>

                        <div className="mt-3 flex gap-2 text-xs">
                          <span
                            className={
                              questionProgress
                                ?.employee_complete
                                ? "text-emerald-700"
                                : "text-slate-400"
                            }
                          >
                            Employee
                          </span>

                          <span
                            className={
                              questionProgress
                                ?.manager_complete
                                ? "text-emerald-700"
                                : "text-slate-400"
                            }
                          >
                            Manager
                          </span>
                        </div>
                      </button>
                    );
                  },
                )}
              </div>
            </aside>

            <section className="rounded-xl bg-white p-8 shadow">
              {selectedQuestion && (
                <>
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
                      {
                        selectedQuestion.domain_name
                      }
                    </p>

                    <h2 className="mt-2 text-2xl font-bold text-slate-900">
                      Question{" "}
                      {
                        selectedQuestion.question_number
                      }
                    </h2>

                    {selectedQuestionProgress && (
                      <div className="mt-4 flex flex-wrap gap-2">
                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${
                            selectedQuestionProgress
                              .employee_complete
                              ? "bg-emerald-100 text-emerald-800"
                              : "bg-slate-100 text-slate-600"
                          }`}
                        >
                          Employee{" "}
                          {selectedQuestionProgress
                            .employee_complete
                            ? "complete"
                            : "incomplete"}
                        </span>

                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${
                            selectedQuestionProgress
                              .manager_complete
                              ? "bg-emerald-100 text-emerald-800"
                              : "bg-slate-100 text-slate-600"
                          }`}
                        >
                          Manager{" "}
                          {selectedQuestionProgress
                            .manager_complete
                            ? "complete"
                            : "incomplete"}
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="mt-6 rounded-lg bg-slate-50 p-5">
                    <p className="text-sm font-semibold text-slate-500">
                      Employee wording
                    </p>

                    <p className="mt-2 text-slate-900">
                      {
                        selectedQuestion.employee_text
                      }
                    </p>

                    <p className="mt-5 text-sm font-semibold text-slate-500">
                      Senior Manager wording
                    </p>

                    <p className="mt-2 text-slate-900">
                      {
                        selectedQuestion.manager_text
                      }
                    </p>
                  </div>

                  <div className="mt-8">
                    <p className="text-sm font-semibold text-slate-700">
                      Respondent group
                    </p>

                    <div className="mt-3 flex flex-wrap gap-3">
                      <button
                        type="button"
                        onClick={() =>
                          setRespondentGroup(
                            "Employee",
                          )
                        }
                        className={`rounded-lg px-4 py-2 font-semibold ${
                          respondentGroup ===
                          "Employee"
                            ? "bg-cyan-700 text-white"
                            : "border border-slate-300 text-slate-700"
                        }`}
                      >
                        Employee
                      </button>

                      <button
                        type="button"
                        onClick={() =>
                          setRespondentGroup(
                            "Senior Manager",
                          )
                        }
                        className={`rounded-lg px-4 py-2 font-semibold ${
                          respondentGroup ===
                          "Senior Manager"
                            ? "bg-cyan-700 text-white"
                            : "border border-slate-300 text-slate-700"
                        }`}
                      >
                        Senior Manager
                      </button>
                    </div>
                  </div>

                  {isLoadingResponses ? (
                    <p className="mt-8 text-slate-600">
                      Loading saved responses...
                    </p>
                  ) : (
                    <>
                      <div className="mt-8 space-y-4">
                        {availableResponseOptions.map(
                          (option) => (
                            <label
                              key={option}
                              className="grid gap-2 rounded-lg border border-slate-200 p-4 sm:grid-cols-[1fr_140px] sm:items-center"
                            >
                              <span className="font-medium text-slate-800">
                                {option}
                              </span>

                              <input
                                type="number"
                                min="0"
                                step="1"
                                value={
                                  responseValues[
                                    option
                                  ]
                                }
                                onChange={(
                                  event,
                                ) =>
                                  handleResponseChange(
                                    option,
                                    event.target
                                      .value,
                                  )
                                }
                                className="rounded-lg border border-slate-300 px-3 py-2"
                              />
                            </label>
                          ),
                        )}
                      </div>

                      <div className="mt-6 rounded-lg bg-slate-100 p-4">
                        <p className="text-sm text-slate-600">
                          Total responses
                        </p>

                        <p className="mt-1 text-2xl font-bold text-slate-900">
                          {totalResponses}
                        </p>
                      </div>

                      <button
                        type="button"
                        onClick={
                          handleSaveResponses
                        }
                        disabled={isSaving}
                        className="mt-8 rounded-lg bg-cyan-700 px-5 py-3 font-semibold text-white disabled:opacity-60"
                      >
                        {isSaving
                          ? "Saving responses..."
                          : "Save responses"}
                      </button>
                    </>
                  )}
                </>
              )}
            </section>
          </div>
        )}
      </section>
    </main>
  );
}

export default AssessmentResponsePage;