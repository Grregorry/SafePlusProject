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
import { useConfirm } from "../../components/useConfirm";

// The five scale answers, lowest to highest, numbered as they are
// scored (Strongly Disagree = 1 ... Strongly Agree = 5).
const scaleOptions: {
  option: ResponseOption;
  value: number;
  label: string;
}[] = [
  {
    option: "Strongly Disagree",
    value: 1,
    label: "Strongly disagree",
  },
  {
    option: "Disagree",
    value: 2,
    label: "Disagree",
  },
  {
    option: "Neither Agree nor Disagree",
    value: 3,
    label: "Neither agree nor disagree",
  },
  {
    option: "Agree",
    value: 4,
    label: "Agree",
  },
  {
    option: "Strongly Agree",
    value: 5,
    label: "Strongly agree",
  },
];

type DomainSection = {
  name: string;
  questions: PublicSurveyQuestion[];
};

// One section per domain, in the order the questions arrive.
function groupByDomain(
  questions: PublicSurveyQuestion[],
): DomainSection[] {
  const sections: DomainSection[] = [];

  for (const question of questions) {
    const section = sections.find(
      (item) =>
        item.name === question.domain_name,
    );

    if (section) {
      section.questions.push(question);
    } else {
      sections.push({
        name: question.domain_name,
        questions: [question],
      });
    }
  }

  return sections;
}

function AnswerChoice({
  value,
  label,
  isSelected,
  isDisabled,
  isNotApplicable = false,
  onSelect,
}: {
  value: string;
  label: string;
  isSelected: boolean;
  isDisabled: boolean;
  isNotApplicable?: boolean;
  onSelect: () => void;
}) {
  const selectedClasses = isNotApplicable
    ? "border-slate-700 bg-slate-700 text-white"
    : "border-cyan-700 bg-cyan-700 text-white";

  return (
    <button
      type="button"
      role="radio"
      aria-checked={isSelected}
      disabled={isDisabled}
      onClick={onSelect}
      className="group flex flex-col items-center gap-1.5 disabled:cursor-wait disabled:opacity-60"
    >
      <span
        className={`flex h-12 w-full items-center justify-center rounded-lg border text-lg font-bold transition ${
          isSelected
            ? selectedClasses
            : "border-slate-300 bg-white text-slate-800 group-hover:border-cyan-600"
        }`}
      >
        {value}
      </span>

      <span
        className={`text-center text-xs leading-tight ${
          isSelected
            ? "font-semibold text-slate-900"
            : "text-slate-500"
        }`}
      >
        {label}
      </span>
    </button>
  );
}

