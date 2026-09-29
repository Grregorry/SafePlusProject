import {
  type AIAnalysis,
  type AIDomainSummary,
  type AIPriorityAction,
  type AIRoadmapItem,
  type SafePlusGuidanceSource,
} from "../../../api/aiAnalysisApi";
import {
} from "../../../api/assessmentsApi";
import { getMaturityBadgeClasses } from "../../../components/maturity";
import SourceLinks from "./SourceLinks";
import {
  formatScore,
  getUrgencyClasses,
} from "./resultsHelpers";

export default function AiAnalysisSection({
  aiAnalysis,
  aiDomainSummaries,
  analysisError,
  analysisMessage,
  guidanceSources,
  handleGenerateAIAnalysis,
  isCompleting,
  isGeneratingAnalysis,
  keyRisks,
  keyStrengths,
  limitations,
  priorityActions,
  roadmap,
}: {
  aiAnalysis: AIAnalysis | null;
  aiDomainSummaries: AIDomainSummary[];
  analysisError: string;
  analysisMessage: string;
  guidanceSources: SafePlusGuidanceSource[];
  handleGenerateAIAnalysis: () => void | Promise<void>;
  isCompleting: boolean;
  isGeneratingAnalysis: boolean;
  keyRisks: string[];
  keyStrengths: string[];
  limitations: string[];
  priorityActions: AIPriorityAction[];
  roadmap: AIRoadmapItem[];
}) {
  return (
    <section
      id="ai-analysis"
      className="mt-8 scroll-mt-20 rounded-xl border-2 border-dashed border-violet-300 bg-white p-8 shadow"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <span className="inline-block rounded-md border border-violet-300 bg-violet-50 px-2 py-0.5 text-xs font-bold uppercase tracking-wide text-violet-800">
            AI analysis
          </span>

          <h2 className="mt-1 text-2xl font-bold text-slate-900">
            WorkSafe-grounded improvement
            analysis
          </h2>

          <p className="mt-2 max-w-3xl text-slate-600">
            Recommendations use the
            assessment evidence together
            with curated official WorkSafe
            SafePlus guidance.
          </p>
        </div>

        <div className="flex shrink-0 flex-col items-end gap-3">
          <button
            type="button"
            onClick={
              handleGenerateAIAnalysis
            }
            disabled={
              isGeneratingAnalysis ||
              isCompleting
            }
            className="rounded-lg bg-violet-700/50 px-4 py-2 text-sm font-semibold text-violet-950 hover:bg-violet-700/60 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isGeneratingAnalysis
              ? "Generating AI analysis..."
              : aiAnalysis
                ? "Regenerate AI analysis"
                : "Generate AI analysis"}
          </button>

          {aiAnalysis && (
            <div className="text-right text-sm text-slate-500">
              <p className="font-semibold text-slate-700">
                {aiAnalysis.ai_provider}
              </p>

              {aiAnalysis.generated_at && (
                <p className="mt-1">
                  Generated{" "}
                  {new Date(
                    aiAnalysis.generated_at,
                  ).toLocaleString()}
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {analysisMessage && (
        <div
          role="status"
          className="mt-6 rounded-lg bg-emerald-50 p-4 text-emerald-800"
        >
          {analysisMessage}
        </div>
      )}

      {isGeneratingAnalysis && (
        <p
          role="status"
          className="mt-6 text-sm text-slate-600"
        >
          Generating the AI analysis. This
          usually takes under a minute.
        </p>
      )}

      {analysisError && (
        <div
          role="alert"
          className="mt-6 rounded-lg bg-red-50 p-4 text-red-700"
        >
          {analysisError}
        </div>
      )}

      {!aiAnalysis ? (
        <div className="mt-8 rounded-lg border border-dashed border-slate-300 p-8 text-center">
          <h3 className="font-bold text-slate-900">
            AI analysis has not been
            generated
          </h3>

          <p className="mt-2 text-slate-600">
            Click Generate AI analysis to
            create one.
          </p>
        </div>
      ) : aiAnalysis.status !==
        "completed" ? (
        <div className="mt-8 rounded-lg bg-slate-50 p-5 text-slate-700">
          AI analysis status:{" "}
          <span className="font-semibold capitalize">
            {aiAnalysis.status}
          </span>
        </div>
      ) : (
        <div className="mt-8 space-y-8">
          <article className="rounded-xl bg-violet-50 p-6">
            <h3 className="text-xl font-bold text-violet-950">
              Overall summary
            </h3>

            <p className="mt-4 whitespace-pre-line leading-7 text-slate-700">
              {aiAnalysis.overall_summary}
            </p>
          </article>

          <div className="grid gap-6 lg:grid-cols-2">
            <article className="rounded-xl border border-slate-200 p-6">
              <h3 className="text-xl font-bold text-slate-900">
                Key strengths
              </h3>

              {keyStrengths.length ===
              0 ? (
                <p className="mt-3 text-slate-600">
                  No strengths were
                  returned.
                </p>
              ) : (
                <ul className="mt-4 space-y-3">
                  {keyStrengths.map(
                    (strength, index) => (
                      <li
                        key={`${strength}-${index}`}
                        className="flex gap-3 text-slate-700"
                      >
                        <span className="font-bold text-cyan-800">
                          ✓
                        </span>

                        <span>
                          {strength}
                        </span>
                      </li>
                    ),
                  )}
                </ul>
              )}
            </article>

            <article className="rounded-xl border border-slate-200 p-6">
              <h3 className="text-xl font-bold text-slate-900">
                Key risks
              </h3>

              {keyRisks.length === 0 ? (
                <p className="mt-3 text-slate-600">
                  No risks were returned.
                </p>
              ) : (
                <ul className="mt-4 space-y-3">
                  {keyRisks.map(
                    (risk, index) => (
                      <li
                        key={`${risk}-${index}`}
                        className="flex gap-3 text-slate-700"
                      >
                        <span className="font-bold text-slate-900">
                          !
                        </span>

                        <span>{risk}</span>
                      </li>
                    ),
                  )}
                </ul>
              )}
            </article>
          </div>

          <section
            id="ai-domain-analysis"
            className="scroll-mt-20"
          >
            <h3 className="text-2xl font-bold text-slate-900">
              Domain analysis
            </h3>

            <div className="mt-5 grid gap-5 lg:grid-cols-3">
              {aiDomainSummaries.map(
                (domainSummary) => (
                  <article
                    key={
                      domainSummary.domain_name
                    }
                    className="rounded-xl border border-slate-200 p-6"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <h4 className="font-bold text-slate-900">
                        {
                          domainSummary.domain_name
                        }
                      </h4>

                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${getMaturityBadgeClasses(
                          domainSummary.maturity_level,
                        )}`}
                      >
                        {
                          domainSummary.maturity_level
                        }
                      </span>
                    </div>

                    <p className="mt-3 text-3xl font-bold text-slate-900">
                      {formatScore(
                        domainSummary.score,
                      )}
                    </p>

                    <p className="mt-4 leading-7 text-slate-700">
                      {
                        domainSummary.summary
                      }
                    </p>

                    {domainSummary
                      .strengths.length >
                      0 && (
                      <div className="mt-5">
                        <p className="text-sm font-bold text-slate-900">
                          Strengths
                        </p>

                        <ul className="mt-2 space-y-2 text-sm text-slate-700">
                          {domainSummary.strengths.map(
                            (
                              strength,
                              index,
                            ) => (
                              <li
                                key={`${strength}-${index}`}
                              >
                                • {strength}
                              </li>
                            ),
                          )}
                        </ul>
                      </div>
                    )}

                    {domainSummary
                      .improvement_areas
                      .length > 0 && (
                      <div className="mt-5">
                        <p className="text-sm font-bold text-slate-900">
                          Improvement areas
                        </p>

                        <ul className="mt-2 space-y-2 text-sm text-slate-700">
                          {domainSummary.improvement_areas.map(
                            (
                              improvement,
                              index,
                            ) => (
                              <li
                                key={`${improvement}-${index}`}
                              >
                                •{" "}
                                {improvement}
                              </li>
                            ),
                          )}
                        </ul>
                      </div>
                    )}

                    <SourceLinks
                      sourceIds={
                        domainSummary.source_ids
                      }
                      sources={
                        guidanceSources
                      }
                    />
                  </article>
                ),
              )}
            </div>
          </section>

          <section
            id="ai-priority-actions"
            className="scroll-mt-20"
          >
            <h3 className="text-2xl font-bold text-slate-900">
              Priority actions
            </h3>

            <div className="mt-5 space-y-5">
              {priorityActions.map(
                (action) => (
                  <article
                    key={`${action.priority}-${action.title}`}
                    className="rounded-xl border border-slate-200 p-6"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold uppercase tracking-wide text-violet-700">
                          Priority{" "}
                          {action.priority}
                        </p>

                        <h4 className="mt-1 text-xl font-bold text-slate-900">
                          {action.title}
                        </h4>

                        <p className="mt-1 text-sm text-slate-500">
                          {
                            action.related_domain
                          }
                        </p>
                      </div>

                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${getUrgencyClasses(
                          action.urgency,
                        )}`}
                      >
                        {action.urgency}
                      </span>
                    </div>

                    <div className="mt-5 grid gap-5 lg:grid-cols-2">
                      <div>
                        <p className="font-bold text-slate-900">
                          Assessment
                          evidence
                        </p>

                        <ul className="mt-2 space-y-2 text-slate-700">
                          {action.assessment_evidence.map(
                            (
                              evidence,
                              index,
                            ) => (
                              <li
                                key={`${evidence}-${index}`}
                              >
                                • {evidence}
                              </li>
                            ),
                          )}
                        </ul>
                      </div>

                      <div>
                        <p className="font-bold text-slate-900">
                          Why this matters
                        </p>

                        <p className="mt-2 leading-7 text-slate-700">
                          {action.reason}
                        </p>
                      </div>
                    </div>

                    <div className="mt-5 rounded-lg bg-slate-50 p-5">
                      <p className="font-bold text-slate-900">
                        Recommended action
                      </p>

                      <p className="mt-2 leading-7 text-slate-700">
                        {
                          action.recommended_action
                        }
                      </p>
                    </div>

                    <p className="mt-4 text-sm text-slate-600">
                      <span className="font-semibold">
                        Source relevance:
                      </span>{" "}
                      {
                        action.source_relevance
                      }
                    </p>

                    <SourceLinks
                      sourceIds={
                        action.source_ids
                      }
                      sources={
                        guidanceSources
                      }
                    />
                  </article>
                ),
              )}
            </div>
          </section>

          <section
            id="ai-improvement-roadmap"
            className="scroll-mt-20"
          >
            <h3 className="text-2xl font-bold text-slate-900">
              Improvement roadmap
            </h3>

            <div className="mt-5 space-y-4">
              {roadmap.map(
                (item, index) => (
                  <article
                    key={`${item.timeframe}-${index}`}
                    className="rounded-xl border border-slate-200 p-6"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-700">
                          {item.timeframe}
                        </p>

                        <h4 className="mt-1 text-lg font-bold text-slate-900">
                          {item.objective}
                        </h4>
                      </div>

                      <span className="rounded-full bg-cyan-50 px-3 py-1 text-xs font-semibold text-cyan-800">
                        Step {index + 1}
                      </span>
                    </div>

                    <div className="mt-5">
                      <p className="font-bold text-slate-900">
                        Actions
                      </p>

                      <ul className="mt-2 space-y-2 text-slate-700">
                        {item.actions.map(
                          (
                            roadmapAction,
                            actionIndex,
                          ) => (
                            <li
                              key={`${roadmapAction}-${actionIndex}`}
                            >
                              •{" "}
                              {roadmapAction}
                            </li>
                          ),
                        )}
                      </ul>
                    </div>

                    <div className="mt-5 rounded-lg bg-slate-50 p-4">
                      <p className="text-sm font-bold text-slate-900">
                        Success indicator
                      </p>

                      <p className="mt-1 text-sm text-slate-700">
                        {
                          item.success_indicator
                        }
                      </p>
                    </div>

                    <SourceLinks
                      sourceIds={
                        item.source_ids
                      }
                      sources={
                        guidanceSources
                      }
                    />
                  </article>
                ),
              )}
            </div>
          </section>

          {guidanceSources.length > 0 && (
            <section className="rounded-xl bg-slate-50 p-6">
              <h3 className="text-xl font-bold text-slate-900">
                Official guidance sources
              </h3>

              <p className="mt-2 text-sm text-slate-600">
                The AI was limited to
                curated summaries of these
                official WorkSafe SafePlus
                resources.
              </p>

              <div className="mt-5 grid gap-4 md:grid-cols-2">
                {guidanceSources.map(
                  (source) => (
                    <a
                      key={source.source_id}
                      href={source.url}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-lg border border-slate-200 bg-white p-4 hover:border-cyan-400"
                    >
                      <p className="font-bold text-cyan-800">
                        {source.title}
                      </p>

                      <p className="mt-1 text-xs text-slate-500">
                        {source.source_id}
                      </p>
                    </a>
                  ),
                )}
              </div>
            </section>
          )}

          {limitations.length > 0 && (
            <section className="rounded-xl border border-slate-300 bg-slate-50 p-6">
              <h3 className="text-xl font-bold text-slate-900">
                Important limitations
              </h3>

              <ul className="mt-4 space-y-3 text-slate-700">
                {limitations.map(
                  (
                    limitation,
                    index,
                  ) => (
                    <li
                      key={`${limitation}-${index}`}
                    >
                      • {limitation}
                    </li>
                  ),
                )}
              </ul>
            </section>
          )}
        </div>
      )}
    </section>
  );
}
