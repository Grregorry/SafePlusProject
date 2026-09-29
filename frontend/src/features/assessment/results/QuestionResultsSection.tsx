import {
  type Dispatch,
  type SetStateAction,
} from "react";
import {
  type AssessmentScoringResult,
  type QuestionScoreResult,
} from "../../../api/assessmentsApi";
import {
  getDomainName,
  LOWEST_COLOUR,
} from "../../../components/maturity";
import {
  type DomainWorking,
  formatScore,
  getInterventionClasses,
  getQuestionStatusLabel,
  getTierRationale,
  isHighOverride,
  type QuestionResultFilter,
} from "./resultsHelpers";

export default function QuestionResultsSection({
  domainWorkings,
  filteredQuestionScores,
  lowestQuestionIds,
  overallScore,
  questionResultFilter,
  results,
  setQuestionResultFilter,
}: {
  domainWorkings: DomainWorking[];
  filteredQuestionScores: QuestionScoreResult[];
  lowestQuestionIds: Set<number>;
  overallScore: number | null;
  questionResultFilter: QuestionResultFilter;
  results: AssessmentScoringResult;
  setQuestionResultFilter: Dispatch<SetStateAction<QuestionResultFilter>>;
}) {
  return (
    <section className="mt-8 rounded-xl bg-white p-8 shadow">
      <h2 className="text-2xl font-bold text-slate-900">
        Question results
      </h2>

      <p className="mt-2 max-w-3xl text-slate-600">
        Each question&rsquo;s Employee and
        Senior Manager scores, side by
        side. Hover over a tier to see why
        it was given. &ldquo;Hidden&rdquo;
        means the two groups differ by 3.00
        or more, so an average would mask
        their opposing views.
      </p>

      <details className="mt-6 rounded-lg border border-slate-200 bg-slate-50 p-5">
        <summary className="cursor-pointer font-semibold text-slate-900">
          How scores and tiers are calculated
        </summary>

        <div className="mt-4 space-y-6 text-sm text-slate-700">
          {domainWorkings.length > 0 && (
            <div>
              <p className="font-semibold text-slate-900">
                Worked example from this
                assessment
              </p>

              <p className="mt-1 text-slate-600">
                A domain score is the
                average of the combined
                means of its scored
                questions. The overall
                score is the average of the
                three domain scores. Each
                step is rounded to two
                decimals.
              </p>

              <ul className="mt-3 space-y-2 tabular-nums">
                {domainWorkings.map(
                  (working) => (
                    <li
                      key={working.domainId}
                      className="rounded-md bg-cyan-50 px-3 py-2"
                    >
                      {getDomainName(
                        working.domainId,
                      )}
                      :{" "}
                      {working.total.toFixed(
                        2,
                      )}{" "}
                      ÷ {working.count}{" "}
                      {working.count === 1
                        ? "question"
                        : "questions"}{" "}
                      ={" "}
                      {working.mean.toFixed(
                        2,
                      )}
                    </li>
                  ),
                )}

                {overallScore !== null && (
                  <li className="rounded-md bg-cyan-50 px-3 py-2">
                    Overall: (
                    {domainWorkings
                      .map((working) =>
                        working.mean.toFixed(
                          2,
                        ),
                      )
                      .join(" + ")}
                    ) ÷{" "}
                    {domainWorkings.length}{" "}
                    ={" "}
                    {overallScore.toFixed(2)}
                  </li>
                )}
              </ul>
            </div>
          )}

          <div>
            <p className="font-semibold text-slate-900">
              Response encoding
            </p>

            <p className="mt-1 text-slate-600">
              Every response is converted
              to a number before any score
              is calculated. N/A responses
              (situation-dependent
              questions only) are excluded
              from both the numerator and
              denominator.
            </p>

            <table className="mt-3 w-full text-left">
              <thead>
                <tr className="border-b border-slate-300">
                  <th className="py-1 pr-4 font-semibold">
                    Response
                  </th>
                  <th className="py-1 font-semibold">
                    Score
                  </th>
                </tr>
              </thead>

              <tbody>
                <tr>
                  <td className="py-1 pr-4">
                    Strongly Agree
                  </td>
                  <td>5</td>
                </tr>
                <tr>
                  <td className="py-1 pr-4">
                    Agree
                  </td>
                  <td>4</td>
                </tr>
                <tr>
                  <td className="py-1 pr-4">
                    Neither Agree nor
                    Disagree
                  </td>
                  <td>3</td>
                </tr>
                <tr>
                  <td className="py-1 pr-4">
                    Disagree
                  </td>
                  <td>2</td>
                </tr>
                <tr>
                  <td className="py-1 pr-4">
                    Strongly Disagree
                  </td>
                  <td>1</td>
                </tr>
                <tr>
                  <td className="py-1 pr-4">
                    N/A
                  </td>
                  <td>Excluded</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div>
            <p className="font-semibold text-slate-900">
              Maturity thresholds
            </p>

            <p className="mt-1 text-slate-600">
              Applied to the Combined mean
              score — the average of the
              Employee mean and the Senior
              Manager mean.
            </p>

            <table className="mt-3 w-full text-left">
              <thead>
                <tr className="border-b border-slate-300">
                  <th className="py-1 pr-4 font-semibold">
                    Maturity level
                  </th>
                  <th className="py-1 pr-4 font-semibold">
                    Combined mean score
                  </th>
                  <th className="py-1 font-semibold">
                    Meaning
                  </th>
                </tr>
              </thead>

              <tbody>
                <tr>
                  <td className="py-1 pr-4">
                    Developing
                  </td>
                  <td className="py-1 pr-4">
                    ≤ 2.50
                  </td>
                  <td className="py-1">
                    Not yet performing
                    well in this area.
                    Action is needed.
                  </td>
                </tr>
                <tr>
                  <td className="py-1 pr-4">
                    Performing
                  </td>
                  <td className="py-1 pr-4">
                    &gt; 2.50 and &lt; 4.50
                  </td>
                  <td className="py-1">
                    Performing adequately.
                    Improvement is
                    possible.
                  </td>
                </tr>
                <tr>
                  <td className="py-1 pr-4">
                    Leading
                  </td>
                  <td className="py-1 pr-4">
                    ≥ 4.50
                  </td>
                  <td className="py-1">
                    Performing at a high
                    level in this area.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div>
            <p className="font-semibold text-slate-900">
              Opinion gap
            </p>

            <p className="mt-1 text-slate-600">
              The absolute difference
              between the Employee mean
              and the Senior Manager mean
              for a question — how
              differently the two groups
              perceive the same practice.
              A higher gap is not
              automatically a problem, but
              it is a signal worth
              investigating.
            </p>
          </div>

          <div>
            <p className="font-semibold text-slate-900">
              Intervention tier
            </p>

            {/* Rows follow get_intervention_tier in
                backend/app/services/scoring.py. */}
            <table className="mt-3 w-full text-left">
              <thead>
                <tr className="border-b border-slate-300">
                  <th className="py-1 pr-4 font-semibold">
                    Tier
                  </th>
                  <th className="py-1 pr-4 font-semibold">
                    Combined mean score
                  </th>
                  <th className="py-1 font-semibold">
                    Opinion gap
                  </th>
                </tr>
              </thead>

              <tbody>
                {/* One row per tier; each "or" line in the
                    score column pairs with the same line in the
                    gap column. */}
                {(
                  [
                    ["High Override", [["Any score", "≥ 3.00"]]],
                    ["High", [["≤ 2.50", "> 1.50 and < 3.00"]]],
                    [
                      "Medium",
                      [
                        ["≤ 2.50", "≤ 1.50"],
                        ["> 2.50 and ≤ 3.50", "> 1.50 and < 3.00"],
                      ],
                    ],
                    [
                      "Low",
                      [
                        ["> 2.50 and ≤ 3.50", "≤ 1.50"],
                        ["> 3.50 and < 4.50", "> 1.50 and < 3.00"],
                      ],
                    ],
                    [
                      "Not flagged",
                      [
                        ["> 3.50 and < 4.50", "≤ 1.50"],
                        ["≥ 4.50", "< 3.00"],
                      ],
                    ],
                  ] as [string, [string, string][]][]
                ).map(([tier, conditions]) => (
                  <tr
                    key={tier}
                    className="align-top"
                  >
                    <td className="py-1.5 pr-4">
                      <span
                        className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${getInterventionClasses(
                          tier === "High Override"
                            ? "High"
                            : tier,
                          tier === "High Override"
                            ? 3
                            : undefined,
                        )}`}
                      >
                        {tier}
                      </span>
                    </td>
                    <td className="py-1.5 pr-4">
                      {conditions.map(
                        ([mean], index) => (
                          <span
                            key={mean}
                            className="block"
                          >
                            {index > 0 && (
                              <span className="text-slate-400">
                                or{" "}
                              </span>
                            )}
                            {mean}
                          </span>
                        ),
                      )}
                    </td>
                    <td className="py-1.5">
                      {conditions.map(
                        ([mean, gap], index) => (
                          <span
                            key={`${mean}-${gap}`}
                            className="block"
                          >
                            {index > 0 && (
                              <span className="text-slate-400">
                                or{" "}
                              </span>
                            )}
                            {gap}
                          </span>
                        ),
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </details>

      <div className="mt-6 flex max-w-3xl flex-wrap items-end justify-between gap-4">
        <div>
          <label
            htmlFor="question-result-filter"
            className="block text-sm font-semibold text-slate-700"
          >
            Filter by intervention tier
          </label>

          <select
            id="question-result-filter"
            value={questionResultFilter}
            onChange={(event) =>
              setQuestionResultFilter(
                event.target
                  .value as QuestionResultFilter,
              )
            }
            className="mt-2 min-w-56 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-slate-900 shadow-sm focus:border-cyan-600 focus:outline-none focus:ring-2 focus:ring-cyan-100"
          >
            <option value="All">
              Show all
            </option>
            <option value="High Override">
              High Override
            </option>
            <option value="High">
              High
            </option>
            <option value="Medium">
              Medium
            </option>
            <option value="Low">
              Low
            </option>
            <option value="Not flagged">
              Not flagged
            </option>
          </select>
        </div>

        <p className="text-sm text-slate-500">
          Showing{" "}
          <span className="font-semibold text-slate-700">
            {filteredQuestionScores.length}
          </span>{" "}
          of{" "}
          <span className="font-semibold text-slate-700">
            {
              results.question_scores
                .length
            }
          </span>{" "}
          questions
        </p>
      </div>

      {results.question_scores
        .length === 0 ? (
        <p className="mt-6 text-slate-600">
          No questions could be
          scored yet.
        </p>
      ) : filteredQuestionScores.length ===
        0 ? (
        <div className="mt-6 rounded-lg border border-dashed border-slate-300 p-6 text-center">
          <p className="font-semibold text-slate-900">
            No questions match this filter
          </p>

          <p className="mt-2 text-sm text-slate-600">
            Choose another intervention
            tier or select Show all.
          </p>
        </div>
      ) : (
        <>
          {/* One row per question; the tier's reason shows on
              hover so the table stays one line per question. */}
          <div className="mt-6 overflow-x-auto">
            <table className="w-full min-w-[36rem] max-w-3xl text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  <th
                    scope="col"
                    className="py-2 pr-4 font-semibold"
                  >
                    Question
                  </th>
                  <th
                    scope="col"
                    className="py-2 pr-4 font-semibold"
                  >
                    Tier
                  </th>
                  <th
                    scope="col"
                    className="py-2 pr-4 text-right font-semibold"
                  >
                    Employee
                  </th>
                  <th
                    scope="col"
                    className="py-2 pr-4 text-right font-semibold"
                  >
                    Senior Manager
                  </th>
                  <th
                    scope="col"
                    className="py-2 pr-4 text-right font-semibold"
                  >
                    Combined
                  </th>
                  <th
                    scope="col"
                    className="py-2 text-right font-semibold"
                  >
                    Opinion gap
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100">
                {filteredQuestionScores.map(
                  (questionScore) => {
                    const isSplit =
                      isHighOverride(
                        questionScore.opinion_gap,
                      );

                    return (
                      <tr
                        key={
                          questionScore.question_id
                        }
                        className="text-slate-700"
                      >
                        <td className="whitespace-nowrap py-2 pr-4 font-semibold text-slate-900">
                          {
                            questionScore.question_number
                          }

                          {lowestQuestionIds.has(
                            questionScore.question_id,
                          ) && (
                            <span
                              className="ml-2 rounded-full px-2 py-0.5 text-xs font-semibold text-white"
                              style={{
                                backgroundColor:
                                  LOWEST_COLOUR,
                              }}
                            >
                              lowest
                            </span>
                          )}
                        </td>

                        <td className="py-2 pr-4">
                          <span
                            title={getTierRationale(
                              questionScore.combined_mean,
                              questionScore.opinion_gap,
                            )}
                            className={`inline-block cursor-help whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-semibold ${getInterventionClasses(
                              questionScore.intervention_tier,
                              questionScore.opinion_gap,
                            )}`}
                          >
                            {getQuestionStatusLabel(
                              questionScore.intervention_tier,
                              questionScore.opinion_gap,
                            )}
                          </span>
                        </td>

                        <td className="py-2 pr-4 text-right tabular-nums">
                          {formatScore(
                            questionScore.employee_mean,
                          )}
                        </td>

                        <td className="py-2 pr-4 text-right tabular-nums">
                          {formatScore(
                            questionScore.manager_mean,
                          )}
                        </td>

                        <td className="py-2 pr-4 text-right tabular-nums">
                          {isSplit ? (
                            <span className="text-slate-500">
                              Hidden
                            </span>
                          ) : (
                            formatScore(
                              questionScore.combined_mean,
                            )
                          )}
                        </td>

                        <td
                          className={`py-2 text-right tabular-nums ${
                            isSplit
                              ? "font-semibold text-slate-900 underline decoration-2 underline-offset-4"
                              : ""
                          }`}
                        >
                          {formatScore(
                            questionScore.opinion_gap,
                          )}
                        </td>
                      </tr>
                    );
                  },
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
