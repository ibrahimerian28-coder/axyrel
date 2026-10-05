# Owner Work Orders + Schedule UX remediation

Branch: `frontend/v1`. Required parent checkpoint: `03295af1a532c87900ff7123f9ace89c3483836b`, verified before editing. This report accompanies the focused remediation commit; its SHA is supplied in the delivery response and Git history.

## Implementation

- Work Order Priority uses the Requests editor's shared canonical select implementation and unchanged `requestPriorities`: Low, Normal, High, Urgent. New Work Orders default to Normal, including creation from a Request. Customer/Asset/Request/Technician/title/description prefills remain intact.
- Existing noncanonical values have a distinct disabled current-value option, for example `Current: High (stored as "high")`. Unknown values remain visible verbatim. Reads and opening an editor do not write data. Unchanged priority is omitted from PATCH; explicitly selecting High saves canonical High. Display casing for known historical values uses the existing Requests helper without rewriting storage.
- `WorkOrderCreate` and `WorkOrderUpdate` reuse the existing backend Requests `request_choice` validator. Submitted priority must be one of the four exact canonical strings. Invalid values, including `super-high`, noncanonical casing and explicit null, produce controlled HTTP 422 validation responses. An omitted PATCH priority is not validated against the old stored priority. Read schemas remain compatible with legacy values.
- Work Order and Schedule detail presentation now labels Description, Priority, Notes, Source, Start (Cairo), End (Cairo). API/database names and payload contracts are unchanged.
- Separate read-only `scheduleEventLabel` and `calendarDateLabel` formatters use textual months: `06 Oct 2026, 10:00 GMT+03:00` and `Tue, 06 Oct 2026`. These cover Week/Agenda cards, Schedule list and detail, and linked Schedule cards under Work Orders. Other domains retain their existing formatter.
- Native date/datetime-local controls, `eventInput`, instant parsing, UTC conversion, Africa/Cairo semantics, explicit offsets, DST handling, API contracts and scheduling business logic are unchanged. No lifecycle/service implementation changed: Work Order transitions, cancellation/completion and Visit synchronization retain their existing rules. Requests canonical values and behavior are preserved.

## Exact files in this checkpoint

1. `backend/schemas/work_order.py`
2. `frontend/src/features/phase3/editor.tsx`
3. `frontend/src/features/phase3/contracts.ts`
4. `frontend/src/features/phase3/calendar.tsx`
5. `frontend/src/features/phase3/screens.tsx`
6. `tests/test_work_order_priority_contract.py`
7. `frontend/tests/phase3/schedule-display.spec.ts`
8. `frontend/tests/phase3/work-order-schedule-ux.spec.ts`
9. `frontend/OWNER_WORK_ORDERS_SCHEDULE_UX_REMEDIATION_REPORT.md`

## Automated validation

All backend tests use isolated temporary fixtures; browser journeys use generated disposable PostgreSQL databases and separate test server ports, never Owner Review.

| Command / coverage | Result |
| --- | --- |
| `.venv/Scripts/python.exe -B tests/isolated_backend_suite.py test_work_order_priority_contract` | 8 passed |
| `.venv/Scripts/python.exe -B tests/isolated_backend_suite.py test_request_editor_contract` | 9 passed |
| `.venv/Scripts/python.exe -B tests/run_phase3_backend_validation.py` | 94 passed: Task 51 = 14, Task 52 = 32, Task 53 = 22, Task 54 = 13, Task 55 = 13 |
| Backend total | 111 passed |
| `npx.cmd playwright test --config playwright.phase3.config.ts` with API 18292 / frontend 13292 | 17 passed, 3.5 minutes: Requests journeys 3, existing service-flow regressions 4, new Work Order/Schedule journeys 3, formatter tests 7 |
| `npm.cmd --prefix frontend run typecheck` | PASS; repeated after final test edits |
| `npm.cmd --prefix frontend run lint` | PASS; repeated after final test edits |
| `npm.cmd --prefix frontend run build` | PASS; optimized production build |
| `git diff --check` | PASS |

Focused API coverage includes all canonical create values, Normal default, invalid create/PATCH atomic rejection, legacy `high`/`LOW`/`normal`/unknown reads and unrelated PATCH preservation, explicit canonical selection and unchanged lifecycle transitions.

