# Requirements Traceability

The codebase cites requirement identifiers in comments and test docstrings.
This index records where, so a reviewer can move between the requirements
specification and the implementation.

## Status

**Incomplete - the requirements specification is not in this repository.**
Either add it under `docs/`, or link to it here. The references below are
currently dangling: a reader can see that `NFR11` is satisfied somewhere but
cannot read what `NFR11` requires.

## Referenced in code

| ID | Location | Context |
|----|----------|---------|
| `NFR02` | `backend/tests/test_system_performance.py:1` | Performance test suite |
| `NFR11` | `backend/app/api/routes/auth.py:261` | Email-failure fallback - verification link returned in the API response when no email provider is configured |
| `NFR11` | `backend/tests/test_system_errors.py:1` | Error-handling test suite |

Only these two identifiers appear in the codebase.

## Suggested next step

Most requirements are implemented but uncited. Completing this table - one row
per requirement, pointing at the code and the test that covers it - is a
high-value, low-effort addition for an R&D deliverable, since it demonstrates
coverage directly. A starting map:

| Area | Implementation | Tests |
|------|---------------|-------|
| Scoring | `backend/app/services/scoring.py` | `tests/test_unit_scoring.py` |
| Priority actions | `backend/app/services/priority_actions.py` | `tests/test_unit_priority.py` |
| Authentication | `backend/app/core/security.py`, `api/routes/auth.py` | `tests/test_unit_auth.py` |
| Report content | `backend/app/services/reports/` | `tests/test_system_report_content.py`, `test_unit_report_components.py` |
| AI analysis | `backend/app/services/gemini_analysis.py` | `tests/test_system_ai_consistency.py` |
| End-to-end flow | - | `tests/test_system_e2e.py` |
| Error handling | - | `tests/test_system_errors.py` |
| Performance | - | `tests/test_system_performance.py` |
