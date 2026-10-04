# AXYREL FRONTEND v1 - MVP IMPLEMENTATION AND VALIDATION REPORT

Accepted Phase 3 baseline: `4a17609a2049afdb97f13d7d78385b4c22d1c416`.
Functional implementation checkpoint: `ad77e7facdfee8e1b6b076f526eddfd77d696c06`, pushed and remote-verified on frontend/v1. The delivery checkpoint adds the persistent review launcher, safety tests and this documentation; its exact SHA is supplied in the final delivery response.

## Completed modules

- Inventory: supported item create/edit/delete; existing IN/OUT/ADJUSTMENT transaction creation and readable references. Transactions remain a record-only ledger and do not silently mutate warehouse quantities.
- Technician Stock: readable inventory/technician selection through the approved directory; supported direct creation and quantity adjustment. No warehouse-to-technician transfer or unsupported delete was invented.
- Invoices: supported create/edit/delete, customer and optional Work Order selection/navigation, dates, status and financial fields. Blank create total delegates calculation to the backend. Existing PATCH total semantics are preserved; no alternative financial calculation or payment processing was added.
- Expenses and Profitability: supported expense CRUD, search/category/status/date filters, authoritative backend summary and expense-category totals. Only the backend's Active-expense semantics determine profitability.
- Reports: backend financial summary/category visualization and real current Work Order status distribution with linked records. No synthetic historical trends, percentages or comparisons.
- Asset Import: working CSV upload, template, preview, structured row/column errors, downloadable JSON error report, explicit confirmation, atomic commit and safe retry after an uncertain response. Successful completion refreshes the actual Asset list.
- Integration: existing navy/teal shell, responsive 390px layouts, logical RTL styles, readable links, loading/error/empty/permission states and accessible labeled inputs/actions. No Store/Catalog primary module. Phase 2 images/contact actions and Phase 3 service navigation retained.

## Narrow Asset Import backend additions

GET `/api/v1/assets/import/template`, POST `/api/v1/assets/import/validate`, POST `/api/v1/assets/import/commit`; exact routes allowlisted by the authenticated same-origin frontend proxy. CSV is carried as bounded UTF-8 text in JSON. Limit: 1 MiB CSV, 1,000 rows, 7 MiB bounded streamed JSON envelope. Only existing Asset fields and a tenant-local displayed Customer reference are allowed; strict headers, column counts, field lengths, dates and existing schema validation produce structured errors. Import requires asset:manage and customer:read.

Serial comparison trims surrounding Unicode whitespace only, remains case-sensitive, and does not case-fold or Unicode-normalize. Original nonblank stored serial text is preserved; empty input follows the existing optional-field convention. Blank/whitespace-only serials may repeat. Nonblank duplicates in the file or any existing same-tenant Asset, including soft-deleted Assets, are rejected; the same serial in another tenant is allowed. No overwrite/upsert, cross-tenant uniqueness or new single-Asset CRUD serial rule was introduced.

A signed tenant/user/checksum-bound preview expires after 15 minutes. Commit revalidates current data, locks resolved Customer rows against deletion races, and uses a tenant-scoped PostgreSQL transaction advisory lock shared with Asset repository create/update/delete. Existing display-ID allocation therefore runs under the same lock. Assets and a deterministic UUID-keyed AuditLog receipt commit in one transaction; failures roll back all rows. The existing receipt is tenant/actor/action scoped and persists only checksum/result metadata, not CSV contents. Retrying the same key returns the committed result, including after preview expiry; mismatched content is rejected. No schema migration, generic import framework or unrelated backend refactoring.

PostgreSQL lock behavior: https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS . Guarantees apply to authorized API/repository writers; direct out-of-band SQL does not participate in the advisory-lock protocol.

## Validation results

All suites used synthetic isolated data; existing tests were not weakened.

| Check | Result |
| --- | --- |
| Asset CSV backend: success, permissions, tenant isolation, malformed/oversized input, references, serial rules, expiry/revalidation, rollback, retry and concurrent allocation/import | 12 passed, 11.146s |
| Relevant existing backend/API regressions (inventory, billing, expenses/profitability, ledger, PostgreSQL repositories, tenant isolation and Phase 2 images) | 97 passed, 353.853s |
| Existing Phase 3 backend/API service-flow suite | 94 passed, 169.368s |
| New MVP browser workflows, actual PostgreSQL/FastAPI | 5 passed, 40.8s |
| Phase 2 browser regression | 7 passed, 53.8s |
| Phase 3 browser regression | 4 passed, 1.1m |
| Foundation browser regression | 5 passed, 12.6s |
| Persistent owner-review login/navigation/mobile/logout | 1 passed, 5.0s (final restart check) |
| Owner-review identity/non-destructive initialization safety | 5 passed, 0.062s (final run) |
| Persistent Customer/Asset records and private image hashes across independent application processes | 2 successful write/read/cleanup runs |
| Typecheck, lint, production build, git diff whitespace check | Passed |

Browser checks covered desktop and 390px mobile, RTL overflow/layout, related-entity navigation, status/quantity persistence after reload, real report values, failed-network import retry without duplication, structured preview/commit errors, forbidden technician mutations, foreign-tenant inaccessible records and API error presentation. Existing Phase 2 suites cover image upload/display/replace/remove/fallback and compact official WhatsApp/contact actions. Existing Phase 3 suites cover Request -> Work Order -> Schedule -> Visit -> authoritative History and inventory integration. Backend suite counts overlap; they are not a unique-test total. The intentional injected import failure logs an exception while the rollback test passes.

Official logo SHA256 remains `CEA11E0B0A7843DD5D03F6A2449564DFEE560C18E457F635F202B988EDEBE1E3`. Its bytes were not modified. Main remains `e8accb377e6f0c32cc919463466ae9ba97995c06`. Streamlit files, backend model/schema definitions and migration history were untouched. No production data/deployment, force push, destructive Git operation or main merge. Explicit staging only; the pre-existing generated next-env.d.ts change is excluded.

## Known limitations and persistent review

Existing unpaginated collection APIs supply client-side list filters. Technician stock supports direct backend adjustment, not a warehouse transfer workflow. Invoice PATCH preserves existing stored totals unless explicitly changed. No unsupported invoice line-item/PDF/payment feature was invented. Charts show current supported data, not unavailable historical series. CSV imports are create-only with strict template fields; image import and arbitrary column mapping are outside scope. The browser retains an uncertain import's retry key while its component remains open; durable server receipts make repeats of that key safe. PostgreSQL remains authoritative; SQLite tests cannot establish its locking guarantees.

Persistent review uses a newly identified local PostgreSQL database and private disk images, not disposable fixtures or an unknown application database. Existing migrations were validated/applied only to that new database. Identity mismatches and occupied ports fail safely. See [OWNER_REVIEW.md](OWNER_REVIEW.md) for the exact launch command, private credentials location, PostgreSQL prerequisite and restart behavior. Application-process persistence was validated; a physical PC reboot was not performed. Back up the database and private image/configuration directory together.
