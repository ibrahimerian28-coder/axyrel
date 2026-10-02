# Axyrel Autonomous Execution Protocol v1.0

Date: 2026-10-02. Authority: explicit owner bootstrap authorization and roadmap clarification. This is governance, not Task 50 implementation.

## 1. Purpose

Codex executes routine task work locally. The Project Owner retains authority over product scope, consequential architecture, Design Freeze changes, unapproved database/schema strategy, destructive operations, main releases/merges, and roadmap changes. Routine implementation choices belong to Codex.

## 2. Source of Truth Order

Use later explicit owner decisions and accepted checkpoints over older conflicting wording. Use docs/90-tasks.rtf for official task numbering, titles, and order, subject to the owner's numbering clarification in AUTONOMOUS_OWNER_DECISIONS.md. Use the existing MASTER handoff (.cursorrules.md) for approved architecture and Design Freeze where not superseded. Actual repository code establishes implementation facts; it does not silently override approved scope.

Older Fieldo/Healthy Water Pro material is historical unless explicitly adopted. An unresolved material scope/architecture conflict requires owner clarification. Checkpoint statements about then-current tasks and uncommitted Git state are historical, not current-state instructions.

## 3. Design Freeze

The MVP remains under Design Freeze. No new feature, module, workflow, entity, architecture, ERD change, or product scope unless an official task explicitly requires it or an owner decision authorizes it. Future ideas belong in Future Roadmap, not the current task.

## 4. Official Operating Mode

API-backed Streamlit → FastAPI → services/business rules → repositories → PostgreSQL is the only required MVP operating mode. Do not restore or expand legacy authentication/fallback or make acceptance depend on it. Legacy remnants remain technical debt for scheduled cleanup tasks.

## 5. Autonomous Task Lifecycle

PRE-FLIGHT → ANALYSIS → OWNER-DECISION GATE → IMPLEMENTATION → FOCUSED TESTS → REGRESSION TESTS → FINAL AUDIT → FINAL CHECKPOINT → GIT COMMIT → GIT PUSH → POST-PUSH VERIFICATION → STATE UPDATE → NEXT TASK.

Continue between stages unless a stop condition applies. This protocol does not itself start execution: the bootstrap stops before Task 50 analysis. Future runs begin on the canonical invocation in the runbook.

## 6. Analysis Rules

One primary analysis per task: inspect current state and relevant code, read the official task definition, identify confirmed gaps, boundaries, genuine owner decisions, implementation plan, and acceptance criteria. Reuse accepted checkpoints; do not repeatedly audit the entire repository. Revisit only findings affected by new evidence.

## 7. Owner Decision Gate

Continue automatically if no genuine owner decision remains. Do not escalate helper naming, routine file organization, internal refactors within scope, test implementation, minor style, reversible implementation details, or choices settled by accepted architecture.

## 8. Owner Decision Stop Conditions

Stop for unresolved scope/Design Freeze changes; new feature/module/entity/workflow; ERD changes; unauthorized schema/migration strategy; public API contract, auth semantics, or tenant-isolation changes; destructive data operations; irreversible migrations; task order changes; main release/merge; materially different security options; consequential architectural choices; or inability to satisfy an approved decision within scope.

Also stop on unresolvable in-scope technical blockers, trusted Git/project state mismatch, unsafe operations, batch limit, or reliable quota threshold. Do not make further production changes beyond the last safe point when a decision is pending. Preserve and describe any uncommitted work; never discard it.

## 9. Owner Decision Report Format

```text
AUTONOMOUS EXECUTION PAUSED
Completed Tasks: <list>
Current Task: <number/title>
Reason: <concise reason>
Owner Decision Required: <question>
Option A: <option>
Option B: <option>
Option C: <only if needed>
Compatibility / Risk: <effects>
Recommended minimum-change option: <option>
Last Safe Commit: <hash>
Working Tree: CLEAN / NOT CLEAN
Further Task Execution: PAUSED
```

Put the owner question prominently. Platform approvals for Git metadata/network access are execution permissions, not new product decisions; request only the exact required command.

## 10. Implementation Rules

Make the minimum coherent change. Preserve existing contracts unless authorized to change them. Reuse existing architecture. No speculative refactors, unrelated cleanup, future features, or task-order drift.

## 11. Testing Rules

Use .\.venv\Scripts\python.exe -B for Python/test commands. Use disposable databases. Run focused tests, impacted regressions, one final regression matrix, and final diff review. Do not repeat successful suites without relevant changes or perform open-ended testing loops.

Current accepted baseline: Task 49 43, Task 46 auth 10, Task 46 Service Visit 6, Task 47 58, Task 48 60 (177 total). Select future task regressions based on impact and retain these contracts; do not claim a suite was rerun when merely citing checkpoint evidence.

## 12. Task Acceptance

Accept only when the official objective and acceptance matrix pass, blocking defects are zero, required tests and git diff --check pass, scope audit is clean, and no future task work is included. Existing owner decisions settle their scope; acceptance does not authorize new scope.

## 13. Checkpoint Policy

Create docs/taskXX_final_checkpoint.md after acceptance. Record date, official title, pre-task baseline, scope, files, tests, status, preserved contracts, exclusions, carry-forward, pre-commit Git state, and next-task status. Wording stays historically accurate; do not insert a future/self-referential commit hash.

## 14. Git Policy