Each new browser journey creates two schedules for its own Work Order: 06 Oct 2026 10:00–11:30 Cairo and 08 Oct 2026 14:00–15:30 Cairo. It independently edits each, reloads and compares exact timestamp/link fields, verifies two linked cards, and checks search, status/customer filters, previous/next week, prefilled Work Order/Technician, clean Schedule forms and Scheduled status. The summer starts persist as 07:00Z and 11:00Z. Formatter coverage also checks winter GMT+02:00, summer GMT+03:00, explicit offsets and existing naive API UTC output. The Add Service Visit button is checked for visibility without invoking it in the new journeys.

Existing Phase 3 tests were run as required, including their established synthetic Visit/lifecycle regressions. No Service Visits Owner Acceptance testing was started. No new Visit behavior tests or Owner Review Visits were created.

Initial new-test runs exposed selector assumptions: a populated Notes label needed a textarea-name selector, and mobile already displays Agenda with its view switches hidden. Only the tests were corrected. The final complete suite above passed without application changes for those test issues.

## Visual verification and limitations

Desktop 1440px, 390px LTR and 390px RTL journeys passed. Screenshots were inspected for the Week layout, mobile Agenda/details, legacy editor and linked schedules. Read labels and textual dates are visible, both schedules remain separate, and document-width assertions report no horizontal overflow. Existing responsive layout and direction handling are retained.

Local ignored evidence is under `frontend/test-results/phase3-13292/work-order-schedule-ux-*`, including `schedule-week-desktop.png`, `schedule-agenda-*.png`, `work-order-legacy-*.png` and `work-order-linked-schedules-*.png`.

Validation uses Chromium; other browser engines were not tested. Native inputs keep browser/locale-specific numeric rendering, as explicitly permitted. Long current-value text may be clipped inside a narrow native select; the full historical value remains in the option and detail display. Desktop Week cards wrap their longer textual dates within existing columns. RTL retains existing browser bidi behavior. Owner's final manual review remains outstanding.

## Preservation and Git governance

Read-only snapshots before and after automated validation compare every Owner Review database table, including all Work Orders/Schedules and relationships, plus private images, migration ledger, configuration and credentials. Exact equality passed. This includes Owner Work Order #1 with stored priority `high`, In Progress status and both Scheduled records, times and notes unchanged.

No application migration was created or applied, and no migration command ran against Owner Review. Existing backend regression tests exercise their historical migration functions only inside disposable test fixtures. No normalization, reset, reseed or record mutation occurred in Owner Review. Only generated test databases were cleaned up. Owner Review servers were left running as found; no broad process killing or PostgreSQL restart/configuration change occurred.

Streamlit, Smart Import and unrelated application domains are unchanged. The official logo file is untouched; verified SHA256:

`CEA11E0B0A7843DD5D03F6A2449564DFEE560C18E457F635F202B988EDEBE1E3`

Only the nine listed files are explicitly staged. Pre-existing `frontend/next-env.d.ts` remains unstaged. No main modification, merge or force push. Remote main before delivery is `e8accb377e6f0c32cc919463466ae9ba97995c06`; the final delivery verifies it unchanged and verifies remote `frontend/v1` equals the new commit SHA.

## Foreground restart for manual review

Both Owner Review foreground servers need restarting to load the backend schema change and new production frontend. Stop only their own foreground terminals with Ctrl+C; confirm batch termination if prompted. Keep PostgreSQL and all other processes untouched. Do not run init, reset, seed or migrate. Do not invoke the older launcher or the migration instructions in earlier review documentation.

Backend terminal, from repository root:

```powershell
.\.venv\Scripts\python.exe -B tools\owner_review.py serve
```

Frontend terminal, from repository root:

```powershell
Set-Location frontend
$env:AXYREL_BACKEND_URL = 'http://127.0.0.1:8140'
$env:AXYREL_FRONTEND_ORIGIN = 'http://127.0.0.1:3140'
npm.cmd run start -- --port 3140
```

Open `http://127.0.0.1:3140/login` with the unchanged private credentials. Review this remediation only. Service Visits Owner Acceptance / Test 29 has not started; control returns to the Owner.
