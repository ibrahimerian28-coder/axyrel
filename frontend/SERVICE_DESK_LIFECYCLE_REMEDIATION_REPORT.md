# Service Desk and service visit lifecycle checkpoint

## Checkpoint

- Workspace: `D:\Axyrel_BACKUP_BEFORE_GEMINI`; branch: `frontend/v1`.
- Verified starting local/remote SHA: `75e157bf1c89b034f623ebff4adc5bf8ce8333ae`.
- Final SHA: the commit containing this report. Retrieve it with `git log -1 --format=%H -- frontend/SERVICE_DESK_LIFECYCLE_REMEDIATION_REPORT.md`. The exact SHA and remote verification are supplied in the delivery response and local ignored validation artifact `frontend/test-results/service-desk-checkpoint.json`, written after push. A commit cannot contain its own literal hash without changing that hash.
- Starting remote main: `e8accb377e6f0c32cc919463466ae9ba97995c06`. Main was not modified or merged.
- No deployment, release, force push, history rewriting, or database deletion. This checkpoint requires manual Owner Acceptance; it is not a production-readiness claim.

## Architecture, orchestration, and atomicity

Service Desk projects the existing Request → Work Order → Schedule → Service Visit → Service History domain. There is no job table or second lifecycle source of truth. Human display IDs label jobs/customers/assets; UUIDs remain internal API references.

The new API provides Quick Service, existing Request/job scheduling, Start, Reschedule, visit outcomes, appointment cancellation, whole-job cancellation, and explicit historical aggregate correction. Reads require `service:read`; writes require `service:manage`. Historical correction additionally requires `audit:read`.

Save Request creates only a Request. Create & Schedule reuses existing services/contracts inside one SQLAlchemy transaction with one API-owned commit. Validation or persistence failure rolls back the complete chain. The browser does not write Request, Work Order, and Schedule independently. Tenant/customer/asset relationships and active technician eligibility are validated.

A PostgreSQL tenant-namespaced transaction advisory lock serializes service mutations across workers; management writes share that lock. Quick Service derives a tenant-specific Request ID from the client command UUID, returning the existing job on retry. Start returns an existing active visit or starts an existing Planned visit before creating a correctly linked new visit. Backend UTC timestamps record execution.

Completion/history/follow-up and inventory reversal share transaction protection. Real PostgreSQL concurrent Start, completion, and reversal tests verify duplicate prevention. SQLite provides isolated API contract coverage, not evidence for PostgreSQL locking.

## Aggregate lifecycle and schedules

The previous bug inferred whole-job terminal states from visits while ignoring remaining appointments. Automatic visit aggregation now selects In Progress for active execution and otherwise keeps the Work Order Open; terminal visits never automatically complete/cancel the entire job. Explicit job operations own terminal decisions.

Complete Job atomically completes the current visit, resolves its appointment, creates history, and explicitly completes the Work Order. Any remaining Planned/In Progress visit or Scheduled appointment rejects completion and rolls back all changes. The UI exposes outstanding appointments and disables inconsistent completion.

Complete Visit & Schedule Follow-up records the finished visit and creates the next appointment under the SAME Work Order. An existing future appointment can instead be retained without creating another. The projection shows Follow-up and permits the next visit to start.

Cancel Visit/appointment affects only that activity. Reasoned Cancel Job explicitly cancels remaining appointments and visits through existing services, preserving inventory reversal behavior. Customer unavailable/no-show records a Cancelled execution with a clear reason, resolves the appointment, creates no completed-service history, and permits rescheduling on the same job or explicit job cancellation.

Executed appointments become Completed or Cancelled using the existing string status column: a minimal vocabulary extension without schema changes. They cannot be reassigned/rescheduled, have lifecycle fields overwritten, or be deleted; notes remain editable. Unexecuted appointments are rescheduled through an authoritative command revalidating technician, tenant references, and schedule time contracts.

Native date/time fields and Today/Tomorrow shortcuts emit explicit Cairo offsets. Existing backend normalization remains authoritative. Read schemas distinguish database UTC instants from local input, preventing double Cairo normalization of SQLite naive UTC results. PostgreSQL instants remain UTC-normalized on the wire.

## History and inventory

Completed activity creates one linked Service History record using recorded customer, asset, visit, Work Order, technician, service time, job title, and visit notes. Generic type is Service visit. Time preference is actual end, actual start, then recorded visit creation time; no execution time or missing description is fabricated. Retries do not duplicate history. Later legitimate cancellation/deletion marks retained history Corrected, preserving its summary, notes, relationships, and evidence. Existing Completed → Cancelled management correction remains available. No historical backfill runs automatically.

Parts require In Progress execution and deliberate Edit parts. Terminal visits display read-only movements, and the backend rejects new installations. Correction fully reverses all outstanding installations for the visit with a reason, then requires deliberate reinstall of corrected items. Partial reversal UI was not introduced.

Existing append-only installation/reversal transactions and inventory rules restore the original technician's stock, subtract prior reversals, and reverse only remaining quantities. Retrying cannot double-credit stock. Completed-visit cancellation retains existing restoration behavior. Transactions are never deleted. A distinct confirmed install remains a distinct inventory operation; a general install command-ID protocol is outside this checkpoint. UI pending state prevents repeated clicks; Start/completion/reversal retry and concurrency are tested.

