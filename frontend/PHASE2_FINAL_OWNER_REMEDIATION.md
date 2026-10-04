# AXYREL FRONTEND v1 — PHASE 2 FINAL OWNER REMEDIATION REPORT

Owner authorization: final Phase 2 remediation request, limited to frontend/v1. Base checkpoint: f2a5bc6a56ca8d3ab3e528f5c70707332130e487. No Phase 3, main merge, Asset Import implementation, production access or real business data.

## Exact implementation

- WhatsApp uses the unmodified `siWhatsapp.path` from pinned Simple Icons 16.33.0, imported through the package with TypeScript support. One new dependency, no transitive dependencies added. Source: https://github.com/simple-icons/simple-icons. No manual brand approximation remains. Customer and Asset customer-contact actions share this renderer. Existing adjacent 44px Call/WhatsApp/Copy buttons, focus/hover behavior, click-only URLs, noopener/noreferrer and explicit international-number requirement remain. Both available and unavailable WhatsApp controls have the exact label/tooltip “WhatsApp”; the unavailable control remains non-navigating with explanatory text.
- Existing Customer and Asset detail profiles now include one optional image, file preview before save, cancel preview, upload/replace, explicit remove, status/error feedback and Customer initials / Asset avatar fallback. Viewers see the image/fallback with no mutation controls. No new image requirement was added to Customer/Asset create forms.
- Shared same-origin private image forwarding supports binary upload and display using the existing HttpOnly session. Blob URLs are local display URLs created only after an authorized fetch and revoked on cleanup; they are not public server URLs.
- Dashboard retains the service-status chart and adds Installed Asset Mix. Navy/teal styling and desktop/390px layouts remain. Official Axyrel logo is unchanged.

## Image-storage architecture

`backend/services/profile_images.py` defines an ImageStorage protocol (`read`, atomic `replace`, `remove`) and PrivateLocalImageStorage. Keys derive exclusively from the authenticated company, Customer/Asset resource and existing record UUID; each key holds exactly one normalized WebP. Clients receive only processed image bytes or safe errors, never keys/filesystem paths.

Local storage uses server-only AXYREL_PRIVATE_IMAGE_ROOT, default `.private-images` outside frontend public assets, ignored by Git. Configure a directory outside all web/static roots and restrict it to the backend service account with OS permissions/Windows ACLs. Temporary output is flushed and atomically renamed; failures preserve the prior image and remove the temporary file. Reads are bounded. Explicit image removal deletes the object. Existing soft-deletion semantics stay intact: deleted records cannot access the image through the API, while their object remains retained with the soft-deleted record pending a reviewed purge policy.

The adapter factory can later select private S3-compatible storage without changing Customer/Asset business logic, keys, API or frontend. An S3 adapter must preserve atomic same-key replacement, bounded reads and deletion; bucket credentials/configuration remain server-only. No signed public image URLs are introduced. Local storage needs persistent disk and backup together with the database; ephemeral deployments need a persistent/object-storage adapter.

Input is bounded to 5 * 1024 * 1024 bytes at both frontend proxy and API stream. Pillow >=12.3,<13 verifies actual JPEG/PNG/WebP content and matching MIME, rejects SVG/unsupported formats, corruption/truncation, animated input, dimensions over 4096px or 16 MP, and decompression-bomb warnings/errors. It decodes, applies orientation, scales within 1024px and creates a fresh pixel-only image before WebP encoding. EXIF/GPS, ICC, XMP and ancillary metadata are not copied; original files and filenames are not stored. CPU processing runs outside the event loop with a two-job concurrency limit.

## API and migration changes

GET /api/v1/customers/{record_id}/image and GET /api/v1/assets/{record_id}/image return image/webp with private/no-store and nosniff headers; absent images return 404. PUT accepts the raw image body with its matching Content-Type and returns 204 after validation/atomic replacement. DELETE returns 204 and is idempotent for an existing record without an image. Invalid MIME returns 415, invalid actual content 422, oversized input 413.

Reads use the existing customer:read / asset:read permission; writes use customer:manage / asset:manage. Every operation uses the existing tenant-scoped non-deleted record lookup before accessing storage. Foreign or deleted records return 404. Tenant headers/query values cannot override authenticated scope. The Next proxy allowlists only Customer/Asset image paths and GET/PUT/DELETE; mutations require exact Origin, authentication remains server-side, upstream redirects are refused, and errors are safely forwarded.

