import { useState } from "react";
import {
  DEVELOPING_MAX,
  getDomainName,
  LEADING_MIN,
  LOWEST_COLOUR,
  toScalePercent,
} from "../../../components/maturity";
import { type ProfilePoint } from "./resultsHelpers";

// One spoke per question rather than per domain: a three-axis radar
// is a triangle whose area exaggerates the gaps between scores.
export default function QuestionProfile({
  points,
}: {
  points: ProfilePoint[];
}) {
  // Which point's scores are showing; set by hover, focus or tap.
  const [activeIndex, setActiveIndex] =
    useState<number | null>(null);

  if (points.length < 3) {
    return (
      <p className="mt-6 text-slate-600">
        At least three scored questions are
        needed for this chart.
      </p>
    );
  }

  // Sized to the rings plus their question labels; domain names sit in
  // a legend below so the chart can use the full card width.
  const width = 500;
  const height = 500;
  const centreX = width / 2;
  const centreY = height / 2;
  const radius = 200;
  const step = (2 * Math.PI) / points.length;

  // Question i sits half a step past spoke i, so each domain boundary
  // falls on a spoke of its own rather than through a question.
  function position(
    index: number,
    distance: number,
  ): [number, number] {
    const angle = -Math.PI / 2 + index * step;

    return [
      centreX + distance * Math.cos(angle),
      centreY + distance * Math.sin(angle),
    ];
  }

  function distanceFor(score: number): number {
    return (radius * toScalePercent(score)) / 100;
  }

  function ring(score: number): string {
    return points
      .map((_, index) =>
        position(
          index + 0.5,
          distanceFor(score),
        ).join(","),
      )
      .join(" ");
  }

  function anchorFor(
    index: number,
  ): "start" | "middle" | "end" {
    const cosine = Math.cos(
      -Math.PI / 2 + index * step,
    );

    if (Math.abs(cosine) < 0.2) {
      return "middle";
    }

    return cosine > 0 ? "start" : "end";
  }

  const domainStarts = points
    .map((point, index) =>
      index === 0 ||
      point.domainId !==
        points[index - 1].domainId
        ? index
        : -1,
    )
    .filter((index) => index >= 0);

  const plotted = points
    .map((point, index) => ({
      point,
      index,
    }))
    .filter(({ point }) => !point.isSplit);

  const lowestPoints = points.filter(
    (point) => point.isLowest,
  );

  const summary =
    `Question profile: ${plotted.length} questions plotted from 1 at the centre to 5 at the outer ring, grouped by domain.` +
    (lowestPoints.length > 0
      ? ` Lowest: ${lowestPoints
          .map(
            (point) =>
              `question ${point.questionNumber} at ${point.score.toFixed(2)}`,
          )
          .join(", ")}.`
      : "");

  // Split questions sit on the outer ring because their combined mean
  // is hidden.
  function pointPosition(
    point: ProfilePoint,
    index: number,
  ): [number, number] {
    return position(
      index + 0.5,
      point.isSplit
        ? radius
        : distanceFor(point.score),
    );
  }

  function describePoint(
    point: ProfilePoint,
  ): string {
    return [
      `Question ${point.questionNumber}${
        point.isLowest ? ", lowest" : ""
      }`,
      `Employee mean ${point.employeeMean.toFixed(2)}`,
      `Senior Manager mean ${point.managerMean.toFixed(2)}`,
      point.isSplit
        ? "Combined mean hidden"
        : `Combined mean ${point.score.toFixed(2)}`,
      `Opinion gap ${point.opinionGap.toFixed(2)}`,
    ].join(". ");
  }

  const activePoint =
    activeIndex !== null &&
    points[activeIndex]
      ? (() => {
          const [x, y] = pointPosition(
            points[activeIndex],
            activeIndex,
          );

          return {
            point: points[activeIndex],
            x,
            y,
          };
        })()
      : null;

  return (
    <>
    <div className="relative mx-auto mt-6 w-full max-w-3xl">
    <svg
      viewBox={`0 0 ${width} ${height}`}
      role="group"
      aria-label={summary}
      className="h-auto w-full"
    >
      {[2, 3, 4, 5].map((score) => (
        <polygon
          key={score}
          points={ring(score)}
          fill="none"
          stroke="#e2e8f0"
        />
      ))}

      {[DEVELOPING_MAX, LEADING_MIN].map(
        (score) => (
          <polygon
            key={score}
            points={ring(score)}
            fill="none"
            stroke="#64748b"
            strokeDasharray="4 4"
          />
        ),
      )}

      {[
        {
          name: "Performing",
          score: DEVELOPING_MAX,
        },
        {
          name: "Leading",
          score: LEADING_MIN,
        },
      ].map((threshold) => (
        <text
          key={threshold.name}
          x={centreX + 6}
          y={
            centreY -
            distanceFor(threshold.score) *
              Math.cos(step / 2) -
            4
          }
          fontSize={11}
          fill="#475569"
        >
          {threshold.name}
        </text>
      ))}

      {points.map((point, index) => {
        const [x, y] = position(
          index + 0.5,
          radius,
        );

        return (
          <line
            key={point.questionId}
            x1={centreX}
            y1={centreY}
            x2={x}
            y2={y}
            stroke="#e2e8f0"
          />
        );
      })}

      {domainStarts.map((start) => {
        const [x, y] = position(
          start,
          radius + 24,
        );

        return (
          <line
            key={start}
            x1={centreX}
            y1={centreY}
            x2={x}
            y2={y}
            stroke="#334155"
            strokeWidth={2}
          />
        );
      })}

      <polygon
        points={plotted
          .map(({ point, index }) =>
            position(
              index + 0.5,
              distanceFor(point.score),
            ).join(","),
          )
          .join(" ")}
        fill="#0891b2"
        fillOpacity={0.18}
        stroke="#0e7490"
        strokeWidth={2}
        strokeLinejoin="round"
      />

      {plotted.map(({ point, index }) => {
        const [x, y] = position(
          index + 0.5,
          distanceFor(point.score),
        );

        return (
          <circle
            key={point.questionId}
            cx={x}
            cy={y}
            r={point.isLowest ? 6 : 3}
            fill={
              point.isLowest
                ? LOWEST_COLOUR
                : "#0e7490"
            }
          />
        );
      })}

      {points.map((point, index) => {
        if (!point.isSplit) {
          return null;
        }

        const [x, y] = position(
          index + 0.5,
          radius,
        );

        return (
          <circle
            key={point.questionId}
            cx={x}
            cy={y}
            r={4.5}
            fill="#ffffff"
            stroke="#475569"
            strokeWidth={1.5}
          />
        );
      })}

      {points.map((point, index) => {
        const [x, y] = position(
          index + 0.5,
          radius + 14,
        );

        const isUpperHalf =
          Math.sin(
            -Math.PI / 2 +
              (index + 0.5) * step,
          ) < 0;

        const baseline = y + 3.5;

        if (!point.isLowest) {
          return (
            <text
              key={point.questionId}
              x={x}
              y={baseline}
              fontSize={11}
              textAnchor={anchorFor(
                index + 0.5,
              )}
              fill="#475569"
            >
              {point.questionNumber}
            </text>
          );
        }

        // "lowest" sits on the outer side so it never runs into the chart.
        const lines = isUpperHalf
          ? ["lowest", point.questionNumber]
          : [point.questionNumber, "lowest"];

        const firstBaseline = isUpperHalf
          ? baseline - 12
          : baseline;

        return (
          <text
            key={point.questionId}
            x={x}
            y={firstBaseline}
            fontSize={11}
            fontWeight={700}
            textAnchor={anchorFor(index + 0.5)}
            fill={LOWEST_COLOUR}
          >
            <tspan x={x} y={firstBaseline}>
              {lines[0]}
            </tspan>

            <tspan
              x={x}
              y={firstBaseline + 12}
            >
              {lines[1]}
            </tspan>
          </text>
        );
      })}

      {activePoint && (
        <circle
          cx={activePoint.x}
          cy={activePoint.y}
          r={9}
          fill="none"
          stroke="#0e7490"
          strokeWidth={2}
          pointerEvents="none"
        />
      )}

      {/* Larger invisible targets make the small points easy to hover. */}
      {points.map((point, index) => {
        const [x, y] = pointPosition(
          point,
          index,
        );

        return (
          <circle
            key={point.questionId}
            cx={x}
            cy={y}
            r={11}
            fill="transparent"
            tabIndex={0}
            aria-label={describePoint(point)}
            className="cursor-pointer outline-none"
            onMouseEnter={() =>
              setActiveIndex(index)
            }
            onMouseLeave={() =>
              setActiveIndex(null)
            }
            onFocus={() =>
              setActiveIndex(index)
            }
            onBlur={() =>
              setActiveIndex(null)
            }
            onClick={() =>
              setActiveIndex((current) =>
                current === index
                  ? null
                  : index,
              )
            }
          />
        );
      })}
    </svg>

    {activePoint && (
      <div
        role="tooltip"
        className="pointer-events-none absolute z-10 w-60 rounded-lg border border-slate-200 bg-white p-3 text-sm shadow-lg"
        style={{
          left: `${(activePoint.x / width) * 100}%`,
          top: `${(activePoint.y / height) * 100}%`,
          // Shift sideways in proportion to the point's position so the
          // card never runs off either edge of the chart.
          transform: `translate(-${Math.round(
            (activePoint.x / width) * 100,
          )}%, ${
            activePoint.y < centreY
              ? "16px"
              : "calc(-100% - 16px)"
          })`,
        }}
      >
        <p className="font-semibold text-slate-900">
          Question{" "}
          {activePoint.point.questionNumber}

          {activePoint.point.isLowest && (
            <span
              style={{
                color: LOWEST_COLOUR,
              }}
            >
              {" "}
              · lowest
            </span>
          )}
        </p>

        <dl className="mt-2 grid grid-cols-[1fr_auto] gap-x-4 gap-y-1 text-slate-600">
          <dt>Employee mean</dt>
          <dd className="text-right font-semibold tabular-nums text-slate-900">
            {activePoint.point.employeeMean.toFixed(
              2,
            )}
          </dd>

          <dt>Senior Manager mean</dt>
          <dd className="text-right font-semibold tabular-nums text-slate-900">
            {activePoint.point.managerMean.toFixed(
              2,
            )}
          </dd>

          <dt>Combined mean</dt>
          <dd className="text-right font-semibold tabular-nums text-slate-900">
            {activePoint.point.isSplit
              ? "Hidden"
              : activePoint.point.score.toFixed(
                  2,
                )}
          </dd>

          <dt>Opinion gap</dt>
          <dd className="text-right font-semibold tabular-nums text-slate-900">
            {activePoint.point.opinionGap.toFixed(
              2,
            )}
          </dd>
        </dl>

        {activePoint.point.isSplit && (
          <p className="mt-2 text-xs text-slate-500">
            The groups differ by 3.00 or
            more, so the combined mean is
            hidden.
          </p>
        )}
      </div>
    )}
    </div>

    <p className="mt-3 text-center text-sm text-slate-600">
      Clockwise from the top:{" "}
      {domainStarts.map((start, domainIndex) => {
        const last =
          (domainStarts[domainIndex + 1] ??
            points.length) - 1;

        return (
          <span key={start}>
            {domainIndex > 0 ? " · " : ""}
            <span className="font-semibold text-slate-900">
              {getDomainName(
                points[start].domainId,
              )}
            </span>{" "}
            {points[start].questionNumber}–
            {points[last].questionNumber}
          </span>
        );
      })}
    </p>

    <p className="mt-1 text-center text-xs text-slate-500">
      Hover over a point, or tab to it, to
      see its scores.
    </p>
    </>
  );
}
