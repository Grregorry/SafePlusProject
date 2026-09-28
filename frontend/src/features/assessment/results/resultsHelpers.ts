import { type SafePlusGuidanceSource } from "../../../api/aiAnalysisApi";
import { type AssessmentSetupQuestion } from "../../../api/assessmentsApi";
import { type SubmissionSummary } from "../../../api/submissionSummaryApi";

export type Participation = {
  summary: SubmissionSummary;
  questions: AssessmentSetupQuestion[];
};

export function formatLongDate(value: string): string {
  return new Date(value).toLocaleDateString(
    undefined,
    {
      day: "numeric",
      month: "long",
      year: "numeric",
    },
  );
}

export function isHighOverride(
  opinionGap: string | number,
): boolean {
  return Number(opinionGap) >= 3;
}

export function getQuestionStatusLabel(
  interventionTier: string,
  opinionGap: string | number,
): string {
  if (isHighOverride(opinionGap)) {
    return "High Override";
  }

  return interventionTier;
}

export type QuestionResultFilter =
  | "All"
  | "High Override"
  | "High"
  | "Medium"
  | "Low"
  | "Not flagged";

// Priority tiers run from dark red (most urgent) to green. The tier
// name is always shown as text too, so colour is never the only cue.
export function getInterventionClasses(
  interventionTier: string,
  opinionGap?: string | number,
): string {
  if (
    opinionGap !== undefined &&
    isHighOverride(opinionGap)
  ) {
    return "bg-red-800 text-white";
  }

  // At 60% the red is too light for white text, so High uses dark text.
  if (interventionTier === "High") {
    return "bg-red-600/60 text-red-950";
  }

  if (interventionTier === "Medium") {
    return "bg-orange-400/60 text-slate-900";
  }

  if (interventionTier === "Low") {
    return "bg-yellow-300/60 text-slate-900";
  }

  // Soft green at low strength so the most common tier stays subtle.
  return "bg-[#A1FB8E]/20 text-slate-800";
}

export function getTierRationale(
  combinedMean: string | number,
  opinionGap: string | number,
): string {
  const mean = Number(combinedMean);
  const gap = Number(opinionGap);

  if (gap >= 3) {
    return "Extreme perception disconnect. Manager confidence and worker experience are irreconcilable — this overrides the mean score.";
  }

  if (mean <= 2.5 && gap > 1.5) {
    return "Poor performance and a significant perception disconnect — two compounding problems.";
  }

  if (mean <= 2.5) {
    return "Poor performance but shared awareness — the organisation is falling short, but aligned enough to act.";
  }

  if (mean <= 3.5 && gap > 1.5) {
    return "Marginal performance and a perception disconnect — risk of deterioration without shared awareness.";
  }

  if (mean <= 3.5) {
    return "Marginal performance with shared awareness. Improvement is possible, not urgent.";
  }

  if (mean < 4.5 && gap > 1.5) {
    return "Adequate performance but a perception gap worth monitoring.";
  }

  if (mean < 4.5) {
    return "Performing well with aligned perceptions. No priority action required.";
  }

  return "Leading performance. No intervention required.";
}

export function getUrgencyClasses(
  urgency: string,
): string {
  const normalisedUrgency =
    urgency.toLowerCase();

  if (
    normalisedUrgency.includes("high") ||
    normalisedUrgency.includes("urgent") ||
    normalisedUrgency.includes("immediate")
  ) {
    return "bg-slate-800 text-white";
  }

  if (
    normalisedUrgency.includes("medium") ||
    normalisedUrgency.includes("moderate")
  ) {
    return "bg-slate-300 text-slate-900";
  }

  return "bg-slate-100 text-slate-700 ring-1 ring-inset ring-slate-300";
}

export function formatScore(
  value: string | number | null,
): string {
  if (value === null) {
    return "Not available";
  }

  const numericValue = Number(value);

  if (Number.isNaN(numericValue)) {
    return String(value);
  }

  return numericValue.toFixed(2);
}

export function getSourceById(
  sourceId: string,
  sources: SafePlusGuidanceSource[],
): SafePlusGuidanceSource | undefined {
  return sources.find(
    (source) =>
      source.source_id === sourceId,
  );
}

export type ProfilePoint = {
  questionId: number;
  questionNumber: string;
  domainId: number;
  score: number;
  employeeMean: number;
  managerMean: number;
  opinionGap: number;
  isSplit: boolean;
  isLowest: boolean;
};

// Question numbers are "<domain>.<item>", e.g. "3.12".
export function getQuestionDomainId(
  questionNumber: string,
): number {
  return Number(questionNumber.split(".")[0]);
}

// Smooth-scrolls to an element, or to the top of the page when no id is
// given, unless the viewer prefers reduced motion.
export function scrollPageTo(elementId: string | null) {
  const behavior: ScrollBehavior = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches
    ? "auto"
    : "smooth";

  if (elementId === null) {
    window.scrollTo({ top: 0, behavior });
    return;
  }

  document
    .getElementById(elementId)
    ?.scrollIntoView({ behavior, block: "start" });
}

export type ReportType =
  | "full"
  | "business-leader"
  | "board"
  | "operational-manager";

export type DomainWorking = {
  domainId: number;
  count: number;
  total: number;
  mean: number;
};

export type DomainQuestionGroup = {
  name: string;
  questions: AssessmentSetupQuestion[];
};
