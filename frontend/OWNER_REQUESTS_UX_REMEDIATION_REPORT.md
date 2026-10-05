# Owner Acceptance Requests UX remediation

Branch: `frontend/v1`. Base checkpoint: `14a9a580090df9be778a104b035712832cf27608`, verified at HEAD before implementation. Scope is Service Requests only and the minimum Request API validation. Manual Requests acceptance results are retained; Work Orders Owner Acceptance testing has not started.

## Exact files changed

- `backend/schemas/service_request.py`: canonical create/PATCH priority and status validators, blank-title rejection and explicit-null Customer PATCH rejection; legacy-compatible read schema remains unrestricted.
- `frontend/src/features/phase3/request-values.ts`: Request canonical choices and a pure case-equivalent display/filter helper.
- `frontend/src/features/phase3/editor.tsx`: Requests-only dropdowns, explicit legacy replacement tracking, safe PATCH omission, accessible Customer/Title inline validation.
- `frontend/src/features/phase3/screens.tsx`: Requests-only display casing, canonical status filters plus discoverable unknown legacy statuses, stable status-filter accessible label.
- `tests/test_request_editor_contract.py`: nine focused API contract tests on temporary SQLite.
- `frontend/tests/phase3/requests-ux.spec.ts`: three Requests browser journeys, one each for desktop, 390px and RTL, using a generated PostgreSQL fixture.
- `frontend/OWNER_REQUESTS_UX_REMEDIATION_REPORT.md`: this report.

## Priority and Status

New Request Priority is a real select with exactly Low / Normal / High / Urgent, default Normal. New Request Status is a real select with exactly Open / In Progress / Resolved / Closed / Cancelled, default Open. Canonical stored values select the corresponding edit option.

For a noncanonical stored value, the editor adds one disabled current-value option showing both its recognizable display casing and exact stored value, for example `Current: High (stored as "high")`. Unknown values are displayed honestly in the same current-value path. The canonical replacement options remain available. A distinct current-value option permits explicitly choosing High even when the stored spelling was high; no change is inferred merely from opening the editor.

The editor records whether Priority or Status was actually selected. Untouched fields are omitted from PATCH, including on unrelated edits to legacy records. Choosing a canonical replacement submits that canonical spelling. Display and filters recognize case-only equivalents without modifying the database. The Requests filter always includes the five canonical statuses; unknown existing statuses appear as `Legacy: <stored value>`, and All statuses remains available. Backend filtering semantics were not changed.

## Backend enforcement and inline errors

ServiceRequestCreate and supplied fields in ServiceRequestUpdate accept only canonical Priority/Status strings. Arbitrary values such as super-high and whatever, newly submitted high/LOW/CLOSED variants, and explicitly submitted null values are rejected with structured HTTP 422 validation responses. Omitted PATCH fields are not validated against legacy stored values. ServiceRequestRead remains tolerant of legacy strings. The existing internal soft-delete path still sets Deleted; clients cannot create or PATCH that status.

The Requests form uses its own concise `Customer is required.` and `Title is required.` errors instead of native browser bubbles. Error text is next to the field, uses role=alert, and is associated through aria-describedby; fields expose aria-invalid. Saving is blocked, the first invalid field receives focus, valid inputs remain intact, and errors clear on correction. The backend also rejects missing/null Customer and missing/null/blank Title as appropriate. No generic form framework was introduced.

Asset remains optional. Customer changes still clear Asset and restrict candidates to that customer's assets. Source, Description and Notes behavior is retained. Work Order, Schedule and Service Visit editor/lifecycle behavior and Request linkage are unchanged.

## Exact validation results

| Validation | Result |
| --- | --- |
| New Requests API contract tests | 9 passed |
| Request / Work Order integration (Task 51) | 14 passed |
| Work Order scheduling regression (Task 52) | 32 passed |
| Schedule / Service Visit regression (Task 53) | 22 passed |
| Visit / History regression (Task 54) | 13 passed |
| Work Order inventory/lifecycle regression (Task 55, including inherited cases) | 13 passed |
| Existing API validation/error regression (Task 48) | 60 passed |
| Full Phase 3 Chromium browser suite | 7 passed: 3 new Requests journeys + 4 existing service-flow journeys |
| Frontend typecheck | PASS |
| Frontend lint | PASS |
| Optimized production build | PASS |
| Git whitespace check | PASS |

Backend total: 163 passing tests. Existing service suites ran through `tests/run_phase3_backend_validation.py`, which executes process-isolated suites with fail-closed database guards. New API and API-error suites also ran through `tests/isolated_backend_suite.py`. Historical migration regression functions in existing scheduling tests operated only on disposable fixtures; no application migration was created or applied, and no Owner Review migration ran.

Browser coverage includes exact dropdown options/defaults, all required-field error associations and clearing, preserved Notes, Customer/Asset dependency, requests without Asset, canonical edit/persistence after reload, legacy high/LOW/CLOSED, unrelated PATCH omission, explicit canonical replacement, unknown legacy Priority/Status, case-equivalent filters, Cancel/reopen defaults and deletion confirmation. Existing journeys cover Request -> Work Order -> Schedule -> Visit -> explicit History, stock reversal, permissions, tenant boundaries and failure presentation. These are automated disposable-fixture regressions, not Work Orders Owner Acceptance.

Desktop (1440px), mobile (390px) and RTL screenshots were inspected. Editors, inline errors and normal display remain usable; document width stays within viewport width. Artifacts are under ignored `frontend/test-results/phase3-13282/requests-ux-*/`, with `requests-errors-*`, `requests-editor-*` and `requests-display-*` PNGs.

Early browser attempts found test setup/timing issues (API-created Customer needed a records refresh; login URL needed a workspace-ready wait) and an ambiguous status-filter label. Test synchronization and the Requests filter label were corrected; a fresh complete suite passed. Interrupted disposable fixtures were cleaned up. No backend guard or business rule was weakened.

## Owner Review preservation and governance

A fresh private before snapshot covers every Owner Review database table, plus private images, configuration, credentials and the migration ledger. Final read-only comparisons show identical contents. This includes Request #1 RO Filter Urgent Maintenance, Request #2 Water Leakage Inspection, Customer/Asset links, Work Order #1, and all prior acceptance data. Tests did not use Owner Review as a fixture. No reset, reseed, bulk normalization or Owner migration ran.

No database schema/migration change, Streamlit change, Smart Import change, inventory/invoice implementation change or main merge is included. Main remains at remote SHA `e8accb377e6f0c32cc919463466ae9ba97995c06`. Official logo bytes remain unchanged, SHA256:

`CEA11E0B0A7843DD5D03F6A2449564DFEE560C18E457F635F202B988EDEBE1E3`

Only the seven paths listed above are explicitly staged. The pre-existing generated `frontend/next-env.d.ts` change remains unstaged. Final commit SHA, remote equality and final git status are reported in the delivery handoff; this report cannot contain its own commit SHA.

## Known limitations and handoff

Visual/browser validation is Chromium on disposable data. Legacy values are preserved on read and unrelated edits; replacing a legacy value requires an explicit dropdown choice. Canonical case-equivalent filtering is a Requests UI treatment; direct backend status-query semantics remain unchanged.

Running Owner servers were left untouched. To load the checkpoint, stop their foreground terminals with Ctrl+C and relaunch the existing commands in `frontend/OWNER_REVIEW.md`; do not run init/reset or migrations. Return control to Owner Acceptance and stop. Do not start Work Orders Owner Acceptance testing.
