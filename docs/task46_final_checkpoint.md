# Task 46 — Final Accepted Checkpoint

- Status: **ACCEPTED** by the project owner.
- Acceptance date: **2026-10-02**.
- Branch: `checkpoint/pre-gemini-task46`.
- Accepted code commit: `3bbc565f419a7c5081e060979a44e747fb8a1b43`.

This checkpoint records previously verified results and the owner's acceptance
and scope decision. Tests were not rerun for this documentation update.

## Automated evidence

| Verification | Result |
|---|---|
| Authentication / Security | 10/10 PASS |
| Service Visit integration / regression | 6/6 PASS |
| Total | 16/16 PASS |
| Code `git diff --check` | PASS |
| Final complete diff review | READY FOR COMMIT; no blockers |

The accepted code commit was created and pushed to the checkpoint branch before
this documentation update. Its working tree was clean at acceptance.

## Fixed and verified

- **D46-01:** A non-cancelled Service Visit cannot be reassigned to a Cancelled Work Order.
- **D46-02:** Cancellation restores installed inventory to the original technician even after the visit is reassigned.
- **Generic inventory reference integrity:** `SERVICE_VISIT_INSTALL` and `SERVICE_VISIT_REVERSAL` are reserved from the generic transaction writer; case and surrounding whitespace cannot bypass validation. Rejection returns HTTP 400, and the integrity regression leaves technician stock at zero.
- **Reference persistence:** Generic transaction UUID `reference_id` values are converted to canonical strings for the existing String ORM field.

## Manual evidence

| Verification | Result |
|---|---|
| Streamlit application startup | PASS |
| FastAPI startup | PASS |
| Login | PASS |
| Work Order creation | PASS |
| Service Visit creation and Work Order linking | PASS |
| Planned → In Progress | PASS |
| Service Visit → Work Order status synchronization | PASS |
| Work Order cancellation → linked Service Visit cancellation | PASS |
| Completed → Cancelled Service Visit | PASS |
| Related Work Order cancellation synchronization | PASS |

## D46-03 — Owner scope decision

**CLOSED BY OWNER SCOPE DECISION**, dated **2026-10-02**, without a code fix.

Runtime verification confirmed that API-disabled mode stops without presenting
legacy login. Requirement reconciliation found conflicting legacy compatibility
wording and classified it as ambiguous pending owner decision.

The owner explicitly approved API-backed mode as the official and only required
operating mode of the current Axyrel MVP. Operational legacy Streamlit
authentication and legacy persistence fallback are not Task 46 acceptance
requirements. Do not reconstruct, restore, or invent legacy authentication.

Older Task 43/45/46 wording requiring operational legacy authentication or
fallback is transitional/stale wherever it conflicts with this decision and the
approved Streamlit → FastAPI → service/repository → PostgreSQL architecture.

## Non-blocking observations

- After cross-entity synchronization, a Streamlit status dropdown can retain its previous value until refresh. Persisted statuses and refreshed displays are correct; this is a UI state observation, not a backend/data correctness failure.
- The technician-stock workflow could not be manually exercised because the local database had no active technician or stock records, and technician provisioning UI/API and a Maintenance technician selector are outside the current acceptance scope. Automated integration tests verified installation deduction, cancellation restoration, original-owner restoration after reassignment, and reserved-reference integrity.

## Governance and next task

Design Freeze remained intact: no schema, ERD, migration, entity, or architecture
change was introduced by the Task 46 corrections. This checkpoint update changes
documentation only; production code, tests, and database records are unchanged.

**Task 47 has NOT started.** The next planned task is **Task 47 — Move Remaining
Business Logic out of UI**, subject to owner approval before execution. No merge
to main is authorized by this checkpoint documentation.