## Operational frontend

Service Desk is added to navigation. Dashboard login and Requests, Work Orders, Schedule, Service Visits, and Service History management screens remain available.

The screen provides New/Scheduled/In Progress/Follow-up/Completed Today summaries, global human-ID/customer/phone/asset search, status/technician/canonical-priority/date filters, desktop table, responsive cards, and contextual Schedule/Start/Reschedule/Open Visit/cancellation/history/detail actions.

Quick Service is a focus-trapped Customer → Service → Schedule drawer. Customer search/context and inline creation reuse the existing CustomerEditor/backend validation. Exactly one eligible asset is preselected; multiple assets require choice. Priorities reuse Low/Normal/High/Urgent, default Normal. Save Request needs no scheduling fields; Create & Schedule requires technician/date/time. The existing-customer workflow targets roughly 6–8 interactions excluding typing; manual Owner timing remains required.

Existing dark sidebar, light workspace, cyan accent, spacing, logical direction-aware layout, and responsive conventions are retained. Unrelated colors and official logo are unchanged.

## Historical Owner Review conflict

The fresh preservation snapshot already contained Work Order #1 Cancelled, two Scheduled appointments, and a Cancelled visit from the earlier manual reproduction. These persistent records were NOT changed. The projection flags the inconsistency instead of silently reopening a terminal job.

An authorized operator may explicitly select Correct job status with a reason. Only terminal jobs with unexecuted scheduled work and no Planned/In Progress visit qualify. This resolves legacy executed appointments according to their visits, reopens the aggregate to Open, and records the previous terminal status/reason in job notes. Visit/inventory/history evidence remains. A genuinely cancelled job with all appointments resolved does not qualify. This action was tested only on disposable fixtures and remains for manual Owner review.

## Security, migrations, and preservation

- Existing authentication, permission checks, authenticated proxy, same-origin/CSRF, private images, display IDs, and tenant-scoped repositories remain authoritative. Foreign-tenant references, permissions, technician eligibility, and terminal actions are tested.
- **No schema migration added; none applied to Owner Review.** Existing historical migration/smoke suites apply existing migrations only to generated disposable databases.
- Every Owner Review table was compared row-for-row with a fresh pre-change private snapshot. Private files, credential/config hashes, customers/assets, and migration ledger are identical. Snapshot stays ignored.
- Tests use in-memory SQLite or generated isolated PostgreSQL databases. Retention mode prevents DROP; test databases remain in place under the no-database-deletion boundary.
- Streamlit source remains unchanged; local reference smoke tests use disposable fixtures.
- Unchanged official logo SHA256: `CEA11E0B0A7843DD5D03F6A2449564DFEE560C18E457F635F202B988EDEBE1E3`.
- Pre-existing `frontend/next-env.d.ts` remains unstaged. Checkpoint staging is explicit.

## Validation

| Check | Result |
| --- | --- |
| Full backend scan plus corrected-module reruns | PASS: 611 tests across 45 modules |
| New SQLite Service Desk API acceptance | PASS: 35 tests, included above |
| New PostgreSQL acceptance/concurrency | PASS: 38 tests, included above |
| Frontend typecheck | PASS |
| Frontend lint | PASS |
| Frontend production build | PASS |
| Final Chromium browser/formatter suite | PASS: 23 tests (16 browser journeys + 7 formatter checks), plus 6 Service Desk reruns after final display cleanup; desktop/390px/RTL |
| Owner Review tables/private files preservation | PASS |
| Logo SHA256 preservation | PASS |
| Diff whitespace check | PASS |

Commands: `npm.cmd --prefix frontend run typecheck`, `npm.cmd --prefix frontend run lint`, `npm.cmd --prefix frontend run build`; backend runner `.venv/Scripts/python.exe -B tests/run_service_desk_regressions.py`; frontend `npx.cmd playwright test --config playwright.phase3.config.ts` with retention mode and unique localhost fixture ports.

The initial full scan found stale automatic-job-terminal expectations, stale unit mocks, and smoke assertions hard-coded to 13 migrations while 14 were already tracked. Tests were updated for explicit completion and tracked migration count; no migration or Streamlit source changed. Retained fixture markers required unique ports. Corrected modules were rerun; the final 611 aggregate uses each module's latest passing log, rather than claiming the initial scan passed unchanged.

Coverage includes Request-only save; atomic chain/rollback; tenant/permissions; linked Start/retries/concurrency; exact two-schedule completed/cancelled first-visit scenario; same-job follow-up/second start; explicit completion/cancellation; no-show; active-only parts; stock deductions/reversals/retry; one automatic history; corrected evidence; and existing core workflows. Full regressions cover imports/customers/assets, priorities/Requests, inventory/billing/auth/timezone, and local disposable migration/reference smoke workflows.

A browser regression caught optional follow-up fields preselecting a technician even when a future appointment already existed, causing an unintended extra appointment. The drawer now leaves that optional technician blank and labels the extra appointment optional; keeping existing scheduled work does not create another record. The assertion continues to require exactly two appointments.

