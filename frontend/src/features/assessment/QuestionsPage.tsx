import { useEffect, useMemo, useState } from "react";

import {
  getQuestionDomains,
  type QuestionDomain,
} from "../../api/questionsApi";

type Audience = "employee" | "manager";

function QuestionsPage() {
  const [domains, setDomains] = useState<QuestionDomain[]>([]);
  const [audience, setAudience] = useState<Audience>("employee");
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    async function loadQuestions() {
      try {
        setIsLoading(true);
        setErrorMessage("");

        const questionDomains = await getQuestionDomains();
        setDomains(questionDomains);
      } catch (error) {
        console.error(error);
        setErrorMessage(
          "The questions could not be loaded. Check that the backend is running.",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadQuestions();
  }, []);

  const totalQuestions = useMemo(
    () =>
      domains.reduce(
        (total, domain) => total + domain.questions.length,
        0,
      ),
    [domains],
  );

  if (isLoading) {
    return (
      <main>
        <p className="text-slate-700">Loading SafePlus questions...</p>
      </main>
    );
  }

  if (errorMessage) {
    return (
      <main>
        <section className="mx-auto max-w-4xl rounded-lg bg-white p-6 shadow">
          <h1 className="text-2xl font-bold text-red-700">
            Unable to load questions
          </h1>

          <p className="mt-3 text-slate-700">{errorMessage}</p>
        </section>
      </main>
    );
  }

  return (
    <main>
      <section>
        <header className="rounded-xl bg-white p-8 shadow">
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
            SafePlus Tool
          </p>

          <h1 className="mt-2 text-4xl font-bold text-slate-900">
            Assessment Questions
          </h1>

          <p className="mt-3 text-slate-600">
            Questions loaded from PostgreSQL through the FastAPI backend.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-4">
            <button
              type="button"
              onClick={() => setAudience("employee")}
              className={`rounded-lg px-4 py-2 font-medium ${
                audience === "employee"
                  ? "bg-cyan-700 text-white"
                  : "bg-slate-200 text-slate-800"
              }`}
            >
              Employee wording
            </button>

            <button
              type="button"
              onClick={() => setAudience("manager")}
              className={`rounded-lg px-4 py-2 font-medium ${
                audience === "manager"
                  ? "bg-cyan-700 text-white"
                  : "bg-slate-200 text-slate-800"
              }`}
            >
              Senior Manager wording
            </button>

            <span className="text-sm text-slate-600">
              {domains.length} domains · {totalQuestions} questions
            </span>
          </div>
        </header>

        <div className="mt-8 space-y-8">
          {domains.map((domain) => (
            <section
              key={domain.id}
              className="rounded-xl bg-white p-8 shadow"
            >
              <div className="border-b border-slate-200 pb-4">
                <p className="text-sm font-medium text-cyan-700">
                  Domain {domain.display_order}
                </p>

                <h2 className="text-2xl font-bold text-slate-900">
                  {domain.name}
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  {domain.questions.length} questions
                </p>
              </div>

              <div className="mt-6 space-y-5">
                {domain.questions.map((question) => (
                  <article
                    key={question.id}
                    className="rounded-lg border border-slate-200 p-5"
                  >
                    <div className="flex flex-wrap items-center gap-3">
                      <span className="font-bold text-slate-900">
                        {question.question_number}
                      </span>

                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${
                          question.is_compulsory
                            ? "bg-emerald-100 text-emerald-800"
                            : "bg-amber-100 text-amber-800"
                        }`}
                      >
                        {question.is_compulsory
                          ? "Compulsory"
                          : "Situation-dependent"}
                      </span>
                    </div>

                    <p className="mt-4 text-slate-700">
                      {audience === "employee"
                        ? question.employee_text
                        : question.manager_text}
                    </p>

                    <div className="mt-5 grid grid-cols-5 gap-2">
                      {[1, 2, 3, 4, 5].map((rating) => (
                        <button
                          key={rating}
                          type="button"
                          className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
                        >
                          {rating}
                        </button>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>
      </section>
    </main>
  );
}

export default QuestionsPage;