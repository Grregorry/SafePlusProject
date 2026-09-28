import {
  type DomainQuestionGroup,
  type Participation,
} from "./resultsHelpers";

export default function SetupPanel({
  domainQuestionGroups,
  handleSaveQuestionSelection,
  hasSelectionChanges,
  isSavingSelection,
  participation,
  selectedOptionalIds,
  selectionMessage,
  toggleOptionalQuestion,
}: {
  domainQuestionGroups: DomainQuestionGroup[];
  handleSaveQuestionSelection: () => void | Promise<void>;
  hasSelectionChanges: boolean;
  isSavingSelection: boolean;
  participation: Participation | null;
  selectedOptionalIds: number[];
  selectionMessage: string;
  toggleOptionalQuestion: (questionId: number) => void;
}) {
  return (
    <>
      <section className="mt-8 grid items-start gap-6 lg:grid-cols-[18rem_1fr]">
        <article className="rounded-xl bg-white p-6 shadow">
          <h2 className="text-xl font-bold text-slate-900">
            Participation
          </h2>

          {participation ? (
            <p className="mt-5 text-slate-700">
              <span className="text-4xl font-bold text-cyan-800">
                {
                  participation.summary
                    .submitted_total
                }
              </span>{" "}
              submitted
            </p>
          ) : (
            <p className="mt-4 text-slate-600">
              Participation details are not
              available.
            </p>
          )}
        </article>

        <article className="rounded-xl bg-white p-6 shadow">
          <h2 className="text-xl font-bold text-slate-900">
            Domains
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Required questions are always
            included. Tick any optional
            questions that apply to your
            organisation.
          </p>

          {domainQuestionGroups.length ===
          0 ? (
            <p className="mt-4 text-slate-600">
              Questions are not available.
            </p>
          ) : (
            <div className="mt-4 divide-y divide-slate-100">
              {domainQuestionGroups.map(
                (group) => {
                  const optionalCount =
                    group.questions.filter(
                      (question) =>
                        question.is_situation_dependent,
                    ).length;

                  const includedCount =
                    group.questions.filter(
                      (question) =>
                        question.is_compulsory ||
                        selectedOptionalIds.includes(
                          question.question_id,
                        ),
                    ).length;

                  return (
                    <details
                      key={group.name}
                      className="group py-3"
                    >
                      <summary className="flex cursor-pointer list-none items-center justify-between gap-4 rounded-md py-1 [&::-webkit-details-marker]:hidden">
                        <span className="font-semibold text-slate-900">
                          {group.name}
                        </span>

                        <span className="flex items-center gap-2 text-sm text-slate-500">
                          {includedCount}{" "}
                          included
                          {optionalCount > 0
                            ? ` · ${optionalCount} optional`
                            : ""}

                          <svg
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth={2}
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            aria-hidden="true"
                            className="h-4 w-4 transition-transform group-open:rotate-90"
                          >
                            <polyline points="9 6 15 12 9 18" />
                          </svg>
                        </span>
                      </summary>

                      <ul className="mt-3 space-y-2">
                        {group.questions.map(
                          (question) => (
                            <li
                              key={
                                question.question_id
                              }
                            >
                              {question.is_situation_dependent ? (
                                <label className="flex cursor-pointer gap-3 rounded-lg border border-slate-200 p-3 hover:bg-slate-50">
                                  <input
                                    type="checkbox"
                                    checked={selectedOptionalIds.includes(
                                      question.question_id,
                                    )}
                                    onChange={() =>
                                      toggleOptionalQuestion(
                                        question.question_id,
                                      )
                                    }
                                    className="mt-1 h-4 w-4 shrink-0 accent-cyan-700"
                                  />

                                  <span>
                                    <span className="text-sm font-semibold text-slate-900">
                                      {
                                        question.question_number
                                      }
                                    </span>{" "}
                                    <span className="ml-1 rounded-full bg-cyan-50 px-2 py-0.5 text-xs font-semibold text-cyan-900 ring-1 ring-inset ring-cyan-200">
                                      Optional
                                    </span>

                                    <span className="mt-1 block text-sm text-slate-600">
                                      {
                                        question.employee_text
                                      }
                                    </span>
                                  </span>
                                </label>
                              ) : (
                                <div className="flex gap-3 rounded-lg bg-slate-50 p-3">
                                  <input
                                    type="checkbox"
                                    checked
                                    disabled
                                    aria-label={`Question ${question.question_number} is required and always included`}
                                    className="mt-1 h-4 w-4 shrink-0 accent-cyan-700"
                                  />

                                  <span>
                                    <span className="text-sm font-semibold text-slate-900">
                                      {
                                        question.question_number
                                      }
                                    </span>{" "}
                                    <span className="ml-1 text-xs font-semibold text-slate-500">
                                      Required
                                    </span>

                                    <span className="mt-1 block text-sm text-slate-600">
                                      {
                                        question.employee_text
                                      }
                                    </span>
                                  </span>
                                </div>
                              )}
                            </li>
                          ),
                        )}
                      </ul>
                    </details>
                  );
                },
              )}
            </div>
          )}

          {participation && (
            <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-slate-100 pt-4">
              <button
                type="button"
                onClick={() =>
                  void handleSaveQuestionSelection()
                }
                disabled={
                  !hasSelectionChanges ||
                  isSavingSelection
                }
                className="rounded-lg bg-cyan-700 px-5 py-2.5 font-semibold text-white hover:bg-cyan-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isSavingSelection
                  ? "Saving..."
                  : "Save selection"}
              </button>

              <p
                role="status"
                className="text-sm text-slate-600"
              >
                {selectionMessage ||
                  (hasSelectionChanges
                    ? "You have unsaved changes."
                    : "")}
              </p>
            </div>
          )}
        </article>
      </section>

      <section className="mt-8 rounded-xl border-l-4 border-slate-900 bg-white p-8 shadow">
        <h2 className="text-xl font-bold text-slate-900">
          Results are locked until the
          assessment is completed
        </h2>

        <p className="mt-3 max-w-3xl text-slate-600">
          No scores, partial results or AI
          suggestions are shown while
          responses are still coming in.
          With a small group, a score that
          changes as each response arrives
          can reveal how the most recent
          person answered, even without
          their name.
        </p>

        <p className="mt-3 max-w-3xl text-slate-600">
          Everything unlocks together when
          you complete the assessment.
        </p>
      </section>
    </>
  );
}
