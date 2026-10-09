# Data Handling and Privacy

What the platform stores, and what it does not. Derived from the models in
`backend/app/models/`.

## Survey respondent anonymity

The public survey tells respondents their answers are anonymous
(`frontend/src/features/survey/PublicSurveyStartPage.tsx`). The data model
supports that claim.

**`survey_submission`** stores only:

| Field | Purpose |
|-------|---------|
| `id` | Primary key |
| `assessment_id` | Which assessment |
| `access_token` | Random token identifying the submission |
| `respondent_group` | `Employee` or `Senior Manager` |
| `status` | Progress state |
| `started_at`, `submitted_at` | Timestamps |

**`individual_response`** stores only a submission reference, a question
reference, and the chosen option.

**No name, email address, IP address, employee ID, job title or device
identifier is collected or stored for any survey respondent.** Submissions are
pseudonymous: the access token lets a respondent resume their own
part-finished survey, and is the only handle on a submission.

Respondent group is recorded because the entire method rests on comparing the
two groups - but it is the only respondent attribute held.

### Residual re-identification risk

Worth acknowledging honestly in any write-up: in a very small organisation, or
a group with few respondents, response patterns combined with group
membership and submission timestamps could in principle narrow identity. This
is inherent to small-sample survey work, not a defect in the data model.
Consider a minimum-responses threshold before reporting group-level results.

## Organisation accounts

**`organisation`** stores: name, industry category, email address, Argon2
password hash, verification state and token, and creation timestamp.

- Passwords are hashed with **Argon2** via `pwdlib` - never stored or logged
  in plain text
- Authentication uses **JWT bearer tokens**, default expiry 60 minutes
  (`ACCESS_TOKEN_EXPIRE_MINUTES`)
- The signing secret comes from `JWT_SECRET` and is never committed

## Email verification

No email provider is configured in this prototype. Verification tokens are
generated with `secrets.token_urlsafe(32)` and **returned in the API response**
rather than emailed - the documented NFR11 email-failure fallback, surfaced to
the user as such.

Note that login does not currently require a verified account.

## Secrets

Nothing sensitive is committed. `.gitignore` excludes all `.env` files;
`backend/.env.example` ships with placeholder values only. Three secrets are
required at runtime:

| Secret | Used for |
|--------|----------|
| `DATABASE_URL` | Contains the PostgreSQL password |
| `JWT_SECRET` | Signs authentication tokens |
| `GEMINI_API_KEY` | Google Gemini access (optional) |

## Data sent to third parties

The AI analysis sends assessment data to **Google Gemini**. What leaves the
system: the organisation name and category, domain and question scores,
question wording, opinion gaps and intervention tiers.

**Individual survey responses are never transmitted** - only aggregate
statistics. No respondent-identifying data exists to send.

Note for any privacy assessment: the organisation's name and its health and
safety performance scores do leave New Zealand infrastructure when AI analysis
is generated. Running an assessment without a configured API key avoids this
entirely.

## Test data isolation

Tests redirect to a separate `safeplus_test` database, create it
automatically, and assert they are not pointed at the configured development
database (`backend/tests/conftest.py`). Running the suite cannot affect real
data.

## Not implemented

Gaps to note as future work rather than defects:

- No data retention or deletion policy; no respondent data export
- No audit log of who viewed or downloaded which report
- No rate limiting on the public survey endpoints
- No user-facing privacy statement beyond the anonymity note on the survey
  start page
- No HTTPS enforcement (appropriate for local development; required before
  any real deployment)

## Ethics approval

**TO BE COMPLETED.** If this project involved human participants under AUTEC
approval, record the approval number, scope and conditions here.
