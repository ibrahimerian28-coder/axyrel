# AXYREL FRONTEND v1 — PHASE 1 COMPLETION CHECKPOINT

Separate owner-approved Phase 1 Foundation, not Task 91. Base: 649a0ba3893c9cfa9d7b3cbfdd89673fde7736c3, verified clean before work. Dedicated branch frontend/v1 created before modifications. Status at creation: accepted locally, pending independent commit/push/actual remote verification. Final delivery supplies the exact commit hash; this artifact uses HEAD to avoid rewriting its own commit.

Delivered: exact pinned Next/React/TypeScript/Tailwind project and npm lockfile; byte-preserved official logo and all three references with hash manifest; shared navy/teal tokens; login and responsive shell/navigation; typed API/session forwarding and React Query; loading/error/empty/permission states; logical RTL/LTR structure and English string foundation; Chromium harness using the production build with loopback synthetic API. Domain navigation is explicitly marked later-phase: no Dashboard, Customers or Assets implementation. No general Users/Settings/Store or unsupported mockup features.

Only backend extension: read-only technician directory plus router registration. Identity mapping established by accepted Task46 fixture using technician User.id on WorkOrder and Task55 stock carry-forward. No FK or tighter assignment policy added; standalone unknown/inactive IDs are not fabricated into named identities. Existing service:read guard and authenticated company boundary; active technician Users only, minimal id/display_name, no email/password exposure, no writes, schema or authorization changes.

| Required acceptance | Evidence |
|---|---|
| Dependency install/resolution | npm install --ignore-scripts completed; npm ls --all and exact direct-pin/lock comparison passed |
| Typecheck / lint | Passed; initial single PostCSS export-style warning corrected and final checks clean |
| Production build | Passed after origin correction; compiled/static pages and dynamic adapters generated |
| Focused browser tests | 5/5 PASS against built Next + synthetic loopback API, 10.9 seconds |
| Directory and auth regression | 13/13 PASS, disposable synthetic SQLite; 3 new directory checks plus 10 inherited auth checks |
| Official logo / three references | All four SHA256 values match original manifest |
| Historical business/schema/auth semantics | Existing paths unchanged except approved router registration/new read-only directory |
| Historical task governance | Tasks 1–90 decisions/queue/state and migrations unchanged |

Initial browser run found genuine frontend origin comparison defect: internal Next request hostname differed from browser Host. Corrected using explicit public origin or local Host/protocol, retaining exact Origin/CSRF validation and not trusting forwarded headers. Scoped alert selectors exclude Next's accessibility announcer. Rebuilt and all five affected scenarios passed. Initial sandbox registry/cache EACCES and test-server teardown restrictions required authorized escalated installation/browser execution; no security rule was weakened. npm's installed ESLint 9.39.1 deprecation notice and NO_COLOR/FORCE_COLOR test notices are non-blocking tool warnings. No claim of cross-browser, real production or complete domain parity.

UI proof covers team login, HttpOnly/SameSite session with no localStorage token, logout/account cache clearing, role navigation, proportional original logo, desktop/mobile/RTL, keyboard entry, placeholder empty state, loading/error/retry/permission states, origin rejection, no arbitrary proxy path, and preserved backend 403. Production HTTPS/host/proxy/operational approval remains future-only; no production server/data/secrets are accessed. Existing Streamlit is retained. No old suites are blindly repeated.

Finalization requires exact scoped stage, independent commit/push to frontend/v1, local HEAD/tracking/actual remote equality and clean tree. Remote main must remain e8accb377e6f0c32cc919463466ae9ba97995c06 and historical checkpoint/pre-gemini-task46 must remain 649a0ba3893c9cfa9d7b3cbfdd89673fde7736c3. These post-push results are confirmed in final delivery, not pre-claimed here. No main merge/force/history rewrite. STOP after report; Phase 2 requires a separate owner instruction.
