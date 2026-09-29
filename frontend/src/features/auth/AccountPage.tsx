import {
  useEffect,
  useMemo,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";

import {
  calculateAssessmentScores,
  createAssessment,
  getAssessments,
  type Assessment,
  type AssessmentScoringResult,
} from "../../api/assessmentsApi";
import {
  getCurrentOrganisation,
  resendVerification,
  type Organisation,
} from "../../api/authApi";
import MaturityLadder from "../../components/MaturityLadder";
import {
  DEVELOPING_MAX,
  LEADING_MIN,
  SCALE_MAX,
  SCALE_MIN,
  getDomainName,
  getMaturityBadgeClasses,
  getNextLevel,
} from "../../components/maturity";

// Only completed assessments count towards where the organisation
// stands; open ones never carry a score.
function getCompletedHistory(
  assessmentList: Assessment[],
): Assessment[] {
  return assessmentList
    .filter(
      (assessment) =>
        assessment.status === "completed" &&
        assessment.completed_at !== null &&
        assessment.overall_combined_mean !== null,
    )
    .sort(
      (first, second) =>
        new Date(
          first.completed_at as string,
        ).getTime() -
        new Date(
          second.completed_at as string,
        ).getTime(),
    );
}

function formatShortDate(
  value: string | null,
): string {
  if (!value) {
    return "";
  }

  return new Date(value).toLocaleDateString(
    undefined,
    {
      day: "numeric",
      month: "short",
      year: "numeric",
    },
  );
}

function describeScoreChange(
  current: number,
  previous: number,
): string {
  const difference =
    Math.round((current - previous) * 100) /
    100;

  if (difference === 0) {
    return "No change";
  }

  return `${difference > 0 ? "Up" : "Down"} ${Math.abs(
    difference,
  ).toFixed(2)}`;
}

// Open assessments first (newest first), then completed ones with the
// most recently completed at the top.
function sortAssessmentsForTable(
  assessmentList: Assessment[],
): Assessment[] {
  const openAssessments = assessmentList
    .filter(
      (assessment) =>
        assessment.status !== "completed",
    )
    .sort(
      (first, second) =>
        new Date(
          second.created_at,
        ).getTime() -
        new Date(
          first.created_at,
        ).getTime(),
    );

  const completedAssessments = [
    ...getCompletedHistory(assessmentList),
  ].reverse();

  return [
    ...openAssessments,
    ...completedAssessments,
  ];
}

type TrendPoint = {
  id: number;
  label: string;
  score: number;
};

function ScoreTrend({
  points,
}: {
  points: TrendPoint[];
}) {
  if (points.length < 2) {
    return (
      <p className="mt-4 text-sm text-slate-600">
        The trend appears once a second
        assessment is completed.
      </p>
    );
  }

  const width = 560;
  const height = 230;
  const left = 56;
  const right = 104;
  const top = 20;
  const bottom = 40;

  function x(index: number): number {
    return (
      left +
      (index * (width - left - right)) /
        (points.length - 1)
    );
  }

  function y(score: number): number {
    return (
      top +
      ((SCALE_MAX - score) /
        (SCALE_MAX - SCALE_MIN)) *
        (height - top - bottom)
    );
  }

  const bands = [
    {
      name: "Leading",
      from: LEADING_MIN,
      to: SCALE_MAX,
      fill: "#155e75",
      opacity: 0.18,
    },
    {
      name: "Performing",
      from: DEVELOPING_MAX,
      to: LEADING_MIN,
      fill: "#a5f3fc",
      opacity: 0.45,
    },
    {
      name: "Developing",
      from: SCALE_MIN,
      to: DEVELOPING_MAX,
      fill: "#ecfeff",
      opacity: 1,
    },
  ];

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={`Overall score by completed assessment: ${points
        .map(
          (point) =>
            `${point.label} ${point.score.toFixed(2)}`,
        )
        .join(", ")}`}
      className="mt-4 h-auto w-full"
    >
      {bands.map((band) => (
        <g key={band.name}>
          <rect
            x={left}
            y={y(band.to)}
            width={width - left - right}
            height={y(band.from) - y(band.to)}
            fill={band.fill}
            fillOpacity={band.opacity}
          />

          <text
            x={width - right + 8}
            y={(y(band.from) + y(band.to)) / 2 + 4}
            fontSize={11}
            fill="#475569"
          >
            {band.name}
          </text>
        </g>
      ))}

      {[
        SCALE_MIN,
        DEVELOPING_MAX,
        LEADING_MIN,
        SCALE_MAX,
      ].map((tick) => (
        <text
          key={tick}
          x={left - 8}
          y={y(tick) + 4}
          fontSize={11}
          textAnchor="end"
          fill="#64748b"
        >
          {tick.toFixed(1)}
        </text>
      ))}

      <polyline
        points={points
          .map(
            (point, index) =>
              `${x(index)},${y(point.score)}`,
          )
          .join(" ")}
        fill="none"
        stroke="#0e7490"
        strokeWidth={2.5}
      />

      {points.map((point, index) => (
        <g key={point.id}>
          <circle
            cx={x(index)}
            cy={y(point.score)}
            r={4.5}
            fill="#0e7490"
          />

          <text
            x={x(index)}
            y={y(point.score) - 10}
            fontSize={12}
            fontWeight={700}
            textAnchor="middle"
            fill="#0f172a"
          >
            {point.score.toFixed(2)}
          </text>

          <text
            x={x(index)}
            y={height - 12}
            fontSize={11}
            textAnchor="middle"
            fill="#64748b"
          >
            {point.label}
          </text>
        </g>
      ))}
    </svg>
  );
}

