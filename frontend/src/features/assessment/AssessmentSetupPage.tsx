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
  getAssessmentQuestions,
  getSurveyAccess,
  updateQuestionSelection,
  type AssessmentSetupQuestion,
  type SurveyAccess,
} from "../../api/assessmentsApi";

function AssessmentSetupPage() {
  const navigate = useNavigate();
  const { assessmentId } = useParams();

  const numericAssessmentId = Number(
    assessmentId,
  );

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
          loadedQuestions,
          loadedSurveyAccess,
        ] = await Promise.all([
          getAssessmentQuestions(
            numericAssessmentId,
            accessToken,
          ),
          getSurveyAccess(
            numericAssessmentId,
            accessToken,
          ),
        ]);

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

  function handleEnterResponses() {
    navigate(
      `/assessments/${numericAssessmentId}/responses`,
    );
  }

  if (isLoading) {
    return (
      <main className="min-h-screen bg-slate-100 p-8">
        <p className="text-slate-700">
          Loading assessment...
        </p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-100 px-6 py-12">
      <section className="mx-auto max-w-4xl">
        <header className="rounded-xl bg-white p-8 shadow">
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
            Assessment #
            {numericAssessmentId}
          </p>

          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            Select applicable risks
          </h1>

          <p className="mt-3 text-slate-600">
            All compulsory questions are
            included automatically. Select any
            additional situation-dependent risks
            that apply to your organisation.
          </p>

          <p className="mt-4 text-sm text-slate-500">
            {compulsoryQuestionCount} compulsory
            questions •{" "}
            {selectedQuestionIds.length}{" "}
            additional questions selected
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

        <section className="mt-8 rounded-xl bg-white p-8 shadow">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
                Respondent survey
              </p>

              <h2 className="mt-2 text-2xl font-bold text-slate-900">
                Share survey link
              </h2>

              <p className="mt-2 text-slate-600">
                Send this link to employees and
                senior managers who need to
                complete the assessment.
              </p>
            </div>

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
          {situationQuestions.length === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center">
              <p className="text-slate-700">
                No situation-dependent
                questions are available.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
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
                      disabled={isSurveyClosed}
                      className="mt-1 h-5 w-5"
                    />

                    <span>
                      <span className="font-semibold text-slate-900">
                        {
                          question.question_number
                        }{" "}
                        • {question.domain_name}
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

          <div className="mt-8 flex flex-wrap gap-4">
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

            <button
              type="button"
              onClick={
                handleEnterResponses
              }
              className="rounded-lg bg-slate-900 px-5 py-3 font-semibold text-white"
            >
              View responses
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
        </section>
      </section>
    </main>
  );
}

export default AssessmentSetupPage;