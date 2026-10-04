# AXYREL FRONTEND v1 — PHASE 2 OWNER REVIEW REMEDIATION REPORT

## Completed UI corrections

- Shared Customer/Asset contact actions now use adjacent 44px icon controls: handset, WhatsApp speech-bubble/handset, overlapping documents. Accessible names, native title tooltips, keyboard interaction, hover and focus styles are provided. Non-international numbers retain a focusable, explicitly unavailable WhatsApp control and explanatory text; no external URL or inferred country code is offered. Clipboard success/failure announcements and original number copying remain intact. Call and external-link safeguards are preserved.
- Add Asset for Customer uses established teal primary styling and a device/plus icon, retaining the preselected customer and existing permission check.
- Dashboard restores a prominent two-column Service Activity visualization using current work-order/service-visit API records grouped by their actual status. Exact counts have an accessible table. No dates, trends, percentages or comparisons are invented; no records yields an empty state. Existing backend summary KPIs remain unchanged.
- Removed visible Frontend v1 labels and browser-title version branding. Sidebar container uses the official image's dark navy surroundings as a continuous navigation surface; the original image is displayed fully and proportionally without filters or transformations.
- No decorative Import button, image persistence, database/backend changes or Phase 3 implementation.

## Customer image proposal - review required

Minimum: one optional image per customer, with initials fallback, preview, explicit upload/replace/remove and accessible alternative text. Reuse customer read/manage authorization and enforce tenant ownership on every upload, read and delete. Use private object storage with server-generated keys; never trust filenames or accept arbitrary image URLs. Server must limit request bytes (proposed 5 MB), decoded dimensions/pixels (proposed 4096px / 16 MP), verify signatures and decode JPEG/PNG/WebP, reject SVG/animated formats, strip EXIF/location metadata and re-encode a bounded thumbnail. Apply limits before expensive decoding. Return field-level validation errors and retain the old image until replacement succeeds.

Required later backend work: reviewed image metadata persistence linked to customer/company (object key, MIME, dimensions, size, checksum), private storage configuration, authenticated multipart PUT/DELETE and read or short-lived signed-image access, cleanup for replacement/deletion/failure, audit and isolation tests. Frontend needs upload progress, error/retry, fallback, cache refresh, and a same-origin authenticated image proxy if bearer authentication cannot be used by an img element. No base64 database blobs or public buckets. Storage retention, file limits and deletion policy need owner review before implementation.

## Asset/device image proposal - review required

Minimum: one optional representative image per asset; gallery/documents are outside this minimum. Same private storage, validation, metadata stripping, tenant checks, replacement safety and cleanup as Customer images, scoped to asset read/manage permission and the actual asset/company relationship. Frontend needs device fallback, preview, upload/replace/remove, useful alternative text and read-only behavior for viewers. Required later APIs and reviewed metadata persistence mirror Customer images under the asset resource. Never inherit an image from another tenant or silently treat a customer avatar as a device photo.

## Asset CSV import proposal - review required

Minimum: a functional Import Assets action opening template download, file selection, column mapping/preview, server validation, error report and explicit commit confirmation. Initially create-only; no upsert, deletion or silent duplicate overwrites. Proposed bounded UTF-8 CSV: 1 MB/1000 rows, strict header allowlist, deterministic encoding/delimiter handling and parser limits. Template uses existing supported AssetCreate fields plus a tenant-local customer display reference resolved by the server; never match customer by ambiguous name or accept company_id/display_id overrides.

Backend requires asset:manage and customer-read/tenant ownership checks, shared existing asset validation, required customer/asset type, field length/type checks, ISO dates, allowed statuses and reviewed warranty/date rules. Validate customer existence in the current tenant and report row/column/code/message errors; detect duplicates within the file and against existing records according to an owner-approved serial-number policy (do not assume global uniqueness). Return row totals and structured downloadable errors, neutralizing spreadsheet formula prefixes in exported reports.

Proposed two-stage POST assets/import/validate then POST assets/import/commit: short-lived tenant/user-bound validated upload token and content checksum, revalidate at commit, idempotency key, transactional all-or-nothing creation for this bounded initial workflow, atomic existing display-ID allocation, race-safe duplicate enforcement after policy approval, audit record, expiry/cleanup, and clear created/rejected counts. No partial writes on failure. Frontend preserves preview/errors, disables commit while errors remain, prevents repeat submits and refreshes assets after success. Required later backend capabilities include CSV parser/service, template/validation/commit contracts, authorization, limits, idempotency/audit persistence and possibly reviewed uniqueness constraints; schema/storage decisions require review. Existing single-record POST is insufficient for safe atomic bulk import.

## Validation and checkpoint

- Final TypeScript check, ESLint, production Next build and git diff whitespace check passed.
- Real FastAPI / production Next browser suite: 5/5 passed (38.6 seconds), including API data, exact chart counts, empty chart, Customer/Asset CRUD, linked customer asset creation, filters, phone URLs, keyboard copy, tooltip/accessible names, 44px targets, clipboard success/failure, unavailable international number, permissions, errors, phone layouts and RTL.
- Foundation browser suite: 5/5 passed (15.0 seconds), including sessions, origin protection, forwarding, permissions, keyboard/mobile/RTL and logo checks.
- Desktop and 390px phone screenshots inspected for Dashboard, Customers and Assets. Final chart and continuous full-width logo container also inspected after layout adjustments. No viewport overflow; tables/tabs retain local horizontal scrolling.
- Initial test launch found the owner's review API already occupying 8110; isolated test ports now use 8120/3120 with configurable API harness port. Initial sandboxed runners passed their assertions but hung in Windows server teardown; approved cleanup and final rerun outside the sandbox exited normally. Existing owner review processes were preserved.
- Original logo hash verified unchanged; no official logo bytes, backend code/schema, production data or Phase 3 screens changed.

Commit and actual remote verification are supplied in the final delivery report (the report file is part of that commit). Baseline remote main: e8accb377e6f0c32cc919463466ae9ba97995c06. Original official-logo SHA256: CEA11E0B0A7843DD5D03F6A2449564DFEE560C18E457F635F202B988EDEBE1E3. Dedicated checkpoint is restricted to frontend/v1. Stop after remediation; Phase 3 is not authorized.
