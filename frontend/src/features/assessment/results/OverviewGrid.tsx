import {
  type AssessmentScoringResult,
  type DomainScoreResult,
  type QuestionScoreResult,
} from "../../../api/assessmentsApi";
import {
  getDomainName,
  LOWEST_COLOUR,
} from "../../../components/maturity";
import MaturityLadder from "../../../components/MaturityLadder";
import QuestionProfile from "./QuestionProfile";
import {
  formatScore,
  getQuestionDomainId,
  type ProfilePoint,
} from "./resultsHelpers";

export default function OverviewGrid({
  lowestQuestionIds,
  overallScore,
  profilePoints,
  results,
  scoredQuestions,
  sortedDomainScores,
}: {
  lowestQuestionIds: Set<number>;
  overallScore: number | null;
  profilePoints: ProfilePoint[];
  results: AssessmentScoringResult;
  scoredQuestions: QuestionScoreResult[];
  sortedDomainScores: DomainScoreResult[];
}) {
  return (
    <div
      id="overview"
      className="mt-8 grid scroll-mt-20 gap-6 lg:grid-cols-[minmax(0,2.3fr)_minmax(0,1fr)]"
    >
      <section className="rounded-xl bg-white p-8 shadow">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">
              SafePlus question profile
            </h2>

            <p className="mt-2 max-w-3xl text-slate-600">
              Each spoke is one scored
              question, grouped by domain,
              so differences between
              questions are shown at their
              true size.
            </p>

            <p className="mt-2 text-sm font-semibold text-slate-700">
              Questions scored:{" "}
              {results.questions_scored}
            </p>
          </div>

          <div className="rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-600">
            <p>Centre = 1</p>

            <p className="mt-1">
              Outer ring = 5
            </p>
          </div>
        </div>

        <QuestionProfile
          points={profilePoints}
        />

        <p className="mt-4 max-w-3xl text-sm leading-6 text-slate-500">
          Heavier spokes mark where each
          domain starts. Dashed rings mark
          the Performing (above 2.50) and
          Leading (4.50) thresholds. Hollow
          points on the outer ring are
          questions where employees and
          managers differ by 3.00 or more;
          their combined score is not
          plotted because it would hide the
          split.
        </p>
      </section>

      <div className="flex flex-col gap-6">
        <article className="rounded-xl bg-white p-6 shadow">
          <p className="text-sm font-semibold text-slate-500">
            Overall result
          </p>

          {overallScore !== null &&
          results.overall_maturity_label ? (
            <>
              <p className="mt-2 text-4xl font-bold text-cyan-800">
                {
                  results.overall_maturity_label
                }
              </p>

              <div className="mt-6">
                <MaturityLadder
                  label="Overall score"
                  score={overallScore}
                />
              </div>
            </>
          ) : (
            <p className="mt-2 text-slate-600">
              Not available yet
            </p>
          )}
        </article>

        <section className="flex flex-1 flex-col rounded-xl bg-white p-8 shadow">
          <h2 className="text-2xl font-bold text-slate-900">
            Domain scores
          </h2>

          {sortedDomainScores.length === 0 ? (
            <p className="mt-4 text-slate-600">
              No domain scores are
              available yet.
            </p>
          ) : (
            <div className="mt-6 flex flex-1 flex-col justify-between gap-5">
              {sortedDomainScores.map(
                (domainScore) => {
                  const domainQuestions =
                    scoredQuestions.filter(
                      (questionScore) =>
                        getQuestionDomainId(
                          questionScore.question_number,
                        ) ===
                        domainScore.domain_id,
                    );

                  const lowestInDomain =
                    domainQuestions.filter(
                      (questionScore) =>
                        lowestQuestionIds.has(
                          questionScore.question_id,
                        ),
                    );

                  return (
                    <article
                      key={
                        domainScore.domain_id
                      }
                      className="rounded-lg border border-slate-200 p-5"
                    >
                      <MaturityLadder
                        as="h3"
                        label={getDomainName(
                          domainScore.domain_id,
                        )}
                        score={Number(
                          domainScore.combined_mean,
                        )}
                      />

                      <p className="mt-3 text-sm text-slate-500">
                        {domainQuestions.length}{" "}
                        scored{" "}
                        {domainQuestions.length ===
                        1
                          ? "question"
                          : "questions"}
                      </p>

                      {lowestInDomain.map(
                        (questionScore) => (
                          <p
                            key={
                              questionScore.question_id
                            }
                            className="mt-2 text-sm font-semibold"
                            style={{
                              color:
                                LOWEST_COLOUR,
                            }}
                          >
                            Question{" "}
                            {
                              questionScore.question_number
                            }{" "}
                            is the lowest
                            scoring question (
                            {formatScore(
                              questionScore.combined_mean,
                            )}
                            )
                          </p>
                        ),
                      )}
                    </article>
                  );
                },
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