Default branch: checkpoint/pre-gemini-task46 until the owner changes strategy. Explicitly stage approved paths, make one accepted-task commit, and normally push only that branch to origin. Never git add . or git add -A.

Without explicit owner approval: no main merge/direct commit, force push/force-with-lease, rebase, historical amend, history rewrite, tag/release, branch deletion, destructive reset, or repository deletion. Do not switch/create branches silently.

Governance bootstrap is one separately authorized governance commit, not a completed roadmap task.

## 15. Git Safety Verification

Before work verify root, branch, expected HEAD, actual remote hash, local/remote synchronization, and expected working tree. After finalization verify the new commit, clean tree, local/tracking/actual remote equality, unchanged main, no force push, and no premature next-task start.

Initial task baseline is Task 49 commit 9520140138fca2c1d7e4d7074ece31dda1546f26. The authorized bootstrap commit may follow it without advancing the completed-task number. Startup must verify that intervening commits are approved governance only, not accept arbitrary descendants.

Avoid self-referential state hashes: pre-commit state/queue/checkpoint updates belong in the same task commit. For future completed-task state, last_completed_commit may use the explicit symbolic value HEAD, resolved and verified against that task's commit/checkpoint after push. Runtime state update means verifying those committed values after push; do not create an uncommitted post-push bookkeeping edit. Exact unexpected HEADs still trigger a stop.

## 16. Autonomous Run Budget

Maximum completed tasks per autonomous run: 3. Count only accepted, committed, pushed, and post-push-verified tasks in that invocation. Bootstrap does not count. After three, complete checkpoint/state verification and stop before analyzing the fourth. Owner may later raise the limit.

The committed batch count records that run's completed tasks. Reset in memory for a new invocation after verifying the previous run; persist with the first accepted task's normal state update, not as a dirty pre-flight edit.

## 17. Usage Preservation Policy

Reuse checkpoints and decisions; read only relevant roadmap/code sections. Avoid repeated analyses, identical test runs, long interim reports, unnecessary network/web research, and cloud execution when local work suffices.

If reliable quota information exists, stop at or below 20% remaining after reaching a safe checkpoint. Never guess a percentage. If unavailable, use the three-task limit. Prioritize an intelligible safe state, then commit/push already accepted work where safe, then stop.

## 18. Blocking Technical Failure

Diagnose root cause, make a bounded in-scope repair, rerun focused tests and necessary regressions. Stop if scope expansion or unresolved architecture is needed, or a safe repair cannot be achieved. No endless repair loop.

## 19. Database / Migration Safety

Do not mutate production data or run destructive database operations. Automated testing uses disposable databases. Schema/migration work requires official task scope or existing owner approval, migration review, and rollback/compatibility analysis. A roadmap title does not authorize destructive production writes or unknown deployment credentials; stop where authority is unclear.

## 20. External / Network Safety

GitHub origin is the approved project remote. Do not upload code or secrets elsewhere. Do not expose .env, passwords, tokens, SECRET_KEY, customer data, or private credentials.

## 21. Secret Handling

Never print secret values or commit .env, secrets, credentials, or tokens. Respect .gitignore. Governance/state must contain no secret values.

## 22. Local Execution Model

Primary workspace: D:\Axyrel_BACKUP_BEFORE_GEMINI. Local files remain the working project. GitHub supplies version history, remote checkpoints, synchronization, and recovery. This is not GitHub-only execution.

## 23. Carry-Forward Decisions

- Task 46: API-backed mode only; no legacy auth restoration. Preserve lifecycle and original-technician stock restoration and reserved-reference integrity.
- Task 47: Decimal invoice CREATE total only when absent; explicit total including zero preserved; PATCH unchanged. A8 inheritance stays a UI preset. No new monetary rules. Expense summary includes non-Deleted records; Cancelled stays counted in Open Work Order KPI; preserve inventory classification presentation and CREATE-only name rules.
- Task 48: exact approved error/validation semantics remain authoritative. PostgreSQL uniqueness requires psycopg, SQLSTATE 23505, and exact allowlisted structured constraint names. Real exception classes/simulated diagnostics were tested; isolated live PostgreSQL write integration was not.
- Task 49: canonical database-backed AuthContext; database identity/company/role authority; informational JWT role/permissions; entry-point-specific error and token contracts preserved.
- Task 52: approve/adopt official Date/Time & Timezone policy before Scheduling final acceptance, including outstanding Schedule effective-state timestamp validation.
- Task 53: apply/verify approved timezone policy for Service Visit integration and outstanding effective-state timestamp validation.
- Direction: timezone-aware UTC instants plus separate timezone metadata; calendar business dates remain DATE. Schema/migration implementation still requires appropriate task/owner authority.
- Roadmap clarification: detailed Tasks 18–90 are authoritative. Trailing numbered phase summary is not Tasks 9–20. Unavailable historical titles, including Task 08, are not invented and do not block continuation from Task 50.

## 24. Autonomous Batch Completion

```text
AUTONOMOUS BATCH COMPLETE
Tasks Completed: <list>
Commits: <hashes>
Tests: <results>
Current HEAD: <hash>
Remote Sync: YES / NO
Working Tree: CLEAN / NOT CLEAN
Next Task: <number/title>
Owner Decisions Pending: NONE / <details>
Usage Stop Reason: TASK LIMIT / QUOTA THRESHOLD / OWNER DECISION / BLOCKER
```