No schema/migration was necessary: the one-image key derives from already-persisted identity, the normalized representation is fixed, and filesystem/object storage supplies existence. No migration SQL, ORM model or existing ledger runner changed. No ledger execution/baseline operation was performed. Existing Customer/Asset CRUD, relationships, status policies and authorization definitions remain unchanged.

## Dashboard data and reference adaptation

Service Activity groups actual records from existing GET work-orders and GET service-visits by their actual statuses, with separate counts/bars and an accessible exact-count table. Installed Asset Mix groups actual GET assets records by asset_type, likewise with exact counts and an accessible table. Both render real bars when records exist and informative empty states only when their respective data is empty. No additional analytics API was added.

The approved reference's seven-day stacked activity graph and prior-period KPI comparisons cannot truthfully be reconstructed: the APIs expose current records/statuses, not daily historical status snapshots or a historical aggregation contract. Creation/event fields do not establish past status totals. The all-time profitability summary also does not provide the reference's month-to-date/prior-month comparison. This implementation shows current distributions and retains explicitly all-time financial labels; it does not fabricate dates, percentages, growth or history. Synthetic review data includes a persisted Planned visit to exercise the real service-visits API series.

## Deferred approved capability

Import Assets is recorded as approved future Frontend v1 scope. Implementation must use the previously proposed bounded CSV template/preview, authoritative row/column validation and error report, tenant-safe customer resolution, reviewed duplicate policy, revalidation and idempotent atomic commit in PHASE2_OWNER_REMEDIATION.md. No Import button or bulk-import API was added here.

## Validation

All backend/API and browser data is synthetic/disposable. The image API harness changes working directory to a temporary directory before importing backend settings, overrides storage to a temporary directory, and uses an isolated SQLite database; no workspace .env or production database is used for the image suite. These tests are not a new PostgreSQL migration/deployment claim.

- Image backend/API suite: 8/8 passed, final run 90.300s. Covers both resources, JPEG/PNG/WebP, absent-image behavior, upload/display/replacement/removal, normalized output size, metadata stripping, invalid MIME/content/truncation/animation/dimensions, oversized streaming without Content-Length, anonymous and read-only denial, authorized viewer reads, tenant header/query forgery, deleted records, live role revocation, path traversal refusal, atomic write failure preservation/cleanup, bounded stored reads and safe error responses.
- Existing Customer/Asset integration regression suite: 19/19 passed, 18.639s. Accepted CRUD, relationship validation, tenant boundaries, permissions and soft-deletion behavior are unchanged.
- Full Phase 2 production-Next/real-FastAPI browser suite: 7/7 passed (runner reported 1.4m). Covers image lifecycle at desktop/390px, preview cancellation/reload, fallback, server invalid-content feedback, client/proxy oversize rejection, same-origin protection, read-only behavior, exact packaged WhatsApp path, contact/clipboard safeguards, Customer/Asset CRUD and navigation, dashboard data/charts, mobile/RTL and backend errors.
- Foundation browser regression: 5/5 passed, 16.8s. Sessions, login/logout, origin/forwarding protection, permissions, keyboard/mobile/RTL and logo checks.
- After final bounded-storage-read and image-fetch cleanup refinements, focused image browser tests passed 2/2 (33.7s); type-check, lint and production build passed.
- Type-check, ESLint and production Next build passed after final application changes. Git whitespace check passed. Desktop and 390px screenshots inspected for Customer/Asset images/contact controls and both Dashboard charts. Tables/tabs retain local scrolling without document overflow.
- Initial new browser failures were ambiguous test record locators; corrected to match only the record-name button. A later logout assertion raced asynchronous sign-out; corrected to await the login page before checking denied access. No unresolved failure is accepted as passing.
- Dependency audit: the new Simple Icons package is not flagged; full audit reports five pre-existing high findings in the ESLint development dependency chain. No unrelated dependency downgrade/force fix was applied. Production-only audit passed with zero reported vulnerabilities.

Official-logo SHA256 remains CEA11E0B0A7843DD5D03F6A2449564DFEE560C18E457F635F202B988EDEBE1E3. Migration/model/ledger paths have no Git diff from the base checkpoint. Remote main baseline remains e8accb377e6f0c32cc919463466ae9ba97995c06.

This report is included in the dedicated checkpoint; its commit hash and actual remote verification are supplied in the final delivery response. Stop after this checkpoint. Phase 3 and main merge remain outside authorization.
