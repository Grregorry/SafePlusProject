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
  getAssessment,
  getAssessmentQuestions,
  getQuestionResponses,
  updateExpectedManualEntries,
  updateQuestionResponses,
  type Assessment,
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

  const [assessment, setAssessment] =
    useState<Assessment | null>(null);

  const [
    expectedManualEntriesEmployeeInput,
    setExpectedManualEntriesEmployeeInput,
  ] = useState("0");

  const [
    expectedManualEntriesManagerInput,
    setExpectedManualEntriesManagerInput,
  ] = useState("0");

  const [
    isSavingTarget,
    setIsSavingTarget,
  ] = useState(false);

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
    manualResponseValues,
    setManualResponseValues,
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
    isLoadingManualResponses,
    setIsLoadingManualResponses,
  ] = useState(false);

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
      }
    },
    [numericAssessmentId],
  );

  async function handleSaveExpectedManualEntries() {
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

    const employeeValue = Number(
      expectedManualEntriesEmployeeInput,
    );

    const managerValue = Number(
      expectedManualEntriesManagerInput,
    );

    if (
      !Number.isInteger(employeeValue) ||
      employeeValue < 0 ||
      !Number.isInteger(managerValue) ||
      managerValue < 0
    ) {
      setErrorMessage(
        "Enter whole numbers of 0 or more.",
      );
      return;
    }

    try {
      setIsSavingTarget(true);
      setErrorMessage("");
      setSuccessMessage("");

      const updatedAssessment =
        await updateExpectedManualEntries(
          numericAssessmentId,
          employeeValue,
          managerValue,
          accessToken,
        );

      setAssessment(updatedAssessment);

      await loadProgress(accessToken);

      setSuccessMessage(
        "Expected manual entries updated.",
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to update expected manual entries.",
      );
    } finally {
      setIsSavingTarget(false);
    }
  }

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

        return;
      }

      try {
        setErrorMessage("");

        const [
          loadedAssessment,
          loadedQuestions,
        ] = await Promise.all([
          getAssessment(
            numericAssessmentId,
            accessToken,
          ),
          getAssessmentQuestions(
            numericAssessmentId,
            accessToken,
          ),
        ]);

        setAssessment(loadedAssessment);

        setExpectedManualEntriesEmployeeInput(
          String(
            loadedAssessment.expected_manual_entries_employee,
          ),
        );

        setExpectedManualEntriesManagerInput(
          String(
            loadedAssessment.expected_manual_entries_manager,
          ),
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
    async function loadManualResponses() {
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
        setIsLoadingManualResponses(
          true,
        );
        setErrorMessage("");
        setSuccessMessage("");

        const response =
          await getQuestionResponses(
            numericAssessmentId,
            selectedQuestionId,
            respondentGroup,
            accessToken,
          );

        setManualResponseValues(
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

        setManualResponseValues(
          createEmptyResponseValues(),
        );
      } finally {
        setIsLoadingManualResponses(
          false,
        );
      }
    }

    void loadManualResponses();
  }, [
    navigate,
    numericAssessmentId,
    respondentGroup,
    selectedQuestionId,
  ]);

  const questionsByDomain = useMemo(
    () => {
      const groups = new Map<
        string,
        AssessmentSetupQuestion[]
      >();

      for (const question of questions) {
        const existingGroup = groups.get(
          question.domain_name,
        );

        if (existingGroup) {
          existingGroup.push(question);
        } else {
          groups.set(
            question.domain_name,
            [question],
          );
        }
      }

      return Array.from(groups.entries());
    },
    [questions],
  );

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

  const isLastQuestionGroup = useMemo(
    () =>
      respondentGroup ===
        "Senior Manager" &&
      questions.length > 0 &&
      selectedQuestionId ===
        questions[questions.length - 1]
          .question_id,
    [
      questions,
      respondentGroup,
      selectedQuestionId,
    ],
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

  const totalManualResponses = useMemo(
    () =>
      availableResponseOptions.reduce(
        (total, option) =>
          total +
          manualResponseValues[option],
        0,
      ),
    [
      availableResponseOptions,
      manualResponseValues,
    ],
  );

  // Paper surveys are tallied one question at a time, so the most
  // entries recorded for any question is how many have been counted.
  const manualEntriesRecorded = useMemo(
    () => {
      const questionProgress =
        progress?.questions ?? [];

      return {
        employee: Math.max(
          0,
          ...questionProgress.map(
            (question) =>
              question.employee_manual_entries_recorded,
          ),
        ),
        manager: Math.max(
          0,
          ...questionProgress.map(
            (question) =>
              question.manager_manual_entries_recorded,
          ),
        ),
      };
    },
    [progress],
  );

  function handleResponseChange(
    option: ResponseOption,
    value: string,
  ) {
    const numericValue = Number(value);

    setSuccessMessage("");

    setManualResponseValues(
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
            manualResponseValues[option],
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

      setManualResponseValues(
        convertResponsesToValues(
          savedResponse.responses,
        ),
      );

      await loadProgress(accessToken);

      const currentIndex =
        questions.findIndex(
          (question) =>
            question.question_id ===
            selectedQuestionId,
        );

      if (respondentGroup === "Employee") {
        setRespondentGroup(
          "Senior Manager",
        );

        setSuccessMessage(
          "Responses saved. Moved to Senior Manager for this question.",
        );
      } else if (
        currentIndex !== -1 &&
        currentIndex <
          questions.length - 1
      ) {
        const nextQuestion =
          questions[currentIndex + 1];

        setSelectedQuestionId(
          nextQuestion.question_id,
        );

        setRespondentGroup("Employee");

        setSuccessMessage(
          `Responses saved. Moved to Question ${nextQuestion.question_number}.`,
        );
      } else {
        setSuccessMessage(
          "Responses saved. That was the last question for both groups.",
        );
      }
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
      <main>
        <p className="text-slate-700">
          Loading assessment questions...
        </p>
      </main>
    );
  }

  return (
    <main>
      <section>
        <header className="rounded-xl bg-white p-8 shadow">
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
            {assessment?.name ?? "Assessment"}
          </p>

          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            Manual entry
          </h1>

          <p className="mt-3 max-w-3xl text-slate-600">
            Record the totals from paper
            surveys here, one question at a
            time. They are combined with the
            online survey responses when the
            assessment is scored.
          </p>

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

        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <section className="rounded-xl bg-white p-5 shadow">
            <h2 className="text-base font-bold text-slate-900">
              Manual entry responses
            </h2>

            <dl className="mt-3 flex flex-wrap gap-x-8 gap-y-2">
              <div className="flex items-baseline gap-2">
                <dd className="text-2xl font-bold text-slate-900">
                  {manualEntriesRecorded.employee}
                </dd>

                <dt className="text-sm text-slate-600">
                  Employee submitted
                </dt>
              </div>

              <div className="flex items-baseline gap-2">
                <dd className="text-2xl font-bold text-slate-900">
                  {manualEntriesRecorded.manager}
                </dd>

                <dt className="text-sm text-slate-600">
                  Senior Manager submitted
                </dt>
              </div>
            </dl>
          </section>

          <section className="rounded-xl bg-white p-5 shadow">
            <h2 className="text-base font-bold text-slate-900">
              Manual entry target
            </h2>

            <p className="mt-1 text-sm text-slate-600">
              Paper surveys to enter per group.
              Each question needs exactly this
              many.
            </p>

            <div className="mt-3 flex flex-wrap items-end gap-3">
              <div className="w-28">
                <label
                  htmlFor="expected-manual-entries-employee"
                  className="block text-xs font-semibold text-slate-700"
                >
                  Employee
                </label>

                <input
                  id="expected-manual-entries-employee"
                  type="number"
                  min="0"
                  step="1"
                  value={
                    expectedManualEntriesEmployeeInput
                  }
                  onChange={(event) =>
                    setExpectedManualEntriesEmployeeInput(
                      event.target.value,
                    )
                  }
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
                />
              </div>

              <div className="w-28">
                <label
                  htmlFor="expected-manual-entries-manager"
                  className="block text-xs font-semibold text-slate-700"
                >
                  Senior Manager
                </label>

                <input
                  id="expected-manual-entries-manager"
                  type="number"
                  min="0"
                  step="1"
                  value={
                    expectedManualEntriesManagerInput
                  }
                  onChange={(event) =>
                    setExpectedManualEntriesManagerInput(
                      event.target.value,
                    )
                  }
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
                />
              </div>

              <button
                type="button"
                onClick={
                  handleSaveExpectedManualEntries
                }
                disabled={isSavingTarget}
                className="rounded-lg bg-cyan-700 px-4 py-1.5 text-sm font-semibold text-white disabled:opacity-60"
              >
                {isSavingTarget
                  ? "Saving..."
                  : "Set target"}
              </button>
            </div>
          </section>
        </div>

        {questions.length === 0 ? (
          <section className="mt-8 rounded-xl bg-white p-8 shadow">
            <p className="text-slate-700">
              This assessment does not have
              any active questions.
            </p>
          </section>
        ) : (
          <div className="mt-8 grid gap-8 lg:grid-cols-[320px_1fr]">
            <aside className="rounded-xl bg-white p-6 shadow lg:sticky lg:top-6 lg:self-start">
              <h2 className="text-lg font-bold text-slate-900">
                Active questions
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                {questions.length} questions
                — tap a number to switch
              </p>

              <div className="mt-5 max-h-[650px] space-y-5 overflow-y-auto pr-1">
                {questionsByDomain.map(
                  ([
                    domainName,
                    domainQuestions,
                  ]) => (
                    <div key={domainName}>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                        {domainName}
                      </p>

                      <div className="mt-2 flex flex-wrap gap-2">
                        {domainQuestions.map(
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

                            const isComplete =
                              questionProgress
                                ?.fully_complete ??
                              false;

                            const manualTooltipParts =
                              [
                                progress &&
                                progress.expected_manual_entries_employee >
                                  0
                                  ? `Employee manual ${
                                      questionProgress?.employee_manual_entries_recorded ??
                                      0
                                    }/${progress.expected_manual_entries_employee}`
                                  : null,
                                progress &&
                                progress.expected_manual_entries_manager >
                                  0
                                  ? `Manager manual ${
                                      questionProgress?.manager_manual_entries_recorded ??
                                      0
                                    }/${progress.expected_manual_entries_manager}`
                                  : null,
                              ].filter(
                                (
                                  part,
                                ): part is string =>
                                  part !== null,
                              );

                            return (
                              <button
                                key={
                                  question.question_id
                                }
                                type="button"
                                title={[
                                  `${question.question_number} — ${
                                    isComplete
                                      ? "Complete"
                                      : "Incomplete"
                                  }`,
                                  ...manualTooltipParts,
                                ].join(" · ")}
                                onClick={() =>
                                  setSelectedQuestionId(
                                    question.question_id,
                                  )
                                }
                                className={`flex h-11 w-11 items-center justify-center rounded-full border text-xs font-semibold transition ${
                                  isSelected
                                    ? "border-cyan-700 bg-cyan-700 text-white"
                                    : isComplete
                                      ? "border-emerald-300 bg-emerald-50 text-emerald-800 hover:border-emerald-400"
                                      : "border-amber-300 bg-amber-50 text-amber-800 hover:border-amber-400"
                                }`}
                              >
                                {
                                  question.question_number
                                }
                              </button>
                            );
                          },
                        )}
                      </div>
                    </div>
                  ),
                )}
              </div>

              <div className="mt-5 flex flex-wrap items-center gap-4 text-xs text-slate-500">
                <span className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
                  Complete
                </span>

                <span className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
                  Incomplete
                </span>
              </div>
            </aside>

            <section className="rounded-xl bg-white p-6 shadow">
              {selectedQuestion && (
                <>
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
                      {
                        selectedQuestion.domain_name
                      }
                    </p>

                    <h2 className="mt-1 text-xl font-bold text-slate-900">
                      Question{" "}
                      {
                        selectedQuestion.question_number
                      }
                    </h2>

                    {selectedQuestionProgress && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
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
                          className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
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

                  <div className="mt-4 rounded-lg bg-slate-50 p-4">
                    <p className="text-xs font-semibold text-slate-500">
                      Employee wording
                    </p>

                    <p className="mt-1 text-sm text-slate-900">
                      {
                        selectedQuestion.employee_text
                      }
                    </p>

                    <p className="mt-3 text-xs font-semibold text-slate-500">
                      Senior Manager wording
                    </p>

                    <p className="mt-1 text-sm text-slate-900">
                      {
                        selectedQuestion.manager_text
                      }
                    </p>
                  </div>

                  <div className="mt-5">
                    <p className="text-sm font-semibold text-slate-700">
                      Respondent group
                    </p>

                    <div className="mt-2 flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() =>
                          setRespondentGroup(
                            "Employee",
                          )
                        }
                        className={`rounded-lg px-3 py-1.5 text-sm font-semibold ${
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
                        className={`rounded-lg px-3 py-1.5 text-sm font-semibold ${
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

                  {isLoadingManualResponses ? (
                      <p className="mt-6 text-slate-600">
                        Loading saved
                        responses...
                      </p>
                    ) : (
                      <>
                        <div className="mt-5 space-y-2">
                          {availableResponseOptions.map(
                            (option) => (
                              <label
                                key={option}
                                className="grid gap-2 rounded-lg border border-slate-200 p-2.5 sm:grid-cols-[1fr_110px] sm:items-center"
                              >
                                <span className="text-sm font-medium text-slate-800">
                                  {option}
                                </span>

                                <input
                                  type="number"
                                  min="0"
                                  step="1"
                                  value={
                                    manualResponseValues[
                                      option
                                    ]
                                  }
                                  onChange={(
                                    event,
                                  ) =>
                                    handleResponseChange(
                                      option,
                                      event
                                        .target
                                        .value,
                                    )
                                  }
                                  className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
                                />
                              </label>
                            ),
                          )}
                        </div>

                        <div className="mt-4 rounded-lg bg-slate-100 p-3">
                          <p className="text-xs text-slate-600">
                            Total manual
                            responses
                          </p>

                          <p className="mt-0.5 text-lg font-bold text-slate-900">
                            {
                              totalManualResponses
                            }
                          </p>
                        </div>

                        <button
                          type="button"
                          onClick={
                            handleSaveResponses
                          }
                          disabled={
                            isSaving
                          }
                          className="mt-5 rounded-lg bg-cyan-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
                        >
                          {isSaving
                            ? "Saving responses..."
                            : isLastQuestionGroup
                              ? "Completed"
                              : "Save & next"}
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
