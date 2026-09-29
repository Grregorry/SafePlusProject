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
  completeAssessment,
  deleteAssessment,
  getAssessment,
  getAssessmentQuestions,
  getSurveyAccess,
  updateQuestionSelection,
  type Assessment,
  type AssessmentSetupQuestion,
  type SurveyAccess,
} from "../../api/assessmentsApi";

import { useConfirm } from "../../components/useConfirm";
import {
  MINIMUM_RESPONSES,
  completeConfirmMessage,
  deleteConfirmMessage,
  fetchEntryTotals,
  tooFewResponsesMessage,
  type EntryTotals,
} from "./assessmentCompletion";
import SubmissionManagementPanel from "./SubmissionManagementPanel";

type SetupTab =
  | "sessions"
  | "questions";

const setupTabs: {
  id: SetupTab;
  label: string;
}[] = [
  {
    id: "sessions",
    label: "Survey sessions",
  },
  {
    id: "questions",
    label:
      "Additional situation-dependent questions",
  },
];

function AssessmentSetupPage() {
  const navigate = useNavigate();
  const { assessmentId } = useParams();

  const numericAssessmentId = Number(
    assessmentId,
  );

  const { choose, confirm, dialog } =
    useConfirm();

  const [isCompleting, setIsCompleting] =
    useState(false);

  const [assessment, setAssessment] =
    useState<Assessment | null>(null);

  const [activeTab, setActiveTab] =
    useState<SetupTab>("sessions");

  const [questions, setQuestions] =
    useState<AssessmentSetupQuestion[]>([]);

  const [
    selectedQuestionIds,
    setSelectedQuestionIds,
  ] = useState<number[]>([]);

  const [surveyAccess, setSurveyAccess] =
    useState<SurveyAccess | null>(null);

  const [isLoading, setIsLoading] =
    useState(true);

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

  useEffect(() => {
    async function loadAssessment() {
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
        setIsLoading(false);
        return;
      }

      try {
        setErrorMessage("");

        const [
          loadedAssessment,
          loadedQuestions,
          loadedSurveyAccess,
        ] = await Promise.all([
          getAssessment(
            numericAssessmentId,
            accessToken,
          ),
          getAssessmentQuestions(
            numericAssessmentId,
            accessToken,
          ),
          getSurveyAccess(
            numericAssessmentId,
            accessToken,
          ),
        ]);

        // Closed assessments have nothing left to set up; show their
        // results instead.
        if (
          loadedAssessment.status ===
          "completed"
        ) {
          navigate(
            `/assessments/${numericAssessmentId}/results`,
            { replace: true },
          );
          return;
        }

        setAssessment(loadedAssessment);
        setQuestions(loadedQuestions);
        setSurveyAccess(
          loadedSurveyAccess,
        );

        setSelectedQuestionIds(
          loadedQuestions
            .filter(
              (question) =>
                question.is_situation_dependent &&
                question.is_active,
            )
            .map(
              (question) =>
                question.question_id,
            ),
        );
      } catch (error) {
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Unable to load this assessment.",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadAssessment();
  }, [
    navigate,
    numericAssessmentId,
  ]);

  const situationQuestions =
    useMemo(
      () =>
        questions.filter(
          (question) =>
            question.is_situation_dependent,
        ),
      [questions],
    );

  const compulsoryQuestionCount =
    useMemo(
      () =>
        questions.filter(
          (question) =>
            question.is_compulsory,
        ).length,
      [questions],
    );

  const publicSurveyUrl = useMemo(
    () => {
      if (!surveyAccess) {
        return "";
      }

      return `${window.location.origin}${surveyAccess.public_path}`;
    },
    [surveyAccess],
  );

  const isSurveyClosed =
    surveyAccess?.status === "completed";

  function toggleQuestion(
    questionId: number,
  ) {
    setSuccessMessage("");

    setSelectedQuestionIds(
      (currentIds) =>
        currentIds.includes(questionId)
          ? currentIds.filter(
              (id) => id !== questionId,
            )
          : [
              ...currentIds,
              questionId,
            ],
    );
  }

  async function handleSave() {
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
      setIsSaving(true);
      setErrorMessage("");
      setSuccessMessage("");

      const updatedQuestions =
        await updateQuestionSelection(
          numericAssessmentId,
          selectedQuestionIds,
          accessToken,
        );

      setQuestions(updatedQuestions);

      setSelectedQuestionIds(
        updatedQuestions
          .filter(
            (question) =>
              question.is_situation_dependent &&
              question.is_active,
          )
          .map(
            (question) =>
              question.question_id,
          ),
      );

      setSuccessMessage(
        "Question selection saved successfully.",
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to save question selection.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleCopySurveyLink() {
    if (!publicSurveyUrl) {
      setErrorMessage(
        "Survey link is unavailable.",
      );
      return;
    }

    try {
      await navigator.clipboard.writeText(
        publicSurveyUrl,
      );

      setErrorMessage("");
      setSuccessMessage(
        "Survey link copied to clipboard.",
      );
    } catch {
      setErrorMessage(
        "Unable to copy automatically. Select and copy the link manually.",
      );
    }
  }

  function handleOpenSurvey() {
    if (!publicSurveyUrl) {
      return;
    }

    window.open(
      publicSurveyUrl,
      "_blank",
      "noopener,noreferrer",
    );
  }

  // Same checks as the in-progress assessment page: at least
  // MINIMUM_RESPONSES responses, with the option to delete instead.
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

    let totals: EntryTotals;

    try {
      setErrorMessage("");
      setSuccessMessage("");

      totals = await fetchEntryTotals(
        numericAssessmentId,
        accessToken,
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to check how many responses this assessment has.",
      );
      return;
    }

    if (
      totals.online + totals.paper <
      MINIMUM_RESPONSES
    ) {
      const choice = await choose(
        tooFewResponsesMessage(totals),
        {
          confirmLabel: "OK",
          showCancel: false,
          extraLabel: "Delete assessment",
        },
      );

      if (choice !== "extra") {
        return;
      }

      const confirmedDelete = await confirm(
        deleteConfirmMessage(
          assessment?.name,
        ),
        {
          confirmLabel: "Delete",
        },
      );

      if (!confirmedDelete) {
        return;
      }

      try {
        await deleteAssessment(
          numericAssessmentId,
          accessToken,
        );

        navigate("/account", {
          replace: true,
        });
      } catch (error) {
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Unable to delete the assessment.",
        );
      }

      return;
    }

    const confirmed = await confirm(
      completeConfirmMessage(totals),
    );

    if (!confirmed) {
      return;
    }

    try {
      setIsCompleting(true);

      await completeAssessment(
        numericAssessmentId,
        accessToken,
      );

      navigate(
        `/assessments/${numericAssessmentId}/results`,
        { replace: true },
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

  if (isLoading) {
    return (
      <main>
        <p className="text-slate-700">
          Loading assessment...
        </p>
      </main>
    );
  }

  return (
    <main>
      {dialog}

      <section>
        <header className="rounded-xl bg-white p-8 shadow">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
                {assessment?.name ??
                  "Assessment overview"}
              </p>

              <h1 className="mt-2 text-3xl font-bold text-slate-900">
                Assessment overview
              </h1>
            </div>

            <button
              type="button"
              onClick={() =>
                void handleCompleteAssessment()
              }
              disabled={isCompleting}
              className="rounded-lg border border-cyan-700 bg-white px-5 py-3 font-semibold text-cyan-800 hover:bg-cyan-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isCompleting
                ? "Completing assessment..."
                : "Complete assessment"}
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
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
            Respondent survey
          </p>

          <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-2xl font-bold text-slate-900">
              Share survey link
            </h2>

            {surveyAccess && (
              <span
                className={`rounded-full px-3 py-1 text-sm font-semibold ${
                  isSurveyClosed
                    ? "bg-slate-200 text-slate-700"
                    : "bg-emerald-100 text-emerald-700"
                }`}
              >
                {isSurveyClosed
                  ? "Survey closed"
                  : "Survey open"}
              </span>
            )}
          </div>

          <p className="mt-2 text-slate-600">
            We recommend distributing this link
            by email to employees and senior
            managers. Anyone with the link can
            respond, so only share it with
            intended participants.
          </p>

          {surveyAccess && (
            <div className="mt-6">
              <label
                htmlFor="public-survey-url"
                className="text-sm font-semibold text-slate-700"
              >
                Public survey URL
              </label>

              <input
                id="public-survey-url"
                type="text"
                value={publicSurveyUrl}
                readOnly
                onFocus={(event) =>
                  event.currentTarget.select()
                }
                className="mt-2 w-full rounded-lg border border-slate-300 bg-slate-50 px-4 py-3 text-slate-800"
              />

              <p className="mt-2 text-sm text-slate-500">
                Survey code:{" "}
                {surveyAccess.public_code}
              </p>

              <div className="mt-5 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={
                    handleCopySurveyLink
                  }
                  disabled={isSurveyClosed}
                  className="rounded-lg bg-cyan-700 px-5 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Copy survey link
                </button>

                <button
                  type="button"
                  onClick={handleOpenSurvey}
                  className="rounded-lg border border-slate-300 px-5 py-3 font-semibold text-slate-700"
                >
                  Open survey
                </button>
              </div>
            </div>
          )}
        </section>

        <section className="mt-8 rounded-xl bg-white p-8 shadow">
          <div
            role="tablist"
            className="flex flex-wrap gap-3"
          >
            {setupTabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={
                  activeTab === tab.id
                }
                onClick={() =>
                  setActiveTab(tab.id)
                }
                className={`rounded-full px-6 py-3 text-base font-semibold transition ${
                  activeTab === tab.id
                    ? "bg-cyan-700 text-white shadow-md scale-105"
                    : "border-2 border-slate-300 text-slate-700 hover:border-slate-400 hover:bg-slate-50"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="mt-8">
            {activeTab === "sessions" && (
              <SubmissionManagementPanel
                assessmentId={
                  numericAssessmentId
                }
              />
            )}

            {activeTab === "questions" && (
              <div>
                <p className="text-slate-600">
                  All compulsory questions are
                  included automatically.
                  Select any additional
                  situation-dependent risks
                  that apply to your
                  organisation.
                </p>

                <p className="mt-2 text-sm text-slate-500">
                  {compulsoryQuestionCount}{" "}
                  compulsory questions •{" "}
                  {selectedQuestionIds.length}{" "}
                  additional questions selected
                </p>

                {situationQuestions.length ===
                0 ? (
                  <div className="mt-6 rounded-lg border border-dashed border-slate-300 p-8 text-center">
                    <p className="text-slate-700">
                      No situation-dependent
                      questions are available.
                    </p>
                  </div>
                ) : (
                  <div className="mt-6 space-y-4">
                    {situationQuestions.map(
                      (question) => (
                        <label
                          key={
                            question.question_id
                          }
                          className="flex cursor-pointer gap-4 rounded-lg border border-slate-200 p-5"
                        >
                          <input
                            type="checkbox"
                            checked={selectedQuestionIds.includes(
                              question.question_id,
                            )}
                            onChange={() =>
                              toggleQuestion(
                                question.question_id,
                              )
                            }
                            disabled={
                              isSurveyClosed
                            }
                            className="mt-1 h-5 w-5"
                          />

                          <span>
                            <span className="font-semibold text-slate-900">
                              {
                                question.question_number
                              }{" "}
                              •{" "}
                              {
                                question.domain_name
                              }
                            </span>

                            <span className="mt-2 block text-slate-600">
                              {
                                question.employee_text
                              }
                            </span>
                          </span>
                        </label>
                      ),
                    )}
                  </div>
                )}

                <div className="mt-8">
                  <button
                    type="button"
                    onClick={handleSave}
                    disabled={
                      isSaving ||
                      isSurveyClosed
                    }
                    className="rounded-lg bg-cyan-700 px-5 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isSaving
                      ? "Saving..."
                      : "Save selection"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>

      </section>
    </main>
  );
}

export default AssessmentSetupPage;