Browser coverage includes Service Desk desktop 1536px, 390px LTR, 390px RTL, no overflow/raw UUIDs, inline customer/multiple assets, Request-only/later scheduling, two-visit job/history, part correction, outstanding appointments, filters, no-show/rescheduling/cancellation, CSRF, and existing management journeys. Logs/screenshots/traces remain ignored under `frontend/test-results/`.

## Limitations

- Chromium is automated; other browsers/real devices require manual review.
- Projection loads existing tenant collections; large-tenant pagination/performance is outside scope.
- Quick Service schedules a same-day range; advanced/multi-day planning remains in Schedule management.
- Part correction reverses all outstanding installations, followed by deliberate reinstall.
- Unknown legacy Request priorities require canonical correction, not silent mapping.
- Persistent historical conflicts remain until explicit Owner correction; no automated repair/backfill.
- Foreground Owner Review services require restart to load changes; PostgreSQL restart/database initialization is unnecessary.

## Next manual Owner Acceptance

1. Stop only the existing Owner Review backend/frontend foreground terminals using Ctrl+C. Do not initialize/reset/reseed/migrate a database or use a broad process-killing launcher.
2. From repository root run `.\.venv\Scripts\python.exe -B tools\owner_review.py serve` (API 8140).
3. In the frontend terminal run:

   ```powershell
   Set-Location D:\Axyrel_BACKUP_BEFORE_GEMINI\frontend
   $env:AXYREL_BACKEND_URL='http://127.0.0.1:8140'
   $env:AXYREL_FRONTEND_ORIGIN='http://127.0.0.1:3140'
   npm.cmd run start -- --port 3140
   ```

4. Log in using existing private credentials. Review Service Desk/navigation/management screens, summaries/search/filters/contextual actions on desktop, 390px, and RTL.
5. Inspect existing Job #1. Only if the Owner confirms premature cancellation, use Correct job status with a reason. Verify original cancelled visit and inventory evidence remain, its appointment becomes Cancelled, the second stays Scheduled, job becomes Follow-up, and the second appointment starts under the same Work Order.
6. Measure existing-customer Quick Service → Create & Schedule. Confirm one job with linked Request/Work Order/Schedule. Test multiple assets require selection and inline customer follows existing validation.
7. Save Request without schedule; verify no placeholder records, then schedule from Service Desk.
8. Start/open visit → Edit parts → install → inspect stock deduction/OUT. Fully reverse with reason, confirm one restoration and retained reversal evidence, then reinstall corrected parts deliberately.
9. Complete Visit & Schedule Follow-up, verify history/resolved appointment/non-terminal same Work Order; start visit #2 and Complete Job. Verify two histories and terminal read-only parts.
10. With two appointments, complete/cancel visit #1 and verify job remains non-terminal and visit #2 starts. Complete Job must remain unavailable/rejected until unresolved work is explicitly handled.
11. Test no-show: no completion history, resolved attempt, non-terminal job, same-job reschedule. Contrast reasoned appointment cancellation with Cancel Job.
12. If legitimately correcting Completed → Cancelled in management, inspect preserved Corrected history and reversal transactions without double stock credit.
13. Review private images/timezone behavior and record acceptance. No later acceptance phase starts automatically.

## Files changed

- `backend/api/v1/__init__.py`
- `backend/api/v1/schedules.py`
- `backend/api/v1/service_desk.py`
- `backend/api/v1/service_visits.py`
- `backend/core/service_lock.py`
- `backend/schemas/schedule.py`
- `backend/schemas/service_desk.py`
- `backend/schemas/service_visit.py`
- `backend/services/schedule.py`
- `backend/services/service_desk.py`
- `backend/services/service_visit.py`
- `backend/services/status_lifecycle.py`
- `backend/services/work_order.py`
- `frontend/SERVICE_DESK_LIFECYCLE_REMEDIATION_REPORT.md`
- `frontend/src/app/api/backend/[...path]/route.ts`
- `frontend/src/app/workspace/page.tsx`
- `frontend/src/features/phase2/screens.tsx`
- `frontend/src/features/phase3/screens.tsx`
- `frontend/src/features/phase3/visit-parts.tsx`
- `frontend/src/features/service-desk/screen.module.css`
- `frontend/src/features/service-desk/screen.tsx`
- `frontend/tests/phase3-api.py`
- `frontend/tests/phase3/service-desk.spec.ts`
- `frontend/tests/phase3/service-flow.spec.ts`
- `tests/isolated_backend_suite.py`
- `tests/run_service_desk_regressions.py`
- `tests/test_service_desk.py`
- `tests/test_service_desk_postgresql.py`
- `tests/test_task46_service_visit.py`
- `tests/test_task53_schedule_service_visit.py`
- `tests/test_task55_work_order_inventory.py`
- `tests/test_task71_core_service_units.py`
- `tests/test_task74_core_workflows.py`
- `tests/test_task86_deployment_rehearsal.py`
- `tests/test_task87_production_smoke.py`
- `tests/test_task89_first_use.py`
