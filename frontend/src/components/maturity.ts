// SafePlus maturity on the 1 to 5 combined-mean scale. Thresholds
// mirror get_maturity_level in backend/app/services/scoring.py:
// Developing <= 2.50, Performing > 2.50 and < 4.50, Leading >= 4.50.

export const SCALE_MIN = 1;
export const SCALE_MAX = 5;
export const DEVELOPING_MAX = 2.5;
export const LEADING_MIN = 4.5;

// Lowest-scoring item. Deliberately not red, and distinct from the
// cyan maturity scale and the violet used for AI content.
export const LOWEST_COLOUR = "#1d4ed8";

export function getDomainName(
  domainId: number,
): string {
  if (domainId === 1) {
    return "Leadership";
  }

  if (domainId === 2) {
    return "Worker Engagement";
  }

  if (domainId === 3) {
    return "Risk Management";
  }

  return `Domain ${domainId}`;
}

export function getMaturityLevel(
  score: number,
): string {
  if (score <= DEVELOPING_MAX) {
    return "Developing";
  }

  if (score >= LEADING_MIN) {
    return "Leading";
  }

  return "Performing";
}

// One hue at three strengths, so levels never read as red/amber/green.
// The level name is always shown as text alongside.
export function getMaturityBadgeClasses(
  maturityLevel: string | null,
): string {
  if (maturityLevel === "Leading") {
    return "bg-cyan-800 text-white";
  }

  if (maturityLevel === "Performing") {
    return "bg-cyan-200 text-cyan-950";
  }

  if (maturityLevel === "Developing") {
    return "bg-cyan-50 text-cyan-950 ring-1 ring-inset ring-cyan-200";
  }

  return "bg-slate-200 text-slate-600";
}

export function toScalePercent(
  score: number,
): number {
  const percent =
    ((score - SCALE_MIN) /
      (SCALE_MAX - SCALE_MIN)) *
    100;

  return Math.min(100, Math.max(0, percent));
}

// Scores are stored to two decimals, so Performing starts at 2.51.
export function getNextLevel(
  score: number,
): { name: string; gap: number } | null {
  if (score <= DEVELOPING_MAX) {
    return {
      name: "Performing",
      gap: 2.51 - score,
    };
  }

  if (score < LEADING_MIN) {
    return {
      name: "Leading",
      gap: LEADING_MIN - score,
    };
  }

  return null;
}
