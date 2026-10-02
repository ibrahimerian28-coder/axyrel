# Frontend v1 Phase 2 checkpoint

Owner authorization: Phase 2 approved-design implementation, supplied in the attached owner request. Base: 5718054c9ddf34676ee37723ba6d5fe8e2b5ce61. Branch: frontend/v1. Separate frontend phase; Tasks 1–90 acceptance is unchanged.

## Implemented scope

Dashboard consumes accepted tenant-scoped APIs for customer/assets counts, work-order information, visits/schedules, low-stock information and backend-calculated profitability. No fabricated trends or frontend accounting calculations.

Customers and Assets provide searchable/filterable lists, status presentation, supported create/edit forms and split detail profiles. Stored relationships expose customer assets, history, requests, work orders and invoices where authorized. Customer ↔ Asset navigation and customer-context asset creation are functional. Other related destinations retain explicitly labelled later-phase placeholders; those domains are not implemented here. Technician labels use the accepted Phase 1 directory. Business labels do not display UUIDs; internal URLs/API references may contain IDs.

Phone actions require interaction. Call uses the device handler, Copy uses the clipboard, and WhatsApp is offered only for an explicitly international number; no country-code inference. Asset customer contact/location context is labelled as customer information.

Shared headers, KPI cards, badges, tables, tabs, forms and states follow the preserved navy/teal references. Desktop and phone layouts and logical RTL styling remain supported. Streamlit remains intact.

## Visual adaptations and capability boundaries

The images are visual references, not schema authorization. Unsupported asset photos/documents/filter-stage entities, asset maintenance cycles/next-service calculations and bulk import are omitted. Customer legacy device/cycle fields remain explicitly customer fields. Existing customer location URLs are linked without introducing asset geolocation persistence. Unsupported historical charts, percentages/comparisons and follow-up classification are not invented. Profitability is labelled all-time rather than falsely claiming an unsupported month-to-date comparison. The exact official logo is displayed proportionally and unchanged, rather than using a different embedded mockup logo.

No new backend capability, schema change or business-policy decision was required. No backend, migration, autonomous state, historical acceptance documentation or dependency lockfile changed. Directory permission and backend validation remain authoritative; unavailable related references are labelled unavailable rather than fabricated.

## Validation evidence

- Real accepted FastAPI / production-built Next integration: 4/4 Chromium journeys passed (33.7 seconds), covering Dashboard API loading; Customers/Assets list/detail/create/edit; stored history/assets; customer-context asset creation; linked navigation; phone actions; human-readable labels; desktop/phone rendering; technician read-only presentation; RTL; empty and backend-error states.
- Focused affected-layout verification after financial-card wrapping fix: 1/1 passed (18.0 seconds), covering desktop Dashboard and all three phone-width screens.
- Foundation/session regressions: 5/5 passed (11.1 seconds), covering login/logout, cookies/session cleanup, incorrect credentials, unauthenticated access, exact-origin mutation protection, permissions, safe forwarding, mobile/RTL/keyboard and shared states.
- Final lint and TypeScript checks passed. Production build passed after final UI changes.
- Installed required dependency versions resolved; no new dependency or lockfile change. Existing optional WASM packages reported as extraneous are not required dependency failures.
- Original logo and all three reference-image SHA256 values match the preserved manifest. Logo: CEA11E0B0A7843DD5D03F6A2449564DFEE560C18E457F635F202B988EDEBE1E3.
- Screenshots inspected for Dashboard, Customers and Assets at desktop/phone sizes. Fixed a table-caption CSS utility collision and financial KPI text overflow. An initial browser-test failure was an overly strict select-label locator; corrected the test locator and verified the actual preselected customer relationship.

The integration harness uses actual FastAPI with an isolated disposable SQLite database and synthetic identities/records, with explicit test environment and no repository .env loading. This is UI/API validation, not a new PostgreSQL migration/deployment claim. Existing accepted PostgreSQL evidence is unchanged. Phone links are checked without contacting external services. No production system, real business data or production secret was used.

## Owner review and final Git procedure

Exact safe local review commands and synthetic credentials are in README.md. Stop both processes with Ctrl+C after review.

This document is included in the independent Phase 2 checkpoint commit. After committing, push only frontend/v1 and compare local HEAD, tracking branch and actual remote; verify a clean working tree. Main remote baseline remains e8accb377e6f0c32cc919463466ae9ba97995c06 and historical checkpoint branch remains 649a0ba3893c9cfa9d7b3cbfdd89673fde7736c3. There is no local main branch; verify origin/main and the actual remote main without creating one. Report concrete commit/remote evidence in the completion response. Stop after Phase 2; no Phase 3 implementation is authorized by this checkpoint.
