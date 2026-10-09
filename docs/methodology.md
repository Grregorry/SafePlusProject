# Scoring and Analysis Methodology

How the platform turns survey responses into maturity scores and
recommendations. Derived from the implementation in
`backend/app/services/scoring.py`, `priority_actions.py` and
`gemini_analysis.py`.

## The question set

49 questions across three domains, seeded by migration
`d1b18544226d_seed_safeplus_question_set`:

| Domain | Questions | Numbering |
|--------|-----------|-----------|
| Leadership | 12 | 1.1 - 1.12 |
| Worker Engagement | 7 | 2.1 - 2.7 |
| Risk Management | 30 | 3.1 - 3.30 |

Of these, **32 are compulsory** and **17 are situation-dependent** (relevant
only to some organisations, and able to be deactivated per assessment).

Every question is worded twice - `employee_text` and `manager_text` - so the
same underlying construct is asked appropriately of each audience.

> **Provenance note:** the question set and the guidance content derive from
> WorkSafe New Zealand's published SafePlus framework. Add the specific source
> and permissions here once confirmed with the client and supervisor.

## Response scale

Five-point Likert, plus a non-scoring option:

| Response | Value |
|----------|-------|
| Strongly Agree | 5 |
| Agree | 4 |
| Neither Agree nor Disagree | 3 |
| Disagree | 2 |
| Strongly Disagree | 1 |
| N/A | *excluded* |

`N/A` is removed from both the numerator and the denominator, so it lowers
the response count rather than pulling the mean toward the middle.

## Respondent groups

Two: **Employee** and **Senior Manager**. Comparing them is central to the
method - the divergence between how leaders and workers perceive the same
practice is treated as a finding in its own right.

Responses arrive two ways and are pooled before scoring:

- **Digital** - individual anonymous submissions via a public survey link
- **Manual** - aggregate counts entered for paper-based surveys

## Per-question scoring

For each active question:

1. **Group means** - the weighted mean of valid responses, per group.
2. **Combined mean** - `(employee_mean + manager_mean) / 2`
3. **Opinion gap** - `|employee_mean - manager_mean|`

All values are rounded to **two decimal places, half-up**.

> **Methodological choice worth noting:** the combined mean is the unweighted
> average *of the two group means*, not a pooled mean of all responses. Each
> group therefore carries equal weight regardless of how many people are in
> it - five managers count as much as eighty employees. This is deliberate:
> it prevents the larger workforce from masking a leadership blind spot. It
> also means small manager samples carry significant influence, which is a
> limitation worth stating in any write-up.

**A question is only scored when both groups have at least one valid
response.** Questions answered by only one group are skipped entirely rather
than scored on partial data.

## Maturity levels

Applied identically to question, domain and overall means:

| Combined mean | Level |
|---------------|-------|
| <= 2.50 | Developing |
| > 2.50 and < 4.50 | Performing |
| >= 4.50 | Leading |

Because scores are stored to two decimals, Performing begins at 2.51.

Defined in `get_maturity_level()` and mirrored in the frontend at
`frontend/src/components/maturity.ts` - **the two must stay in sync.**

## Domain and overall scores

- **Domain score** - the mean of the combined means of that domain's scored
  questions. Note this is a mean *of question scores*, so each question
  contributes equally regardless of how many people answered it.
- **Overall score** - the mean of the three domain scores, **set only when
  all three domains have a score**. A partially completed assessment has no
  overall maturity level rather than a misleading one.

## Intervention tiers

Each scored question is assigned a tier combining *how low* the score is with
*how much the two groups disagree*. Rules are evaluated in order; the first
match wins.

| # | Condition | Tier |
|---|-----------|------|
| 1 | gap >= 3.00 | **High** |
| 2 | mean <= 2.50 and gap > 1.50 | **High** |
| 3 | mean <= 2.50 | **Medium** |
| 4 | mean <= 3.50 and gap > 1.50 | **Medium** |
| 5 | mean <= 3.50 | **Low** |
| 6 | mean < 4.50 and gap > 1.50 | **Low** |
| 7 | otherwise | Not flagged |

The design intent: a very large gap (rule 1) is escalated on its own, even
where the average looks healthy, because it indicates leadership and workers
hold incompatible views of the same practice. Rule 6 likewise flags a
well-scoring question where the groups still disagree substantially.

## Priority actions

Candidates are every question tiered High, Medium or Low, ranked by:

1. Tier severity (High first)
2. Combined mean, **ascending** (weakest first)
3. Opinion gap, **descending** (greatest disagreement first)

The top **five** are passed to the AI layer. Selection is entirely
deterministic - the AI receives a fixed shortlist and writes narrative for it.
It cannot choose which issues are prioritised.

## AI analysis

Google Gemini (`gemini-2.5-flash` by default), with these constraints:

- **Temperature 0.2** - low variability, for reproducibility
- **Structured JSON output** enforced by a response schema, not free text
- **Curated sources only** - the prompt supplies a fixed set of WorkSafe
  SafePlus guidance entries, each with a `source_id`
- **Citation validation** - `validate_source_ids()` rejects any citation not
  in the supplied set, and `validate_priority_action_question_ids()` rejects
  any action attached to a question not on the shortlist

Those last two are the substantive safeguard: the model cannot invent a
guidance reference or redirect a recommendation onto a question the scoring
logic did not flag.

**Stated limitations** (`SAFEPLUS_AI_LIMITATIONS` in
`backend/app/data/safeplus_guidance.py`) are carried through to the reports:
the analysis is decision support, not legal advice, cannot determine legal
compliance, and does not replace a qualified SafePlus onsite assessment.

The platform scores and reports normally when no API key is configured; only
the AI section is unavailable.

## Reports

Four PDF outputs, generated with ReportLab:

| Report | Endpoint |
|--------|----------|
| Full | `GET /api/assessments/{id}/report` |
| Business leader | `GET /api/assessments/{id}/report/business-leader` |
| Board | `GET /api/assessments/{id}/report/board` |
| Operational manager | `GET /api/assessments/{id}/report/operational-manager` |

Each presents the same underlying scores at the altitude its audience needs.
