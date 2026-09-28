import {
  useEffect,
  useState,
} from "react";
import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";
import {
  type AIAnalysis,
  generateAIAnalysis,
  getAIAnalysis,
} from "../../api/aiAnalysisApi";
import {
  type Assessment,
  type AssessmentCompletionResult,
  type AssessmentScoringResult,
  type AssessmentSetupQuestion,
  calculateAssessmentScores,
  completeAssessment,
  deleteAssessment,
  downloadAssessmentReport,
  downloadBoardReport,
  downloadBusinessLeaderReport,
  downloadOperationalManagerReport,
  getAssessment,
  getAssessmentQuestions,
  updateQuestionSelection,
} from "../../api/assessmentsApi";
import { getCurrentOrganisation } from "../../api/authApi";
import { getSubmissionSummary } from "../../api/submissionSummaryApi";
import { useConfirm } from "../../components/useConfirm";
import {
  completeConfirmMessage,
  deleteConfirmMessage,
  type EntryTotals,
  fetchEntryTotals,
  MINIMUM_RESPONSES,
  tooFewResponsesMessage,
} from "./assessmentCompletion";
import PendingHeader from "./results/PendingHeader";
import ActionBar from "./results/ActionBar";
import ResultsHeader from "./results/ResultsHeader";
import SetupPanel from "./results/SetupPanel";
import OverviewGrid from "./results/OverviewGrid";
import QuestionResultsSection from "./results/QuestionResultsSection";
import AiAnalysisSection from "./results/AiAnalysisSection";
import {
  type DomainQuestionGroup,
  type DomainWorking,
  getQuestionDomainId,
  getQuestionStatusLabel,
  isHighOverride,
  type Participation,
  type ProfilePoint,
  type QuestionResultFilter,
  type ReportType,
} from "./results/resultsHelpers";

