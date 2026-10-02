# Task 89 — Synthetic First-Use / User-Acceptance Rehearsal

Date: 2026-10-03. Authority: OD-29. **LOCAL SYNTHETIC FIRST-USE / USER-ACCEPTANCE REHEARSAL PASSED.** No real customer/employee/business usage, onboarding, adoption, deployment or operational acceptance is claimed.

## Journeys and results

New focused AppTest first-use case uses an initially empty migrated disposable PostgreSQL database, one literal synthetic company/admin and actual production-mode loopback API. No dependency override or mocked UI/API/database rules. The accepted relative logo asset is copied into the isolated temporary directory; application code is unchanged.

| First-use action | Result |
|---|---|
| Log in through existing Streamlit form | Synthetic admin authenticated against actual API/PostgreSQL |
| Navigate Dashboard, Customers, Maintenance, Inventory, Expenses, Invoices, Profitability and Store | All eight render without app exception/API error, both initially and after entries |
| Submit blank Customer, then valid name | Existing Name is required refusal; exactly one valid Customer persists |
| Create Work Order and record Visit through existing Maintenance forms | Exactly one Order and one Visit persist; no invented UI workflow |
| Add inventory item quantity 3, cost 2.50 | Exactly one item; accepted stock valuation 7.50 |
| Create invoice subtotal 10, discount 1, tax 2, paid amount 3 | Exactly one Draft invoice, computed total 11; supplied Draft state preserved |
| Record expense amount 2 and view Profitability | Exactly one expense; Draft revenue excluded, expenses 2 and net profit -2 |
| Log out, log in again, revisit Customer/Inventory | Authentication state reset/restored; persisted counts remain one |
| Read explicit Notification/Audit APIs | Both empty; no unapproved automatic events generated |
| Complete orderly server shutdown | Normal process exit; migration ledger unchanged |

Evidence: tests/test_task89_first_use.py, **1/1 PASS**, initial run. Parent HTTP independently verifies stored records and literal summary totals. This is one integrated case with the listed stages, not a claim of separate tests per stage. No usability/operational blocker or approved-MVP defect found; no correction required. No broad accepted suite reruns.

## Reused accepted journeys

[Task 80](task80_final_checkpoint.md) and [Task 87](task87_final_checkpoint.md) already establish Customer/Asset/Request/Order/Schedule/Visit completion/explicit History, billing/expense/reporting, tenant denial and restart persistence using accepted explicit relationships. Task 87 exercises actual production-mode local HTTP/DB and UI login. [Task 84](task84_final_checkpoint.md) establishes stock/movement/rollback/valuation; [Task 58](task58_final_checkpoint.md) verifies explicit Notification read/unread and immutable Audit flows. These were not rerun merely to recreate evidence.

The new rehearsal stays within the existing UI. Asset/scheduling/history and explicit Notification/Audit flows rely on their accepted API evidence; no new screen or UX requirement is inferred. Store remains the existing inventory catalog, not customer checkout. [Task 88 handoff](task88_mvp_owner_handoff.md) documents frozen scope and deferred non-MVP items.

## Limits and actual first-use prerequisites

This is automated AppTest/API rehearsal by the agent with literal synthetic identities/data, not feedback or approval from real users or a public browser/mobile/production usability certification. No actual Healthy Water/customer/business data, production DB/infrastructure/credentials or external customer system was accessed. Existing bare-mode/deprecation warnings are not review blockers. No new features, role/security/accounting/tenant policy or source mappings. Startup checks and tracked migration safeguards remain in force.

Actual first real-world usage remains owner-controlled after explicit production deployment approval: approve actual target/security/access, deployment and live smoke, operational backup/recovery, participant/onboarding/role/data boundaries and acceptance criteria. Real source/tenant/ID/reference/duplicate/invalid-row policies, including Expenses mapping, remain unresolved where applicable; no automatic baseline or production-data change. Use secure credential delivery, not chat/Git. Approval of synthetic first-use does not authorize customer contact, account provisioning or real operational writes.

Reproduce only on approved disposable local infrastructure with:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_task89_first_use.py
```

The harness retains Task 86's local-host/name guards, temporary working directory without workspace .env, synthetic production config and connection/process cleanup before generated database removal.
