import {
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  clearSurveyAnswer,
  getSurveySubmission,
  saveSurveyAnswer,
  submitSurvey,
  type PublicSurveyQuestion,
  type ResponseOption,
  type SurveySubmissionDetail,
} from "../../api/publicSurveyApi";

const standardResponseOptions: ResponseOption[] = [
  "Strongly Agree",
  "Agree",
  "Neither Agree nor Disagree",
  "Disagree",
  "Strongly Disagree",
];

function PublicSurveyQuestionnairePage() {
  const navigate = useNavigate();
  const { submissionToken } =
    useParams();

  const [
    submission,
    setSubmission,
  ] =
    useState<SurveySubmissionDetail | null>(
      null,
    );

  const [
    currentQuestionIndex,
    setCurrentQuestionIndex,
  ] = useState(0);

  const [isLoading, setIsLoading] =
    useState(true);

  const [isSaving, setIsSaving] =
    useState(false);

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState("");

  const [
    successMessage,
    setSuccessMessage,
  ] = useState("");

  useEffect(() => {
    async function loadSubmission() {
      if (!submissionToken) {
        setErrorMessage(
          "Submission token is missing.",
        );
        setIsLoading(false);
        return;
      }

      try {
        setErrorMessage("");

        const loadedSubmission =
          await getSurveySubmission(
            submissionToken,
          );

        setSubmission(loadedSubmission);

        const firstUnansweredIndex =
          loadedSubmission.questions.findIndex(
            (question) =>
              question.selected_response ===
              null,
          );

        if (firstUnansweredIndex >= 0) {
          setCurrentQuestionIndex(
            firstUnansweredIndex,
          );
        }
      } catch (error) {
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Unable to load this survey.",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadSubmission();
  }, [submissionToken]);

  const currentQuestion =
    useMemo<PublicSurveyQuestion | null>(
      () =>
        submission?.questions[
          currentQuestionIndex
        ] ?? null,
      [
        currentQuestionIndex,
        submission,
      ],
    );

  const availableOptions =
    useMemo(() => {
      if (
        submission?.respondent_group ===
          "Employee" &&
        currentQuestion
          ?.is_situation_dependent
      ) {
        return [
          ...standardResponseOptions,
          "N/A" as ResponseOption,
        ];
      }

      return standardResponseOptions;
    }, [
      currentQuestion,
      submission,
    ]);

  const progressPercentage =
    useMemo(() => {
      if (
        !submission ||
        submission.total_question_count === 0
      ) {
        return 0;
      }

      return Math.round(
        (submission.answered_question_count /
          submission.total_question_count) *
          100,
      );
    }, [submission]);

  async function handleSelectAnswer(
  responseOption: ResponseOption,
) {
  if (
    !submissionToken ||
    !currentQuestion ||
    !submission
  ) {
    return;
  }

  try {
    setIsSaving(true);
    setErrorMessage("");
    setSuccessMessage("");

    const isDeselecting =
      currentQuestion.selected_response ===
      responseOption;

    const result = isDeselecting
      ? await clearSurveyAnswer(
          submissionToken,
          currentQuestion.question_id,
        )
      : await saveSurveyAnswer(
          submissionToken,
          currentQuestion.question_id,
          responseOption,
        );

    setSubmission(
      (currentSubmission) => {
        if (!currentSubmission) {
          return null;
        }

        return {
          ...currentSubmission,
          answered_question_count:
            result.answered_question_count,
          questions:
            currentSubmission.questions.map(
              (question) =>
                question.question_id ===
                currentQuestion.question_id
                  ? {
                      ...question,
                      selected_response:
                        isDeselecting
                          ? null
                          : responseOption,
                    }
                  : question,
            ),
        };
      },
    );

    setSuccessMessage(
      isDeselecting
        ? "Answer removed."
        : "Answer saved.",
    );
  } catch (error) {
    setErrorMessage(
      error instanceof Error
        ? error.message
        : "Unable to update your answer.",
    );
  } finally {
    setIsSaving(false);
  }
}
  function handlePrevious() {
    setSuccessMessage("");

    setCurrentQuestionIndex(
      (currentIndex) =>
        Math.max(
          currentIndex - 1,
          0,
        ),
    );
  }

  function handleNext() {
    setSuccessMessage("");

    if (!submission) {
      return;
    }

    setCurrentQuestionIndex(
      (currentIndex) =>
        Math.min(
          currentIndex + 1,
          submission.questions.length - 1,
        ),
    );
  }

  async function handleSubmitSurvey() {
    if (
      !submissionToken ||
      !submission
    ) {
      return;
    }

    if (
      submission.answered_question_count !==
      submission.total_question_count
    ) {
      setErrorMessage(
        `Please answer all questions before submitting. ${submission.answered_question_count} of ${submission.total_question_count} are answered.`,
      );
      return;
    }

    const confirmed = window.confirm(
      "Submit this survey? You will not be able to change your answers afterward.",
    );

    if (!confirmed) {
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMessage("");

      const result =
        await submitSurvey(
          submissionToken,
        );

      setSubmission(
        (currentSubmission) =>
          currentSubmission
            ? {
                ...currentSubmission,
                status: result.status,
                submitted_at:
                  result.submitted_at,
              }
            : null,
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to submit the survey.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isLoading) {
    return (
      <main className="min-h-screen bg-slate-100 p-8">
        <p className="text-slate-700">
          Loading questionnaire...
        </p>
      </main>
    );
  }

  if (!submission) {
    return (
      <main className="min-h-screen bg-slate-100 px-6 py-12">
        <section className="mx-auto max-w-2xl rounded-xl bg-white p-8 shadow">
          <h1 className="text-2xl font-bold text-red-700">
            Survey unavailable
          </h1>

          <p className="mt-3 text-slate-700">
            {errorMessage ||
              "This survey could not be loaded."}
          </p>
        </section>
      </main>
    );
  }

  if (
    submission.status === "submitted"
  ) {
    return (
      <main className="min-h-screen bg-slate-100 px-6 py-12">
        <section className="mx-auto max-w-2xl rounded-xl bg-white p-8 text-center shadow">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-2xl text-emerald-700">
            ✓
          </div>

          <h1 className="mt-5 text-3xl font-bold text-slate-900">
            Survey submitted
          </h1>

          <p className="mt-3 text-slate-600">
            Thank you. Your responses have
            been submitted successfully.
          </p>

          {submission.submitted_at && (
            <p className="mt-3 text-sm text-slate-500">
              Submitted{" "}
              {new Date(
                submission.submitted_at,
              ).toLocaleString()}
            </p>
          )}

          <button
            type="button"
            onClick={() =>
              navigate(
                `/survey/${submission.public_code}`,
              )
            }
            className="mt-8 rounded-lg border border-slate-300 px-5 py-3 font-semibold text-slate-700"
          >
            Return to survey page
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-100 px-6 py-12">
      <section className="mx-auto max-w-4xl">
        <header className="rounded-xl bg-white p-8 shadow">
            <div className="mb-6">
                <button
                type="button"
                onClick={() =>
                navigate(
                `/survey/${submission.public_code}`,
                )
            }
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                    >
                    ← Back to respondent selection
                </button>
            </div>
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
            SafePlus survey
          </p>

          <h1 className="mt-2 text-2xl font-bold text-slate-900">
            {submission.organisation_name}
          </h1>

          <p className="mt-2 text-slate-600">
            Responding as{" "}
            <span className="font-semibold">
              {submission.respondent_group}
            </span>
          </p>

          <div className="mt-6">
            <div className="flex items-center justify-between gap-4">
              <p className="text-sm font-medium text-slate-600">
                {submission.answered_question_count}{" "}
                of{" "}
                {submission.total_question_count}{" "}
                answered
              </p>

              <p className="text-sm font-bold text-slate-900">
                {progressPercentage}%
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

        {currentQuestion && (
          <section className="mt-8 rounded-xl bg-white p-8 shadow">
            <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
              {currentQuestion.domain_name}
            </p>

            <p className="mt-2 text-sm text-slate-500">
              Question{" "}
              {currentQuestionIndex + 1} of{" "}
              {submission.total_question_count}
              {" · "}
              {currentQuestion.question_number}
            </p>

            <h2 className="mt-5 text-2xl font-bold leading-relaxed text-slate-900">
              {currentQuestion.question_text}
            </h2>

            <div className="mt-8 space-y-3">
              {availableOptions.map(
                (option) => {
                  const isSelected =
                    currentQuestion.selected_response ===
                    option;

                  return (
                    <button
                      key={option}
                      type="button"
                      onClick={() =>
                        handleSelectAnswer(
                          option,
                        )
                      }
                      disabled={isSaving}
                      className={`w-full rounded-lg border p-4 text-left font-medium transition ${
                        isSelected
                          ? "border-cyan-700 bg-cyan-50 text-cyan-900"
                          : "border-slate-200 bg-white text-slate-800 hover:border-slate-400"
                      } disabled:opacity-60`}
                    >
                      {option}
                    </button>
                  );
                },
              )}
            </div>

            <div className="mt-8 flex flex-wrap items-center justify-between gap-4">
              <button
                type="button"
                onClick={handlePrevious}
                disabled={
                  currentQuestionIndex === 0
                }
                className="rounded-lg border border-slate-300 px-5 py-3 font-semibold text-slate-700 disabled:opacity-40"
              >
                Previous
              </button>

              <div className="flex flex-wrap gap-3">
                {currentQuestionIndex <
                submission.questions.length -
                  1 ? (
                  <button
                    type="button"
                    onClick={handleNext}
                    className="rounded-lg bg-slate-900 px-5 py-3 font-semibold text-white"
                  >
                    Next question
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={
                      handleSubmitSurvey
                    }
                    disabled={
                      isSubmitting ||
                      submission.answered_question_count !==
                        submission.total_question_count
                    }
                    className="rounded-lg bg-emerald-700 px-5 py-3 font-semibold text-white disabled:opacity-50"
                  >
                    {isSubmitting
                      ? "Submitting..."
                      : "Submit survey"}
                  </button>
                )}
              </div>
            </div>
          </section>
        )}
      </section>
    </main>
  );
}

export default PublicSurveyQuestionnairePage;