function PublicSurveyQuestionnairePage() {
  const navigate = useNavigate();
  const { submissionToken } =
    useParams();

  const { confirm, dialog } = useConfirm();

  const [
    submission,
    setSubmission,
  ] =
    useState<SurveySubmissionDetail | null>(
      null,
    );

  const [
    currentSectionIndex,
    setCurrentSectionIndex,
  ] = useState(0);

  const [isLoading, setIsLoading] =
    useState(true);

  const [
    savingQuestionId,
    setSavingQuestionId,
  ] = useState<number | null>(null);

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState("");

  // Save errors are shown under the question they belong to.
  const [
    questionErrors,
    setQuestionErrors,
  ] = useState<Record<number, string>>({});

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

        // Resume at the first section that still needs answers.
        const firstIncompleteSection =
          groupByDomain(
            loadedSubmission.questions,
          ).findIndex((section) =>
            section.questions.some(
              (question) =>
                question.selected_response ===
                null,
            ),
          );

        if (firstIncompleteSection >= 0) {
          setCurrentSectionIndex(
            firstIncompleteSection,
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

  const sections = useMemo(
    () =>
      groupByDomain(
        submission?.questions ?? [],
      ),
    [submission],
  );

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

  // N/A is only offered to employees on situation-dependent questions;
  // the backend enforces the same rule.
  function allowsNotApplicable(
    question: PublicSurveyQuestion,
  ): boolean {
    return (
      submission?.respondent_group ===
        "Employee" &&
      question.is_situation_dependent
    );
  }

  function goToSection(index: number) {
    setErrorMessage("");
    setCurrentSectionIndex(index);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  async function handleSelectAnswer(
    question: PublicSurveyQuestion,
    responseOption: ResponseOption,
  ) {
    if (!submissionToken || !submission) {
      return;
    }

    try {
      setSavingQuestionId(
        question.question_id,
      );
      setErrorMessage("");
      setQuestionErrors((current) => {
        const next = { ...current };
        delete next[question.question_id];
        return next;
      });

      // Choosing the selected answer again clears it.
      const isDeselecting =
        question.selected_response ===
        responseOption;

      const result = isDeselecting
        ? await clearSurveyAnswer(
            submissionToken,
            question.question_id,
          )
        : await saveSurveyAnswer(
            submissionToken,
            question.question_id,
            responseOption,
          );

      setSubmission((currentSubmission) => {
        if (!currentSubmission) {
          return null;
        }

        return {
          ...currentSubmission,
          answered_question_count:
            result.answered_question_count,
          questions:
            currentSubmission.questions.map(
              (item) =>
                item.question_id ===
                question.question_id
                  ? {
                      ...item,
                      selected_response:
                        isDeselecting
                          ? null
                          : responseOption,
                    }
                  : item,
            ),
        };
      });
    } catch (error) {
      setQuestionErrors((current) => ({
        ...current,
        [question.question_id]:
          error instanceof Error
            ? error.message
            : "Unable to save this answer.",
      }));
    } finally {
      setSavingQuestionId(null);
    }
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
      const firstIncompleteSection =
        sections.findIndex((section) =>
          section.questions.some(
            (question) =>
              question.selected_response ===
              null,
          ),
        );

      if (firstIncompleteSection >= 0) {
        goToSection(firstIncompleteSection);
      }

      setErrorMessage(
        `Please answer all questions before submitting. ${submission.answered_question_count} of ${submission.total_question_count} are answered.`,
      );
      return;
    }

    const confirmed = await confirm(
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
        </section>
      </main>
    );
  }

  const currentSection =
    sections[currentSectionIndex] ?? null;

  const isLastSection =
    currentSectionIndex ===
    sections.length - 1;

  const nextSection =
    sections[currentSectionIndex + 1] ??
    null;

  // Keep the 1-5 buttons lined up when some questions in this section
  // offer N/A and others don't.
  const showNotApplicableColumn =
    currentSection?.questions.some(
      allowsNotApplicable,
    ) ?? false;

  return (
    <main className="min-h-screen bg-slate-100 px-6 py-12">
      {dialog}

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

          <ol className="mt-6 grid gap-2 sm:grid-cols-3">
            {sections.map((section, index) => {
              const answered =
                section.questions.filter(
                  (question) =>
                    question.selected_response !==
                    null,
                ).length;

              const isCurrent =
                index === currentSectionIndex;

              return (
                <li key={section.name}>
                  <button
                    type="button"
                    onClick={() =>
                      goToSection(index)
                    }
                    aria-current={
                      isCurrent
                        ? "step"
                        : undefined
                    }
                    className={`w-full rounded-lg border px-4 py-3 text-left transition ${
                      isCurrent
                        ? "border-cyan-700 bg-cyan-50"
                        : "border-slate-200 hover:border-slate-400"
                    }`}
                  >
                    <span className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Section {index + 1}
                    </span>

                    <span className="block font-semibold text-slate-900">
                      {section.name}
                    </span>

                    <span className="block text-sm text-slate-500">
                      {answered} of{" "}
                      {section.questions.length}{" "}
                      answered
                    </span>
                  </button>
                </li>
              );
            })}
          </ol>

          {errorMessage && (
            <div
              role="alert"
              className="mt-6 rounded-lg bg-red-50 p-4 text-red-700"
            >
              {errorMessage}
            </div>
          )}
        </header>

        {currentSection && (
          <section
            aria-labelledby="section-heading"
            className="mt-8 rounded-xl bg-white p-8 shadow"
          >
            <div className="flex flex-wrap items-baseline justify-between gap-3">
              <h2
                id="section-heading"
                className="text-2xl font-bold text-slate-900"
              >
                {currentSection.name}
              </h2>

              <p className="text-sm text-slate-500">
                {
                  currentSection.questions.filter(
                    (question) =>
                      question.selected_response !==
                      null,
                  ).length
                }{" "}
                of{" "}
                {currentSection.questions.length}{" "}
                answered
              </p>
            </div>

            <p className="mt-2 text-sm text-slate-600">
              For each statement, choose how
              much you agree, from 1 (strongly
              disagree) to 5 (strongly agree).
            </p>

            <ol className="mt-4 divide-y divide-slate-100">
              {currentSection.questions.map(
                (question) => {
                  const canAnswerNotApplicable =
                    allowsNotApplicable(question);

                  const isSaving =
                    savingQuestionId ===
                    question.question_id;

                  const promptId = `question-${question.question_id}`;

                  return (
                    <li
                      key={question.question_id}
                      className="py-6"
                    >
                      <p
                        id={promptId}
                        className="text-lg font-semibold leading-relaxed text-slate-900"
                      >
                        <span className="mr-2 text-slate-500">
                          {
                            question.question_number
                          }
                        </span>
                        {question.question_text}
                      </p>

                      <div
                        role="radiogroup"
                        aria-labelledby={promptId}
                        className={`mt-4 grid gap-2 ${
                          showNotApplicableColumn
                            ? "grid-cols-6"
                            : "grid-cols-5"
                        }`}
                      >
                        {showNotApplicableColumn &&
                          (canAnswerNotApplicable ? (
                            <div className="border-r border-slate-200 pr-2">
                              <AnswerChoice
                                value="N/A"
                                label="Not applicable"
                                isSelected={
                                  question.selected_response ===
                                  "N/A"
                                }
                                isDisabled={
                                  isSaving
                                }
                                isNotApplicable
                                onSelect={() =>
                                  void handleSelectAnswer(
                                    question,
                                    "N/A",
                                  )
                                }
                              />
                            </div>
                          ) : (
                            <span aria-hidden="true" />
                          ))}

                        {scaleOptions.map(
                          (scaleOption) => (
                            <AnswerChoice
                              key={
                                scaleOption.option
                              }
                              value={String(
                                scaleOption.value,
                              )}
                              label={
                                scaleOption.label
                              }
                              isSelected={
                                question.selected_response ===
                                scaleOption.option
                              }
                              isDisabled={isSaving}
                              onSelect={() =>
                                void handleSelectAnswer(
                                  question,
                                  scaleOption.option,
                                )
                              }
                            />
                          ),
                        )}
                      </div>

                      {questionErrors[
                        question.question_id
                      ] && (
                        <p
                          role="alert"
                          className="mt-3 text-sm text-red-700"
                        >
                          {
                            questionErrors[
                              question.question_id
                            ]
                          }
                        </p>
                      )}
                    </li>
                  );
                },
              )}
            </ol>

            <div className="mt-2 flex flex-wrap items-center justify-between gap-4 border-t border-slate-100 pt-6">
              <button
                type="button"
                onClick={() =>
                  goToSection(
                    currentSectionIndex - 1,
                  )
                }
                disabled={
                  currentSectionIndex === 0
                }
                className="rounded-lg border border-slate-300 px-5 py-3 font-semibold text-slate-700 disabled:opacity-40"
              >
                ← Previous section
              </button>

              {isLastSection ? (
                <button
                  type="button"
                  onClick={() =>
                    void handleSubmitSurvey()
                  }
                  disabled={isSubmitting}
                  className="rounded-lg bg-emerald-700 px-5 py-3 font-semibold text-white disabled:opacity-50"
                >
                  {isSubmitting
                    ? "Submitting..."
                    : "Submit survey"}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() =>
                    goToSection(
                      currentSectionIndex + 1,
                    )
                  }
                  className="rounded-lg bg-slate-900 px-5 py-3 font-semibold text-white"
                >
                  Next: {nextSection?.name} →
                </button>
              )}
            </div>
          </section>
        )}
      </section>
    </main>
  );
}

export default PublicSurveyQuestionnairePage;
