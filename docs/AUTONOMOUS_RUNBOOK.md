# Axyrel Autonomous Runbook

Canonical invocation:

**START AXYREL AUTONOMOUS EXECUTION**

When received in the project root, execute this runbook under the owner-approved protocol instead of requesting another detailed task prompt. Mere bootstrap creation or dry run does not invoke it.

1. Read .autonomous/state.json; verify protocol 1.0, local root/branch, task number/status, budget, and pending owner decisions.
2. Read docs/AUTONOMOUS_EXECUTION_PROTOCOL.md.
3. Read docs/AUTONOMOUS_OWNER_DECISIONS.md.
4. Read only the current task section in docs/TASK_EXECUTION_QUEUE.md and material carry-forward.
5. Verify Git root/branch/HEAD, clean expected tree, local/tracking/actual remote agreement, and unchanged main. Resolve the accepted-task commit using protocol section 15. At first startup, the Task 49 commit must be followed only by the approved governance bootstrap; verify its subject and file set. Stop on unexplained changes.
6. Load the current official task title/definition from docs/90-tasks.rtf, excluding the trailing phase summary. Do not fabricate more detailed acceptance semantics from a title; derive minimum scope from existing architecture and checkpoints and stop on genuine unresolved decisions.
7. Execute the full protocol lifecycle: one analysis, owner gate, implementation, focused tests, impacted regressions, final audit, checkpoint, explicit staging, one commit, normal push, post-push verification.
8. Include state and queue changes with the accepted task/checkpoint before its commit; verify state after push without a dirty bookkeeping follow-up. The protocol's symbolic HEAD convention avoids a self-referential hash. Record current task completion and next not-started task. Reset the new invocation's counter in memory; stop after three finalized tasks.
9. Stop on protocol conditions and report either the owner decision/blocker or batch completion. Never start the next task before the previous task is pushed and verified.

Use .\.venv\Scripts\python.exe -B for all Python/test commands. Disposable tests only; never print secrets. Request exact platform Git/network approval when required.

## Bootstrap dry-run boundary

Read and validate these files, resolve Task 50 — Customer → Asset Integration, confirm three-task capacity and timezone carry-forward, then stop **before Task 50 analysis or implementation**. No task counter increment occurs.

## Recovery

If interrupted, inspect actual Git/state/checkpoint evidence before resuming the current stage. A committed-but-unpushed accepted task must be verified and finalized before continuing; no duplicate task commit. Unexplained divergence or unaccepted changes require a stop, not reset or history rewriting.
