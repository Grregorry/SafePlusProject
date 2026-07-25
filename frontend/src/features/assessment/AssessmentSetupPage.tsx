import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  getAssessmentQuestions,
  updateQuestionSelection,
  type AssessmentSetupQuestion,
} from "../../api/assessmentsApi";

function AssessmentSetupPage() {
  const navigate = useNavigate();
  const { assessmentId } = useParams();

  const [questions, setQuestions] = useState<
    AssessmentSetupQuestion[]
  >([]);

  const [selectedQuestionIds, setSelectedQuestionIds] =
    useState<number[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const numericAssessmentId = Number(assessmentId);

  useEffect(() => {
    async function loadQuestions() {
      const accessToken = localStorage.getItem(
        "safeplus_access_token",
      );

      if (!accessToken) {
        navigate("/login", {
          replace: true,
        });
        return;
      }

      if (!Number.isInteger(numericAssessmentId)) {
        setErrorMessage("Invalid assessment ID.");
        setIsLoading(false);
        return;
      }

      try {
        setErrorMessage("");

        const loadedQuestions = await getAssessmentQuestions(
          numericAssessmentId,
          accessToken,
        );

        setQuestions(loadedQuestions);

        setSelectedQuestionIds(
          loadedQuestions
            .filter(
              (question) =>
                question.is_situation_dependent &&
                question.is_active,
            )
            .map((question) => question.question_id),
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

    void loadQuestions();
  }, [navigate, numericAssessmentId]);

  const situationQuestions = useMemo(
    () =>
      questions.filter(
        (question) => question.is_situation_dependent,
      ),
    [questions],
  );

  const compulsoryQuestionCount = useMemo(
    () =>
      questions.filter(
        (question) => question.is_compulsory,
      ).length,
    [questions],
  );

  function toggleQuestion(questionId: number) {
    setSuccessMessage("");

    setSelectedQuestionIds((currentIds) =>
      currentIds.includes(questionId)
        ? currentIds.filter((id) => id !== questionId)
        : [...currentIds, questionId],
    );
  }

  async function handleSave() {
    const accessToken = localStorage.getItem(
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

      const updatedQuestions = await updateQuestionSelection(
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
          .map((question) => question.question_id),
      );

      setSuccessMessage("Question selection saved successfully.");
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

  if (isLoading) {
    return (
      <main className="min-h-screen bg-slate-100 p-8">
        <p className="text-slate-700">Loading assessment...</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-100 px-6 py-12">
      <section className="mx-auto max-w-4xl">
        <header className="rounded-xl bg-white p-8 shadow">
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
            Assessment #{numericAssessmentId}
          </p>

          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            Select applicable risks
          </h1>

          <p className="mt-3 text-slate-600">
            All compulsory questions are included automatically.
            Select any additional situation-dependent risks that apply
            to your organisation.
          </p>

          <p className="mt-4 text-sm text-slate-500">
            {compulsoryQuestionCount} compulsory questions ·{" "}
            {selectedQuestionIds.length} additional questions selected
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
          <div className="space-y-4">
            {situationQuestions.map((question) => (
              <label
                key={question.question_id}
                className="flex cursor-pointer gap-4 rounded-lg border border-slate-200 p-5"
              >
                <input
                  type="checkbox"
                  checked={selectedQuestionIds.includes(
                    question.question_id,
                  )}
                  onChange={() =>
                    toggleQuestion(question.question_id)
                  }
                  className="mt-1 h-5 w-5"
                />

                <span>
                  <span className="font-semibold text-slate-900">
                    {question.question_number} ·{" "}
                    {question.domain_name}
                  </span>

                  <span className="mt-2 block text-slate-600">
                    {question.employee_text}
                  </span>
                </span>
              </label>
            ))}
          </div>

          <div className="mt-8 flex flex-wrap gap-4">
            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving}
              className="rounded-lg bg-cyan-700 px-5 py-3 font-semibold text-white disabled:opacity-60"
            >
              {isSaving ? "Saving..." : "Save selection"}
            </button>

            <button
              type="button"
              onClick={() => navigate("/account")}
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