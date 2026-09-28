import {
  DEVELOPING_MAX,
  LEADING_MIN,
  getMaturityLevel,
  getNextLevel,
  toScalePercent,
} from "./maturity";

type MaturityLadderProps = {
  label: string;
  score: number;
  as?: "span" | "h3";
};

const developingWidth =
  toScalePercent(DEVELOPING_MAX);

const performingWidth =
  toScalePercent(LEADING_MIN) -
  developingWidth;

const leadingWidth =
  100 - developingWidth - performingWidth;

// A track split into the three levels with a marker at the score, so
// the distance to the next threshold is visible, not just the number.
function MaturityLadder({
  label,
  score,
  as: LabelTag = "span",
}: MaturityLadderProps) {
  const level = getMaturityLevel(score);
  const nextLevel = getNextLevel(score);

  const distanceText = nextLevel
    ? `${nextLevel.gap.toFixed(2)} below ${nextLevel.name}`
    : "At the highest level";

  return (
    <div>
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <LabelTag className="min-w-0 font-bold text-slate-900">
          {label}
        </LabelTag>

        <span className="whitespace-nowrap text-sm text-slate-600">
          <span className="text-lg font-bold text-slate-900">
            {score.toFixed(2)}
          </span>{" "}
          {level}
        </span>
      </div>

      <div
        role="img"
        aria-label={`${label}: ${score.toFixed(
          2,
        )} out of 5, ${level}. ${distanceText}.`}
        className="relative mt-2 flex h-3"
      >
        <div
          className="rounded-l-full bg-cyan-50 ring-1 ring-inset ring-cyan-200"
          style={{
            width: `${developingWidth}%`,
          }}
        />

        <div
          className="bg-cyan-200"
          style={{
            width: `${performingWidth}%`,
          }}
        />

        <div
          className="rounded-r-full bg-cyan-800"
          style={{
            width: `${leadingWidth}%`,
          }}
        />

        <div
          aria-hidden="true"
          className="absolute -bottom-1.5 -top-1.5 -ml-0.5 w-1 rounded-full bg-slate-900"
          style={{
            left: `${toScalePercent(score)}%`,
          }}
        />
      </div>

      <div
        aria-hidden="true"
        className="mt-1.5 flex text-[11px] text-slate-500"
      >
        <span
          style={{
            width: `${developingWidth}%`,
          }}
        >
          Developing
        </span>

        <span
          style={{
            width: `${performingWidth}%`,
          }}
        >
          Performing
        </span>

        <span
          className="flex justify-end whitespace-nowrap"
          style={{
            width: `${leadingWidth}%`,
          }}
        >
          Leading
        </span>
      </div>

      <p className="mt-1 text-xs font-semibold text-slate-600">
        {distanceText}
      </p>
    </div>
  );
}

export default MaturityLadder;
