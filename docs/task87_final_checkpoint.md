# Task 87 — Final Checkpoint

Date: 2026-10-03. Official title: **Production Smoke Test**.
Status at creation: ACCEPTED — pending commit/push under OD-27 local synthetic scope only.
Pre-task HEAD 9b375c2796d7d4dd5ad5c02bfa4ad8c50ba65dea; last accepted Task 86 5bc2185fb3fd35e858b686b8b4c7beeaf8d28332. Clean local/tracking/actual remote verified. Root D:\Axyrel_BACKUP_BEFORE_GEMINI; branch checkpoint/pre-gemini-task46; main unchanged at e8accb377e6f0c32cc919463466ae9ba97995c06.

OD-27 resolves the prior smoke scope gate and is recorded in owner decisions. Analysis reused Task 86's isolated real Uvicorn/PostgreSQL harness, accepted core journey and movement semantics. Added smoke tests with actual production-mode configuration and real loopback HTTP, no DB dependency override or mocked authentication/tenant/business rules. No approved-MVP defect found; no runtime/UI/API/schema/security/migration changes.

| Executed once in separate project-interpreter -B processes | Result |
|---|---|
| New local production smoke and security-refusal cases | 2/2 PASS |
| Task 78 PostgreSQL tenant-isolation regression matrices | 3/3 PASS |
| Total | 5/5 PASS |
| Whitespace/scope audit; confirmed blocking defects within tested scope | PASS; 0 |

The smoke creates thirteen-file tracked schema, checks health and PostgreSQL-backed login/me, rejects bad login/unauthenticated access, then exercises Customer/Asset/Request/Order/Schedule/Visit completion/explicit History, Inventory and a generic movement, Invoice/Expense/profitability. Literal results: stock value 7.50; invoice total 95.25; net profit 90.00; cash net profit 14.75. Generic movement does not alter stock, as accepted; no invented balance adjustment. Two actual admin tenants prove foreign lists/IDs invisible across ten resource types and denied customer mutation leaves data intact. Explicit Notification/Audit remain empty. The actual Streamlit login form submits to the running API and renders authenticated admin state via AppTest.

Normal server exit, verified migration rerun skip, real restart/new login and reads of all ten stored records confirm persistence, Completed Visit state, stock quantity and identical financial report. Migration ledger remains unchanged. Separate blank/default secret and malformed URL subcases refuse startup before schema work. No successful suites repeated; recent Task 86 migration safety and Task 85 startup-security evidence remains accepted, not claimed as rerun. Existing deprecation warnings non-blocking.

Only generated local disposable PostgreSQL and maintenance postgres for guarded create/drop, synthetic tenants/users/data/configuration and loopback HTTP. Production subprocesses run without workspace .env access; only existing local test connection credentials passed in memory. UI's accepted logo asset is copied into the isolated temporary directory to preserve its relative path; no actual source/business data read. Processes/connections close before guarded cleanup. Captured output/logs checked for configuration secret/URL disclosure. No cloud/VPS/managed production DB, real production environment/DNS/TLS/secrets/data or external services accessed.

Acceptance: **LOCAL SYNTHETIC PRODUCTION SMOKE TEST PASSED**. Not a live production smoke/deployment/infrastructure approval or real customer test. Real smoke remains required after a future approved live deployment. Bounded representative coverage, not exhaustive movement/concurrency/precision/security/browser certification; AppTest is not a public UI/browser test. Prior constraints, OD-14 optional explicit links/accounting/report populations and Design Freeze preserved. Real-data mapping/security/hosting/operational prerequisites remain unresolved.

Reproduce with .\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_task87_production_smoke.py. Task 86 procedure remains authoritative for disposable setup, startup/health versus DB readiness and rollback boundaries.

Six paths pending commit: tests/test_task87_production_smoke.py, this checkpoint, docs/AUTONOMOUS_OWNER_DECISIONS.md, docs/task87_owner_decision_required.md (historical resolution annotation), docs/TASK_EXECUTION_QUEUE.md and .autonomous/state.json. State records Task 87 complete, Task 88/not_started, symbolic HEAD and eight final-run completions under OD-24. Independent commit/push/actual remote/state verification precedes Task 88 analysis. No main merge, force, rebase/amend; no pending Task 87 decision. Later launch/real-world scope remains separately gated.
