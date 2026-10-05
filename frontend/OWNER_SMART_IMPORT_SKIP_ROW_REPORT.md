# Smart Import explicit Skip Row checkpoint

Scope: owner-approved reversible row exclusion only, on `frontend/v1`, based on `c0d38b7b13a35896fea870f63831f87750075474`. Owner Acceptance Test 19 has not started.

## Exact files changed

- `backend/services/smart_import.py`: validate bounded unique integer source-row exclusions; return Skipped previews; exclude those rows before matching, geography, serial validation, grouping and creation planning; report skipped counts and block all-skipped imports.
- `frontend/src/features/phase4/smart-import.tsx`: explicit Skip this row / Restore row controls, retained Skipped section, automatic fresh review, skipped counts in review/confirmation/receipt, no-op message and disabled confirmation.
- `frontend/src/styles/globals.css`: Smart Import-scoped dashed border and existing canvas background for skipped cards.
- `tests/test_smart_import.py`: eight focused exclusion/integrity regression tests.
- `frontend/tests/smart-import/skip-rows.spec.ts`: real workbook Owner scenario on a disposable fixture, keyboard skip/restore, Ready-row exclusion, all-skipped blocking, desktop/390px/RTL evidence and exact existing-record comparisons.
- `frontend/OWNER_SMART_IMPORT_SKIP_ROW_REPORT.md`: this report.

## Backend integrity and counts

`skipped_rows` contains the original uploaded data-row ordinals (2 onwards). Source rows are retained, never filtered or reordered by the client. The existing signed review checksum covers the complete source, mapping, corrections and exact skip list, while the signed plan covers only actionable rows. Any changed skip state or source order fails confirmation with the old token. Skip/Restore invalidates the frontend token and confirmation immediately and requests fresh backend review.

Skipped rows are structurally bounded as before but are excluded before business validation and customer matching. They cannot affect phone groups, customer identity conflicts or serial duplicate detection, and have no creation-plan entry. The backend commit revalidates under the existing locks and writes only actionable entries. Atomic rollback, tenant/account binding, permissions, create-only behavior, deleted-serial reservation, audit receipts and retry keys remain in the existing implementation.

All summary counts describe actionable rows; skipped rows contribute only to the separate skipped count. Fully skipped batches report `No rows selected for import.`, receive no token and cannot create an empty receipt, including a direct commit with a server-signed empty plan. Existing receipt replay is preserved; older summaries display zero skipped rows.

For the approved mixed workbook, skipping Row 2 yields 1 new Customer, 0 existing Customers matched, 1 new Asset, 0 overwrites, 1 skipped row and 0 attention rows. Restore returns the collision and blocks confirmation. Only New Import Customer and SMART-TEST-002 are created, with the correct relationship; Customer #1010 and SMART-TEST-001 remain equal in every returned field.

## Validation

- Smart Import backend/API/file suite: **33 passed**, including all 25 existing tests and 8 new tests.
- Existing Asset CSV Import regression: **12 passed**.
- Customer/Asset integration regression: **19 passed**.
- Smart Import Chromium browser suite: **5 passed** (4 existing journeys and 1 new workbook journey).
- `npm.cmd run typecheck`: **PASS**.
- `npm.cmd run lint`: **PASS**.
- `npm.cmd run build`: **PASS**, optimized production output generated.
- `git diff --check`: **PASS**.

New backend tests cover collision skip/restore and mixed commit, unchanged existing records, grouping/conflicts after exclusions, all-skipped/no receipt, Customers-only and Assets-only, Ready rows, malformed business values, source/skip/correction tampering, bounded skip types, tenant isolation and durable replay. Existing tests retain concurrency, rollback, matching, geography, serial reservation, permissions and file-security coverage.

Browser screenshots (local ignored artifacts) are under `frontend/test-results/smart-import/skip-rows-explicit-source--7e039-ok-on-desktop-390px-and-RTL-chromium/`: `skip-review-desktop.png`, `skip-review-390.png`, `skip-review-390-rtl.png`, `skip-receipt-390-rtl.png`. Review and receipt were inspected; controls and skipped cards remain visible, source identity survives category changes, and document width does not exceed viewport width. No raw UUID appears in the review. Keyboard Enter activates Skip and Restore.

An initial combined invocation of the PostgreSQL Asset Import and SQLite Customer/Asset suites produced a fixture setup conflict; both suites were rerun independently and passed. The first new browser fixture setup omitted the Origin header and was correctly rejected by the existing guard; the test was corrected and the complete suite passed. No application guard was weakened. Expected synthetic rollback tracebacks and existing SQLAlchemy/Node warnings do not indicate failed tests.

## Preservation and checkpoint governance

A fresh private snapshot was captured before implementation. Read-only comparisons confirm that all Owner Review Customer and Asset records, private images, configuration, credential file and migration ledger are unchanged, including manual Customer #1010 and SMART-TEST-001 / IMPORT-TEST-001. Automated tests use generated disposable PostgreSQL databases or temporary SQLite fixtures. No Owner Review reset, seed or migration ran. Test-created PostgreSQL fixtures are cleaned up.

No database migration, dependency change, Streamlit change, logo edit or main merge is included. The official logo bytes are unchanged; SHA256 remains:

`CEA11E0B0A7843DD5D03F6A2449564DFEE560C18E457F635F202B988EDEBE1E3`

Remote main remains `e8accb377e6f0c32cc919463466ae9ba97995c06`. Only the six paths above are explicitly staged. The pre-existing generated `frontend/next-env.d.ts` change remains unstaged. The final commit SHA and remote branch equality are reported in the checkpoint handoff (a report cannot contain its own commit hash).

## Limitations and Owner handoff

Skip is reversible during Review, before explicit confirmation. A lost commit response continues to freeze the reviewed request and retry the same receipt. Business-invalid rows may be excluded; unsafe oversized/malformed source structures still fail file/request limits. Matching and serial comparison policies are unchanged.

Visual/browser validation used Chromium and synthetic disposable records, not the Owner Review database. The running Owner servers were not restarted. To load the checkpoint for manual review, stop their foreground terminals with Ctrl+C and relaunch the existing backend/frontend commands in `frontend/OWNER_REVIEW.md`; do not run init/reset or migrations. Return control to Owner Acceptance. Do not start Test 19.