function AssessmentResultsPage() {
  const navigate = useNavigate();
  const { assessmentId } = useParams();

  const { choose, confirm, dialog } =
    useConfirm();

  const numericAssessmentId =
    Number(assessmentId);

  const [
    assessment,
    setAssessment,
  ] = useState<Assessment | null>(
    null,
  );

  const [results, setResults] =
    useState<AssessmentScoringResult | null>(
      null,
    );

  const [
    completionResult,
    setCompletionResult,
  ] =
    useState<AssessmentCompletionResult | null>(
      null,
    );

  const [
    aiAnalysis,
    setAIAnalysis,
  ] = useState<AIAnalysis | null>(
    null,
  );

  const [
    isLoadingPage,
    setIsLoadingPage,
  ] = useState(true);

  const [
    isCompleting,
    setIsCompleting,
  ] = useState(false);

  const [
    isGeneratingAnalysis,
    setIsGeneratingAnalysis,
  ] = useState(false);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState("");

  const [
    analysisMessage,
    setAnalysisMessage,
  ] = useState("");

  // Generation errors are shown in the AI section, next to the button.
  const [
    analysisError,
    setAnalysisError,
  ] = useState("");

  const [
    participation,
    setParticipation,
  ] = useState<Participation | null>(
    null,
  );

  const [
    organisationName,
    setOrganisationName,
  ] = useState("");

  const [
    selectedOptionalIds,
    setSelectedOptionalIds,
  ] = useState<number[]>([]);

  const [
    isSavingSelection,
    setIsSavingSelection,
  ] = useState(false);

  const [
    selectionMessage,
    setSelectionMessage,
  ] = useState("");

  const [
    entryTotals,
    setEntryTotals,
  ] = useState<EntryTotals | null>(null);

  const [
    questionResultFilter,
    setQuestionResultFilter,
  ] = useState<QuestionResultFilter>(
    "All",
  );

  const isAssessmentCompleted =
    assessment?.status === "completed" ||
    completionResult?.status ===
      "completed";

  const domainData =
    aiAnalysis?.domain_summaries;

  const keyStrengths =
    domainData?.key_strengths ?? [];

  const keyRisks =
    domainData?.key_risks ?? [];

  const aiDomainSummaries =
    domainData?.domains ?? [];

  const guidanceSources =
    domainData?.guidance_sources ?? [];

  const limitations =
    domainData?.limitations ?? [];

  const priorityActions =
    aiAnalysis?.priority_actions ?? [];

  const roadmap =
    aiAnalysis?.roadmap ?? [];

  const scoredQuestions = [
    ...(results?.question_scores ?? []),
  ].sort((first, second) =>
    first.question_number.localeCompare(
      second.question_number,
      undefined,
      { numeric: true },
    ),
  );

  // Split questions are left out: their combined mean is hidden
  // because it would mask opposing perceptions.
  const comparableScores = scoredQuestions
    .filter(
      (questionScore) =>
        !isHighOverride(
          questionScore.opinion_gap,
        ),
    )
    .map((questionScore) =>
      Number(questionScore.combined_mean),
    );

  const lowestScore =
    comparableScores.length > 0
      ? Math.min(...comparableScores)
      : null;

  const lowestQuestionIds = new Set(
    scoredQuestions
      .filter(
        (questionScore) =>
          !isHighOverride(
            questionScore.opinion_gap,
          ) &&
          Number(
            questionScore.combined_mean,
          ) === lowestScore,
      )
      .map(
        (questionScore) =>
          questionScore.question_id,
      ),
  );

  const profilePoints: ProfilePoint[] =
    scoredQuestions.map((questionScore) => ({
      questionId: questionScore.question_id,
      questionNumber:
        questionScore.question_number,
      domainId: getQuestionDomainId(
        questionScore.question_number,
      ),
      score: Number(
        questionScore.combined_mean,
      ),
      employeeMean: Number(
        questionScore.employee_mean,
      ),
      managerMean: Number(
        questionScore.manager_mean,
      ),
      opinionGap: Number(
        questionScore.opinion_gap,
      ),
      isSplit: isHighOverride(
        questionScore.opinion_gap,
      ),
      isLowest: lowestQuestionIds.has(
        questionScore.question_id,
      ),
    }));

  const sortedDomainScores = [
    ...(results?.domain_scores ?? []),
  ].sort(
    (first, second) =>
      first.domain_id - second.domain_id,
  );

  const domainWorkings: DomainWorking[] =
    sortedDomainScores.map((domainScore) => {
      const domainQuestions =
        scoredQuestions.filter(
          (questionScore) =>
            getQuestionDomainId(
              questionScore.question_number,
            ) === domainScore.domain_id,
        );

      return {
        domainId: domainScore.domain_id,
        count: domainQuestions.length,
        total: domainQuestions.reduce(
          (total, questionScore) =>
            total +
            Number(
              questionScore.combined_mean,
            ),
          0,
        ),
        mean: Number(
          domainScore.combined_mean,
        ),
      };
    });

  const overallScore =
    results &&
    results.overall_combined_mean !== null
      ? Number(results.overall_combined_mean)
      : null;

  // Questions grouped by domain, in question-number order, for the
  // open assessment. Required questions are always included; optional
  // (situation-dependent) ones can be ticked in or out.
  const domainQuestionGroups: DomainQuestionGroup[] = (() => {
    if (!participation) {
      return [];
    }

    const groups = new Map<
      string,
      AssessmentSetupQuestion[]
    >();

    [...participation.questions]
      .sort((first, second) =>
        first.question_number.localeCompare(
          second.question_number,
          undefined,
          { numeric: true },
        ),
      )
      .forEach((question) => {
        const list =
          groups.get(question.domain_name) ??
          [];

        list.push(question);
        groups.set(question.domain_name, list);
      });

    return [...groups.entries()].map(
      ([name, questions]) => ({
        name,
        questions,
      }),
    );
  })();

  const savedOptionalIds = participation
    ? participation.questions
        .filter(
          (question) =>
            question.is_situation_dependent &&
            question.is_active,
        )
        .map((question) => question.question_id)
    : [];

  const hasSelectionChanges =
    savedOptionalIds.length !==
      selectedOptionalIds.length ||
    savedOptionalIds.some(
      (questionId) =>
        !selectedOptionalIds.includes(
          questionId,
        ),
    );

  const filteredQuestionScores =
    results?.question_scores.filter(
      (questionScore) => {
        if (
          questionResultFilter === "All"
        ) {
          return true;
        }

        return (
          getQuestionStatusLabel(
            questionScore.intervention_tier,
            questionScore.opinion_gap,
          ) === questionResultFilter
        );
      },
    ) ?? [];

  const reportOptions: {
    type: ReportType;
    label: string;
  }[] = [
    { type: "full", label: "Full report" },
    {
      type: "business-leader",
      label: "Business leader",
    },
    { type: "board", label: "Board" },
    {
      type: "operational-manager",
      label: "Operational manager",
    },
  ];

  // Which download is being prepared, e.g. "board-ai", so only that
  // button shows "Preparing...".
  const [
    downloadingReport,
    setDownloadingReport,
  ] = useState<string | null>(null);

  const [
    isReportMenuOpen,
    setIsReportMenuOpen,
  ] = useState(false);

  // Links to parts of the AI analysis appear in the navigation bar
  // once the user jumps to it.
  const [showAiLinks, setShowAiLinks] =
    useState(false);

  // Close the download menu on Escape or a click outside it.
  useEffect(() => {
    if (!isReportMenuOpen) {
      return;
    }

    function handleKeyDown(
      event: KeyboardEvent,
    ) {
      if (event.key === "Escape") {
        setIsReportMenuOpen(false);
      }
    }

    function handlePointerDown(
      event: MouseEvent,
    ) {
      if (
        !(event.target instanceof Element) ||
        !event.target.closest(
          "[data-report-menu]",
        )
      ) {
        setIsReportMenuOpen(false);
      }
    }

    document.addEventListener(
      "keydown",
      handleKeyDown,
    );
    document.addEventListener(
      "mousedown",
      handlePointerDown,
    );

    return () => {
      document.removeEventListener(
        "keydown",
        handleKeyDown,
      );
      document.removeEventListener(
        "mousedown",
        handlePointerDown,
      );
    };
  }, [isReportMenuOpen]);

  useEffect(() => {
    async function loadPage() {
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

      if (
        !Number.isInteger(
          numericAssessmentId,
        ) ||
        numericAssessmentId <= 0
      ) {
        setErrorMessage(
          "Invalid assessment ID.",
        );

        setIsLoadingPage(false);
        return;
      }

      try {
        setErrorMessage("");

        const assessmentResult =
          await getAssessment(
            numericAssessmentId,
            accessToken,
          );

        setAssessment(assessmentResult);

        if (
          assessmentResult.status ===
          "completed"
        ) {
          const [
            scoringResult,
            savedAnalysis,
            totals,
          ] = await Promise.all([
            calculateAssessmentScores(
              numericAssessmentId,
              accessToken,
            ),
            getAIAnalysis(
              numericAssessmentId,
              accessToken,
            ),
            fetchEntryTotals(
              numericAssessmentId,
              accessToken,
            ),
          ]);

          setResults(scoringResult);
          setAIAnalysis(savedAnalysis);
          setEntryTotals(totals);
        } else {
          // Open assessments show participation only. Scores are
          // never requested, so none reach the browser.
          const [
            organisation,
            summary,
            questions,
          ] = await Promise.all([
            getCurrentOrganisation(
              accessToken,
            ),
            getSubmissionSummary(
              numericAssessmentId,
              accessToken,
            ),
            getAssessmentQuestions(
              numericAssessmentId,
              accessToken,
            ),
          ]);

          setOrganisationName(
            organisation.name,
          );

          setParticipation({
            summary,
            questions,
          });

          setSelectedOptionalIds(
            questions
              .filter(
                (question) =>
                  question.is_situation_dependent &&
                  question.is_active,
              )
              .map(
                (question) =>
                  question.question_id,
              ),
          );
        }
      } catch (error) {
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Unable to load assessment results.",
        );
      } finally {
        setIsLoadingPage(false);
      }
    }

    void loadPage();
  }, [
    navigate,
    numericAssessmentId,
  ]);

  function toggleOptionalQuestion(
    questionId: number,
  ) {
    setSelectionMessage("");

    setSelectedOptionalIds((currentIds) =>
      currentIds.includes(questionId)
        ? currentIds.filter(
            (id) => id !== questionId,
          )
        : [...currentIds, questionId],
    );
  }

  async function handleSaveQuestionSelection() {
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

    if (!participation) {
      return;
    }

    const removedCount = savedOptionalIds.filter(
      (questionId) =>
        !selectedOptionalIds.includes(
          questionId,
        ),
    ).length;

    if (
      removedCount > 0 &&
      participation.summary.submitted_total > 0
    ) {
      const confirmed = await confirm(
        `Remove ${removedCount} optional ${
          removedCount === 1
            ? "question"
            : "questions"
        }?\n\nAny responses already given to ${
          removedCount === 1 ? "it" : "them"
        } will be deleted.`,
      );

      if (!confirmed) {
        return;
      }
    }

    try {
      setIsSavingSelection(true);
      setErrorMessage("");
      setSelectionMessage("");

      const updatedQuestions =
        await updateQuestionSelection(
          numericAssessmentId,
          selectedOptionalIds,
          accessToken,
        );

      setParticipation((current) =>
        current
          ? {
              ...current,
              questions: updatedQuestions,
            }
          : current,
      );

      setSelectedOptionalIds(
        updatedQuestions
          .filter(
            (question) =>
              question.is_situation_dependent &&
              question.is_active,
          )
          .map(
            (question) =>
              question.question_id,
          ),
      );

      setSelectionMessage(
        "Question selection saved.",
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to save the question selection.",
      );
    } finally {
      setIsSavingSelection(false);
    }
  }

  // Offered when an assessment has too few responses to complete.
  async function handleDeleteAssessment() {
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

    const confirmed = await confirm(
      deleteConfirmMessage(assessment?.name),
      {
        confirmLabel: "Delete",
      },
    );

    if (!confirmed) {
      return;
    }

    try {
      setErrorMessage("");

      await deleteAssessment(
        numericAssessmentId,
        accessToken,
      );

      navigate("/account", {
        replace: true,
      });
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to delete the assessment.",
      );
    }
  }

  async function handleCompleteAssessment() {
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

    let totals: EntryTotals;

    try {
      setErrorMessage("");

      totals = await fetchEntryTotals(
        numericAssessmentId,
        accessToken,
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to check how many responses this assessment has.",
      );

      return;
    }

    const responseTotal =
      totals.online + totals.paper;

    if (responseTotal < MINIMUM_RESPONSES) {
      const choice = await choose(
        tooFewResponsesMessage(totals),
        {
          confirmLabel: "OK",
          showCancel: false,
          extraLabel: "Delete assessment",
        },
      );

      if (choice === "extra") {
        await handleDeleteAssessment();
      }

      return;
    }

    const confirmed = await confirm(
      completeConfirmMessage(totals),
    );

    if (!confirmed) {
      return;
    }

    try {
      setIsCompleting(true);
      setErrorMessage("");
      setAnalysisMessage("");

      const completedAssessment =
        await completeAssessment(
          numericAssessmentId,
          accessToken,
        );

      setCompletionResult(
        completedAssessment,
      );

      const scoringResult =
        await calculateAssessmentScores(
          numericAssessmentId,
          accessToken,
        );

      setResults(scoringResult);

      const updatedAssessment =
        await getAssessment(
          numericAssessmentId,
          accessToken,
        );

      setAssessment(
        updatedAssessment,
      );

      setEntryTotals(
        await fetchEntryTotals(
          numericAssessmentId,
          accessToken,
        ),
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to complete the assessment.",
      );
    } finally {
      setIsCompleting(false);
    }
  }

  async function handleGenerateAIAnalysis() {
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

    if (!isAssessmentCompleted) {
      setErrorMessage(
        "Complete the assessment before generating AI analysis.",
      );

      return;
    }

    const confirmed = await confirm(
      aiAnalysis
        ? "Regenerate the AI analysis? The existing saved analysis will be replaced."
        : "Generate an AI analysis using the assessment results and curated WorkSafe SafePlus guidance?",
    );

    if (!confirmed) {
      return;
    }

    try {
      setIsGeneratingAnalysis(true);
      setErrorMessage("");
      setAnalysisMessage("");
      setAnalysisError("");

      const generatedAnalysis =
        await generateAIAnalysis(
          numericAssessmentId,
          accessToken,
        );

      setAIAnalysis(
        generatedAnalysis,
      );

      setAnalysisMessage(
        generatedAnalysis.message,
      );
    } catch (error) {
      setAnalysisError(
        error instanceof Error
          ? error.message
          : "Unable to generate AI analysis.",
      );
    } finally {
      setIsGeneratingAnalysis(false);
    }
  }

  async function handleDownloadReport(
    reportType: ReportType,
    includeAi: boolean,
  ) {
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

    const downloadByType: Record<
      ReportType,
      (
        assessmentId: number,
        includeAi: boolean,
        accessToken: string,
      ) => Promise<void>
    > = {
      full: downloadAssessmentReport,
      "business-leader":
        downloadBusinessLeaderReport,
      board: downloadBoardReport,
      "operational-manager":
        downloadOperationalManagerReport,
    };

    try {
      setDownloadingReport(
        `${reportType}-${includeAi ? "ai" : "review"}`,
      );
      setErrorMessage("");
      setAnalysisMessage("");

      await downloadByType[reportType](
        numericAssessmentId,
        includeAi,
        accessToken,
      );

      setIsReportMenuOpen(false);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to download the PDF report.",
      );
    } finally {
      setDownloadingReport(null);
    }
  }

  if (isLoadingPage) {
    return (
      <main>
        <p className="text-slate-700">
          Loading assessment results...
        </p>
      </main>
    );
  }

  // Without the assessment we can't tell whether it is open or closed,
  // so show the reason rather than guessing a layout.
  if (!assessment) {
    return (
      <main>
        <section className="mx-auto max-w-3xl rounded-xl bg-white p-8 shadow">
          <h1 className="text-2xl font-bold text-slate-900">
            Assessment unavailable
          </h1>

          <p className="mt-3 text-slate-700">
            {errorMessage ||
              "This assessment could not be loaded."}
          </p>

          <Link
            to="/account"
            className="mt-6 inline-block font-semibold text-cyan-700 underline hover:text-cyan-900"
          >
            Back to dashboard
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main>
      {dialog}

      <section>
        {!isAssessmentCompleted && (
          <PendingHeader
            assessment={assessment}
            errorMessage={errorMessage}
            handleCompleteAssessment={handleCompleteAssessment}
            isCompleting={isCompleting}
            numericAssessmentId={numericAssessmentId}
            organisationName={organisationName}
          />
        )}

        {/* Stays at the top of the content area while scrolling, beside
            the sidebar whether it is expanded or collapsed. */}
        {isAssessmentCompleted && (
          <ActionBar
            aiAnalysis={aiAnalysis}
            assessment={assessment}
            downloadingReport={downloadingReport}
            errorMessage={errorMessage}
            handleDownloadReport={handleDownloadReport}
            isReportMenuOpen={isReportMenuOpen}
            reportOptions={reportOptions}
            setIsReportMenuOpen={setIsReportMenuOpen}
            setShowAiLinks={setShowAiLinks}
            showAiLinks={showAiLinks}
          />
        )}

        {isAssessmentCompleted && (
          <ResultsHeader
            assessment={assessment}
            completionResult={completionResult}
            entryTotals={entryTotals}
            errorMessage={errorMessage}
          />
        )}

        {!isAssessmentCompleted ? (
          <>
            <SetupPanel
              domainQuestionGroups={domainQuestionGroups}
              handleSaveQuestionSelection={handleSaveQuestionSelection}
              hasSelectionChanges={hasSelectionChanges}
              isSavingSelection={isSavingSelection}
              participation={participation}
              selectedOptionalIds={selectedOptionalIds}
              selectionMessage={selectionMessage}
              toggleOptionalQuestion={toggleOptionalQuestion}
            />
          </>
        ) : !results ? (
          <section className="mt-8 rounded-xl bg-white p-8 text-center shadow">
            <h2 className="text-xl font-bold text-slate-900">
              Results are not available
            </h2>

            <p className="mt-2 text-slate-600">
              The scores for this assessment
              could not be loaded. Refresh the
              page to try again.
            </p>
          </section>
        ) : (
          <>
            {/* Left: question profile. Right: overall result above
                domain scores, which fills the rest of the column. */}
            <OverviewGrid
              lowestQuestionIds={lowestQuestionIds}
              overallScore={overallScore}
              profilePoints={profilePoints}
              results={results}
              scoredQuestions={scoredQuestions}
              sortedDomainScores={sortedDomainScores}
            />

            <QuestionResultsSection
              domainWorkings={domainWorkings}
              filteredQuestionScores={filteredQuestionScores}
              lowestQuestionIds={lowestQuestionIds}
              overallScore={overallScore}
              questionResultFilter={questionResultFilter}
              results={results}
              setQuestionResultFilter={setQuestionResultFilter}
            />
          </>
        )}

        {/* AI content stays visually separate from calculated
            results and only reaches a report when a person includes it. */}
        {isAssessmentCompleted && (
          <AiAnalysisSection
            aiAnalysis={aiAnalysis}
            aiDomainSummaries={aiDomainSummaries}
            analysisError={analysisError}
            analysisMessage={analysisMessage}
            guidanceSources={guidanceSources}
            handleGenerateAIAnalysis={handleGenerateAIAnalysis}
            isCompleting={isCompleting}
            isGeneratingAnalysis={isGeneratingAnalysis}
            keyRisks={keyRisks}
            keyStrengths={keyStrengths}
            limitations={limitations}
            priorityActions={priorityActions}
            roadmap={roadmap}
          />
        )}

      </section>
    </main>
  );
}

export default AssessmentResultsPage;