function AccountPage() {
  const navigate = useNavigate();

  const [
    organisation,
    setOrganisation,
  ] = useState<Organisation | null>(null);

  const [
    assessments,
    setAssessments,
  ] = useState<Assessment[]>([]);

  const [
    assessmentName,
    setAssessmentName,
  ] = useState("");

  const [
    showCreateForm,
    setShowCreateForm,
  ] = useState(false);

  const [isLoading, setIsLoading] =
    useState(true);

  const [
    isCreatingAssessment,
    setIsCreatingAssessment,
  ] = useState(false);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState("");

  const [
    verificationToken,
    setVerificationToken,
  ] = useState("");

  const [
    isSendingVerification,
    setIsSendingVerification,
  ] = useState(false);

  const [
    verificationError,
    setVerificationError,
  ] = useState("");

  const [
    latestScores,
    setLatestScores,
  ] = useState<AssessmentScoringResult | null>(
    null,
  );

  const [
    latestScoresError,
    setLatestScoresError,
  ] = useState("");

  const [
    isLoadingLatestScores,
    setIsLoadingLatestScores,
  ] = useState(false);

  async function handleSendVerificationLink() {
    const accessToken =
      localStorage.getItem(
        "safeplus_access_token",
      );

    if (!accessToken) {
      navigate("/login", {
        replace: true,
      });
      return;
    }

    try {
      setIsSendingVerification(true);
      setVerificationError("");

      const result = await resendVerification(
        accessToken,
      );

      setVerificationToken(
        result.verification_token,
      );
    } catch (error) {
      setVerificationError(
        error instanceof Error
          ? error.message
          : "Unable to generate a verification link.",
      );
    } finally {
      setIsSendingVerification(false);
    }
  }

  // Loaded inside the effect so state is only set after the requests resolve.
  useEffect(() => {
    // Domain scores for the current standing come from the most
    // recently completed assessment only.
    async function loadLatestScores(
      assessmentList: Assessment[],
      accessToken: string,
    ) {
      const history =
        getCompletedHistory(assessmentList);

      const latest =
        history[history.length - 1];

      if (!latest) {
        setLatestScores(null);
        return;
      }

      try {
        setIsLoadingLatestScores(true);
        setLatestScoresError("");

        setLatestScores(
          await calculateAssessmentScores(
            latest.id,
            accessToken,
          ),
        );
      } catch (error) {
        setLatestScores(null);
        setLatestScoresError(
          error instanceof Error
            ? error.message
            : "Unable to load domain scores.",
        );
      } finally {
        setIsLoadingLatestScores(false);
      }
    }

    async function loadAccount() {
      const accessToken =
        localStorage.getItem(
          "safeplus_access_token",
        );

      if (!accessToken) {
        navigate("/login", {
          replace: true,
        });
        return;
      }

      try {
        const [
          account,
          existingAssessments,
        ] = await Promise.all([
          getCurrentOrganisation(
            accessToken,
          ),
          getAssessments(accessToken),
        ]);

        setOrganisation(account);
        setAssessments(
          existingAssessments,
        );

        await loadLatestScores(
          existingAssessments,
          accessToken,
        );
      } catch (error) {
        localStorage.removeItem(
          "safeplus_access_token",
        );

        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Your session could not be verified.",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadAccount();
  }, [navigate]);

  const completedHistory = useMemo(
    () =>
      getCompletedHistory(assessments),
    [assessments],
  );

  const openAssessmentCount = useMemo(
    () =>
      assessments.filter(
        (assessment) =>
          assessment.status !== "completed",
      ).length,
    [assessments],
  );

  // The header button opens the most recently created assessment that
  // is still open; with none open it offers a new assessment instead.
  const openAssessment = useMemo(
    () =>
      assessments
        .filter(
          (assessment) =>
            assessment.status !== "completed",
        )
        .sort(
          (first, second) =>
            new Date(
              second.created_at,
            ).getTime() -
            new Date(
              first.created_at,
            ).getTime(),
        )[0] ?? null,
    [assessments],
  );

  async function handleCreateAssessment(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const cleanedName =
      assessmentName.trim();

    if (!cleanedName) {
      setErrorMessage(
        "Enter a name for the assessment.",
      );
      return;
    }

    const accessToken =
      localStorage.getItem(
        "safeplus_access_token",
      );

    if (!accessToken) {
      navigate("/login", {
        replace: true,
      });
      return;
    }

    try {
      setIsCreatingAssessment(true);
      setErrorMessage("");

      const newAssessment =
        await createAssessment(
          cleanedName,
          accessToken,
        );

      setAssessmentName("");
      setShowCreateForm(false);

      // Open the new assessment so its survey link can be shared.
      navigate(
        `/assessments/${newAssessment.id}`,
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to create the assessment.",
      );
    } finally {
      setIsCreatingAssessment(false);
    }
  }

  if (isLoading) {
    return (
      <main>
        <p className="text-slate-700">
          Loading dashboard...
        </p>
      </main>
    );
  }

  if (
    errorMessage &&
    !organisation
  ) {
    return (
      <main>
        <section className="mx-auto max-w-3xl rounded-xl bg-white p-8 shadow">
          <h1 className="text-2xl font-bold text-red-700">
            Session unavailable
          </h1>

          <p className="mt-3 text-slate-700">
            {errorMessage}
          </p>

          <button
            type="button"
            onClick={() =>
              navigate("/login")
            }
            className="mt-6 rounded-lg bg-cyan-700 px-4 py-2 font-semibold text-white"
          >
            Return to login
          </button>
        </section>
      </main>
    );
  }

  if (!organisation) {
    return null;
  }

  const latestCompleted =
    completedHistory.length > 0
      ? completedHistory[
          completedHistory.length - 1
        ]
      : null;

  const latestScore = latestCompleted
    ? Number(
        latestCompleted.overall_combined_mean,
      )
    : 0;

  const previousCompleted =
    completedHistory.length > 1
      ? completedHistory[
          completedHistory.length - 2
        ]
      : null;

  const firstCompleted =
    completedHistory.length > 2
      ? completedHistory[0]
      : null;

  const nextLevel = latestCompleted
    ? getNextLevel(latestScore)
    : null;

  let lastLevelMove: {
    from: string;
    to: string;
    name: string;
  } | null = null;

  for (
    let index = 1;
    index < completedHistory.length;
    index += 1
  ) {
    const previous =
      completedHistory[index - 1];
    const current = completedHistory[index];

    if (
      previous.overall_maturity_label !==
      current.overall_maturity_label
    ) {
      lastLevelMove = {
        from:
          previous.overall_maturity_label ??
          "",
        to:
          current.overall_maturity_label ?? "",
        name: current.name,
      };
    }
  }

  const trendPoints = completedHistory.map(
    (assessment) => ({
      id: assessment.id,
      label: formatShortDate(
        assessment.completed_at,
      ),
      score: Number(
        assessment.overall_combined_mean,
      ),
    }),
  );

  const latestDomainScores = [
    ...(latestScores?.domain_scores ?? []),
  ].sort(
    (first, second) =>
      first.domain_id - second.domain_id,
  );

  return (
    <main>
      <section>
        <header className="rounded-xl bg-white p-8 shadow">
          <div className="flex flex-wrap items-center justify-between gap-6">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">
                {organisation.name}
              </h1>

              <p className="mt-2 text-slate-600">
                {organisation.category}
              </p>
            </div>

            {openAssessment ? (
              <button
                type="button"
                onClick={() =>
                  navigate(
                    `/assessments/${openAssessment.id}/results`,
                  )
                }
                className="rounded-lg bg-cyan-700 px-5 py-3 font-semibold text-white hover:bg-cyan-800"
              >
                View assessment in progress
              </button>
            ) : (
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(
                    (currentValue) =>
                      !currentValue,
                  );
                  setErrorMessage("");
                }}
                aria-expanded={showCreateForm}
                className={`rounded-lg px-5 py-3 font-semibold ${
                  showCreateForm
                    ? "border border-slate-300 text-slate-700 hover:bg-slate-50"
                    : "bg-cyan-700 text-white hover:bg-cyan-800"
                }`}
              >
                {showCreateForm
                  ? "Cancel"
                  : "New assessment"}
              </button>
            )}
          </div>

          {showCreateForm && !openAssessment && (
            <form
              onSubmit={
                handleCreateAssessment
              }
              className="mt-6 rounded-xl border border-cyan-200 bg-cyan-50 p-6"
            >
              <label
                htmlFor="assessment-name"
                className="block text-sm font-semibold text-slate-900"
              >
                Name
              </label>

              <p className="mt-1 text-sm text-slate-600">
                Use a clear name you'll
                recognise later.
              </p>

              <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                <input
                  id="assessment-name"
                  type="text"
                  value={assessmentName}
                  onChange={(event) =>
                    setAssessmentName(
                      event.target.value,
                    )
                  }
                  maxLength={150}
                  autoFocus
                  placeholder="Example: 2026 Annual Safety Review"
                  className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-100"
                />

                <button
                  type="submit"
                  disabled={
                    isCreatingAssessment
                  }
                  className="rounded-lg bg-cyan-700 px-5 py-3 font-semibold text-white disabled:opacity-60"
                >
                  {isCreatingAssessment
                    ? "Creating..."
                    : "Create"}
                </button>
              </div>

              {errorMessage && (
                <p className="mt-3 text-sm text-red-700">
                  {errorMessage}
                </p>
              )}
            </form>
          )}

          {errorMessage && !showCreateForm && (
            <div className="mt-6 rounded-lg bg-red-50 p-4 text-red-700">
              {errorMessage}
            </div>
          )}
        </header>

        {/* Verification status itself is shown in the sidebar; this
            stays only while a verification link is still needed. */}
        {!organisation.is_verified && (
          <section className="mt-8 rounded-xl border border-amber-200 bg-amber-50 p-5 shadow">
            <p className="font-semibold text-amber-900">
              Verify your organisation
            </p>

            <p className="mt-1 text-sm text-amber-800">
              No email provider is configured
              for this prototype, so
              verification links are shown
              here directly instead of being
              emailed.
            </p>

            <button
              type="button"
              onClick={
                handleSendVerificationLink
              }
              disabled={
                isSendingVerification
              }
              className="mt-3 rounded-lg bg-amber-700 px-4 py-2 font-semibold text-white disabled:opacity-60"
            >
              {isSendingVerification
                ? "Generating link..."
                : "Get verification link"}
            </button>

            {verificationError && (
              <p className="mt-3 text-sm text-red-700">
                {verificationError}
              </p>
            )}

            {verificationToken && (
              <div className="mt-3 rounded-lg bg-white p-3">
                <p className="text-sm text-slate-600">
                  Verification link (valid
                  24 hours):
                </p>

                <a
                  href={`/verify?token=${encodeURIComponent(
                    verificationToken,
                  )}`}
                  className="mt-1 block break-all text-sm font-semibold text-cyan-700"
                >
                  {`${window.location.origin}/verify?token=${verificationToken}`}
                </a>
              </div>
            )}
          </section>
        )}

        {/* Where the organisation sits now and how that has changed.
            Detail about a single assessment lives on its results page. */}
        <section
          aria-labelledby="standing-heading"
          className="mt-8"
        >
          <h2
            id="standing-heading"
            className="sr-only"
          >
            Where you stand
          </h2>

          {latestCompleted ? (
            <>
              <div className="grid gap-6 lg:grid-cols-[18rem_1fr]">
                <article className="flex flex-col justify-between rounded-xl bg-white p-6 shadow">
                  <div>
                    <p className="text-sm font-semibold text-slate-500">
                      Current maturity
                    </p>

                    <p className="mt-2 text-4xl font-bold text-cyan-800">
                      {
                        latestCompleted.overall_maturity_label
                      }
                    </p>

                    <p className="mt-2 text-slate-600">
                      <span className="text-2xl font-bold text-slate-900">
                        {latestScore.toFixed(2)}
                      </span>{" "}
                      out of 5
                    </p>
                  </div>

                  <p className="mt-6 text-sm leading-6 text-slate-500">
                    From {latestCompleted.name},
                    completed{" "}
                    {formatShortDate(
                      latestCompleted.completed_at,
                    )}
                    . This only changes when an
                    assessment is completed
                    {openAssessmentCount > 0
                      ? `, so ${
                          openAssessmentCount === 1
                            ? "the open assessment is"
                            : `${openAssessmentCount} open assessments are`
                        } not counted yet.`
                      : "."}
                  </p>
                </article>

                <article className="rounded-xl bg-white p-6 shadow">
                  <p className="text-sm font-semibold text-slate-500">
                    By domain
                  </p>

                  {isLoadingLatestScores ? (
                    <p className="mt-4 text-sm text-slate-500">
                      Loading domain scores...
                    </p>
                  ) : latestDomainScores.length >
                    0 ? (
                    <div className="mt-4 space-y-6">
                      {latestDomainScores.map(
                        (domainScore) => (
                          <MaturityLadder
                            key={
                              domainScore.domain_id
                            }
                            label={getDomainName(
                              domainScore.domain_id,
                            )}
                            score={Number(
                              domainScore.combined_mean,
                            )}
                          />
                        ),
                      )}
                    </div>
                  ) : (
                    <p className="mt-4 text-sm text-slate-600">
                      {latestScoresError ||
                        "Domain scores are not available."}
                    </p>
                  )}
                </article>
              </div>

              <div className="mt-6 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
                <article className="rounded-xl bg-white p-6 shadow">
                  <h3 className="text-lg font-bold text-slate-900">
                    Overall score over time
                  </h3>

                  <ScoreTrend
                    points={trendPoints}
                  />
                </article>

                <article className="rounded-xl bg-white p-6 shadow">
                  <h3 className="text-lg font-bold text-slate-900">
                    What has changed
                  </h3>

                  <ul className="mt-4 divide-y divide-slate-100 text-slate-700">
                    {previousCompleted ? (
                      <li className="py-3 first:pt-0">
                        <span className="text-lg font-bold text-slate-900">
                          {describeScoreChange(
                            latestScore,
                            Number(
                              previousCompleted.overall_combined_mean,
                            ),
                          )}
                        </span>{" "}
                        since {previousCompleted.name}
                      </li>
                    ) : (
                      <li className="py-3 first:pt-0">
                        Change appears once a
                        second assessment is
                        completed.
                      </li>
                    )}

                    {firstCompleted && (
                      <li className="py-3">
                        <span className="text-lg font-bold text-slate-900">
                          {describeScoreChange(
                            latestScore,
                            Number(
                              firstCompleted.overall_combined_mean,
                            ),
                          )}
                        </span>{" "}
                        since the first
                        assessment,{" "}
                        {firstCompleted.name}
                      </li>
                    )}

                    {previousCompleted && (
                      <li className="py-3">
                        {lastLevelMove ? (
                          <>
                            Moved from{" "}
                            <span className="font-bold text-slate-900">
                              {lastLevelMove.from}
                            </span>{" "}
                            to{" "}
                            <span className="font-bold text-slate-900">
                              {lastLevelMove.to}
                            </span>{" "}
                            at {lastLevelMove.name}
                          </>
                        ) : (
                          <>
                            Has stayed{" "}
                            <span className="font-bold text-slate-900">
                              {
                                latestCompleted.overall_maturity_label
                              }
                            </span>{" "}
                            across all{" "}
                            {
                              completedHistory.length
                            }{" "}
                            completed assessments
                          </>
                        )}
                      </li>
                    )}

                    <li className="py-3">
                      {nextLevel ? (
                        <>
                          <span className="text-lg font-bold text-slate-900">
                            {nextLevel.gap.toFixed(
                              2,
                            )}
                          </span>{" "}
                          below {nextLevel.name}
                        </>
                      ) : (
                        "At the highest level"
                      )}
                    </li>
                  </ul>

                  <button
                    type="button"
                    onClick={() =>
                      navigate(
                        `/assessments/${latestCompleted.id}/results`,
                      )
                    }
                    className="mt-2 text-sm font-semibold text-cyan-700 underline hover:text-cyan-900"
                  >
                    See why the latest
                    assessment landed here
                  </button>
                </article>
              </div>
            </>
          ) : (
            <article className="rounded-xl bg-white p-6 shadow">
              <h3 className="text-lg font-bold text-slate-900">
                Current maturity
              </h3>

              <p className="mt-2 text-slate-600">
                Your maturity appears here once
                your first assessment is
                completed. While an assessment
                is open, only participation is
                shown.
              </p>
            </article>
          )}
        </section>

        <section
          aria-labelledby="assessments-heading"
          className="mt-8 rounded-xl bg-white p-8 shadow"
        >
          <h2
            id="assessments-heading"
            className="text-xl font-bold text-slate-900"
          >
            Assessments
          </h2>

          {assessments.length === 0 ? (
            <p className="mt-4 text-slate-600">
              No assessments yet. Use New
              assessment above to start one.
            </p>
          ) : (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[40rem] text-left">
                <thead>
                  <tr className="border-b border-slate-200 text-sm text-slate-500">
                    <th
                      scope="col"
                      className="py-3 pr-4 font-semibold"
                    >
                      Completed
                    </th>

                    <th
                      scope="col"
                      className="py-3 pr-4 font-semibold"
                    >
                      Assessment
                    </th>

                    <th
                      scope="col"
                      className="py-3 pr-4 font-semibold"
                    >
                      Overall score
                    </th>

                    <th
                      scope="col"
                      className="py-3 pr-4 font-semibold"
                    >
                      Maturity
                    </th>

                    <th
                      scope="col"
                      className="py-3 font-semibold"
                    >
                      <span className="sr-only">
                        Actions
                      </span>
                    </th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-100">
                  {sortAssessmentsForTable(
                    assessments,
                  ).map((assessment) => {
                    const isCompleted =
                      assessment.status ===
                      "completed";

                    return (
                      <tr
                        key={assessment.id}
                        className="text-slate-700"
                      >
                        <td className="py-4 pr-4">
                          {isCompleted ? (
                            formatShortDate(
                              assessment.completed_at,
                            )
                          ) : (
                            <>
                              <span className="block">
                                {assessment.status ===
                                "draft"
                                  ? "Draft"
                                  : "In progress"}
                              </span>

                              <span className="block text-sm text-slate-500">
                                {assessment.status ===
                                "draft"
                                  ? "Created"
                                  : "Opened"}{" "}
                                {formatShortDate(
                                  assessment.created_at,
                                )}
                              </span>
                            </>
                          )}
                        </td>

                        <td className="py-4 pr-4">
                          {assessment.name}
                        </td>

                        <td className="py-4 pr-4">
                          {isCompleted ? (
                            <span className="font-bold text-slate-900">
                              {Number(
                                assessment.overall_combined_mean,
                              ).toFixed(2)}
                            </span>
                          ) : (
                            "Locked"
                          )}
                        </td>

                        <td className="py-4 pr-4">
                          {isCompleted &&
                          assessment.overall_maturity_label ? (
                            <span
                              className={`inline-block rounded-md px-2.5 py-1 text-sm font-semibold ${getMaturityBadgeClasses(
                                assessment.overall_maturity_label,
                              )}`}
                            >
                              {
                                assessment.overall_maturity_label
                              }
                            </span>
                          ) : (
                            <span className="text-slate-600">
                              Available when
                              completed
                            </span>
                          )}
                        </td>

                        <td className="py-4">
                          <button
                            type="button"
                            onClick={() =>
                              navigate(
                                `/assessments/${assessment.id}/results`,
                              )
                            }
                            className="font-semibold text-cyan-700 underline hover:text-cyan-900"
                          >
                            {isCompleted
                              ? "Open"
                              : "View progress"}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

export default AccountPage;