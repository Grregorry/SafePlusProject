import {
  useEffect,
  useState,
} from "react";
import {
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  createSurveySubmission,
  getPublicSurvey,
  type PublicSurveyOverview,
  type RespondentGroup,
} from "../../api/publicSurveyApi";

function PublicSurveyStartPage() {
  const navigate = useNavigate();
  const { publicCode } = useParams();

  const [survey, setSurvey] =
    useState<PublicSurveyOverview | null>(
      null,
    );

  const [
    respondentGroup,
    setRespondentGroup,
  ] = useState<RespondentGroup>(
    "Employee",
  );

  const [isLoading, setIsLoading] =
    useState(true);

  const [isStarting, setIsStarting] =
    useState(false);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState("");

  useEffect(() => {
    async function loadSurvey() {
      if (!publicCode) {
        setErrorMessage(
          "Survey code is missing.",
        );
        setIsLoading(false);
        return;
      }

      try {
        setErrorMessage("");

        const loadedSurvey =
          await getPublicSurvey(
            publicCode,
          );

        setSurvey(loadedSurvey);
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

    void loadSurvey();
  }, [publicCode]);

  async function handleStartSurvey() {
    if (!publicCode) {
      setErrorMessage(
        "Survey code is missing.",
      );
      return;
    }

    try {
      setIsStarting(true);
      setErrorMessage("");

      const submission =
        await createSurveySubmission(
          publicCode,
          respondentGroup,
        );

      navigate(
        `/survey/submission/${submission.submission_token}`,
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to start the survey.",
      );
    } finally {
      setIsStarting(false);
    }
  }

  if (isLoading) {
    return (
      <main className="min-h-screen bg-slate-100 p-8">
        <p className="text-slate-700">
          Loading survey...
        </p>
      </main>
    );
  }

  if (!survey) {
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

  return (
    <main className="min-h-screen bg-slate-100 px-6 py-12">
      <section className="mx-auto max-w-3xl">
        <header className="rounded-xl bg-white p-8 shadow">
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
            SafePlus survey
          </p>

          <h1 className="mt-2 text-3xl font-bold text-slate-900">
            {survey.organisation_name}
          </h1>

          <p className="mt-3 text-slate-600">
            This assessment contains{" "}
            {survey.active_question_count}{" "}
            questions. Choose the respondent
            group that applies to you before
            beginning.
          </p>

          <div className="mt-8">
            <p className="text-sm font-semibold text-slate-700">
              Respondent group
            </p>

            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              <button
                type="button"
                onClick={() =>
                  setRespondentGroup(
                    "Employee",
                  )
                }
                className={`rounded-xl border p-6 text-left ${
                  respondentGroup ===
                  "Employee"
                    ? "border-cyan-700 bg-cyan-50"
                    : "border-slate-200 bg-white"
                }`}
              >
                <span className="block text-lg font-bold text-slate-900">
                  Employee
                </span>

                <span className="mt-2 block text-sm text-slate-600">
                  Select this option if you
                  are responding as an
                  employee or worker.
                </span>
              </button>

              <button
                type="button"
                onClick={() =>
                  setRespondentGroup(
                    "Senior Manager",
                  )
                }
                className={`rounded-xl border p-6 text-left ${
                  respondentGroup ===
                  "Senior Manager"
                    ? "border-cyan-700 bg-cyan-50"
                    : "border-slate-200 bg-white"
                }`}
              >
                <span className="block text-lg font-bold text-slate-900">
                  Senior Manager
                </span>

                <span className="mt-2 block text-sm text-slate-600">
                  Select this option if you
                  are responding as a senior
                  manager.
                </span>
              </button>
            </div>
          </div>

          {errorMessage && (
            <div className="mt-6 rounded-lg bg-red-50 p-4 text-red-700">
              {errorMessage}
            </div>
          )}

          <button
            type="button"
            onClick={handleStartSurvey}
            disabled={isStarting}
            className="mt-8 rounded-lg bg-cyan-700 px-6 py-3 font-semibold text-white disabled:opacity-60"
          >
            {isStarting
              ? "Starting survey..."
              : "Begin survey"}
          </button>
        </header>
      </section>
    </main>
  );
}

export default PublicSurveyStartPage;