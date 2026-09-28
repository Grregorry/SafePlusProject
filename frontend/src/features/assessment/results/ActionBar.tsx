import {
  type Dispatch,
  type SetStateAction,
} from "react";
import { type AIAnalysis } from "../../../api/aiAnalysisApi";
import { type Assessment } from "../../../api/assessmentsApi";
import {
  type ReportType,
  scrollPageTo,
} from "./resultsHelpers";

export default function ActionBar({
  aiAnalysis,
  assessment,
  downloadingReport,
  errorMessage,
  handleDownloadReport,
  isReportMenuOpen,
  reportOptions,
  setIsReportMenuOpen,
  setShowAiLinks,
  showAiLinks,
}: {
  aiAnalysis: AIAnalysis | null;
  assessment: Assessment;
  downloadingReport: string | null;
  errorMessage: string;
  handleDownloadReport: (reportType: ReportType, includeAi: boolean) => void | Promise<void>;
  isReportMenuOpen: boolean;
  reportOptions: { type: ReportType; label: string }[];
  setIsReportMenuOpen: Dispatch<SetStateAction<boolean>>;
  setShowAiLinks: Dispatch<SetStateAction<boolean>>;
  showAiLinks: boolean;
}) {
  return (
    <nav
      aria-label="Assessment actions"
      className="sticky top-0 z-30 -mx-6 -mt-10 mb-6 flex items-center justify-between gap-4 border-b border-slate-200 bg-slate-100/95 px-6 py-3 backdrop-blur"
    >
      <div className="flex min-w-0 items-center gap-5">
        <button
          type="button"
          onClick={() => {
            setShowAiLinks(false);
            scrollPageTo(null);
          }}
          title="Back to top"
          className="truncate font-semibold text-slate-900 hover:text-cyan-800"
        >
          {assessment.name}
        </button>

        <button
          type="button"
          onClick={() => {
            setShowAiLinks(false);
            scrollPageTo("overview");
          }}
          className="shrink-0 text-sm font-semibold text-slate-600 hover:text-cyan-800"
        >
          Overview
        </button>

        <button
          type="button"
          onClick={() => {
            setShowAiLinks(true);
            scrollPageTo("ai-analysis");
          }}
          aria-expanded={
            aiAnalysis?.status ===
            "completed"
              ? showAiLinks
              : undefined
          }
          className={`shrink-0 text-sm font-semibold hover:text-cyan-800 ${
            showAiLinks
              ? "text-cyan-800"
              : "text-slate-600"
          }`}
        >
          AI analysis
        </button>

        {showAiLinks &&
          aiAnalysis?.status ===
            "completed" && (
            <div className="flex shrink-0 items-center gap-4 border-l border-slate-300 pl-4">
              {[
                {
                  id: "ai-domain-analysis",
                  label: "Domain analysis",
                },
                {
                  id: "ai-priority-actions",
                  label: "Priority actions",
                },
                {
                  id: "ai-improvement-roadmap",
                  label: "Improvement roadmap",
                },
              ].map((link) => (
                <button
                  key={link.id}
                  type="button"
                  onClick={() =>
                    scrollPageTo(link.id)
                  }
                  className="text-sm text-slate-500 hover:text-cyan-800"
                >
                  {link.label}
                </button>
              ))}
            </div>
          )}
      </div>

      {/* Choose a report and whether it includes the AI analysis;
          AI text never goes into a report unless chosen here. */}
      <div
        data-report-menu
        className="relative shrink-0"
      >
        <button
          type="button"
          onClick={() =>
            setIsReportMenuOpen(
              (open) => !open,
            )
          }
          aria-haspopup="true"
          aria-expanded={isReportMenuOpen}
          className="flex items-center gap-2 rounded-lg bg-cyan-700 px-4 py-2 text-sm font-semibold text-white hover:bg-cyan-800"
        >
          Download report

          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            className={`h-4 w-4 transition-transform ${
              isReportMenuOpen
                ? "rotate-180"
                : ""
            }`}
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>

        {isReportMenuOpen && (
          <div className="absolute right-0 z-40 mt-2 w-[26rem] max-w-[calc(100vw-2rem)] rounded-xl border border-slate-200 bg-white p-4 shadow-xl">
            <p className="text-sm font-semibold text-slate-900">
              Download a report
            </p>

            <p className="mt-1 text-xs text-slate-500">
              {aiAnalysis?.status ===
              "completed"
                ? "Choose whether each report includes the AI analysis."
                : "Generate the AI analysis to download a report that includes it."}
            </p>

            <ul className="mt-3 divide-y divide-slate-100">
              {reportOptions.map(
                (option) => (
                  <li
                    key={option.type}
                    className="flex items-center justify-between gap-3 py-2"
                  >
                    <span className="text-sm font-medium text-slate-800">
                      {option.label}
                    </span>

                    <span className="flex shrink-0 gap-2">
                      <button
                        type="button"
                        onClick={() =>
                          void handleDownloadReport(
                            option.type,
                            false,
                          )
                        }
                        disabled={
                          downloadingReport !==
                          null
                        }
                        className="rounded-md border border-slate-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {downloadingReport ===
                        `${option.type}-review`
                          ? "Preparing..."
                          : "Review only"}
                      </button>

                      <button
                        type="button"
                        onClick={() =>
                          void handleDownloadReport(
                            option.type,
                            true,
                          )
                        }
                        disabled={
                          aiAnalysis?.status !==
                            "completed" ||
                          downloadingReport !==
                            null
                        }
                        title={
                          aiAnalysis?.status ===
                          "completed"
                            ? undefined
                            : "Generate the AI analysis first"
                        }
                        className="rounded-md bg-violet-700/50 px-2.5 py-1 text-xs font-semibold text-violet-950 hover:bg-violet-700/60 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        {downloadingReport ===
                        `${option.type}-ai`
                          ? "Preparing..."
                          : "With AI analysis"}
                      </button>
                    </span>
                  </li>
                ),
              )}
            </ul>

            {errorMessage && (
              <p
                role="alert"
                className="mt-2 text-xs text-red-700"
              >
                {errorMessage}
              </p>
            )}
          </div>
        )}
      </div>
    </nav>
  );
}
